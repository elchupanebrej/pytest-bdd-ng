"""Regression tests for Phase 01 foundation cleanup."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_allure_plugin_cleanup_remains_complete() -> None:
    """Verify dead Allure plugin registration and files stay removed."""
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()

    assert "allure" not in pyproject
    assert not (PROJECT_ROOT / "src/pytest_bdd/plugin/allure_logger").exists()
    assert not (PROJECT_ROOT / "src/pytest_bdd/compatibility/allure.py").exists()
    assert not (PROJECT_ROOT / "tests/allure_").exists()
    assert not (PROJECT_ROOT / "tests/e2e/allure").exists()


def test_legacy_cucumberjson_flag_is_rejected(testdir) -> None:
    """Verify the removed --cucumberjson alias is not accepted by pytest."""
    result = testdir.runpytest("--cucumberjson", "report.json")

    assert result.ret != 0
    result.stderr.fnmatch_lines(["*error: unrecognized arguments: --cucumberjson*"])
