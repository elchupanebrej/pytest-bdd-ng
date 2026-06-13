"""Contract tests: validate Allure plugin golden equivalence.

Tests that hook mode and NDJSON import mode produce equivalent Allure results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.pytester import Testdir

pytestmark = [pytest.mark.contract]


class TestAllureHookVsImportGolden:
    """Validate hook mode and import mode produce equivalent Allure results."""

    def test_hook_and_import_modes_produce_equivalent_results(self, testdir: Testdir, tmp_path: Path):
        """Hook mode and NDJSON import mode produce identical Allure results for same scenario."""
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
            Feature: Golden equivalence test
              Scenario: Passing scenario
                Given a passing step
                Then the test passes
            """,
        )

        # Step 1: Run in hook mode to generate NDJSON
        ndjson_dir = tmp_path / "hook-ndjson"
        ndjson_dir.mkdir()
        ndjson_file = ndjson_dir / "messages.ndjson"
        result = testdir.runpytest(f"--messages-ndjson={ndjson_file}")
        assert result.ret == 0, f"Hook mode NDJSON generation failed: {result.stdout.str()}"

        # Step 2: Run in hook mode to generate Allure results
        hook_output = tmp_path / "hook-allure"
        hook_output.mkdir()
        result = testdir.runpytest(f"--allure-formatter-output={hook_output}")
        assert result.ret == 0, f"Hook mode failed: {result.stdout.str()}"

        # Step 3: Run in import mode using the NDJSON from step 1
        import_output = tmp_path / "import-allure"
        import_output.mkdir()
        result = testdir.runpytest(
            f"--allure-formatter-output={import_output}",
            f"--cucumber-messages={ndjson_file}",
        )
        # Import mode exits 5 (NO_TESTS_COLLECTED) because collection is cleared
        assert result.ret in {0, 5}, f"Import mode failed: {result.stdout.str()}"

        # Step 4: Compare results
        hook_results = list(hook_output.glob("*-result.json"))
        import_results = list(import_output.glob("*-result.json"))

        assert len(hook_results) == len(import_results), (
            f"Result count mismatch: hook={len(hook_results)}, import={len(import_results)}"
        )

        # Compare scenario names and statuses
        hook_data = {}
        for f in hook_results:
            with Path(f).open(encoding="utf-8") as fh:
                data = json.load(fh)
            hook_data[data["name"]] = data

        import_data = {}
        for f in import_results:
            with Path(f).open(encoding="utf-8") as fh:
                data = json.load(fh)
            import_data[data["name"]] = data

        assert set(hook_data.keys()) == set(import_data.keys()), (
            f"Scenario names differ: hook={set(hook_data.keys())}, import={set(import_data.keys())}"
        )

        for name in hook_data:
            assert hook_data[name]["status"] == import_data[name]["status"], (
                f"Status mismatch for {name}: hook={hook_data[name]['status']}, import={import_data[name]['status']}"
            )
