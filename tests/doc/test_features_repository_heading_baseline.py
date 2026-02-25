from __future__ import annotations

from pathlib import Path

from pytest_bdd.script.validate_feature_headings import build_baseline_audit


def test_repository_feature_documents_have_no_empty_parsed_headings() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    features_root = repository_root / "features"

    baseline = build_baseline_audit(features_root)

    assert baseline.compliant
    assert baseline.violations_count == 0
