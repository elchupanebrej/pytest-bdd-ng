"""Provide live formatter runtime helpers."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess  # noqa: S404
import sys
import tempfile
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from threading import Thread
from typing import IO, TYPE_CHECKING, Protocol, cast

import pytest
from filelock import FileLock

from pytest_bdd.compatibility.pytest import get_config_root_path
from pytest_bdd.model.cucumber_formatter_adapter import normalize_formatter_envelope_dicts
from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_serialization import MessageSerializationProfile
from pytest_bdd.plugin.gherkin_message_reporter.html_report import render_html_report_content
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase
from pytest_bdd.plugin.gherkin_message_reporter.session import (
    CucumberFormatterRenderResult,
    CucumberFormatterRequest,
    NodePackageProvisionResult,
    format_requested_cucumber_formatter_labels,
    render_live_formatter_runtime_assets,
)
from pytest_bdd.plugin.gherkin_message_reporter.stream_relay import relay_live_formatter_output
from pytest_bdd.util.npm_resource import find_resource

if TYPE_CHECKING:
    from collections.abc import Mapping

    from cucumber_messages import Envelope as Message

    from pytest_bdd.types.json import JSONArray, JSONObject

logger = logging.getLogger(__name__)


class LiveFormatterProcess(Protocol):
    """Represent live formatter process state."""

    stdin: IO[str] | None
    stdout: IO[str] | None
    stderr: IO[str] | None
    returncode: int | None

    def poll(self) -> int | None:
        """Handle poll."""
        ...

    def wait(self, timeout: float | None = None) -> int:
        """Handle wait."""
        ...

    def kill(self) -> None:
        """Handle kill."""
        ...


class LiveFormatterService(ReporterServiceBase):
    """Represent live formatter service state."""

    def _finalize_live_formatter_process(self, process: LiveFormatterProcess) -> None:
        flush_lines = self._build_live_formatter_flush_json_lines()
        if flush_lines:
            self._emit_live_formatter_json_lines(flush_lines, source="formatter session final flush")
        if process.stdin is not None:
            with suppress(OSError, ValueError):
                process.stdin.close()
        self._wait_for_live_formatter_process(process)
        if process.returncode not in {None, 0}:
            self._record_live_formatter_failure(
                f"Live cucumber formatter session exited with code {process.returncode}.",
            )

    def _wait_for_live_formatter_process(self, process: LiveFormatterProcess) -> None:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._record_live_formatter_failure("Live cucumber formatter session did not terminate after stdin closed.")
            with suppress(OSError):
                process.kill()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._record_live_formatter_failure(
                    "Live cucumber formatter session did not terminate after forced shutdown.",
                )
        finally:
            if process.poll() is None:
                with suppress(OSError):
                    process.kill()
                with suppress(subprocess.TimeoutExpired, OSError):
                    process.wait(timeout=5)

    def _join_live_formatter_threads(self) -> None:
        if self.reporter._live_formatter_stdout_thread is not None:
            self.reporter._live_formatter_stdout_thread.join(timeout=5)
            self.reporter._live_formatter_stdout_thread = None
        if self.reporter._live_formatter_stderr_thread is not None:
            self.reporter._live_formatter_stderr_thread.join(timeout=5)
            self.reporter._live_formatter_stderr_thread = None

    def _record_live_formatter_failure(self, message: str) -> None:
        if self.reporter._live_formatter_failure_message == message:
            return
        if self.reporter._live_formatter_failure_message is None:
            self.reporter._live_formatter_failure_message = message
            restore_terminal_reporter = getattr(self.reporter, "_restore_terminal_reporter", None)
            if restore_terminal_reporter is not None:
                restore_terminal_reporter()
                self.reporter._restore_terminal_reporter = None
        logger.error("%s", message)
        sys.stderr.write(f"{message}\n")
        sys.stderr.flush()

    def _emit_live_formatter_json_lines(self, message_json_lines: list[str], *, source: str) -> None:
        normalized_lines = self._normalize_live_formatter_json_lines(message_json_lines)
        if not normalized_lines or self.reporter._live_formatter_failure_message is not None:
            return
        process = self.reporter._live_formatter_process
        if process is None:
            return
        stdin = process.stdin
        if stdin is None:
            self._record_live_formatter_failure(
                f"Live cucumber formatter delivery from {source} failed because "
                "the formatter stdin pipe is unavailable.",
            )
            return
        if process.poll() is not None:
            self._record_live_formatter_failure(
                f"Live cucumber formatter session exited early with code {process.returncode} while handling {source}.",
            )
            return
        with self.reporter._live_formatter_lock:
            try:
                for message_json in normalized_lines:
                    stdin.write(message_json)
                    stdin.write("\n")
                stdin.flush()
            except OSError as exc:
                self._record_live_formatter_failure(
                    f"Live cucumber formatter delivery from {source} failed before session completion: {exc}",
                )

    def emit_live_formatter_json_lines(self, message_json_lines: list[str], *, source: str) -> None:
        """Handle emit live formatter json lines."""
        self._emit_live_formatter_json_lines(message_json_lines, source=source)

    def _normalize_live_formatter_json_lines(self, message_json_lines: list[str]) -> list[str]:
        normalized_lines: list[str] = []
        for message_json in message_json_lines:
            envelope_dict = json.loads(message_json)
            normalized_lines.extend(
                json.dumps(adapted_envelope_dict)
                for adapted_envelope_dict in self.reporter._live_formatter_envelope_adapter.adapt_envelope_dict(
                    envelope_dict,
                )
            )
        return normalized_lines

    def _build_live_formatter_flush_json_lines(self) -> list[str]:
        return [json.dumps(envelope_dict) for envelope_dict in self.reporter._live_formatter_envelope_adapter.flush()]

    @staticmethod
    def _close_live_formatter_stream(stream: IO[str] | None) -> None:
        if stream is None:
            return
        with suppress(OSError, ValueError):
            stream.close()

    @staticmethod
    def _prepend_node_path(env: Mapping[str, str], *node_modules_roots: Path) -> dict[str, str]:
        merged_env = {key: str(value) for key, value in env.items()}
        search_roots = [str(path) for path in node_modules_roots if str(path)]
        existing_node_path = merged_env.get("NODE_PATH")
        if existing_node_path:
            search_roots.append(existing_node_path)
        if search_roots:
            merged_env["NODE_PATH"] = os.pathsep.join(dict.fromkeys(search_roots))
        return merged_env

    @classmethod
    def _build_node_execution_env(cls, *node_modules_roots: Path) -> dict[str, str]:
        return cls._prepend_node_path(os.environ, *node_modules_roots)

    def _node_package_installed(self, node_executable: str, package_name: str, *, env: Mapping[str, str]) -> bool:
        return self._resolve_node_package_root(node_executable, package_name, env=env) is not None

    def _resolve_global_node_modules_root(
        self,
        npm_executable: str,
        *,
        env: Mapping[str, str],
    ) -> Path | None:
        completed = subprocess.run(  # noqa: S603
            [npm_executable, "root", "-g"],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(get_config_root_path(self.reporter.config)),
            env=dict(env),
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            return None
        return Path(completed.stdout.strip()).resolve()

    @staticmethod
    def _infer_node_modules_root_from_resolved_package_path(
        resolved_package_path: Path,
        package_name: str,
    ) -> Path | None:
        package_parts = tuple(package_name.split("/"))
        resolved_parts = resolved_package_path.parts
        for index in range(len(resolved_parts) - len(package_parts) + 1):
            if resolved_parts[index : index + len(package_parts)] == package_parts:
                return Path(*resolved_parts[:index])
        return None

    def _resolve_node_package_root(
        self,
        node_executable: str,
        package_name: str,
        *,
        env: Mapping[str, str],
    ) -> Path | None:
        completed = subprocess.run(  # noqa: S603
            [node_executable, "-e", "process.stdout.write(require.resolve(process.argv[1]))", package_name],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(get_config_root_path(self.reporter.config)),
            env=dict(env),
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            return None
        return self._infer_node_modules_root_from_resolved_package_path(
            Path(completed.stdout.strip()).resolve(),
            package_name,
        )

    def _ensure_node_packages_available(
        self,
        package_names: tuple[str, ...],
        *,
        purpose: str,
    ) -> NodePackageProvisionResult:
        node_executable = shutil.which("node") or shutil.which("nodejs")
        if node_executable is None:
            return NodePackageProvisionResult(env={}, missing_packages=tuple(sorted(package_names)), missing_node=True)

        discovered_node_modules_roots = tuple(
            dict.fromkeys(
                filter(
                    None,
                    (
                        self._resolve_node_package_root(
                            node_executable,
                            package_name,
                            env=self._build_node_execution_env(),
                        )
                        for package_name in package_names
                    ),
                ),
            ),
        )
        base_env = self._build_node_execution_env(*discovered_node_modules_roots)
        missing_from_env = tuple(
            sorted(
                package_name
                for package_name in package_names
                if not self._node_package_installed(node_executable, package_name, env=base_env)
            ),
        )
        if not missing_from_env:
            return NodePackageProvisionResult(env=base_env, node_modules_roots=discovered_node_modules_roots)

        npm_executable = shutil.which("npm")
        if npm_executable is None:
            return NodePackageProvisionResult(
                env=base_env,
                missing_packages=missing_from_env,
                node_modules_roots=discovered_node_modules_roots,
                missing_npm=True,
            )

        global_node_modules_root = self._resolve_global_node_modules_root(npm_executable, env=base_env)
        if global_node_modules_root is None:
            return NodePackageProvisionResult(
                env=base_env,
                missing_packages=missing_from_env,
                node_modules_roots=discovered_node_modules_roots,
                missing_npm=True,
            )

        global_env = self._build_node_execution_env(*discovered_node_modules_roots, global_node_modules_root)
        missing_from_global = tuple(
            sorted(
                package_name
                for package_name in missing_from_env
                if not self._node_package_installed(node_executable, package_name, env=global_env)
            ),
        )
        if not missing_from_global:
            return NodePackageProvisionResult(
                env=global_env,
                node_modules_roots=(*discovered_node_modules_roots, global_node_modules_root),
            )

        lock = FileLock(str(Path(tempfile.gettempdir()) / "pytest-bdd-ng-global-npm-install.lock"))
        install_env = dict(global_env)
        install_env.setdefault("npm_config_audit", "false")
        install_env.setdefault("npm_config_fund", "false")
        install_env.setdefault("npm_config_update_notifier", "false")

        with lock:
            packages_to_install = tuple(
                sorted(
                    package_name
                    for package_name in missing_from_global
                    if not self._node_package_installed(node_executable, package_name, env=global_env)
                ),
            )
            if packages_to_install:
                sys.stderr.write(
                    f"Installing missing global npm package(s) for {purpose}: {', '.join(packages_to_install)}\n",
                )
                sys.stderr.flush()
                completed = subprocess.run(  # noqa: S603
                    [
                        npm_executable,
                        "install",
                        "-g",
                        "--silent",
                        "--ignore-scripts",
                        "--no-audit",
                        "--no-fund",
                        *packages_to_install,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=str(get_config_root_path(self.reporter.config)),
                    env=install_env,
                )
                if completed.stderr:
                    sys.stderr.write(completed.stderr)
                    sys.stderr.flush()
                if completed.returncode != 0:
                    logger.warning(
                        "Automatic npm installation failed for %s while %s with exit code %s.",
                        ", ".join(packages_to_install),
                        purpose,
                        completed.returncode,
                    )

        final_missing_packages = tuple(
            sorted(
                package_name
                for package_name in missing_from_env
                if not self._node_package_installed(node_executable, package_name, env=global_env)
            ),
        )
        installed_packages = tuple(sorted(set(missing_from_env) - set(final_missing_packages)))
        return NodePackageProvisionResult(
            env=global_env,
            missing_packages=final_missing_packages,
            installed_packages=installed_packages,
            node_modules_roots=(*discovered_node_modules_roots, global_node_modules_root),
        )

    def _resolve_runnable_cucumber_formatter_requests(
        self,
        *,
        formatter_labels: str,
    ) -> tuple[
        str | None,
        dict[str, str],
        list[CucumberFormatterRequest],
        dict[str, list[CucumberFormatterRequest]],
        tuple[str, ...],
    ]:
        provision_result = self._ensure_node_packages_available(
            tuple(
                sorted(
                    {
                        "@cucumber/cucumber",
                        *(request.package_name for request in self.reporter.requested_cucumber_formatters),
                    },
                ),
            ),
            purpose=f"cucumber formatter rendering ({formatter_labels})",
        )
        if provision_result.missing_node:
            return None, {}, [], {}, ()

        node_executable = shutil.which("node") or shutil.which("nodejs")
        if node_executable is None:
            return None, {}, [], {}, ()

        node_env = provision_result.env or self._build_node_execution_env()
        runnable_requests: list[CucumberFormatterRequest] = []
        missing_packages: dict[str, list[CucumberFormatterRequest]] = {}
        for formatter_request in self.reporter.requested_cucumber_formatters:
            if (
                "@cucumber/cucumber" not in provision_result.missing_packages
                and formatter_request.package_name not in provision_result.missing_packages
            ):
                runnable_requests.append(formatter_request)
            else:
                missing_packages.setdefault(formatter_request.package_name, []).append(formatter_request)

        return node_executable, node_env, runnable_requests, missing_packages, provision_result.missing_packages

    def _warn_about_missing_cucumber_formatter_packages(
        self,
        missing_packages: dict[str, list[CucumberFormatterRequest]],
    ) -> None:
        for package_name, formatter_requests in missing_packages.items():
            logger.warning(
                "Skipping cucumber formatter rendering for %s because npm package '%s' is unavailable. "
                "Install it manually with `npm install --save-dev %s` if auto-provisioning is not possible.",
                format_requested_cucumber_formatter_labels(formatter_requests),
                package_name,
                package_name,
            )

    @staticmethod
    def _augment_node_env_for_live_terminal_stream(env: dict[str, str]) -> dict[str, str]:
        augmented_env = dict(env)
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        augmented_env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_ISATTY"] = "1" if sys.stdout.isatty() else "0"
        augmented_env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_COLUMNS"] = str(max(terminal_size.columns, 1))
        augmented_env["PYTEST_BDD_LIVE_FORMATTER_STDOUT_ROWS"] = str(max(terminal_size.lines, 1))
        return augmented_env

    @staticmethod
    def _resolve_formatter_expression_constructor_name(pattern_type: object | None) -> str:
        type_name = getattr(pattern_type, "name", None) or str(pattern_type or "")
        normalized = type_name.upper()
        if "REGULAR" in normalized:
            return "RegularExpression"
        return "CucumberExpression"

    @staticmethod
    def _resolve_source_reference_uri(source_reference: object | None) -> str:
        uri = getattr(source_reference, "uri", None)
        return "" if uri is None else str(uri)

    @staticmethod
    def _resolve_source_reference_line(source_reference: object | None) -> int:
        location = getattr(source_reference, "location", None)
        line = getattr(location, "line", 0)
        return int(line or 0)

    def _build_cucumber_formatter_support_code_payload(self, envelopes: list[Message]) -> JSONObject:
        step_definitions: JSONArray = []
        hooks: JSONArray = []
        parameter_types: JSONArray = []
        seen_step_definition_ids: set[str] = set()
        seen_hook_ids: set[str] = set()
        seen_parameter_type_ids: set[str] = set()

        for envelope in envelopes:
            step_definition = getattr(envelope, "step_definition", None)
            if step_definition is not None and step_definition.id not in seen_step_definition_ids:
                seen_step_definition_ids.add(step_definition.id)
                source_reference = getattr(step_definition, "source_reference", None)
                java_method = getattr(source_reference, "java_method", None)
                pattern = getattr(step_definition, "pattern", None)
                code_reference = ".".join(
                    part
                    for part in (
                        getattr(java_method, "class_name", None),
                        getattr(java_method, "method_name", None),
                    )
                    if part is not None
                )
                if not code_reference:
                    code_reference = (
                        f"{self._resolve_source_reference_uri(source_reference)}:"
                        f"{self._resolve_source_reference_line(source_reference)}"
                    )
                step_definitions.append(
                    {
                        "id": str(step_definition.id),
                        "uri": self._resolve_source_reference_uri(source_reference),
                        "line": self._resolve_source_reference_line(source_reference),
                        "pattern": "" if pattern is None else str(getattr(pattern, "source", "")),
                        "expressionConstructorName": self._resolve_formatter_expression_constructor_name(
                            getattr(pattern, "type", None),
                        ),
                        "code": code_reference,
                    },
                )

            hook = getattr(envelope, "hook", None)
            if hook is not None and hook.id not in seen_hook_ids:
                seen_hook_ids.add(hook.id)
                source_reference = getattr(hook, "source_reference", None)
                hook_type = getattr(hook, "type", None)
                hook_type_name = getattr(hook_type, "name", None) or str(hook_type or "")
                hooks.append(
                    {
                        "id": str(hook.id),
                        "name": None if getattr(hook, "name", None) is None else str(hook.name),
                        "uri": self._resolve_source_reference_uri(source_reference),
                        "line": self._resolve_source_reference_line(source_reference),
                        "type": hook_type_name.split(".")[-1].lower(),
                        "tagExpression": None
                        if getattr(hook, "tag_expression", None) is None
                        else str(hook.tag_expression),
                    },
                )

            parameter_type = getattr(envelope, "parameter_type", None)
            if parameter_type is not None and parameter_type.id not in seen_parameter_type_ids:
                seen_parameter_type_ids.add(parameter_type.id)
                parameter_types.append(
                    {
                        "name": None if getattr(parameter_type, "name", None) is None else str(parameter_type.name),
                        "regularExpressions": [
                            str(regular_expression)
                            for regular_expression in getattr(parameter_type, "regular_expressions", ())
                        ],
                        "preferForRegularExpressionMatch": bool(
                            getattr(parameter_type, "prefer_for_regular_expression_match", False),
                        ),
                        "useForSnippets": bool(getattr(parameter_type, "use_for_snippets", True)),
                    },
                )

        return {
            "stepDefinitions": step_definitions,
            "hooks": hooks,
            "parameterTypes": parameter_types,
        }

    def build_cucumber_formatter_support_code_payload(self, envelopes: list[Message]) -> JSONObject:
        """
        Build cucumber formatter support code payload.

        Returns:
            Support code payload.

        """
        return self._build_cucumber_formatter_support_code_payload(envelopes)

    def _build_cucumber_formatter_payload(
        self,
        *,
        envelopes: list[Message],
        formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
        messages_path: Path | None = None,
    ) -> JSONObject:
        return {
            "cwd": str(get_config_root_path(self.reporter.config)),
            "messagesPath": str(messages_path) if messages_path is not None else None,
            "formatters": [
                {
                    "formatter": formatter_request.formatter,
                    "outputPath": None if formatter_request.output_path is None else str(formatter_request.output_path),
                    "cliFlag": formatter_request.cli_flag,
                    "runtime": {
                        "kind": formatter_request.runtime_kind.value,
                        "specifier": formatter_request.runtime_specifier,
                        "modulePath": formatter_request.runtime_module_path,
                        "exportName": formatter_request.runtime_export_name,
                    },
                }
                for formatter_request in formatter_requests
            ],
            "formatOptions": {},
            "supportCode": self._build_cucumber_formatter_support_code_payload(envelopes),
        }

    def _render_cucumber_formatter_runtime_assets(
        self,
        formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
    ) -> dict[str, str]:
        render_runtime_assets = getattr(self.reporter, "render_runtime_assets", None)
        if callable(render_runtime_assets):
            return cast(
                Callable[[list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...]], dict[str, str]],
                render_runtime_assets,
            )(formatter_requests)
        pluginmanager = getattr(self.reporter.config, "pluginmanager", None)
        return render_live_formatter_runtime_assets(formatter_requests, pluginmanager=pluginmanager)

    def _start_live_formatters(self) -> None:
        if (
            self.reporter.is_disabled
            or self.reporter.is_xdist_worker
            or not self.reporter.requested_cucumber_formatters
        ):
            return

        formatter_labels = format_requested_cucumber_formatter_labels(self.reporter.requested_cucumber_formatters)
        (
            node_executable,
            node_env,
            runnable_requests,
            missing_packages,
            _missing_package_names,
        ) = self._resolve_runnable_cucumber_formatter_requests(
            formatter_labels=formatter_labels,
        )
        node_env = self._augment_node_env_for_live_terminal_stream(node_env)
        if node_executable is None:
            self._record_live_formatter_failure(
                f"Unable to start the live cucumber formatter session for {formatter_labels} "
                "because Node.js was not found in PATH.",
            )
            return

        self._warn_about_missing_cucumber_formatter_packages(missing_packages)

        if not runnable_requests:
            self._record_live_formatter_failure(
                f"Unable to start the live cucumber formatter session for {formatter_labels} "
                "because required formatter packages are unavailable.",
            )
            return

        self.reporter._live_formatter_temp_dir = tempfile.TemporaryDirectory(prefix="pytest-bdd-live-formatters-")
        temp_dir = Path(self.reporter._live_formatter_temp_dir.name)
        script_path = temp_dir / "render_cucumber_formatters.js"
        payload_path = temp_dir / "formatter_payload.json"
        runtime_assets = self._render_cucumber_formatter_runtime_assets(runnable_requests)
        for relative_path, rendered_asset in runtime_assets.items():
            asset_path = temp_dir / relative_path
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            asset_path.write_text(rendered_asset, encoding="utf-8")
        payload_path.write_text(
            json.dumps(
                self._build_cucumber_formatter_payload(
                    envelopes=[],
                    formatter_requests=runnable_requests,
                    messages_path=None,
                ),
            ),
            encoding="utf-8",
        )
        try:
            self.reporter._live_formatter_process = subprocess.Popen(  # noqa: S603
                [node_executable, str(script_path), str(payload_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(get_config_root_path(self.reporter.config)),
                env=node_env,
            )
            if self.reporter._live_formatter_process.stdout is not None:
                self.reporter._live_formatter_stdout_thread = Thread(
                    target=relay_live_formatter_output,
                    args=(self.reporter._live_formatter_process.stdout, sys.stdout),
                    daemon=True,
                )
                self.reporter._live_formatter_stdout_thread.start()
            if self.reporter._live_formatter_process.stderr is not None:
                self.reporter._live_formatter_stderr_thread = Thread(
                    target=relay_live_formatter_output,
                    args=(self.reporter._live_formatter_process.stderr, sys.stderr),
                    daemon=True,
                )
                self.reporter._live_formatter_stderr_thread.start()
            if self.reporter._live_formatter_process.poll() is not None:
                self._record_live_formatter_failure(
                    "Live cucumber formatter session exited early with code "
                    f"{self.reporter._live_formatter_process.returncode} during startup.",
                )
                return
            self.reporter._live_formatter_session_started = True
        except OSError:
            logger.exception(
                "Unable to execute Node.js while streaming to cucumber formatters for %s.",
                formatter_labels,
            )
            self._record_live_formatter_failure(
                f"Unable to execute Node.js while starting the live cucumber formatter session for {formatter_labels}.",
            )

    def _run_requested_cucumber_formatters(
        self,
        envelopes: list[Message],
    ) -> CucumberFormatterRenderResult:
        if not self.reporter.requested_cucumber_formatters:
            return CucumberFormatterRenderResult(success=True, rendered_formatters=())

        formatter_labels = format_requested_cucumber_formatter_labels(self.reporter.requested_cucumber_formatters)
        (
            node_executable,
            node_env,
            runnable_requests,
            missing_packages,
            missing_package_names,
        ) = self._resolve_runnable_cucumber_formatter_requests(
            formatter_labels=formatter_labels,
        )
        node_env = self._augment_node_env_for_live_terminal_stream(node_env)
        if node_executable is None:
            logger.warning(
                "Skipping cucumber formatter rendering for %s because Node.js was not found in PATH.",
                formatter_labels,
            )
            return CucumberFormatterRenderResult(
                success=False,
                rendered_formatters=(),
                missing_node=True,
            )

        self._warn_about_missing_cucumber_formatter_packages(missing_packages)

        if not runnable_requests:
            return CucumberFormatterRenderResult(
                success=False,
                rendered_formatters=(),
                missing_packages=missing_package_names,
            )

        try:
            with tempfile.TemporaryDirectory(prefix="pytest-bdd-cucumber-formatters-") as temp_dir_name:
                temp_dir = Path(temp_dir_name)
                script_path = temp_dir / "render_cucumber_formatters.js"
                payload_path = temp_dir / "formatter_payload.json"
                runtime_assets = self._render_cucumber_formatter_runtime_assets(runnable_requests)
                for relative_path, rendered_asset in runtime_assets.items():
                    asset_path = temp_dir / relative_path
                    asset_path.parent.mkdir(parents=True, exist_ok=True)
                    asset_path.write_text(rendered_asset, encoding="utf-8")
                normalized_messages_path = temp_dir / "formatter_messages.ndjson"
                normalized_messages_path.write_text(
                    "".join(
                        f"{json.dumps(envelope_dict)}\n"
                        for envelope_dict in normalize_formatter_envelope_dicts(
                            [
                                ExecutionMessageAdapter.serialize_to_dict(
                                    envelope,
                                    profile=MessageSerializationProfile.schema_compatible,
                                )
                                for envelope in envelopes
                            ],
                        )
                    ),
                    encoding="utf-8",
                )
                payload_path.write_text(
                    json.dumps(
                        self._build_cucumber_formatter_payload(
                            envelopes=envelopes,
                            formatter_requests=runnable_requests,
                            messages_path=normalized_messages_path,
                        ),
                    ),
                    encoding="utf-8",
                )
                completed = subprocess.run(  # noqa: S603
                    [node_executable, str(script_path), str(payload_path)],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=str(get_config_root_path(self.reporter.config)),
                    env=node_env,
                )
        except OSError:
            logger.exception(
                "Unable to execute Node.js while rendering cucumber formatter output for %s.",
                formatter_labels,
            )
            return CucumberFormatterRenderResult(
                success=False,
                rendered_formatters=tuple(runnable_requests),
                process_exit_code=None,
            )

        if completed.stdout:
            sys.stdout.write(completed.stdout)
            sys.stdout.flush()
        if completed.stderr:
            sys.stderr.write(completed.stderr)
            sys.stderr.flush()
        if completed.returncode != 0:
            logger.warning(
                "Cucumber formatter subprocess failed for %s with exit code %s.",
                format_requested_cucumber_formatter_labels(runnable_requests),
                completed.returncode,
            )
        return CucumberFormatterRenderResult(
            success=not missing_packages and completed.returncode == 0,
            rendered_formatters=tuple(runnable_requests),
            missing_packages=missing_package_names,
            process_exit_code=completed.returncode,
        )

    def run_requested_cucumber_formatters(
        self,
        envelopes: list[Message],
    ) -> CucumberFormatterRenderResult:
        """
        Run requested cucumber formatters.

        Returns:
            Cucumber formatter render result.

        """
        return self._run_requested_cucumber_formatters(envelopes)

    def generate_html_report(self) -> None:
        """Handle generate html report."""
        if self.reporter.is_disabled:
            return
        script_path = Path(
            next(
                find_resource(
                    self.reporter.npm_formatter_package,
                    str(Path("dist") / "main.js"),
                    additional_roots=self.reporter._auto_provisioned_node_modules_roots,
                ),
            ),
        )
        css_path = Path(
            next(
                find_resource(
                    self.reporter.npm_formatter_package,
                    str(Path("dist") / "main.css"),
                    additional_roots=self.reporter._auto_provisioned_node_modules_roots,
                ),
            ),
        )
        template_path = Path(
            next(
                find_resource(
                    self.reporter.npm_formatter_package,
                    str(Path("src") / "index.mustache.html"),
                    additional_roots=self.reporter._auto_provisioned_node_modules_roots,
                ),
            ),
        )
        template = template_path.read_text(encoding="utf-8")
        icon = ""
        if "{{icon}}" in template:
            icon_match = next(
                find_resource(
                    self.reporter.npm_formatter_package,
                    str(Path("src") / "icon.url"),
                    additional_roots=self.reporter._auto_provisioned_node_modules_roots,
                ),
                None,
            )
            if icon_match is not None:
                icon = Path(icon_match).read_text(encoding="utf-8").strip()

        with self.reporter.final_messages_file_path.open(mode="r", encoding="utf-8") as f:
            messages = tuple(line.strip() for line in f if line.strip())

        html_report_path = Path(self.reporter.config.option.cucumber_html_path)
        html_report_path.parent.mkdir(parents=True, exist_ok=True)
        html_report_path.write_text(
            render_html_report_content(
                template=template,
                title="Cucumber",
                icon=icon,
                css=css_path.read_text(encoding="utf-8"),
                custom_css="",
                messages=messages,
                script=script_path.read_text(encoding="utf-8"),
                custom_script="",
            ),
            encoding="utf-8",
        )

    def check_npm_and_cucumber_packages(self) -> None:
        """Check npm and cucumber packages."""
        provision_result = self._ensure_node_packages_available(
            (self.reporter.npm_formatter_package,),
            purpose="HTML report generation",
        )
        if provision_result.missing_node:
            pytest.exit("Node.js wasn't found in the environment so unable generate html report")
        if provision_result.missing_npm and provision_result.missing_packages:
            pytest.exit(
                "Npm wasn't found in the environment and the HTML formatter package could not be auto-provisioned, "
                "so unable generate html report",
            )
        if provision_result.missing_packages:
            pytest.exit(
                f"Npm package '{self.reporter.npm_formatter_package}' could not be provisioned automatically so unable "
                "generate html report. Install it manually with "
                f"`npm install --save-dev {self.reporter.npm_formatter_package}`",
            )
        self.reporter._auto_provisioned_node_modules_roots = provision_result.node_modules_roots
