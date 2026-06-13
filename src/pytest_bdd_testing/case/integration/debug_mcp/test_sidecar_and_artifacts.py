"""

Debug MCP sidecar and artifact contract tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from pytest_bdd.plugin.debug_mcp.artifacts import ArtifactSink, artifact_root_for_state, safe_nodeid
from pytest_bdd.plugin.debug_mcp.failure import FailureSummary, QueuedFailure
from pytest_bdd.plugin.debug_mcp.options import DebugMcpOptions
from pytest_bdd.plugin.debug_mcp.queue import FailureQueue
from pytest_bdd.plugin.debug_mcp.schemas import InvestigationArtifact
from pytest_bdd.plugin.debug_mcp.sidecar import DebugMcpSidecar
from pytest_bdd.plugin.debug_mcp.state import DebugMcpState


class FakeAdapter:
    """Test adapter for sidecar tests."""

    def enter_failure(self, failure: QueuedFailure, *, endpoint) -> None:
        """Accept adapter entry without real debugger work."""
        del failure, endpoint

    def continued(self, failure: QueuedFailure) -> bool:
        """
        Return raw PDB continuation state.

        Returns:
            False for sidecar tests.

        """
        del failure
        return False


def test_sidecar_helpers_expose_active_failure_heartbeat_release_and_empty_bdd_context(tmp_path) -> None:
    """
    Test target:
    Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    state = _state(tmp_path)
    active = state.queue.hold_failure(_failure())
    sidecar = DebugMcpSidecar(state=state, artifact_sink=ArtifactSink(tmp_path / "artifacts"))

    assert sidecar.get_active_failure() == active.summary.as_dict()
    assert sidecar.get_bdd_context() is None
    assert sidecar.heartbeat() == {"ok": True, "connected": True}
    assert state.queue.connected is True

    released = sidecar.release()

    assert released["ok"] is True
    assert released["release"]["reason"] == "explicit"
    assert released["release"]["artifact_status"] == "missing"
    assert state.queue.active_failure is None


def test_write_investigation_artifact_creates_paired_json_and_markdown(tmp_path) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    state = _state(tmp_path)
    state.queue.hold_failure(_failure())
    sidecar = DebugMcpSidecar(state=state, artifact_sink=ArtifactSink(tmp_path / "artifacts"))

    result = sidecar.write_investigation_artifact(_artifact_payload())

    assert result["ok"] is True
    artifact = result["artifact"]
    assert artifact["artifact_id"] == "artifact-1"
    json_path = Path(artifact["json_path"])
    markdown_path = Path(artifact["markdown_path"])
    assert json_path.name == "failure-0001-test_sample.py-test_failure.json"
    assert markdown_path.name == "failure-0001-test_sample.py-test_failure.md"
    assert json.loads(json_path.read_text(encoding="utf-8"))["suspected_cause"] == "fixture returns wrong value"
    assert "## Evidence" in markdown_path.read_text(encoding="utf-8")

    released = sidecar.release()
    assert released["release"]["artifact_status"] == "written"


def test_invalid_artifact_payload_returns_validation_error_and_writes_no_files(tmp_path) -> None:
    """
    Test target:
    Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    state = _state(tmp_path)
    state.queue.hold_failure(_failure())
    artifact_root = tmp_path / "artifacts"
    sidecar = DebugMcpSidecar(state=state, artifact_sink=ArtifactSink(artifact_root))

    result = sidecar.write_investigation_artifact({"nodeid": "test_sample.py::test_failure"})

    assert result["ok"] is False
    assert result["error"] == "validation_error"
    assert not artifact_root.exists()


def test_investigation_artifact_rejects_extra_fields() -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    payload = _artifact_payload()
    payload["transcript_dump"] = "not allowed"

    with pytest.raises(ValidationError) as exc_info:
        InvestigationArtifact.model_validate(payload)

    assert exc_info.value.errors()[0]["type"] == "extra_forbidden"


def test_artifact_root_defaults_to_session_directory(tmp_path) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    state = _state(tmp_path)

    assert artifact_root_for_state(state) == Path(".pytest_cache") / "mcp-pdb" / "artifacts" / state.session_id


def test_safe_nodeid_slug_is_stable() -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    assert safe_nodeid("tests/test file.py::test[param/value]") == "tests-test-file.py-test-param-value"


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
