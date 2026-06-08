"""Debug MCP failure hold lifecycle tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.plugin.debug_mcp import entrypoint as debug_mcp_entrypoint
from pytest_bdd.plugin.debug_mcp.failure import FailureSummary, QueuedFailure
from pytest_bdd.plugin.debug_mcp.queue import FailureQueue

if TYPE_CHECKING:
    from pytest_bdd.plugin.debug_mcp.failure import ReleaseRecord
    from pytest_bdd.plugin.debug_mcp.state import Endpoint


class FakeAdapter:
    """Test adapter that records debug entries."""

    def __init__(self, *, continued: bool = False) -> None:
        self.entries: list[tuple[QueuedFailure, Endpoint]] = []
        self._continued = continued

    def enter_failure(self, failure: QueuedFailure, *, endpoint: Endpoint) -> None:
        """Record adapter entry."""
        self.entries.append((failure, endpoint))

    def continued(self, failure: QueuedFailure) -> bool:
        """
        Return configured continuation state.

        Returns:
            Whether raw PDB continuation occurred.

        """
        del failure
        return self._continued


class FakeClock:
    """Mutable clock for timeout and lease tests."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        """
        Return current fake timestamp.

        Returns:
            Current monotonic timestamp.

        """
        return self.now


def _run_debug_mcp_failure(testdir, body: str):
    testdir.monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    testdir.monkeypatch.setattr(debug_mcp_entrypoint, "McpPdbAdapter", FakeAdapter)
    testdir.makeconftest(
        """\
        import json

        from pytest_bdd.plugin.debug_mcp.state import DebugMcpState


        def pytest_sessionfinish(session):
            state = DebugMcpState.from_stash(session.config.stash)
            active = state.queue.active_failure
            payload = {
                "capture": session.config.option.capture,
                "active": None if active is None else active.summary.as_dict(),
                "entries": [
                    {
                        "nodeid": entry.summary.nodeid,
                        "phase": entry.summary.pytest_phase,
                    }
                    for entry in [active]
                    if entry is not None
                ],
            }
            (session.config.rootpath / "debug-state.json").write_text(json.dumps(payload), encoding="utf-8")
        """,
    )
    testdir.makepyfile(test_sample=body)
    result = testdir.runpytest_inprocess("--mcp-pdb-on-fail", plugins=[debug_mcp_entrypoint])
    payload = json.loads((Path(str(testdir.tmpdir)) / "debug-state.json").read_text(encoding="utf-8"))
    discovery = json.loads(
        (Path(str(testdir.tmpdir)) / ".pytest_cache" / "mcp-pdb" / "session.json").read_text(encoding="utf-8"),
    )
    return result, payload, discovery


@pytest.mark.parametrize(
    ("body", "phase"),
    [
        (
            """\
            import pytest


            @pytest.fixture
            def broken():
                raise RuntimeError("setup boom")


            def test_setup_failure(broken):
                pass
            """,
            "setup",
        ),
        (
            """\
            def test_call_failure():
                raise AssertionError("call boom")
            """,
            "call",
        ),
        (
            """\
            import pytest


            @pytest.fixture
            def broken_teardown():
                yield
                raise RuntimeError("teardown boom")


            def test_teardown_failure(broken_teardown):
                pass
            """,
            "teardown",
        ),
    ],
)
def test_debug_mcp_holds_setup_call_and_teardown_failures(testdir, body: str, phase: str) -> None:
    result, payload, discovery = _run_debug_mcp_failure(testdir, body)

    assert result.ret != 0
    assert payload["capture"] == "fd"
    assert payload["active"]["pytest_phase"] == phase
    assert payload["active"]["nodeid"].startswith("test_sample.py::test_")
    assert payload["active"]["artifact_status"] == "missing"
    assert discovery["status"] == "holding_failure"
    assert discovery["active_failure"]["pytest_phase"] == phase


def test_passing_reports_do_not_enqueue(testdir) -> None:
    testdir.monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    testdir.monkeypatch.setattr(debug_mcp_entrypoint, "McpPdbAdapter", FakeAdapter)
    testdir.makeconftest(
        """\
        import json

        from pytest_bdd.plugin.debug_mcp.state import DebugMcpState


        def pytest_sessionfinish(session):
            state = DebugMcpState.from_stash(session.config.stash)
            payload = {"active": state.queue.active_failure is not None}
            (session.config.rootpath / "debug-state.json").write_text(json.dumps(payload), encoding="utf-8")
        """,
    )
    testdir.makepyfile(
        test_sample="""\
        def test_passes():
            assert True
        """,
    )

    result = testdir.runpytest_inprocess("--mcp-pdb-on-fail", plugins=[debug_mcp_entrypoint])
    payload = json.loads((Path(str(testdir.tmpdir)) / "debug-state.json").read_text(encoding="utf-8"))

    assert result.ret == 0
    assert payload == {"active": False}


def test_queue_timeout_lease_release_and_pdb_continue(tmp_path) -> None:
    clock = FakeClock()
    adapter = FakeAdapter()
    queue = FailureQueue(discovery_path=tmp_path / "session.json", adapter=adapter, clock=clock)
    queue.hold_failure(_failure())

    clock.now = 29.0
    assert queue.expire_without_client(timeout_seconds=30.0) is None
    clock.now = 30.0
    timeout = queue.expire_without_client(timeout_seconds=30.0)
    assert_release(timeout, reason="timeout")

    queue.hold_failure(_failure())
    queue.heartbeat()
    clock.now = 35.0
    assert queue.expire_missed_heartbeat(lease_seconds=10.0) is None
    clock.now = 40.0
    lease = queue.expire_missed_heartbeat(lease_seconds=10.0)
    assert_release(lease, reason="lease_expired")

    queue.hold_failure(_failure())
    explicit = queue.release()
    assert_release(explicit, reason="explicit")
    assert explicit.artifact_status == "missing"

    continued_queue = FailureQueue(
        discovery_path=tmp_path / "session.json",
        adapter=FakeAdapter(continued=True),
        clock=clock,
    )
    continued_queue.hold_failure(_failure())
    continued = continued_queue.release_if_pdb_continued()
    assert_release(continued, reason="pdb_continue")


def test_mcp_pdb_imports_are_adapter_only() -> None:
    plugin_root = Path("src/pytest_bdd/plugin/debug_mcp")
    offenders = []
    for path in plugin_root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if path.name != "mcp_pdb_adapter.py" and ("from mcp_pdb" in text or "import mcp_pdb" in text):
            offenders.append(path)

    assert offenders == []


def _failure() -> QueuedFailure:
    return QueuedFailure(
        summary=FailureSummary(
            sequence_id=0,
            nodeid="test_sample.py::test_failure",
            pytest_phase="call",
            exception_type="AssertionError",
            message="boom",
        ),
        longrepr="AssertionError: boom",
    )


def assert_release(record: ReleaseRecord | None, *, reason: str) -> None:
    assert record is not None
    assert record.reason == reason
