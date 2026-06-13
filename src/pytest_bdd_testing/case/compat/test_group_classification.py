"""

Provide test group classification helpers.
"""

from pathlib import Path

from pytest_bdd.util.matrix import discover_user_facing_test_scenario_ids


def test_only_selected_migration_candidates_are_user_facing(tmp_path: Path):
    """
    Verify only selected migration candidates are user facing.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
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
