"""
Provide live formatter runner orchestration helpers.

Responsibility:
    Provide live formatter runner orchestration helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner` because
    it keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _resolve_npm_formatter_resource: owns nested behavior below this boundary
    - LiveFormatterRunnerMixin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
      `live_formatter_runner`

State and side effects:
    mutates node_env, script_path, formatter_labels, node_executable, runnable_requests; depends on
    __future__.annotations, json, logging, subprocess, sys.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Failure semantics:
    Raises or re-raises RuntimeError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

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

    Responsibility:
        Resolve a required npm formatter resource. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner._resolve_npm_formatter_resource` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - next: collaborator call used by this boundary
        - find_resource: collaborator call used by this boundary
        - RuntimeError: collaborator call used by this boundary
        - Path: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
          `_resolve_npm_formatter_resource`

    State and side effects:
        mutates match, message.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner._resolve_npm_formatter_resource` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

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
    """
    Provide live formatter startup and render orchestration behavior.

    Responsibility:
        Provide live formatter startup and render orchestration behavior. It directly owns the observable contract,
        local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _render_cucumber_formatter_runtime_assets: owns nested behavior below this boundary
        - _start_live_formatters: owns nested behavior below this boundary
        - _spawn_live_formatter_subprocess: owns nested behavior below this boundary
        - _execute_cucumber_formatter_subprocess: owns nested behavior below this boundary
        - _run_requested_cucumber_formatters: owns nested behavior below this boundary
        - run_requested_cucumber_formatters: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
          `LiveFormatterRunnerMixin`

    State and side effects:
        mutates node_env, script_path, formatter_labels, node_executable, runnable_requests.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

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
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._render_cucumber_formatter_runtime_assets`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._render_cucumber_formatter_runtime_assets`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - callable: collaborator call used by this boundary
            - render_live_formatter_runtime_assets: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_render_cucumber_formatter_runtime_assets`

        State and side effects:
            mutates render_runtime_assets, pluginmanager.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._render_cucumber_formatter_runtime_assets`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        render_runtime_assets = getattr(self.reporter, "render_runtime_assets", None)
        if callable(render_runtime_assets):
            return cast(
                "Callable[[list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...]], dict[str, str]]",
                render_runtime_assets,
            )(formatter_requests)
        pluginmanager = getattr(self.reporter.config, "pluginmanager", None)
        return render_live_formatter_runtime_assets(formatter_requests, pluginmanager=pluginmanager)

    def _start_live_formatters(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._start_live_formatters`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._start_live_formatters`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._record_live_formatter_failure: collaborator call used by this boundary
            - format_requested_cucumber_formatter_labels: collaborator call used by this boundary
            - self._resolve_runnable_cucumber_formatter_requests: collaborator call used by this boundary
            - self._augment_node_env_for_live_terminal_stream: collaborator call used by this boundary
            - self._warn_about_missing_cucumber_formatter_packages: collaborator call used by this boundary
            - tempfile.TemporaryDirectory: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_start_live_formatters`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_start_live_formatters`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_start_live_formatters`

        State and side effects:
            mutates node_env, formatter_labels, node_executable, runnable_requests, missing_packages.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._start_live_formatters`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
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
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._spawn_live_formatter_subprocess`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._spawn_live_formatter_subprocess`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - Thread: collaborator call used by this boundary
            - subprocess.Popen: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - self.reporter._live_formatter_stdout_thread.start: collaborator call used by this boundary
            - self.reporter._live_formatter_stderr_thread.start: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_spawn_live_formatter_subprocess`

        State and side effects:
            mutates self.reporter._live_formatter_process, self.reporter._live_formatter_stdout_thread,
            self.reporter._live_formatter_stderr_thread, self.reporter._live_formatter_session_started.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._spawn_live_formatter_subprocess`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
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
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._execute_cucumber_formatter_subprocess`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._execute_cucumber_formatter_subprocess`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - json.dumps: collaborator call used by this boundary
            - tempfile.TemporaryDirectory: collaborator call used by this boundary
            - self._render_cucumber_formatter_runtime_assets: collaborator call used by this boundary
            - runtime_assets.items: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_execute_cucumber_formatter_subprocess`

        State and side effects:
            mutates temp_dir, script_path, payload_path, runtime_assets, asset_path.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._execute_cucumber_formatter_subprocess`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
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
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._run_requested_cucumber_formatters`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._run_requested_cucumber_formatters`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - CucumberFormatterRenderResult: collaborator call used by this boundary
            - format_requested_cucumber_formatter_labels: collaborator call used by this boundary
            - logger.warning: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - self._resolve_runnable_cucumber_formatter_requests: collaborator call used by this boundary
            - self._augment_node_env_for_live_terminal_stream: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_run_requested_cucumber_formatters`

        State and side effects:
            mutates node_env, formatter_labels, node_executable, runnable_requests, missing_packages.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin._run_requested_cucumber_formatters`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
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

        Responsibility:
            Run requested cucumber formatters. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin.run_requested_cucumber_formatters`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._run_requested_cucumber_formatters: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `run_requested_cucumber_formatters`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `run_requested_cucumber_formatters`
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `run_requested_cucumber_formatters`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        return self._run_requested_cucumber_formatters(envelopes)

    def generate_html_report(self) -> None:
        """
        Handle generate html report.

        Responsibility:
            Handle generate html report. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin.generate_html_report`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Path: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - _resolve_npm_formatter_resource: collaborator call used by this boundary
            - line.strip: collaborator call used by this boundary
            - template_path.read_text: collaborator call used by this boundary
            - next: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `generate_html_report`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `generate_html_report`

        State and side effects:
            mutates template_path, icon, script_path, css_path, template.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin.generate_html_report`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
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
        """
        Check npm and cucumber packages.

        Responsibility:
            Check npm and cucumber packages. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin.check_npm_and_cucumber_packages`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - pytest.exit: collaborator call used by this boundary
            - self._ensure_node_packages_available: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `check_npm_and_cucumber_packages`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `check_npm_and_cucumber_packages`

        State and side effects:
            mutates provision_result, self.reporter._auto_provisioned_node_modules_roots.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.LiveFormatterRunnerMixin.check_npm_and_cucumber_packages`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
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
