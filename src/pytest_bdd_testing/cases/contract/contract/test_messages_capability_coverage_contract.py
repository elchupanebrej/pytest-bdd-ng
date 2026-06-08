"""Provide test messages capability coverage contract helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pytest_bdd.model.coverage.inventory import generate_inventory, inventory_to_capability_payload
from pytest_bdd.model.message_capability_inventory import resolve_messages_schema_dir
from pytest_bdd.script.message_capability_governance import discover_governance_schema_path

FEATURE_CONTRACT_DIR = Path(__file__).resolve().parents[5] / "specs" / "008-maximize-messages-coverage" / "contracts"
OPENAPI_CONTRACT_PATH = FEATURE_CONTRACT_DIR / "messages-capability-governance.openapi.yaml"
GOVERNANCE_SCHEMA_PATH = FEATURE_CONTRACT_DIR / "governance-report.schema.json"


def _openapi_text() -> str:
    return OPENAPI_CONTRACT_PATH.read_text(encoding="utf-8")


def _governance_schema() -> dict[str, Any]:
    return json.loads(GOVERNANCE_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_feature_contract_files_exist() -> None:
    """Verify feature contract files exist."""
    assert OPENAPI_CONTRACT_PATH.exists()
    assert GOVERNANCE_SCHEMA_PATH.exists()


def test_openapi_contract_has_required_paths() -> None:
    """Verify openapi contract has required paths."""
    contract_text = _openapi_text()
    assert "/coverage/capabilities/sync:" in contract_text
    assert "/coverage/mappings/validate:" in contract_text
    assert "/coverage/baseline/diff:" in contract_text
    assert "/coverage/checklist/render:" in contract_text


def test_openapi_contract_sync_schema_bootstrap() -> None:
    """Verify openapi contract sync schema bootstrap."""
    contract_text = _openapi_text()
    assert "CapabilitySyncRequest:" in contract_text
    assert "CapabilitySyncResponse:" in contract_text
    assert "duplicate_capability_ids" in contract_text
    assert "total_relevant" in contract_text
    assert "total_out_of_scope" in contract_text


def test_openapi_contract_mapping_validation_semantics() -> None:
    """Verify openapi contract mapping validation semantics."""
    contract_text = _openapi_text()
    assert "MappingValidationRequest:" in contract_text
    assert "MappingValidationResult:" in contract_text
    assert "fixed_release_readiness_v1" in contract_text
    assert "coverage_ratio" in contract_text
    assert "ambiguous_terms" in contract_text


def test_openapi_contract_checklist_render_semantics() -> None:
    """Verify openapi contract checklist render semantics."""
    contract_text = _openapi_text()
    assert "ChecklistRenderRequest:" in contract_text
    assert "ChecklistRenderResponse:" in contract_text
    assert "blockers" in contract_text
    assert "deferred" in contract_text
    assert "approved" in contract_text


def test_openapi_contract_baseline_diff_semantics() -> None:
    """Verify openapi contract baseline diff semantics."""
    contract_text = _openapi_text()
    assert "BaselineDiffRequest:" in contract_text
    assert "BaselineDiffResponse:" in contract_text
    assert "added_capability_ids" in contract_text
    assert "changed_capability_ids" in contract_text
    assert "removed_capability_ids" in contract_text


def test_governance_report_schema_bootstrap() -> None:
    """Verify governance report schema bootstrap."""
    schema = _governance_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False

    required = set(schema["required"])
    assert {"version", "generated_at", "baseline_release", "summary", "capabilities"}.issubset(required)

    summary_required = set(schema["properties"]["summary"]["required"])
    assert {
        "total_capabilities",
        "implemented_capabilities",
        "blocked_capabilities",
        "deferred_capabilities",
        "coverage_percentage",
        "runtime_required_total",
        "runtime_required_covered",
        "runtime_required_missing",
        "non_runtime_required_total",
        "non_runtime_covered",
        "non_runtime_classified",
        "mandatory_scope_violations",
    }.issubset(summary_required)

    capability_required = set(schema["properties"]["capabilities"]["items"]["required"])
    assert {
        "capability_id",
        "status",
        "disposition",
        "mandatory_scope",
        "runtime_required",
        "observed_runtime",
    }.issubset(capability_required)

    capability_item = schema["properties"]["capabilities"]["items"]
    status_enum = set(capability_item["properties"]["status"]["enum"])
    assert "Partly-Applicable" in status_enum
    non_impl_requirements = [
        clause["then"]["required"]
        for clause in capability_item.get("allOf", [])
        if clause.get("if", {}).get("properties", {}).get("status", {}).get("const") == "Non-Implementable"
    ]
    assert non_impl_requirements
    assert any("hard_limitation" in required for required in non_impl_requirements)
    assert any("recheck_trigger" in required for required in non_impl_requirements)


def test_openapi_contract_includes_mandatory_governance_report_flags() -> None:
    """Verify openapi contract includes mandatory governance report flags."""
    contract_text = _openapi_text()
    assert "/coverage/governance/report:" in contract_text
    assert "mandatory_capabilities_file" in contract_text
    assert "runtime_required_capabilities_file" in contract_text
    assert "require_runtime_required_covered" in contract_text
    assert "require_non_runtime_classified" in contract_text
    assert "mandatory_scope_violations" in contract_text
    assert "hard_limitation" in contract_text


def test_inventory_export_emits_unique_canonical_capability_ids() -> None:
    """Verify inventory export emits unique canonical capability ids."""
    inventory = generate_inventory(resolve_messages_schema_dir())
    payload = inventory_to_capability_payload(inventory, baseline_release="v32.0.1")
    capability_ids = [entry["capability_id"] for entry in payload]

    assert len(capability_ids) == len(set(capability_ids))
    assert all("_" not in capability_id.split(".", 1)[0] for capability_id in capability_ids)


def test_governance_schema_discovery_matches_contract_fixture() -> None:
    """Verify governance schema discovery matches contract fixture."""
    assert discover_governance_schema_path() == GOVERNANCE_SCHEMA_PATH.resolve()
