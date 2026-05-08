"""Provide test e2e migration threshold helpers."""

from pathlib import Path

from pytest_bdd.compatibility.matrix import build_migration_coverage_summary


def test_migration_threshold_met_when_features_cover_user_facing_ids(tmp_path: Path):
    """Verify migration threshold met when features cover user facing ids."""
    tests_feature_dir = tmp_path / "tests" / "feature"
    tests_feature_dir.mkdir(parents=True)
    (tests_feature_dir / "test_feature_base_dir.py").write_text("def test_x():\n    pass\n", encoding="utf-8")

    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "feature-base-dir.feature.md").write_text("Feature: base\n", encoding="utf-8")

    summary = build_migration_coverage_summary(tmp_path / "tests", tmp_path / "features", threshold_percent=80)

    assert summary.coverage_percent >= 80


def test_migration_threshold_fails_when_coverage_too_low(tmp_path: Path):
    """Verify migration threshold fails when coverage too low."""
    tests_feature_dir = tmp_path / "tests" / "feature"
    tests_feature_dir.mkdir(parents=True)
    (tests_feature_dir / "test_no_scenario.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    (tests_feature_dir / "test_feature_base_dir.py").write_text("def test_y():\n    pass\n", encoding="utf-8")

    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "no-scenario.feature.md").write_text("Feature: no scenario\n", encoding="utf-8")

    summary = build_migration_coverage_summary(tmp_path / "tests", tmp_path / "features", threshold_percent=80)

    assert summary.coverage_percent < 80
    assert summary.threshold_met is False
