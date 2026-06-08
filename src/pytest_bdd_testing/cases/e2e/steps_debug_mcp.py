"""Step definitions for debug MCP feature docs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest

from pytest_bdd import given, parsers, then, when
from pytest_bdd.plugin.debug_mcp.discovery import SessionDiscovery
from pytest_bdd.plugin.debug_mcp.failure import FailureSummary, QueuedFailure
from pytest_bdd.plugin.debug_mcp.options import DebugMcpOptions
from pytest_bdd.plugin.debug_mcp.queue import FailureQueue
from pytest_bdd.plugin.debug_mcp.sidecar import DebugMcpSidecar
from pytest_bdd.plugin.debug_mcp.state import DebugMcpState
from pytest_bdd.plugin.debug_mcp.xdist import debug_mcp_discovery_path, write_debug_mcp_discovery

if TYPE_CHECKING:
    from pytest_bdd.plugin.debug_mcp.failure import PytestPhase


class FakeAdapter:
    """No-op adapter for feature-level debug MCP tests."""

    def enter_failure(self, failure: QueuedFailure, *, endpoint) -> None:
        """Ignore real debugger entry."""
        del failure, endpoint

    def continued(self, failure: QueuedFailure) -> bool:
        """Report no raw continuation."""
        del failure
        return False


class FakeConfig:
    """Minimal xdist config for feature-level debug MCP tests."""

    def __init__(self, rootpath: Path, worker_id: str) -> None:
        self.rootpath = rootpath
        self.workerinput: dict[str, Any] = {"workerid": worker_id}


@pytest.fixture
def debug_mcp_context(tmp_path: Path) -> dict[str, Any]:
    """Return mutable debug MCP feature context."""
    return {"root": tmp_path, "states": {}, "results": {}}


@given(parsers.parse('a debug MCP session on worker "{worker_id}"'))
def debug_mcp_worker_session(debug_mcp_context: dict[str, Any], worker_id: str) -> None:
    """Create a worker-local debug MCP state."""
    config = FakeConfig(debug_mcp_context["root"], worker_id)
    port_offset = len(debug_mcp_context["states"])
    options = DebugMcpOptions(enabled=True)
    path = debug_mcp_discovery_path(config)
    queue = FailureQueue(
        discovery_path=path,
        adapter=FakeAdapter(),
        discovery_writer=lambda state, discovery: write_debug_mcp_discovery(config, state, discovery),
    )
    state = DebugMcpState.from_options(
        options,
        mcp_port=12000 + port_offset,
        sidecar_port=13000 + port_offset,
        queue=queue,
    )
    debug_mcp_context["states"][worker_id] = {"config": config, "state": state}


@given(parsers.parse('worker "{worker_id}" holds a "{phase}" failure'))
@when(parsers.parse('worker "{worker_id}" holds a "{phase}" failure'))
def worker_holds_failure(debug_mcp_context: dict[str, Any], worker_id: str, phase: str) -> None:
    """Hold a worker-local failure."""
    state = _state(debug_mcp_context, worker_id)
    state.queue.hold_failure(_failure(phase=phase, bdd=None), state=state)


@given(parsers.parse('worker "{worker_id}" holds a "{phase}" failure with BDD metadata'))
def worker_holds_failure_with_bdd(debug_mcp_context: dict[str, Any], worker_id: str, phase: str) -> None:
    """Hold a worker-local failure enriched with BDD metadata."""
    state = _state(debug_mcp_context, worker_id)
    bdd = {
        "feature_path": "features/17 Debug MCP/01 Agentic debugging.feature.md",
        "feature_name": "Agentic debugging",
        "scenario_name": "BDD metadata is included in investigation artifacts",
        "step_keyword": "When",
        "step_text": "the agent writes a valid investigation artifact",
        "tags": ["debug-mcp"],
        "example_row": {},
    }
    state.queue.hold_failure(_failure(phase=phase, bdd=bdd), state=state)


@when(parsers.parse('worker "{worker_id}" announces debug MCP discovery'))
def worker_announces_discovery(debug_mcp_context: dict[str, Any], worker_id: str) -> None:
    """Write worker waiting discovery."""
    entry = _entry(debug_mcp_context, worker_id)
    write_debug_mcp_discovery(entry["config"], entry["state"], SessionDiscovery.waiting(entry["state"]))


@when("the worker announces debug MCP discovery")
def first_worker_announces_discovery(debug_mcp_context: dict[str, Any]) -> None:
    """Write waiting discovery for the first worker in context."""
    worker_id = next(iter(debug_mcp_context["states"]))
    worker_announces_discovery(debug_mcp_context, worker_id)


@when("the agent writes a valid investigation artifact")
def agent_writes_valid_artifact(debug_mcp_context: dict[str, Any]) -> None:
    """Write a valid artifact through the sidecar API."""
    state = _first_state(debug_mcp_context)
    active = state.queue.require_active()
    sidecar = DebugMcpSidecar(state=state)
    result = sidecar.write_investigation_artifact(_artifact_payload(active.summary.bdd or {}))
    debug_mcp_context["results"]["artifact"] = result


@when("the agent writes an invalid investigation artifact")
def agent_writes_invalid_artifact(debug_mcp_context: dict[str, Any]) -> None:
    """Attempt to write an invalid sidecar artifact."""
    state = _first_state(debug_mcp_context)
    sidecar = DebugMcpSidecar(state=state)
    debug_mcp_context["results"]["artifact"] = sidecar.write_investigation_artifact({"nodeid": "tests/test_debug.py"})


@then(parsers.parse('the debug MCP root discovery lists worker "{worker_id}"'))
def root_discovery_lists_worker(debug_mcp_context: dict[str, Any], worker_id: str) -> None:
    """Assert root discovery references a worker."""
    workers = _workers(debug_mcp_context)
    assert worker_id in workers


@then(parsers.parse('worker "{worker_id}" exposes mcp-pdb and sidecar endpoints'))
def worker_exposes_endpoints(debug_mcp_context: dict[str, Any], worker_id: str) -> None:
    """Assert endpoint details are visible."""
    worker = _workers(debug_mcp_context)[worker_id]
    assert worker["mcp_pdb"]["port"] > 0
    assert worker["sidecar"]["port"] > 0


@then(parsers.parse('worker "{worker_id}" is holding a "{phase}" failure'))
def worker_is_holding_failure(debug_mcp_context: dict[str, Any], worker_id: str, phase: str) -> None:
    """Assert worker active failure state."""
    worker = _workers(debug_mcp_context)[worker_id]
    assert worker["status"] == "holding_failure"
    assert worker["active_failure"]["pytest_phase"] == phase


@then(parsers.parse('worker "{worker_id}" is waiting for a failure'))
def worker_is_waiting(debug_mcp_context: dict[str, Any], worker_id: str) -> None:
    """Assert worker waiting state."""
    worker = _workers(debug_mcp_context)[worker_id]
    assert worker["status"] == "waiting_for_failure"
    assert worker["active_failure"] is None


@then("the investigation artifact JSON is accepted")
def artifact_json_is_accepted(debug_mcp_context: dict[str, Any]) -> None:
    """Assert artifact JSON was written."""
    result = debug_mcp_context["results"]["artifact"]
    assert result["ok"] is True
    assert Path(result["artifact"]["json_path"]).exists()


@then("the investigation artifact Markdown is created")
def artifact_markdown_is_created(debug_mcp_context: dict[str, Any]) -> None:
    """Assert artifact Markdown was written."""
    result = debug_mcp_context["results"]["artifact"]
    assert Path(result["artifact"]["markdown_path"]).exists()


@then("the investigation artifact is rejected")
def artifact_is_rejected(debug_mcp_context: dict[str, Any]) -> None:
    """Assert invalid artifact response."""
    result = debug_mcp_context["results"]["artifact"]
    assert result["ok"] is False
    assert result["error"] == "validation_error"


@then("the investigation artifact JSON contains BDD metadata")
def artifact_contains_bdd_metadata(debug_mcp_context: dict[str, Any]) -> None:
    """Assert persisted artifact includes BDD context."""
    result = debug_mcp_context["results"]["artifact"]
    payload = json.loads(Path(result["artifact"]["json_path"]).read_text(encoding="utf-8"))
    assert payload["bdd_metadata"]["feature_name"] == "Agentic debugging"
    assert payload["bdd_metadata"]["scenario_name"] == "BDD metadata is included in investigation artifacts"


def _entry(debug_mcp_context: dict[str, Any], worker_id: str) -> dict[str, Any]:
    return debug_mcp_context["states"][worker_id]


def _state(debug_mcp_context: dict[str, Any], worker_id: str) -> DebugMcpState:
    return _entry(debug_mcp_context, worker_id)["state"]


def _first_state(debug_mcp_context: dict[str, Any]) -> DebugMcpState:
    first = next(iter(debug_mcp_context["states"].values()))
    return first["state"]


def _workers(debug_mcp_context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    root = debug_mcp_context["root"] / ".pytest_cache" / "mcp-pdb" / "session.json"
    payload = json.loads(root.read_text(encoding="utf-8"))
    return {worker["worker_id"]: worker for worker in payload["workers"]}


def _failure(*, phase: str, bdd: dict[str, Any] | None) -> QueuedFailure:
    return QueuedFailure(
        summary=FailureSummary(
            sequence_id=0,
            nodeid=f"tests/test_debug.py::test_{phase}",
            pytest_phase=cast("PytestPhase", phase),
            exception_type="AssertionError",
            message="boom",
            bdd=bdd,
        ),
        longrepr="AssertionError: boom",
    )


def _artifact_payload(bdd: dict[str, Any]) -> dict[str, object]:
    return {
        "artifact_id": "debug-mcp-artifact",
        "links": ["session://debug-mcp/current"],
        "nodeid": "tests/test_debug.py::test_call",
        "pytest_phase": "call",
        "status": "investigated",
        "summary": "The paused failure was inspected.",
        "inspected_commands": ["where", "p scenario_name"],
        "evidence": ["The active failure points at the expected BDD scenario."],
        "suspected_cause": "The test fixture returned an unexpected value.",
        "next_action": "Update the fixture and rerun the failing scenario.",
        "bdd_metadata": bdd,
    }
