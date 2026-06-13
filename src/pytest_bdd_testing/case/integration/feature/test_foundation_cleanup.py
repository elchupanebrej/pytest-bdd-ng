"""

Regression tests for Phase 01 foundation cleanup.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]


def test_allure_plugin_cleanup_remains_complete() -> None:
    """
    Verify dead Allure plugin files stay removed (allure lives as optional-dependency extra).

    Test target:
        Ensure proper resource cleanup and prevent memory leaks between test runs.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure proper resource cleanup and prevent memory leaks between
        test runs., then the expected outcome is produced.
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
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()

    assert "allure-python-commons" in pyproject
    assert not (PROJECT_ROOT / "src/pytest_bdd/plugin/allure_logger").exists()
    assert not (PROJECT_ROOT / "src/pytest_bdd/compatibility/allure.py").exists()
    assert not (PROJECT_ROOT / "tests/allure_").exists()
    assert not (PROJECT_ROOT / "tests/e2e/allure").exists()


def test_legacy_cucumberjson_flag_is_rejected(testdir) -> None:
    """
    Verify the removed --cucumberjson alias is not accepted by pytest.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    result = testdir.runpytest("--cucumberjson", "report.json")

    assert result.ret != 0
    result.stderr.fnmatch_lines(["*error: unrecognized arguments: --cucumberjson*"])
