from pathlib import Path

from pytest_bdd.compatibility.matrix import (
    discover_feature_scenario_ids,
    discover_user_facing_test_scenario_ids,
)


def test_discovers_feature_scenario_ids(tmp_path: Path):
    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "Feature base dir.feature.md").write_text("Feature: Base dir\n", encoding="utf-8")

    ids = discover_feature_scenario_ids(tmp_path / "features")

    assert "feature-base-dir" in ids


def test_discovers_user_facing_tests_from_tests_feature_folder(tmp_path: Path):
    user_facing_dir = tmp_path / "tests" / "feature"
    user_facing_dir.mkdir(parents=True)
    (user_facing_dir / "test_no_scenario.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    (user_facing_dir / "test_other.py").write_text("def test_y():\n    pass\n", encoding="utf-8")

    ids = discover_user_facing_test_scenario_ids(tmp_path / "tests")

    assert "no-scenario" in ids
    assert "other" not in ids


def test_e2e_report_doc_tests_are_not_treated_as_migration_candidates(tmp_path: Path):
    e2e_dir = tmp_path / "tests" / "e2e"
    e2e_dir.mkdir(parents=True)
    (e2e_dir / "test_report_doc_cucumber_formatters.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    (tmp_path / "tests" / "feature").mkdir(parents=True)

    ids = discover_user_facing_test_scenario_ids(tmp_path / "tests")

    assert "report-doc-cucumber-formatters" not in ids


def test_e2e_xdist_html_tests_are_not_treated_as_migration_candidates(tmp_path: Path):
    e2e_dir = tmp_path / "tests" / "e2e"
    e2e_dir.mkdir(parents=True)
    (e2e_dir / "test_xdist_html_reporting.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    (tmp_path / "tests" / "feature").mkdir(parents=True)

    ids = discover_user_facing_test_scenario_ids(tmp_path / "tests")

    assert "xdist-html-reporting" not in ids
