from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import pytest

from pytest_cuke.debug_mcp.discovery import DiscoveryPublisher
from pytest_cuke.debug_mcp.server import (
    DebuggerMcpProcess,
    DebugMcpDependencyError,
    InspectionMcpServer,
    allocate_port,
    ensure_optional_dependencies,
)
from pytest_cuke.debug_mcp.state import FailureQueue
from pytest_cuke.model import Feature, Scenario
from pytest_cuke.model.session_run import RunContext

if TYPE_CHECKING:
    from collections.abc import Generator

    from pytest_cuke.debug_mcp.options import DebugMcpOptions
    from pytest_cuke.model.scenario_run import ScenarioRun


class DebugMcpPlugin:
    """Start opt-in Debug MCP endpoints and hold failed pytest reports for inspection."""

    def __init__(self, config: Any, options: DebugMcpOptions) -> None:
        self.config = config
        self.options = options
        self.discovery: DiscoveryPublisher | None = None
        self.queue: FailureQueue | None = None
        self.debugger: DebuggerMcpProcess | None = None
        self.inspection: InspectionMcpServer | None = None
        self._closed = False

    def pytest_sessionstart(self, session: Any) -> None:
        if session.config is not self.config:
            return
        if self._closed:
            return
        try:
            self._start()
        except Exception as error:
            self._cleanup(remove_discovery=True)
            if isinstance(error, pytest.UsageError):
                raise
            if isinstance(error, DebugMcpDependencyError):
                raise pytest.UsageError(str(error)) from error
            raise pytest.UsageError(f"could not start Debug MCP failure inspection: {error}") from error

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Any, call: Any) -> Generator[Any, Any, None]:
        outcome = yield
        report = outcome.get_result()
        queue = self.queue
        if queue is None or not report.failed or report.when not in {"setup", "call", "teardown"}:
            return

        exc_info = getattr(call, "excinfo", None)
        exception = getattr(exc_info, "value", None)
        error_type = type(exception).__name__ if exception is not None else "PytestFailure"
        report_message = getattr(report, "longreprtext", None) or getattr(
            report,
            "longrepr",
            "pytest reported a failure",
        )
        error_message = str(exception) if exception is not None else str(report_message)
        try:
            queue.hold_failure(
                nodeid=str(item.nodeid),
                phase=str(report.when),
                error_type=error_type,
                error_message=error_message,
                bdd_context=_bdd_context(item),
            )
        except KeyboardInterrupt:
            self._cleanup(remove_discovery=False)
            raise

    def pytest_sessionfinish(self, session: Any, exitstatus: int) -> None:
        if session.config is self.config:
            self._cleanup(remove_discovery=False)
        _ = exitstatus

    def pytest_unconfigure(self, config: Any) -> None:
        if config is self.config:
            self._cleanup(remove_discovery=False)

    def _start(self) -> None:
        cache_path = _cache_discovery_path(self.config)
        cache_path.unlink(missing_ok=True)
        ensure_optional_dependencies()

        debugger_port = self.options.port
        if debugger_port is None:
            debugger_port = allocate_port(self.options.host)
        inspection_port = allocate_port(self.options.host, excluding={debugger_port})

        session_id = self._session_id()
        self.queue = FailureQueue(
            session_id=session_id,
            timeout_seconds=self.options.timeout_seconds,
            lease_seconds=self.options.lease_seconds,
        )
        self.inspection = InspectionMcpServer(queue=self.queue, host=self.options.host, port=inspection_port)
        self.inspection.start()

        self.debugger = DebuggerMcpProcess(
            host=self.options.host,
            port=debugger_port,
            inspection_endpoint=self.inspection.endpoint,
        )
        self.debugger.start()

        self.discovery = DiscoveryPublisher(
            path=cache_path,
            session_id=session_id,
            host=self.options.host,
            debugger_endpoint=self.debugger.endpoint,
            inspection_endpoint=self.inspection.endpoint,
            debugger_pid=self.debugger.process.pid if self.debugger.process is not None else 0,
        )
        self.queue.set_change_callback(self._publish_state)
        self.discovery.write_initial()
        self._announce()

    def _session_id(self) -> str:
        context = RunContext.find_in_config(self.config)
        return context.run_id if context is not None else uuid4().hex

    def _announce(self) -> None:
        reporter = self.config.pluginmanager.get_plugin("terminalreporter")
        if reporter is None:
            return
        if self.options.uses_nonlocal_host:
            reporter.write_line(
                "WARNING: Debug MCP is bound to a non-local host; use only in a trusted environment.",
                yellow=True,
            )
        if self.queue is not None:
            reporter.write_line(f"Debug MCP session: {self.queue.session_id} (waiting)")
        if self.debugger is not None and self.inspection is not None and self.discovery is not None:
            reporter.write_line(f"Debug MCP debugger: {self.debugger.endpoint}")
            reporter.write_line(f"Debug MCP inspection: {self.inspection.endpoint}")
            reporter.write_line(f"Debug MCP discovery: {self.discovery.path}")

    def _publish_state(self, state: dict[str, Any]) -> None:
        if self.discovery is None:
            return
        self.discovery.publish_queue_state(state)
        active = state.get("active_failure")
        if not isinstance(active, dict):
            return
        reporter = self.config.pluginmanager.get_plugin("terminalreporter")
        if reporter is None:
            return
        reporter.write_line(
            "Debug MCP holding failure "
            f"#{active['sequence']} ({active['phase']}) at {active['nodeid']}: "
            f"{active['error_type']}: {active['error_message']}"
        )

    def _cleanup(self, *, remove_discovery: bool) -> None:
        if self._closed:
            return
        self._closed = True
        errors: list[Exception] = []
        for service in (self.debugger, self.inspection):
            if service is not None:
                try:
                    service.close()
                except Exception as error:
                    errors.append(error)
        if self.queue is not None:
            with suppress(Exception):
                self.queue.close()
        if self.discovery is not None:
            if remove_discovery:
                with suppress(OSError):
                    self.discovery.remove()
            else:
                last_release = self.queue.last_release if self.queue is not None else None
                with suppress(OSError):
                    self.discovery.close(last_release)
        if errors:
            reporter = self.config.pluginmanager.get_plugin("terminalreporter")
            if reporter is not None:
                reporter.write_line(f"Debug MCP shutdown warning: {errors[0]}", yellow=True)


def _bdd_context(item: Any) -> dict[str, Any] | None:
    callspec = getattr(item, "callspec", None)
    params = getattr(callspec, "params", {}) if callspec is not None else {}
    feature = params.get("feature")
    scenario = params.get("scenario")

    run_context = RunContext.find_in_config(item.config)
    scenario_run = run_context.get_scenario_run(str(item.nodeid)) if run_context is not None else None
    if scenario_run is not None:
        feature = scenario_run.feature or feature
        scenario = scenario_run.scenario or scenario
    if not isinstance(feature, Feature) or not isinstance(scenario, Scenario):
        return None

    step = _active_step(scenario_run)
    step_keyword = step.keyword.strip() if step is not None else None
    step_text = step.text if step is not None else None
    tags = sorted(set(feature.tag_names).union(scenario.tag_names))
    outline_row, outline_identity = _outline_context(feature, scenario)
    feature_path = feature.filename or feature.uri or None
    breadcrumb = {
        "nodeid": str(item.nodeid),
        "feature_path": feature_path,
        "feature_name": feature.name,
        "scenario_name": scenario.name,
        "step": {"keyword": step_keyword, "text": step_text},
        "outline_row": outline_row,
        "outline_identity": outline_identity,
    }
    return {
        "feature_path": feature_path,
        "feature_name": feature.name,
        "scenario_name": scenario.name,
        "step_keyword": step_keyword,
        "step_text": step_text,
        "tags": tags,
        "outline_row": outline_row,
        "breadcrumb": breadcrumb,
    }


def _cache_discovery_path(config: Any) -> Path:
    option = getattr(config, "option", None)
    configured_path = getattr(option, "cache_dir", None)
    if configured_path is None:
        try:
            configured_path = config.getini("cache_dir")
        except ValueError:
            configured_path = ".pytest_cache"
    if not configured_path:
        configured_path = ".pytest_cache"

    cache_dir = Path(configured_path)
    if not cache_dir.is_absolute():
        root = getattr(config, "rootpath", getattr(config, "rootdir", Path.cwd()))
        cache_dir = Path(root) / cache_dir
    return cache_dir / "cuke" / "debug-mcp" / "session.json"


def _active_step(scenario_run: ScenarioRun | None) -> Any | None:
    if scenario_run is None:
        return None
    if scenario_run.current_step_run is not None and scenario_run.current_step_run.step is not None:
        return scenario_run.current_step_run.step
    for step_run in reversed(scenario_run.steps):
        if step_run.step is not None and step_run.status == "failed":
            return step_run.step
    if scenario_run.steps:
        return scenario_run.steps[-1].step
    return None


def _outline_context(feature: Feature, scenario: Scenario) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    source = scenario.external_example_source
    source_node_ids = scenario.source_ast_node_ids
    row_id = source.row_id if source is not None else (source_node_ids[-1] if len(source_node_ids) > 1 else None)
    origin_id = source_node_ids[0] if len(source_node_ids) > 1 else None
    identity = None

    if source is not None:
        identity = {
            "path": source.path,
            "section_index": source.section_index,
            "row_index": source.row_index,
            "source_line": source.source_line,
            "row_id": source.row_id,
        }

    for original in feature.all_scenarios:
        if origin_id is not None and original.id != origin_id:
            continue
        for section_index, examples in enumerate(original.examples, start=1):
            if examples.header is None:
                continue
            for row_index, row in enumerate(examples.rows, start=1):
                if row.id != row_id and row_index != getattr(source, "row_index", None):
                    continue
                headers = examples.header.values
                values = row.values
                outline_row = {header: values[index] for index, header in enumerate(headers) if index < len(values)}
                if identity is None:
                    identity = {
                        "section_index": section_index,
                        "row_index": row_index,
                        "source_line": row.line,
                        "row_id": row.id,
                    }
                return outline_row, identity
    return None, identity


__all__ = ["DebugMcpPlugin"]
