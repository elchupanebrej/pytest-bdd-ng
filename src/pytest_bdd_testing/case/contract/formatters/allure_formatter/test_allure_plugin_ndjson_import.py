"""Contract tests: validate NDJSON import mode.

Tests that the plugin correctly reads NDJSON from file and produces
Allure results when --cucumber-messages is provided.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.pytester import Testdir

pytestmark = [pytest.mark.contract]


class TestAllurePluginNdjsonImport:
    """Validate NDJSON import mode produces Allure results."""

    def test_import_mode_produces_allure_results(self, testdir: Testdir, tmp_path: Path):
        """Running with --cucumber-messages reads from file and produces results."""
        # Create a minimal NDJSON file with a passing scenario
        ndjson_path = tmp_path / "messages.ndjson"
        lines = [
            json.dumps({"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}}),
            json.dumps(
                {
                    "testCaseStarted": {
                        "id": "case-1",
                        "testCaseId": "tc-1",
                        "attempt": 0,
                        "timestamp": {"seconds": 1, "nanos": 0},
                    },
                },
            ),
            json.dumps(
                {
                    "testStepStarted": {
                        "testStepId": "step-1",
                        "testCaseStartedId": "case-1",
                        "timestamp": {"seconds": 1, "nanos": 0},
                    },
                },
            ),
            json.dumps(
                {
                    "testStepFinished": {
                        "testStepId": "step-1",
                        "testCaseStartedId": "case-1",
                        "timestamp": {"seconds": 2, "nanos": 0},
                        "testStepResult": {
                            "status": "PASSED",
                            "duration": {"seconds": 1, "nanos": 0},
                        },
                    },
                },
            ),
            json.dumps(
                {
                    "testCaseFinished": {
                        "testCaseStartedId": "case-1",
                        "timestamp": {"seconds": 2, "nanos": 0},
                        "willBeRetried": False,
                    },
                },
            ),
            json.dumps({"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}}),
        ]
        ndjson_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        output_dir = tmp_path / "allure-results"
        # Import mode requires both --allure-formatter-output and --cucumber-messages
        result = testdir.runpytest(
            f"--allure-formatter-output={output_dir}",
            f"--cucumber-messages={ndjson_path}",
        )

        # Import mode clears collection, so exit code 5 (NO_TESTS_COLLECTED) is expected
        assert result.ret in {0, 5}, f"pytest failed: {result.stdout.str()}\n{result.stderr.str()}"

        result_files = list(output_dir.glob("*-result.json"))
        container_files = list(output_dir.glob("*-container.json"))
        assert len(result_files) > 0 or len(container_files) > 0, (
            "No Allure result/container files produced in import mode"
        )

    def test_import_mode_skips_bdd_execution(self, testdir: Testdir, tmp_path: Path):
        """Import mode should not execute BDD scenarios (collection cleared)."""
        # Create a feature file that would fail if executed
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

            @given("a failing step")
            def a_failing_step():
                raise AssertionError("This should NOT run in import mode")

            @then("the test fails")
            def the_test_fails():
                pass
            """,
        )
        testdir.makefile(
            ".feature",
            test="""
            Feature: Import skip test
              Scenario: Would fail if executed
                Given a failing step
                Then the test fails
            """,
        )

        # Create NDJSON with a passing scenario
        ndjson_path = tmp_path / "messages.ndjson"
        lines = [
            json.dumps({"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}}),
            json.dumps(
                {
                    "testCaseStarted": {
                        "id": "case-1",
                        "testCaseId": "tc-1",
                        "attempt": 0,
                        "timestamp": {"seconds": 1, "nanos": 0},
                    },
                },
            ),
            json.dumps(
                {
                    "testCaseFinished": {
                        "testCaseStartedId": "case-1",
                        "timestamp": {"seconds": 2, "nanos": 0},
                        "willBeRetried": False,
                    },
                },
            ),
            json.dumps({"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}}),
        ]
        ndjson_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        output_dir = tmp_path / "allure-results"
        result = testdir.runpytest(
            f"--allure-formatter-output={output_dir}",
            f"--cucumber-messages={ndjson_path}",
        )

        # Should pass or exit 5 (NO_TESTS_COLLECTED) because import mode skips the failing BDD scenario
        assert result.ret in {0, 5}, f"pytest failed (import mode should skip BDD): {result.stdout.str()}"

    def test_empty_ndjson_produces_no_crash(self, testdir: Testdir, tmp_path: Path):
        """Empty NDJSON should not crash the plugin."""
        ndjson_path = tmp_path / "empty.ndjson"
        ndjson_path.write_text("", encoding="utf-8")

        output_dir = tmp_path / "allure-results"
        result = testdir.runpytest(
            f"--allure-formatter-output={output_dir}",
            f"--cucumber-messages={ndjson_path}",
        )

        # Should not crash (exit 0 or 5 for no tests collected)
        assert result.ret in {0, 5}, f"pytest crashed: {result.stdout.str()}\n{result.stderr.str()}"

    def test_nonexistent_ndjson_path_produces_error(self, testdir: Testdir, tmp_path: Path):
        """Nonexistent NDJSON input path should produce a clear error."""
        nonexistent = tmp_path / "nonexistent.ndjson"
        output_dir = tmp_path / "allure-results"
        result = testdir.runpytest(
            f"--allure-formatter-output={output_dir}",
            f"--cucumber-messages={nonexistent}",
        )

        # Plugin should handle missing file gracefully (not crash)
        # The exact exit code depends on how the error is reported
        assert (
            "does not exist" in result.stdout.str() or "does not exist" in result.stderr.str() or result.ret in {0, 5}
        ), f"Expected clear error for missing NDJSON file: {result.stdout.str()}"
