"""Provide test event message reporting contract helpers."""

from __future__ import annotations

from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parents[4]
    / "specs"
    / "006-unify-event-messages"
    / "contracts"
    / "event-message-reporting.openapi.yaml"
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def test_event_message_reporting_contract_exists() -> None:
    """Verify event message reporting contract exists."""
    assert CONTRACT_PATH.exists()


def test_contract_has_required_paths() -> None:
    """Verify contract has required paths."""
    contract_text = _contract_text()
    assert "/reporting/messages/emit:" in contract_text
    assert "/reporting/messages/validate:" in contract_text
    assert "/reporting/reports/derive:" in contract_text
    assert "/governance/spec-prefix/audit:" in contract_text


def test_contract_has_status_governance_schemas() -> None:
    """Verify contract has status governance schemas."""
    contract_text = _contract_text()
    assert "ImplementationStatus:" in contract_text
    assert "StatusApplicability:" in contract_text
    assert "StatusGovernancePolicy:" in contract_text
    assert "MISSING_REQUIRED_IMPLEMENTATION_COMMENT" in contract_text
    assert "UNKNOWN_IMPLEMENTATION_STATUS" in contract_text


def test_contract_has_prefix_audit_schema() -> None:
    """Verify contract has prefix audit schema."""
    contract_text = _contract_text()
    assert "SpecPrefixAuditRequest:" in contract_text
    assert "SpecPrefixAuditResponse:" in contract_text
    assert "SpecPrefixConflict:" in contract_text


def test_validate_path_documents_stream_consistency_violations() -> None:
    """Verify validate path documents stream consistency violations."""
    contract_text = _contract_text()
    assert "/reporting/messages/validate:" in contract_text
    assert "ORPHAN_REFERENCE" in contract_text
    assert "DUPLICATE_LIFECYCLE_ID" in contract_text
    assert "OUT_OF_ORDER_LIFECYCLE" in contract_text
    assert "UNSUPPORTED_PROTOCOL_VERSION" in contract_text


def test_prefix_audit_path_includes_conflict_payload() -> None:
    """Verify prefix audit path includes conflict payload."""
    contract_text = _contract_text()
    assert "/governance/spec-prefix/audit:" in contract_text
    assert "recommended_next_prefix" in contract_text
    assert "conflicting_paths" in contract_text
