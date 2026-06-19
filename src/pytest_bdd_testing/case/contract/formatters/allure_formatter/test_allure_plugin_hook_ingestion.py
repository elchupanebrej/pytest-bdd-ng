"""Contract tests: validate live mode hook ingestion.

Tests that the plugin correctly consumes pytest_bdd_message envelopes
from running scenarios and produces Allure results without NDJSON file input.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.pytester import Testdir

pytestmark = [pytest.mark.contract]


class TestAllurePluginHookIngestion:
    """Validate hook ingestion mode produces Allure results."""

    def test_live_mode_produces_allure_results(self, testdir: Testdir, tmp_path: Path):
        """Running pytest with --allure-cucumber-out only produces Allure results."""
        testdir.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            addopts = "-v"
            """,
        )
        testdir.makeconftest(
            """
            from pytest_bdd import scenarios, given, then, parsers

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
            Feature: Hook ingestion test
              Scenario: Passing scenario
                Given a passing step
                Then the test passes
            """,
        )

        output_dir = tmp_path / "allure-results"
        result = testdir.runpytest(f"--allure-cucumber-out={output_dir}")

        assert result.ret == 0, f"pytest failed: {result.stdout.str()}\n{result.stderr.str()}"

        result_files = list(output_dir.glob("*-result.json"))
        assert len(result_files) > 0, "No Allure result files produced in live mode"

        for result_file in result_files:
            with Path(result_file).open(encoding="utf-8") as f:
                data = json.load(f)
            assert "name" in data, f"Result file {result_file.name} missing 'name' field"
            assert "status" in data, f"Result file {result_file.name} missing 'status' field"

    def test_live_mode_does_not_use_messages_ndjson(self, testdir: Testdir, tmp_path: Path):
        """Live mode works without an NDJSON import flag."""
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
            Feature: No NDJSON flag test
              Scenario: Simple scenario
                Given a passing step
                Then the test passes
            """,
        )

        output_dir = tmp_path / "allure-results"
        result = testdir.runpytest(f"--allure-cucumber-out={output_dir}")

        assert result.ret == 0, f"pytest failed: {result.stdout.str()}\n{result.stderr.str()}"

        result_files = list(output_dir.glob("*-result.json"))
        assert len(result_files) > 0, "No Allure result files produced"

        # Verify the result contains a valid scenario name
        for result_file in result_files:
            with Path(result_file).open(encoding="utf-8") as f:
                data = json.load(f)
            assert data.get("name"), "Result file has empty name"
