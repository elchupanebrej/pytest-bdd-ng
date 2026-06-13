"""E2E tests: validate Allure plugin behavior with xdist parallel execution.

Tests that xdist runs produce one total Allure result directory with all scenarios.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.pytester import Testdir

pytestmark = [pytest.mark.e2e]


class TestAllureXdistTotalReport:
    """Validate xdist total report produces single output directory."""

    def test_single_output_directory_with_multiple_scenarios(self, testdir: Testdir, tmp_path: Path):
        """Multiple scenarios produce results in a single output directory."""
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
            Feature: Multiple scenarios
              Scenario: Scenario one
                Given a passing step
                Then the test passes

              Scenario: Scenario two
                Given a passing step
                Then the test passes

              Scenario: Scenario three
                Given a passing step
                Then the test passes
            """,
        )

        output_dir = tmp_path / "allure-results"
        result = testdir.runpytest(f"--allure-formatter-output={output_dir}")

        assert result.ret == 0, f"pytest failed: {result.stdout.str()}\n{result.stderr.str()}"

        # Verify all results are in the single output directory (no subdirectories per worker)
        result_files = list(output_dir.glob("*-result.json"))
        assert len(result_files) >= 3, f"Expected at least 3 result files (one per scenario), got {len(result_files)}"

        # Verify no subdirectories were created (xdist workers should not create separate dirs)
        subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 0, f"Expected no subdirectories, found: {subdirs}"

    def test_result_files_have_valid_json(self, testdir: Testdir, tmp_path: Path):
        """All result files contain valid JSON with required fields."""
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
            Feature: Valid JSON test
              Scenario: Passing scenario
                Given a passing step
                Then the test passes
            """,
        )

        output_dir = tmp_path / "allure-results"
        result = testdir.runpytest(f"--allure-formatter-output={output_dir}")

        assert result.ret == 0, f"pytest failed: {result.stdout.str()}\n{result.stderr.str()}"

        result_files = list(output_dir.glob("*-result.json"))
        assert len(result_files) > 0, "No result files produced"

        for result_file in result_files:
            with Path(result_file).open(encoding="utf-8") as f:
                data = json.load(f)
            assert "name" in data, f"Result file {result_file.name} missing 'name' field"
            assert "status" in data, f"Result file {result_file.name} missing 'status' field"
