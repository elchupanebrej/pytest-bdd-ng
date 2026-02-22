from pathlib import Path

from pytest_bdd.compatibility.matrix import build_migration_coverage_summary


def test_duplicate_user_facing_scenarios_are_detected(tmp_path: Path):
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
    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "only-doc.feature.md").write_text("Feature: only doc\n", encoding="utf-8")

    summary = build_migration_coverage_summary(tmp_path / "tests", tmp_path / "features", threshold_percent=80)

    assert summary.duplicates_in_tests == 0
    assert summary.threshold_met is True


def test_inventory_keeps_non_removable_retained_and_deferred_tests():
    inventory = Path("specs/002-e2e-test-conversion/e2e-migration-inventory.md").read_text(encoding="utf-8")

    assert "`tests/e2e/test_e2e.py`" in inventory
    assert "`tests/e2e/allure/test_e2e_allure.py`" in inventory
    assert "e2e_retain_technical" in inventory

    assert "`tests/feature/test_outline.py`" in inventory
    assert "`tests/feature/test_http.py`" in inventory
    assert "e2e_deferred_conversion" in inventory
