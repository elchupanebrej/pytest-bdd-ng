"""Provide test e2e no duplicates helpers."""

from pathlib import Path

from pytest_bdd.util.matrix import build_migration_coverage_summary


def test_duplicate_user_facing_scenarios_are_detected(tmp_path: Path):
    """Verify duplicate user facing scenarios are detected."""
    tests_feature_dir = tmp_path / "tests" / "feature"
    tests_feature_dir.mkdir(parents=True)
    (tests_feature_dir / "test_no_scenario.py").write_text("def test_x():\n    pass\n", encoding="utf-8")

    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "no-scenario.feature.md").write_text("Feature: no scenario\n", encoding="utf-8")

    summary = build_migration_coverage_summary(tmp_path / "tests", tmp_path / "features", threshold_percent=80)

    assert summary.duplicates_in_tests == 1
    assert summary.threshold_met is False


def test_no_duplicates_when_user_facing_tests_removed(tmp_path: Path):
    """Verify no duplicates when user facing tests removed."""
    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "only-doc.feature.md").write_text("Feature: only doc\n", encoding="utf-8")

    summary = build_migration_coverage_summary(tmp_path / "tests", tmp_path / "features", threshold_percent=80)

    assert summary.duplicates_in_tests == 0
    assert summary.threshold_met is True


def test_e2e_doc_tests_do_not_count_as_migration_duplicates(tmp_path: Path):
    """Verify e2e doc tests do not count as migration duplicates."""
    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "cucumber-formatter-reports.feature.md").write_text("Feature: report docs\n", encoding="utf-8")

    e2e_dir = tmp_path / "tests" / "e2e"
    e2e_dir.mkdir(parents=True)
    (e2e_dir / "test_report_doc_cucumber_formatters.py").write_text("def test_x():\n    pass\n", encoding="utf-8")

    summary = build_migration_coverage_summary(tmp_path / "tests", tmp_path / "features", threshold_percent=80)

    assert summary.duplicates_in_tests == 0
