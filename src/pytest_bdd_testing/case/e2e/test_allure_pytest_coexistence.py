"""E2E tests: validate Allure-Cucumber does not depend on allure-pytest."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.pytester import Testdir

pytestmark = [pytest.mark.e2e]


def test_works_without_allure_pytest(testdir: Testdir, tmp_path: Path):
    """Allure-Cucumber plugin works without allure-pytest."""
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
    result = testdir.runpytest(f"--allure-cucumber-out={output_dir}")

    assert result.ret == 0, f"pytest failed: {result.stdout.str()}\n{result.stderr.str()}"

    result_files = list(output_dir.glob("*-result.json"))
    assert len(result_files) == 1, f"Expected 1 result file, got {len(result_files)}"
