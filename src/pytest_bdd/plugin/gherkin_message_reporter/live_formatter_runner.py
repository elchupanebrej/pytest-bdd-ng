"""Provide live formatter runner orchestration helpers."""

from __future__ import annotations

import json
import logging
import subprocess  # noqa: S404
import sys
import tempfile
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, cast

import pytest

from pytest_bdd.model.cucumber_formatter_adapter import normalize_formatter_envelope_dicts
from pytest_bdd.model.cucumber_formatter_contract import CucumberFormatterRenderResult, CucumberFormatterRequest
from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_serialization import MessageSerializationProfile
from pytest_bdd.plugin.gherkin_message_reporter.html_report import render_html_report_content
from pytest_bdd.plugin.gherkin_message_reporter.session import (
    format_requested_cucumber_formatter_labels,
    render_live_formatter_runtime_assets,
)
from pytest_bdd.plugin.gherkin_message_reporter.stream_relay import relay_live_formatter_output
from pytest_bdd.util.npm_resource import find_resource

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from cucumber_messages import Envelope as Message

    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter


logger = logging.getLogger(__name__)


def _resolve_npm_formatter_resource(
    package_name: str,
    resource_path: str,
    *,
    additional_roots: tuple[Path, ...] = (),
) -> Path:
    """
    Resolve a required npm formatter resource.

    Returns:
        Resolved resource path.

    Raises:
        RuntimeError: If the resource cannot be found.

    """
    match = next(
        find_resource(
            package_name,
            resource_path,
            additional_roots=additional_roots,
        ),
        None,
    )
    if match is None:
        message = f"Npm package '{package_name}' does not contain required formatter asset '{resource_path}'."
        raise RuntimeError(message)
    return Path(match)


class LiveFormatterRunnerMixin:
    """Provide live formatter startup and render orchestration behavior."""

    if TYPE_CHECKING:
        reporter: GherkinMessageReporter
        _resolve_runnable_cucumber_formatter_requests: Callable[..., Any]
        _augment_node_env_for_live_terminal_stream: Callable[..., Any]
        _record_live_formatter_failure: Callable[..., Any]
        _warn_about_missing_cucumber_formatter_packages: Callable[..., Any]
        _build_cucumber_formatter_payload: Callable[..., Any]
        _ensure_node_packages_available: Callable[..., Any]

    def _render_cucumber_formatter_runtime_assets(
        self,
        formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
    ) -> dict[str, str]:
        render_runtime_assets = getattr(self.reporter, "render_runtime_assets", None)
        if callable(render_runtime_assets):
            return cast(
                "Callable[[list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...]], dict[str, str]]",
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

        self.reporter._live_formatter_temp_dir = tempfile.TemporaryDirectory(prefix="pytest-bdd-live-formatters-")  # noqa: SLF001
        temp_dir = Path(self.reporter._live_formatter_temp_dir.name)  # noqa: SLF001
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
            self._spawn_live_formatter_subprocess(
                node_executable=node_executable,
                script_path=script_path,
                payload_path=payload_path,
                node_env=node_env,
            )
        except OSError:
            logger.exception(
                "Unable to execute Node.js while streaming to cucumber formatters for %s.",
                formatter_labels,
            )
            self._record_live_formatter_failure(
                f"Unable to execute Node.js while starting the live cucumber formatter session for {formatter_labels}.",
            )

    def _spawn_live_formatter_subprocess(
        self,
        *,
        node_executable: str,
        script_path: Path,
        payload_path: Path,
        node_env: dict[str, str],
    ) -> None:
        self.reporter._live_formatter_process = subprocess.Popen(  # noqa: S603, SLF001
            [node_executable, str(script_path), str(payload_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(self.reporter.config.rootpath)),
            env=node_env,
        )
        if self.reporter._live_formatter_process.stdout is not None:  # noqa: SLF001
            self.reporter._live_formatter_stdout_thread = Thread(  # noqa: SLF001
                target=relay_live_formatter_output,
                args=(self.reporter._live_formatter_process.stdout, sys.stdout),  # noqa: SLF001
                daemon=True,
            )
            self.reporter._live_formatter_stdout_thread.start()  # noqa: SLF001
        if self.reporter._live_formatter_process.stderr is not None:  # noqa: SLF001
            self.reporter._live_formatter_stderr_thread = Thread(  # noqa: SLF001
                target=relay_live_formatter_output,
                args=(self.reporter._live_formatter_process.stderr, sys.stderr),  # noqa: SLF001
                daemon=True,
            )
            self.reporter._live_formatter_stderr_thread.start()  # noqa: SLF001
        if self.reporter._live_formatter_process.poll() is not None:  # noqa: SLF001
            self._record_live_formatter_failure(
                "Live cucumber formatter session exited early with code "
                f"{self.reporter._live_formatter_process.returncode} during startup.",  # noqa: SLF001
            )
            return
        self.reporter._live_formatter_session_started = True  # noqa: SLF001

    def _execute_cucumber_formatter_subprocess(
        self,
        *,
        node_executable: str,
        node_env: dict[str, str],
        runnable_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
        envelopes: list[Message],
    ) -> subprocess.CompletedProcess[str]:
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
            return subprocess.run(  # noqa: S603
                [node_executable, str(script_path), str(payload_path)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(Path(self.reporter.config.rootpath)),
                env=node_env,
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
            completed = self._execute_cucumber_formatter_subprocess(
                node_executable=node_executable,
                node_env=node_env,
                runnable_requests=runnable_requests,
                envelopes=envelopes,
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
        script_path = _resolve_npm_formatter_resource(
            self.reporter.npm_formatter_package,
            str(Path("dist") / "main.js"),
            additional_roots=self.reporter._auto_provisioned_node_modules_roots,  # noqa: SLF001
        )
        css_path = _resolve_npm_formatter_resource(
            self.reporter.npm_formatter_package,
            str(Path("dist") / "main.css"),
            additional_roots=self.reporter._auto_provisioned_node_modules_roots,  # noqa: SLF001
        )
        try:
            template_path = _resolve_npm_formatter_resource(
                self.reporter.npm_formatter_package,
                str(Path("src") / "index.mustache.html"),
                additional_roots=self.reporter._auto_provisioned_node_modules_roots,  # noqa: SLF001
            )
        except RuntimeError:
            template_path = _resolve_npm_formatter_resource(
                self.reporter.npm_formatter_package,
                str(Path("src") / "index.mustache"),
                additional_roots=self.reporter._auto_provisioned_node_modules_roots,  # noqa: SLF001
            )
        template = template_path.read_text(encoding="utf-8")
        icon = ""
        if "{{icon}}" in template:
            icon_match = next(
                find_resource(
                    self.reporter.npm_formatter_package,
                    str(Path("src") / "icon.url"),
                    additional_roots=self.reporter._auto_provisioned_node_modules_roots,  # noqa: SLF001
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
        self.reporter._auto_provisioned_node_modules_roots = provision_result.node_modules_roots  # noqa: SLF001
