"""Parity and xdist contract tests for pytest-native Allure plugin."""

from __future__ import annotations

import json

import pytest

pytestmark = [pytest.mark.contract]


def test_native_allure_reporting(testdir, tmp_path) -> None:
    """Verify that live pytest execution with --allure-formatter-output produces valid Allure results."""
    output_dir = tmp_path / "allure-results"

    # Create feature file
    feature_path = testdir.tmpdir.join("simple.feature")
    feature_path.write(
        "Feature: Native Allure Reporting\n  Scenario: Successful Login\n    Given a passing step\n",
    )

    # Create conftest with step definitions (required for autoloaded feature files)
    testdir.makeconftest(
        """
        from pytest_bdd import given

        @given("a passing step")
        def passing_step():
            pass
        """,
    )

    result = testdir.runpytest_subprocess(
        f"--allure-formatter-output={output_dir}",
    )
    result.assert_outcomes(passed=1)

    result_files = list(output_dir.glob("*-result.json"))
    container_files = list(output_dir.glob("*-container.json"))

    assert len(result_files) == 1
    assert len(container_files) == 1

    with result_files[0].open(encoding="utf-8") as f:
        res = json.load(f)

    assert res["name"] == "Successful Login"
    assert res["status"] == "passed"
    assert len(res["steps"]) == 1
    assert res["steps"][0]["name"] == "a passing step"
    assert res["steps"][0]["status"] == "passed"


def test_native_import_mode_runs_no_scenarios(testdir, tmp_path) -> None:
    """Verify that --cucumber-messages skips scenario run and writes results from NDJSON."""
    output_dir = tmp_path / "allure-results"
    messages_file = tmp_path / "messages.ndjson"

    # 1. Create a valid NDJSON file representing a passing run
    lines = [
        json.dumps({"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}}),
        json.dumps(
            {
                "pickle": {
                    "id": "pk-1",
                    "name": "Imported Scenario",
                    "language": "en",
                    "astNodeIds": [],
                    "tags": [],
                    "uri": "features/test.feature",
                    "steps": [{"id": "ps-1", "type": "Action", "text": "I enter valid credentials", "astNodeIds": []}],
                },
            },
        ),
        json.dumps(
            {
                "testCase": {
                    "id": "tc-1",
                    "pickleId": "pk-1",
                    "testSteps": [{"id": "ts-1", "pickleStepId": "ps-1"}],
                },
            },
        ),
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
                    "testStepId": "ts-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
        ),
        json.dumps(
            {
                "testStepFinished": {
                    "testStepId": "ts-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 1, "nanos": 0}},
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
    messages_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 2. Setup a dummy pytest run with BDD scenario that WOULD fail if run
    feature_path = testdir.tmpdir.join("simple.feature")
    feature_path.write(
        "Feature: Native Allure Reporting\n  Scenario: Successful Login\n    Given a passing step\n",
    )

    testdir.makeconftest(
        """
        from pytest_bdd import given

        @given("a passing step")
        def passing_step():
            raise RuntimeError("Should not be executed!")
        """,
    )

    result = testdir.runpytest_subprocess(
        f"--allure-formatter-output={output_dir}",
        f"--cucumber-messages={messages_file}",
    )

    # 3. Assert no tests executed, session success
    assert result.ret == 0

    # 4. Verify results are written from imported file
    result_files = list(output_dir.glob("*-result.json"))
    assert len(result_files) == 1

    with result_files[0].open(encoding="utf-8") as f:
        res = json.load(f)

    assert res["name"] == "Imported Scenario"
    assert res["status"] == "passed"
    assert len(res["steps"]) == 1
    assert res["steps"][0]["name"] == "I enter valid credentials"


def test_native_xdist_allure_reporting(testdir, tmp_path) -> None:
    """Verify that running pytest -n 2 generates exactly one aggregated Allure report without duplicates."""
    output_dir = tmp_path / "allure-results"

    # Create feature file with 2 scenarios
    feature_path = testdir.tmpdir.join("simple.feature")
    feature_path.write(
        "Feature: Native Allure Reporting\n"
        "  Scenario: Successful Login 1\n"
        "    Given a passing step\n"
        "\n"
        "  Scenario: Successful Login 2\n"
        "    Given a passing step\n",
    )

    # Create conftest with step definitions
    testdir.makeconftest(
        """
        from pytest_bdd import given

        @given("a passing step")
        def passing_step():
            pass
        """,
    )

    result = testdir.runpytest_subprocess(
        "-p",
        "xdist",
        "-n",
        "2",
        f"--allure-formatter-output={output_dir}",
    )
    result.assert_outcomes(passed=2)

    result_files = list(output_dir.glob("*-result.json"))
    container_files = list(output_dir.glob("*-container.json"))

    assert len(result_files) == 2
    assert len(container_files) == 1

    names = {json.loads(f.read_text(encoding="utf-8"))["name"] for f in result_files}
    assert names == {"Successful Login 1", "Successful Login 2"}
