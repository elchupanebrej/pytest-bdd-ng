from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("pydantic")

from pytest_cuke.debug_mcp.discovery import DiscoveryPublisher
from pytest_cuke.debug_mcp.options import DebugMcpOptions
from pytest_cuke.debug_mcp import plugin as debug_mcp_plugin
from pytest_cuke.debug_mcp.plugin import DebugMcpPlugin, _artifact_root, _cache_discovery_path
from pytest_cuke.debug_mcp.registry import DiscoveryRegistryError
from pytest_cuke.debug_mcp.state import FailureQueue


def test_debug_mcp_discovery_path_uses_pytest_cache_dir_setting(tmp_path) -> None:
    config = SimpleNamespace(
        rootpath=tmp_path,
        option=SimpleNamespace(cache_dir=None),
        getini=lambda name: "custom-cache" if name == "cache_dir" else None,
    )

    assert _cache_discovery_path(config) == tmp_path / "custom-cache" / "cuke" / "debug-mcp" / "session.json"


def test_debug_mcp_discovery_path_uses_cli_cache_dir_over_ini(tmp_path) -> None:
    cli_cache_dir = tmp_path / "cli-cache"
    config = SimpleNamespace(
        rootpath=tmp_path,
        option=SimpleNamespace(cache_dir=cli_cache_dir),
        getini=lambda name: "ini-cache",
    )

    assert _cache_discovery_path(config) == cli_cache_dir / "cuke" / "debug-mcp" / "session.json"


def test_debug_mcp_artifact_root_defaults_to_session_isolated_cache_directory(tmp_path) -> None:
    config = SimpleNamespace(
        rootpath=tmp_path,
        option=SimpleNamespace(cache_dir=None),
        getini=lambda name: ".pytest_cache",
    )

    root = _artifact_root(config, None, "session-42")

    assert root == (tmp_path / ".pytest_cache" / "cuke" / "debug-mcp" / "artifacts" / "session-42").resolve()
    assert _artifact_root(config, None, "session-43") != root


def test_debug_mcp_artifact_root_resolves_configured_relative_path_from_pytest_root(tmp_path) -> None:
    config = SimpleNamespace(rootpath=tmp_path)

    root = _artifact_root(config, Path("reports/debug-artifacts"), "unused-session")

    assert root == (tmp_path / "reports" / "debug-artifacts").resolve()


def test_configured_artifact_root_scopes_xdist_workers_and_sessions(tmp_path) -> None:
    config = SimpleNamespace(rootpath=tmp_path)
    configured_root = Path("reports/debug-artifacts")
    base = (tmp_path / configured_root).resolve()

    first_worker_run = _artifact_root(config, configured_root, "session-42", worker_id="gw0")
    repeated_worker_run = _artifact_root(config, configured_root, "session-43", worker_id="gw0")
    peer_worker_run = _artifact_root(config, configured_root, "session-42", worker_id="gw1")

    assert first_worker_run == base / "workers" / "gw0" / "session-42"
    assert len({first_worker_run, repeated_worker_run, peer_worker_run}) == 3


def test_startup_failure_removes_stale_discovery_record(tmp_path, monkeypatch) -> None:
    config = SimpleNamespace(
        rootpath=tmp_path,
        option=SimpleNamespace(cache_dir=None),
        getini=lambda name: ".pytest_cache",
    )
    discovery_path = _cache_discovery_path(config)
    discovery_path.parent.mkdir(parents=True)
    discovery_path.write_text('{"status":"holding_failure"}\n', encoding="utf-8")

    def fail_dependency_check() -> None:
        raise debug_mcp_plugin.DebugMcpDependencyError("optional backend unavailable")

    monkeypatch.setattr(debug_mcp_plugin, "ensure_optional_dependencies", fail_dependency_check)
    plugin = DebugMcpPlugin(config=config, options=DebugMcpOptions(enabled=True))

    with pytest.raises(pytest.UsageError, match="optional backend unavailable"):
        plugin.pytest_sessionstart(SimpleNamespace(config=config))

    assert not discovery_path.exists()


def test_xdist_controller_reports_inaccessible_discovery_root_without_starting_services(tmp_path, monkeypatch) -> None:
    cache_root = tmp_path / "cache-is-a-file"
    cache_root.write_text("cache path is not a directory", encoding="utf-8")
    config = SimpleNamespace(
        rootpath=tmp_path,
        option=SimpleNamespace(cache_dir=cache_root, numprocesses=2),
        getini=lambda name: ".pytest_cache",
        pluginmanager=SimpleNamespace(get_plugin=lambda name: object() if name == "dsession" else None),
    )
    monkeypatch.setattr(debug_mcp_plugin, "ensure_optional_dependencies", lambda: None)
    plugin = DebugMcpPlugin(config=config, options=DebugMcpOptions(enabled=True))

    with pytest.raises(
        pytest.UsageError,
        match=(
            r"could not (clear stale Debug MCP discovery record|create worker discovery root directory)"
        ),
    ):
        plugin.pytest_sessionstart(SimpleNamespace(config=config))

    assert cache_root.read_text(encoding="utf-8") == "cache path is not a directory"
    assert plugin.debugger is None
    assert plugin.inspection is None
    assert plugin.discovery is None


class _FailureQueue:
    def __init__(self) -> None:
        self.failures: list[dict[str, object]] = []

    def hold_failure(self, **failure: object) -> None:
        self.failures.append(failure)


@pytest.mark.parametrize("phase", ["setup", "call", "teardown"])
def test_failed_pytest_reports_hold_with_their_phase(phase: str) -> None:
    plugin = DebugMcpPlugin(config=SimpleNamespace(), options=DebugMcpOptions(enabled=True))
    queue = _FailureQueue()
    plugin.queue = queue  # type: ignore[assignment]
    item = SimpleNamespace(nodeid="tests/test_example.py::test_failure", callspec=None, config=SimpleNamespace())
    call = SimpleNamespace(excinfo=SimpleNamespace(value=RuntimeError("failure sentinel")))
    report = SimpleNamespace(failed=True, when=phase, longreprtext="failure sentinel")
    hook = plugin.pytest_runtest_makereport(item, call)

    next(hook)
    with pytest.raises(StopIteration):
        hook.send(SimpleNamespace(get_result=lambda: report))

    assert queue.failures == [
        {
            "nodeid": "tests/test_example.py::test_failure",
            "phase": phase,
            "error_type": "RuntimeError",
            "error_message": "failure sentinel",
            "bdd_context": None,
            "environment": None,
            "fixtures": {},
            "traceback": "failure sentinel",
        }
    ]


def test_passing_report_does_not_create_a_failure_hold() -> None:
    plugin = DebugMcpPlugin(config=SimpleNamespace(), options=DebugMcpOptions(enabled=True))
    queue = _FailureQueue()
    plugin.queue = queue  # type: ignore[assignment]
    item = SimpleNamespace(nodeid="tests/test_example.py::test_pass", callspec=None, config=SimpleNamespace())
    call = SimpleNamespace(excinfo=None)
    report = SimpleNamespace(failed=False, when="call", longreprtext="")
    hook = plugin.pytest_runtest_makereport(item, call)

    next(hook)
    with pytest.raises(StopIteration):
        hook.send(SimpleNamespace(get_result=lambda: report))

    assert queue.failures == []


def test_nonlocal_binding_prints_a_trusted_environment_warning() -> None:
    lines: list[str] = []

    class _Reporter:
        def write_line(self, line: str, **markup: object) -> None:
            lines.append(line)

    reporter = _Reporter()
    plugin = DebugMcpPlugin(
        config=SimpleNamespace(pluginmanager=SimpleNamespace(get_plugin=lambda name: reporter)),
        options=DebugMcpOptions(enabled=True, host="0.0.0.0"),
    )
    plugin.queue = SimpleNamespace(session_id="session-1")  # type: ignore[assignment]
    plugin.debugger = SimpleNamespace(endpoint="http://0.0.0.0:40001/mcp")  # type: ignore[assignment]
    plugin.inspection = SimpleNamespace(endpoint="http://0.0.0.0:40002/mcp")  # type: ignore[assignment]
    plugin.discovery = SimpleNamespace(path=".pytest_cache/cuke/debug-mcp/session.json")  # type: ignore[assignment]

    plugin._announce()

    assert any("trusted environment" in line for line in lines)
    assert "Debug MCP session: session-1 (waiting)" in lines


def test_active_failure_is_written_to_discovery_and_terminal() -> None:
    lines: list[str] = []

    class _Reporter:
        def write_line(self, line: str, **markup: object) -> None:
            lines.append(line)

    class _Discovery:
        def __init__(self) -> None:
            self.states: list[dict[str, object]] = []

        def publish_queue_state(self, state: dict[str, object]) -> None:
            self.states.append(state)

    reporter = _Reporter()
    plugin = DebugMcpPlugin(
        config=SimpleNamespace(pluginmanager=SimpleNamespace(get_plugin=lambda name: reporter)),
        options=DebugMcpOptions(enabled=True),
    )
    discovery = _Discovery()
    plugin.discovery = discovery  # type: ignore[assignment]

    plugin._publish_state(
        {
            "session_id": "session-1",
            "status": "holding_failure",
            "active_failure": {
                "sequence": 2,
                "phase": "call",
                "nodeid": "tests/test_example.py::test_failure",
                "error_type": "RuntimeError",
                "error_message": "failure sentinel",
            },
        }
    )

    assert discovery.states[0]["status"] == "holding_failure"
    assert lines == [
        "Debug MCP holding failure #2 (call) at tests/test_example.py::test_failure: "
        "RuntimeError: failure sentinel"
    ]


def test_failure_hold_includes_redacted_fixtures_and_traceback(monkeypatch) -> None:
    monkeypatch.setenv("TEST_TOKEN", "top-secret-123")

    class Widget:
        pass

    plugin = DebugMcpPlugin(config=SimpleNamespace(), options=DebugMcpOptions(enabled=True))
    queue = _FailureQueue()
    plugin.queue = queue  # type: ignore[assignment]
    item = SimpleNamespace(
        nodeid="tests/test_example.py::test_failure",
        callspec=None,
        config=SimpleNamespace(),
        funcargs={"token_value": "top-secret-123", "count": 3, "widget": Widget()},
    )
    call = SimpleNamespace(excinfo=SimpleNamespace(value=RuntimeError("failed with top-secret-123")))
    report = SimpleNamespace(failed=True, when="call", longreprtext="trace contains top-secret-123")
    hook = plugin.pytest_runtest_makereport(item, call)

    next(hook)
    with pytest.raises(StopIteration):
        hook.send(SimpleNamespace(get_result=lambda: report))

    failure = queue.failures[0]
    assert failure["error_message"] == "failed with <redacted>"
    assert failure["traceback"] == "trace contains <redacted>"
    assert failure["fixtures"]["token_value"] == "<redacted>"
    assert failure["fixtures"]["count"] == 3
    assert failure["fixtures"]["widget"].startswith("<Widget:")


def test_oversized_failure_diagnostics_are_truncated_before_the_hold() -> None:
    oversized = "あ" * 2_000_000
    plugin = DebugMcpPlugin(config=SimpleNamespace(), options=DebugMcpOptions(enabled=True))
    queue = _FailureQueue()
    plugin.queue = queue  # type: ignore[assignment]
    item = SimpleNamespace(nodeid="tests/test_example.py::test_failure", callspec=None, config=SimpleNamespace())
    call = SimpleNamespace(excinfo=SimpleNamespace(value=RuntimeError(oversized)))
    report = SimpleNamespace(failed=True, when="call", longreprtext=oversized)
    hook = plugin.pytest_runtest_makereport(item, call)

    next(hook)
    with pytest.raises(StopIteration):
        hook.send(SimpleNamespace(get_result=lambda: report))

    failure = queue.failures[0]
    error_message = failure["error_message"]
    traceback = failure["traceback"]
    assert isinstance(error_message, str)
    assert isinstance(traceback, str)
    assert len(error_message) < 100_000
    assert len(traceback) < 100_000
    assert "truncated" in traceback
    assert len(json.dumps(failure)) < 1_000_000


class _Reporter:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def write_line(self, line: str, **markup: object) -> None:
        self.lines.append(line)


class _FailingDiscovery:
    def __init__(self) -> None:
        self.attempts = 0

    def publish_queue_state(self, state: dict[str, object]) -> None:
        self.attempts += 1
        raise DiscoveryRegistryError("registry unreachable")


class _CountingDiscovery:
    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.attempts = 0

    def publish_queue_state(self, state: dict[str, object]) -> None:
        self.attempts += 1
        self.inner.publish_queue_state(state)


class _RecordingDiscovery:
    def __init__(self) -> None:
        self.states: list[dict[str, object]] = []

    def publish_queue_state(self, state: dict[str, object]) -> None:
        self.states.append(state)


def _wait_until(predicate: Callable[[], bool], timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    pytest.fail("timed out waiting for the Debug MCP publish state")


def _wait_for_active(queue: FailureQueue, timeout: float = 2.0) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        active = queue.inspect_failure().get("active_failure")
        if isinstance(active, dict):
            return active
        time.sleep(0.005)
    pytest.fail("the Debug MCP failure hold did not become active")


def _start_failure_hold(
    plugin: DebugMcpPlugin,
    *,
    nodeid: str = "tests/test_example.py::test_failure",
    error_message: str = "failure sentinel",
) -> tuple[threading.Thread, list[BaseException]]:
    errors: list[BaseException] = []
    item = SimpleNamespace(nodeid=nodeid, callspec=None, config=SimpleNamespace())
    call = SimpleNamespace(excinfo=SimpleNamespace(value=RuntimeError(error_message)))
    report = SimpleNamespace(failed=True, when="call", longreprtext=error_message)

    def run() -> None:
        try:
            hook = plugin.pytest_runtest_makereport(item, call)
            next(hook)
            with suppress(StopIteration):
                hook.send(SimpleNamespace(get_result=lambda: report))
        except BaseException as error:
            errors.append(error)

    thread = threading.Thread(target=run)
    thread.start()
    return thread, errors


@pytest.mark.parametrize("transport", ["registry", "cache"])
def test_failed_discovery_publish_keeps_the_hold_and_warns_once(transport: str, tmp_path) -> None:
    reporter = _Reporter()
    plugin = DebugMcpPlugin(
        config=SimpleNamespace(pluginmanager=SimpleNamespace(get_plugin=lambda name: reporter)),
        options=DebugMcpOptions(enabled=True),
    )
    queue = FailureQueue(session_id="session-1", timeout_seconds=5.0, lease_seconds=5.0)
    plugin.queue = queue
    if transport == "registry":
        counting = _CountingDiscovery(_FailingDiscovery())
        plugin.discovery = counting  # type: ignore[assignment]
        failing = counting  # type: ignore[assignment]
    else:
        blocker = tmp_path / "cache-is-a-file"
        blocker.write_text("not a directory", encoding="utf-8")
        counting = _CountingDiscovery(
            DiscoveryPublisher(
                path=blocker / "session.json",
                session_id="session-1",
                host="127.0.0.1",
                debugger_endpoint="http://127.0.0.1:40001/mcp",
                inspection_endpoint="http://127.0.0.1:40002/mcp",
                debugger_pid=0,
            )
        )
        plugin.discovery = counting  # type: ignore[assignment]
        failing = counting  # type: ignore[assignment]
    queue.set_change_callback(plugin._publish_state)

    hold, errors = _start_failure_hold(plugin)
    active = _wait_for_active(queue)
    _wait_until(lambda: failing.attempts >= 1)
    _wait_until(lambda: any("holding failure #1" in line for line in reporter.lines))
    _wait_until(lambda: any("discovery publish failed" in line for line in reporter.lines))
    assert errors == []
    assert plugin._holds == 1
    assert sum("discovery publish failed" in line for line in reporter.lines) == 1

    queue.release_failure(session_id="session-1", sequence=active["sequence"])
    hold.join(timeout=2.0)
    assert not hold.is_alive()
    _wait_until(lambda: failing.attempts >= 2)
    assert sum("discovery publish failed" in line for line in reporter.lines) == 1

    recording = _RecordingDiscovery()
    plugin.discovery = recording  # type: ignore[assignment]
    hold, errors = _start_failure_hold(plugin, nodeid="tests/test_example.py::test_second", error_message="second")
    active = _wait_for_active(queue)
    assert active["sequence"] == 2
    _wait_until(lambda: any(state.get("active_failure") for state in recording.states))
    queue.release_failure(session_id="session-1", sequence=active["sequence"])
    hold.join(timeout=2.0)
    _wait_until(lambda: any("holding failure #2" in line for line in reporter.lines))

    assert not hold.is_alive()
    assert errors == []
    assert plugin._holds == 2
    assert any("holding failure #2" in line for line in reporter.lines)
    assert sum("discovery publish failed" in line for line in reporter.lines) == 1
