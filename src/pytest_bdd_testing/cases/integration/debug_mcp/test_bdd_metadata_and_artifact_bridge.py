"""Debug MCP BDD metadata and artifact hook bridge tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from returns.maybe import Nothing, Some

from pytest_bdd.compatibility.pytest import PytestPluginManager
from pytest_bdd.plugin.debug_mcp import bdd_adapter
from pytest_bdd.plugin.debug_mcp.artifacts import ArtifactSink
from pytest_bdd.plugin.debug_mcp.bdd_adapter import BddContextExtractor, enrich_failure_with_bdd_context
from pytest_bdd.plugin.debug_mcp.failure import FailureSummary, QueuedFailure
from pytest_bdd.plugin.debug_mcp.hookspec import DebugMcpHookSpec
from pytest_bdd.plugin.debug_mcp.options import DebugMcpOptions
from pytest_bdd.plugin.debug_mcp.queue import FailureQueue
from pytest_bdd.plugin.debug_mcp.sidecar import DebugMcpSidecar
from pytest_bdd.plugin.debug_mcp.state import DebugMcpState


def test_bdd_context_extractor_reads_active_scenario_metadata(monkeypatch) -> None:
    config = SimpleNamespace(stash={})
    monkeypatch.setattr(bdd_adapter, "Run", RunWith(_scenario_run()))

    metadata = BddContextExtractor.extract(config)

    assert metadata is not None
    assert metadata.feature_path == "features/debug.feature"
    assert metadata.feature_name == "Debug MCP"
    assert metadata.scenario_name == "Agent inspects failure"
    assert metadata.step_keyword == "When "
    assert metadata.step_text == "the step fails"
    assert metadata.tags == ["debug", "smoke"]
    assert metadata.example_row == {"breadcrumb": "Examples: row 1"}


def test_bdd_context_extractor_returns_none_for_plain_pytest(monkeypatch) -> None:
    config = SimpleNamespace(stash={})
    monkeypatch.setattr(bdd_adapter, "Run", EmptyRun())

    assert BddContextExtractor.extract(config) is None


def test_enriched_failure_and_sidecar_bdd_context_match(monkeypatch, tmp_path) -> None:
    config = SimpleNamespace(stash={})
    monkeypatch.setattr(bdd_adapter, "Run", RunWith(_scenario_run()))
    state = _state(tmp_path)

    failure = enrich_failure_with_bdd_context(config, _failure())
    active = state.queue.hold_failure(failure)
    sidecar = DebugMcpSidecar(state=state, artifact_sink=ArtifactSink(tmp_path / "artifacts"))

    assert active.summary.bdd is not None
    assert sidecar.get_bdd_context() == active.summary.bdd
    assert active.summary.bdd["scenario_name"] == "Agent inspects failure"


def test_artifact_hook_receives_bdd_metadata_and_paths(tmp_path) -> None:
    pluginmanager = PytestPluginManager()
    pluginmanager.add_hookspecs(DebugMcpHookSpec)
    recorder = HookRecorder()
    pluginmanager.register(recorder)
    state = _state(tmp_path)
    state.queue.hold_failure(_failure())
    sidecar = DebugMcpSidecar(
        state=state,
        artifact_sink=ArtifactSink(tmp_path / "artifacts"),
        pluginmanager=pluginmanager,
    )
    payload = _artifact_payload()
    payload["bdd_metadata"] = {
        "feature_path": "features/debug.feature",
        "feature_name": "Debug MCP",
        "scenario_name": "Agent inspects failure",
        "step_keyword": "When ",
        "step_text": "the step fails",
        "tags": ["debug"],
        "example_row": {},
    }

    result = sidecar.write_investigation_artifact(payload)

    assert result["ok"] is True
    assert len(recorder.events) == 1
    event = recorder.events[0]
    assert event["nodeid"] == "test_sample.py::test_failure"
    assert event["pytest_phase"] == "call"
    assert event["bdd_metadata"]["scenario_name"] == "Agent inspects failure"
    assert Path(event["json_path"]).exists()
    assert Path(event["markdown_path"]).exists()
    assert event["status"] == "investigated"
    assert "wrong fixture" in event["summary"]


def test_plain_pytest_artifact_write_succeeds_without_hook_consumers(tmp_path) -> None:
    state = _state(tmp_path)
    state.queue.hold_failure(_failure())
    sidecar = DebugMcpSidecar(state=state, artifact_sink=ArtifactSink(tmp_path / "artifacts"))

    result = sidecar.write_investigation_artifact(_artifact_payload())

    assert result["ok"] is True


class HookRecorder:
    """Record debug MCP artifact hook calls."""

    @pytest.hookimpl
    def pytest_bdd_debug_mcp_artifact_created(
        self,
        nodeid,
        pytest_phase,
        bdd_metadata,
        json_path,
        markdown_path,
        status,
        summary,
    ) -> None:
        """Record artifact-created event."""
        self.events.append(
            {
                "nodeid": nodeid,
                "pytest_phase": pytest_phase,
                "bdd_metadata": bdd_metadata,
                "json_path": json_path,
                "markdown_path": markdown_path,
                "status": status,
                "summary": summary,
            },
        )

    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []


class RunWith:
    def __init__(self, scenario_run) -> None:
        self._run = SimpleNamespace(active_scenario_run=scenario_run)

    def find_in_stash(self, stash):
        del stash
        return Some(self._run)


class EmptyRun:
    def find_in_stash(self, stash):
        del stash
        return Nothing


def _scenario_run():
    step = SimpleNamespace(text="the step fails")
    pickle = SimpleNamespace(
        name="Agent inspects failure",
        tags=[SimpleNamespace(name="@debug"), SimpleNamespace(name="@smoke")],
    )
    feature = SimpleNamespace(name="Debug MCP")
    binding = SimpleNamespace(
        filename="features/debug.feature",
        gherkin_document=SimpleNamespace(feature=feature),
        pickle_step_ast_step=lambda _step: SimpleNamespace(keyword="When "),
        pickle_table_rows_breadcrumb=lambda _pickle: "Examples: row 1",
    )
    return SimpleNamespace(
        feature_binding=binding,
        gherkin_document=SimpleNamespace(feature=feature),
        pickle=pickle,
        step_object=step,
        feature_uri="features/debug.feature",
    )


def _state(tmp_path) -> DebugMcpState:
    options = DebugMcpOptions(enabled=True)
    queue = FailureQueue(discovery_path=tmp_path / "session.json", adapter=FakeAdapter())
    return DebugMcpState.from_options(options, mcp_port=12345, sidecar_port=12346, queue=queue)


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


class FakeAdapter:
    """Test adapter for artifact bridge tests."""

    def enter_failure(self, failure: QueuedFailure, *, endpoint) -> None:
        """Accept adapter entry without real debugger work."""
        del failure, endpoint

    def continued(self, failure: QueuedFailure) -> bool:
        """
        Return raw PDB continuation state.

        Returns:
            False for bridge tests.

        """
        del failure
        return False


def _artifact_payload() -> dict[str, object]:
    return {
        "artifact_id": "artifact-1",
        "links": ["session://debug-mcp/current"],
        "nodeid": "test_sample.py::test_failure",
        "pytest_phase": "call",
        "status": "investigated",
        "summary": "Failure caused by a wrong fixture value.",
        "inspected_commands": ["where", "p local_value"],
        "evidence": ["local_value was 41"],
        "suspected_cause": "fixture returns wrong value",
        "next_action": "change fixture to return 42",
        "bdd_metadata": {},
    }
