from __future__ import annotations

from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "007-maximize-messages-coverage"
    / "contracts"
    / "messages-capability-coverage.openapi.yaml"
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def test_messages_capability_coverage_contract_exists() -> None:
    assert CONTRACT_PATH.exists()


def test_contract_has_required_paths() -> None:
    contract_text = _contract_text()
    assert "/coverage/capabilities/sync:" in contract_text
    assert "/coverage/decisions/upsert:" in contract_text
    assert "/coverage/mappings/validate:" in contract_text
    assert "/coverage/baseline/diff:" in contract_text
    assert "/coverage/checklist/render:" in contract_text


def test_contract_sync_and_decision_paths_reference_required_schemas() -> None:
    contract_text = _contract_text()
    assert "CapabilitySyncRequest:" in contract_text
    assert "CapabilitySyncResponse:" in contract_text
    assert "CapabilityDecisionRequest:" in contract_text
    assert "CapabilityDecisionResponse:" in contract_text


def test_contract_enforces_mandatory_evidence_fields() -> None:
    contract_text = _contract_text()
    assert "missing_required_evidence_fields" in contract_text
    assert "rationale" in contract_text
    assert "decision_owner" in contract_text
    assert "evidence_refs" in contract_text
    assert "reviewed_at" in contract_text


def test_contract_mapping_validation_schema_defines_fixed_matrix_profile() -> None:
    contract_text = _contract_text()
    assert "MappingValidationRequest:" in contract_text
    assert "MappingValidationResult:" in contract_text
    assert "fixed_release_readiness_v1" in contract_text
    assert "missing_required_matrix_cases" in contract_text
    assert "ambiguous_outcomes" in contract_text
    assert "unmapped_outcomes" in contract_text


def test_contract_baseline_diff_and_checklist_schemas_include_governance_fields() -> None:
    contract_text = _contract_text()
    assert "BaselineDiffRequest:" in contract_text
    assert "BaselineDiffResponse:" in contract_text
    assert "ChecklistRenderRequest:" in contract_text
    assert "ChecklistRenderResponse:" in contract_text
    assert "added_capability_ids" in contract_text
    assert "changed_capability_ids" in contract_text
    assert "removed_capability_ids" in contract_text
    assert "release_blocker" in contract_text
    assert "unresolved_blockers" in contract_text
