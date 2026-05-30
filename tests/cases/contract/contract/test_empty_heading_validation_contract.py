"""Provide test empty heading validation contract helpers."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import yaml

from pytest_bdd.script.validate_feature_headings import (
    build_baseline_audit,
    heading_validation_policy_payload,
    run_heading_validation_scan,
)

CONTRACT_PATH = (
    Path(__file__).resolve().parents[4]
    / "specs"
    / "005-no-empty-bdd-headings"
    / "contracts"
    / "empty-heading-validation.openapi.yaml"
)


def _write_feature(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).strip() + "\n", encoding="utf-8")


def test_empty_heading_validation_contract_exists() -> None:
    """Verify empty heading validation contract exists."""
    assert CONTRACT_PATH.exists()


def test_empty_heading_validation_contract_has_required_paths() -> None:
    """Verify empty heading validation contract has required paths."""
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    paths = data["paths"]

    assert "/validation/feature-headings/policy" in paths
    assert "/validation/feature-headings/scan" in paths
    assert "/validation/feature-headings/baseline-audit" in paths


def test_empty_heading_validation_contract_has_required_schemas() -> None:
    """Verify empty heading validation contract has required schemas."""
    data = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    schemas = data["components"]["schemas"]

    assert "HeadingValidationPolicy" in schemas
    assert "HeadingValidationScanRequest" in schemas
    assert "HeadingValidationScanResponse" in schemas
    assert "HeadingValidationViolation" in schemas
    assert "BaselineAuditResponse" in schemas


def test_policy_payload_matches_contract_shape() -> None:
    """Verify policy payload matches contract shape."""
    payload = heading_validation_policy_payload()

    assert payload["policy_id"] == "feature-heading-policy-v1"
    assert payload["trim_whitespace"] is True
    assert payload["empty_name_is_violation"] is True
    assert payload["snippet_text_excluded"] is True
    assert payload["enforced_heading_types"] == ["feature", "scenario", "scenario_outline"]


def test_scan_payload_contains_deterministic_fields(tmp_path: Path) -> None:
    """Verify scan payload contains deterministic fields."""
    _write_feature(
        tmp_path / "sample.feature",
        """
        Feature: Example
          Scenario:
            Given step
        """,
    )

    run = run_heading_validation_scan(tmp_path)
    payload = run.to_payload()

    assert payload["documents_scanned"] == 1
    assert payload["status"] == "fail"
    assert isinstance(payload["violations"], list)
    assert payload["violations"][0]["path"] == "sample.feature"
    assert payload["violations"][0]["code"] == "EMPTY_HEADING_TITLE"


def test_baseline_audit_payload_contains_compliance_flags(tmp_path: Path) -> None:
    """Verify baseline audit payload contains compliance flags."""
    _write_feature(
        tmp_path / "valid.feature",
        """
        Feature: Example
          Scenario: Named scenario
            Given step
        """,
    )

    baseline = build_baseline_audit(tmp_path)
    payload = baseline.to_payload()

    assert payload["violations_count"] == 0
    assert payload["compliant"] is True
