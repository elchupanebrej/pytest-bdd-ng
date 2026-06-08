"""Debug MCP xdist worker discovery tests."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pytest_bdd.plugin.debug_mcp.discovery import SessionDiscovery
from pytest_bdd.plugin.debug_mcp.failure import FailureSummary, QueuedFailure
from pytest_bdd.plugin.debug_mcp.options import DebugMcpOptions
from pytest_bdd.plugin.debug_mcp.queue import FailureQueue
from pytest_bdd.plugin.debug_mcp.state import DebugMcpState
from pytest_bdd.plugin.debug_mcp.xdist import debug_mcp_discovery_path, write_debug_mcp_discovery

if TYPE_CHECKING:
    from pathlib import Path


class FakeAdapter:
    """No-op debug adapter for worker tests."""

    def enter_failure(self, failure: QueuedFailure, *, endpoint) -> None:
        """Ignore real debugger entry."""
        del failure, endpoint

    def continued(self, failure: QueuedFailure) -> bool:
        """Report no raw PDB continuation."""
        del failure
        return False


class FakeConfig:
    """Minimal config object for xdist discovery helpers."""

    def __init__(self, rootpath: Path, worker_id: str | None = None) -> None:
        self.rootpath = rootpath
        if worker_id is not None:
            self.workerinput: dict[str, Any] = {"workerid": worker_id}


def test_non_xdist_discovery_path_is_root_session(tmp_path: Path) -> None:
    config = FakeConfig(tmp_path)

    assert debug_mcp_discovery_path(config) == tmp_path / ".pytest_cache" / "mcp-pdb" / "session.json"


def test_xdist_worker_writes_worker_file_and_root_index(tmp_path: Path) -> None:
    gw0 = FakeConfig(tmp_path, worker_id="gw0")
    gw1 = FakeConfig(tmp_path, worker_id="gw1")
    state0 = _state(gw0, mcp_port=12000, sidecar_port=13000)
    state1 = _state(gw1, mcp_port=12001, sidecar_port=13001)

    write_debug_mcp_discovery(gw0, state0, SessionDiscovery.waiting(state0))
    write_debug_mcp_discovery(gw1, state1, SessionDiscovery.waiting(state1))

    worker0 = tmp_path / ".pytest_cache" / "mcp-pdb" / "workers" / "gw0.json"
    worker1 = tmp_path / ".pytest_cache" / "mcp-pdb" / "workers" / "gw1.json"
    root = tmp_path / ".pytest_cache" / "mcp-pdb" / "session.json"
    assert worker0.exists()
    assert worker1.exists()

    payload = json.loads(root.read_text(encoding="utf-8"))
    assert payload["status"] == "waiting_for_failure"
    assert [worker["worker_id"] for worker in payload["workers"]] == ["gw0", "gw1"]
    assert payload["workers"][0]["mcp_pdb"]["port"] == 12000
    assert payload["workers"][1]["sidecar"]["port"] == 13001


def test_worker_hold_updates_only_that_worker_active_failure_and_root_status(tmp_path: Path) -> None:
    gw0 = FakeConfig(tmp_path, worker_id="gw0")
    gw1 = FakeConfig(tmp_path, worker_id="gw1")
    state0 = _state(gw0, mcp_port=12000, sidecar_port=13000)
    state1 = _state(gw1, mcp_port=12001, sidecar_port=13001)

    state0.queue.hold_failure(_failure("tests/test_a.py::test_a"), state=state0)
    assert state1.queue.discovery_writer is not None
    state1.queue.discovery_writer(state1, SessionDiscovery.waiting(state1))

    root = tmp_path / ".pytest_cache" / "mcp-pdb" / "session.json"
    payload = json.loads(root.read_text(encoding="utf-8"))
    workers = {worker["worker_id"]: worker for worker in payload["workers"]}

    assert payload["status"] == "holding_failure"
    assert workers["gw0"]["status"] == "holding_failure"
    assert workers["gw0"]["active_failure"]["nodeid"] == "tests/test_a.py::test_a"
    assert workers["gw1"]["status"] == "waiting_for_failure"
    assert workers["gw1"]["active_failure"] is None


def _state(config: FakeConfig, *, mcp_port: int, sidecar_port: int) -> DebugMcpState:
    options = DebugMcpOptions(enabled=True)
    path = debug_mcp_discovery_path(config)
    queue = FailureQueue(
        discovery_path=path,
        adapter=FakeAdapter(),
        discovery_writer=lambda state, discovery: write_debug_mcp_discovery(config, state, discovery),
    )
    return DebugMcpState.from_options(options, mcp_port=mcp_port, sidecar_port=sidecar_port, queue=queue)


def _failure(nodeid: str) -> QueuedFailure:
    return QueuedFailure(
        summary=FailureSummary(
            sequence_id=0,
            nodeid=nodeid,
            pytest_phase="call",
            exception_type="AssertionError",
            message="boom",
        ),
        longrepr="AssertionError: boom",
    )
