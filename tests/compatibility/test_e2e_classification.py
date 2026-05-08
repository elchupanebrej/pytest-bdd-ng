"""Provide test e2e classification helpers."""

from pathlib import Path

from pytest_bdd.compatibility.matrix import discover_user_facing_test_scenario_ids


def test_only_selected_migration_candidates_are_user_facing(tmp_path: Path):
    """Verify only selected migration candidates are user facing."""
    (tmp_path / "tests" / "feature").mkdir(parents=True)
    (tmp_path / "tests" / "e2e").mkdir(parents=True)
    (tmp_path / "tests" / "compatibility").mkdir(parents=True)

    (tmp_path / "tests" / "feature" / "test_feature_base_dir.py").write_text(
        "def test_x():\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "e2e" / "test_xdist_html_reporting.py").write_text(
        "def test_x():\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "compatibility" / "test_internal.py").write_text(
        "def test_y():\n    pass\n",
        encoding="utf-8",
    )

    ids = discover_user_facing_test_scenario_ids(tmp_path / "tests")

    assert "feature-base-dir" in ids
    assert "xdist-html-reporting" not in ids
    assert "internal" not in ids
