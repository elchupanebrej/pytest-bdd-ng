"""E2E tests: validate Allure plugin coexistence with allure-pytest.

Tests that allure-bdd works both with and without allure-pytest installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.pytester import Testdir

pytestmark = [pytest.mark.e2e]


def _has_allure_pytest() -> bool:
    """Check if allure-pytest is importable."""
    try:
        import allure_pytest  # optional dependency check
    except ImportError:
        return False
    else:
        return True


class TestAllurePytestCoexistence:
    """Validate allure-bdd works with and without allure-pytest."""

    def test_works_without_allure_pytest(self, testdir: Testdir, tmp_path: Path):
        """Allure plugin works when allure-pytest is NOT installed."""
        testdir.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            addopts = "-v"
            """,
        )
        testdir.makeconftest(
            """
            from pytest_bdd import scenarios, given, then

            scenarios("test.feature")

            @given("a passing step")
            def a_passing_step():
                pass

            @then("the test passes")
            def the_test_passes():
                pass
            """,
        )
        testdir.makefile(
            ".feature",
            test="""
            Feature: No allure-pytest
              Scenario: Passing scenario
                Given a passing step
                Then the test passes
            """,
        )

        output_dir = tmp_path / "allure-results"
        result = testdir.runpytest(f"--allure-formatter-output={output_dir}")

        assert result.ret == 0, f"pytest failed: {result.stdout.str()}\n{result.stderr.str()}"

        # Verify Allure result files were created
        result_files = list(output_dir.glob("*-result.json"))
        assert len(result_files) == 1, f"Expected 1 result file, got {len(result_files)}"

    @pytest.mark.skipif(not _has_allure_pytest(), reason="allure-pytest not installed")
    def test_no_duplicates_with_allure_pytest(self, testdir: Testdir, tmp_path: Path):
        """No duplicate BDD results when allure-pytest is installed."""
        testdir.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            addopts = "-v"
            """,
        )
        testdir.makeconftest(
            """
            from pytest_bdd import scenarios, given, then

            scenarios("test.feature")

            @given("a passing step")
            def a_passing_step():
                pass

            @then("the test passes")
            def the_test_passes():
                pass
            """,
        )
        testdir.makefile(
            ".feature",
            test="""
            Feature: Coexistence test
              Scenario: Passing scenario
                Given a passing step
                Then the test passes
            """,
        )

        output_dir = tmp_path / "allure-results"
        result = testdir.runpytest(f"--allure-formatter-output={output_dir}")

        # Should exit without errors
        assert result.ret == 0, f"pytest failed: {result.stdout.str()}\n{result.stderr.str()}"

        # Verify no duplicate results
        result_files = list(output_dir.glob("*-result.json"))
        assert len(result_files) == 1, f"Expected 1 result file (no duplicates), got {len(result_files)}"

    @pytest.mark.skipif(not _has_allure_pytest(), reason="allure-pytest not installed")
    def test_no_registration_conflicts(self, testdir: Testdir, tmp_path: Path):
        """No plugin registration conflicts when both plugins are active."""
        testdir.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            addopts = "-v"
            """,
        )
        testdir.makeconftest(
            """
            from pytest_bdd import scenarios, given, then

            scenarios("test.feature")

            @given("a passing step")
            def a_passing_step():
                pass

            @then("the test passes")
            def the_test_passes():
                pass
            """,
        )
        testdir.makefile(
            ".feature",
            test="""
            Feature: Registration conflict test
              Scenario: Passing scenario
                Given a passing step
                Then the test passes
            """,
        )

        output_dir = tmp_path / "allure-results"
        result = testdir.runpytest(f"--allure-formatter-output={output_dir}")

        # Should exit without errors or warnings about registration conflicts
        assert result.ret == 0, f"pytest failed: {result.stdout.str()}\n{result.stderr.str()}"
        assert "DuplicatePlugin" not in result.stdout.str()
        assert "DuplicatePlugin" not in result.stderr.str()
