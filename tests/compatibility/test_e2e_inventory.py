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
