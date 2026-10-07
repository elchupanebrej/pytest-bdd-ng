from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import pytest

from pytest_cuke.debug_mcp.artifacts import ArtifactSink
from pytest_cuke.debug_mcp.discovery import DiscoveryPublisher
from pytest_cuke.debug_mcp.server import (
    DebuggerMcpProcess,
    DebugMcpDependencyError,
    InspectionMcpServer,
    allocate_port,
    ensure_optional_dependencies,
)
from pytest_cuke.debug_mcp.state import FailureQueue
from pytest_cuke.debug_mcp.xdist import (
    XdistDiscoveryError,
    XdistDiscoveryIndex,
    is_local_xdist_spec,
    is_xdist_controller,
    safe_worker_id,
    xdist_root_session_id,
    xdist_worker_id,
)
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
        self.artifact_sink: ArtifactSink | None = None
        self.debugger: DebuggerMcpProcess | None = None
        self.inspection: InspectionMcpServer | None = None
        self.xdist_index: XdistDiscoveryIndex | None = None
        self.worker_id: str | None = None
        self.root_session_id = uuid4().hex
        self._xdist_controller = False
        self._closed = False

    def pytest_sessionstart(self, session: Any) -> None:
        if session.config is not self.config:
            return
        if self._closed:
            return
        try:
            self.worker_id = xdist_worker_id(self.config)
            self._xdist_controller = self.worker_id is None and is_xdist_controller(self.config)
            self._start()
        except Exception as error:
            if self.worker_id is not None and self.xdist_index is not None and self.discovery is None:
                with suppress(Exception):
                    self.xdist_index.mark_worker_down(self.worker_id, str(error))
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

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_setupnodes(self, specs: Any) -> None:
        """Reject unsupported remote discovery before xdist starts worker processes."""
        if not self.options.enabled:
            return
        for spec in specs:
            if not is_local_xdist_spec(spec):
                raise pytest.UsageError(
                    "Debug MCP xdist discovery supports local popen workers on a shared filesystem; "
                    "remote gateways are unsupported because workers must publish to the root cache. "
                    "Use local pytest-xdist workers or disable --cuke-mcp-on-fail."
                )

    @pytest.hookimpl(optionalhook=True)
    def pytest_configure_node(self, node: Any) -> None:
        """Share the controller's run identity with each worker and register it as starting."""
        if not self.options.enabled or not is_xdist_controller(self.config):
            return
        if self.xdist_index is None:
            raise pytest.UsageError("Debug MCP worker discovery index was not initialized before xdist setup")
        worker_id = _worker_id_for_node(node)
        worker_input = getattr(node, "workerinput", None)
        if not isinstance(worker_input, dict):
            raise pytest.UsageError(f"Debug MCP xdist worker {worker_id!r} has no worker input record")
        worker_input["cuke_debug_mcp_root_session_id"] = self.root_session_id
        try:
            self.xdist_index.register_worker(worker_id)
        except XdistDiscoveryError as error:
            raise pytest.UsageError(str(error)) from error

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node: Any, error: object | None) -> None:
        """Clear endpoints for a worker that exited without a normal closed record."""
        if not self.options.enabled or not is_xdist_controller(self.config) or self.xdist_index is None:
            return
        worker_id = _worker_id_for_node(node)
        if error is None:
            try:
                if self.xdist_index.worker_is_closed(worker_id):
                    return
            except XdistDiscoveryError as discovery_error:
                error = f"worker exited without a valid closed discovery record: {discovery_error}"
            else:
                error = "worker exited without publishing a closed discovery record"
        try:
            self.xdist_index.mark_worker_down(worker_id, str(error))
        except XdistDiscoveryError as publish_error:
            reporter = self.config.pluginmanager.get_plugin("terminalreporter")
            if reporter is not None:
                reporter.write_line(f"Debug MCP worker discovery error for {worker_id}: {publish_error}", yellow=True)

    def _start(self) -> None:
        if self._xdist_controller:
            self._start_xdist_controller()
            return
        if self.worker_id is not None:
            self._start_xdist_worker()
            return

        cache_path = _cache_discovery_path(self.config)
        self._clear_stale_cache_discovery(cache_path)
        _xdist_index(self.config).clear_previous()
        self._start_services(discovery_path=cache_path)

    def _start_xdist_controller(self) -> None:
        cache_path = _cache_discovery_path(self.config)
        self._clear_stale_cache_discovery(cache_path)
        ensure_optional_dependencies()
        self.xdist_index = XdistDiscoveryIndex(
            path=_xdist_index_path(self.config),
            workers_dir=_xdist_workers_dir(self.config),
            session_id=self.root_session_id,
        )
        try:
            self.xdist_index.initialize()
        except XdistDiscoveryError as error:
            raise DebugMcpDependencyError(str(error)) from error
        reporter = self.config.pluginmanager.get_plugin("terminalreporter")
        if reporter is not None:
            reporter.write_line(f"Debug MCP worker discovery index: {_xdist_index_path(self.config)}")

    @staticmethod
    def _clear_stale_cache_discovery(cache_path: Path) -> None:
        try:
            cache_path.unlink(missing_ok=True)
        except OSError as error:
            raise DebugMcpDependencyError(
                f"could not clear stale Debug MCP discovery record {cache_path}: {error}"
            ) from error

    def _start_xdist_worker(self) -> None:
        root_session_id = xdist_root_session_id(self.config)
        if root_session_id is None or self.worker_id is None:
            raise DebugMcpDependencyError("Debug MCP xdist worker identity is missing")
        self.root_session_id = root_session_id
        self.xdist_index = XdistDiscoveryIndex(
            path=_xdist_index_path(self.config),
            workers_dir=_xdist_workers_dir(self.config),
            session_id=root_session_id,
        )
        if self.options.port is not None:
            raise DebugMcpDependencyError(
                "Debug MCP xdist workers need --cuke-mcp-port=auto so each worker can bind a distinct debugger endpoint"
            )
        self._start_services(
            discovery_path=self.xdist_index.worker_path(self.worker_id),
            worker_id=self.worker_id,
            root_session_id=root_session_id,
            on_publish=self.xdist_index.publish_worker,
            on_remove=self.xdist_index.remove_worker,
        )

    def _start_services(
        self,
        *,
        discovery_path: Path,
        worker_id: str | None = None,
        root_session_id: str | None = None,
        on_publish: Any | None = None,
        on_remove: Any | None = None,
    ) -> None:
        ensure_optional_dependencies()
        debugger_port = self.options.port
        if debugger_port is None:
            debugger_port = allocate_port(self.options.host)
        inspection_port = allocate_port(self.options.host, excluding={debugger_port})

        session_id = self._session_id()
        self.artifact_sink = ArtifactSink(
            _artifact_root(self.config, self.options.artifacts_root, session_id, worker_id=worker_id)
        )
        self.queue = FailureQueue(
            session_id=session_id,
            timeout_seconds=self.options.timeout_seconds,
            lease_seconds=self.options.lease_seconds,
        )
        self.inspection = InspectionMcpServer(
            queue=self.queue,
            host=self.options.host,
            port=inspection_port,
            artifact_sink=self.artifact_sink,
            pluginmanager=self.config.pluginmanager,
        )
        self.inspection.start()

        self.debugger = DebuggerMcpProcess(
            host=self.options.host,
            port=debugger_port,
            inspection_endpoint=self.inspection.endpoint,
        )
        self.debugger.start()

        self.discovery = DiscoveryPublisher(
            path=discovery_path,
            session_id=session_id,
            host=self.options.host,
            debugger_endpoint=self.debugger.endpoint,
            inspection_endpoint=self.inspection.endpoint,
            debugger_pid=self.debugger.process.pid if self.debugger.process is not None else 0,
            worker_id=worker_id,
            root_session_id=root_session_id,
            on_publish=on_publish,
            on_remove=on_remove,
        )
        self.queue.set_change_callback(self._publish_state)
        self.discovery.write_initial()
        self._announce()

    def _session_id(self) -> str:
        if self.worker_id is not None:
            return uuid4().hex
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
                with suppress(Exception):
                    self.discovery.remove()
            else:
                last_release = self.queue.last_release if self.queue is not None else None
                with suppress(Exception):
                    self.discovery.close(last_release)
        if self._xdist_controller and self.xdist_index is not None:
            try:
                if remove_discovery:
                    self.xdist_index.remove()
                else:
                    self.xdist_index.close()
            except Exception as error:
                errors.append(error)
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


def _xdist_index_path(config: Any) -> Path:
    return _cache_discovery_path(config).with_name("workers.json")


def _xdist_workers_dir(config: Any) -> Path:
    return _cache_discovery_path(config).with_name("workers")


def _xdist_index(config: Any) -> XdistDiscoveryIndex:
    return XdistDiscoveryIndex(
        path=_xdist_index_path(config),
        workers_dir=_xdist_workers_dir(config),
        session_id=uuid4().hex,
    )


def _worker_id_for_node(node: Any) -> str:
    worker_input = getattr(node, "workerinput", None)
    if isinstance(worker_input, dict):
        for key in ("workerid", "gateway", "gateway_id"):
            worker_id = worker_input.get(key)
            if isinstance(worker_id, str) and worker_id.strip():
                return worker_id
    gateway = getattr(node, "gateway", None)
    worker_id = getattr(gateway, "id", None)
    if isinstance(worker_id, str) and worker_id.strip():
        return worker_id
    raise XdistDiscoveryError("pytest-xdist worker node has no worker or gateway identity")


def _artifact_root(
    config: Any,
    configured_root: Path | None,
    session_id: str,
    *,
    worker_id: str | None = None,
) -> Path:
    if configured_root is None:
        return (_cache_discovery_path(config).parent / "artifacts" / session_id).resolve()
    root = configured_root
    if not root.is_absolute():
        pytest_root = getattr(config, "rootpath", getattr(config, "rootdir", Path.cwd()))
        root = Path(pytest_root) / root
    resolved_root = root.resolve()
    if worker_id is None:
        return resolved_root
    return resolved_root / "workers" / safe_worker_id(worker_id) / session_id


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
