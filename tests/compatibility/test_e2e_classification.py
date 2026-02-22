from pathlib import Path

from pytest_bdd.compatibility.matrix import discover_user_facing_test_scenario_ids


def test_only_selected_migration_candidates_are_user_facing(tmp_path: Path):
    (tmp_path / "tests" / "feature").mkdir(parents=True)
    (tmp_path / "tests" / "compatibility").mkdir(parents=True)

    (tmp_path / "tests" / "feature" / "test_feature_base_dir.py").write_text(
        "def test_x():\n    pass\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "compatibility" / "test_internal.py").write_text(
        "def test_y():\n    pass\n", encoding="utf-8"
    )

    ids = discover_user_facing_test_scenario_ids(tmp_path / "tests")

    assert "feature-base-dir" in ids
    assert "internal" not in ids
