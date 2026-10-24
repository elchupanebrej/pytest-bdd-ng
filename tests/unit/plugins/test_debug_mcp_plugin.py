from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("pydantic")

from pytest_cuke.debug_mcp.options import DebugMcpOptions
from pytest_cuke.debug_mcp import plugin as debug_mcp_plugin
from pytest_cuke.debug_mcp.plugin import DebugMcpPlugin, _artifact_root, _cache_discovery_path


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
            "could not (clear stale Debug MCP discovery record|create worker discovery root directory)"
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
