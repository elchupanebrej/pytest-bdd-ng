"""Step definitions for Allure-Cucumber Converter feature."""

import json
import os
import re
import subprocess
import sys
from contextlib import closing, contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING

import pytest

from hamcrest import (
    assert_that,
    contains_string,
    empty,
    equal_to,
    greater_than,
    has_length,
    is_,
    is_not,
)
from pytest_bdd import given, parsers, then, when
from pytest_bdd.plugin.allure_formatter.converter import convert
from pytest_bdd_testing.tool.docker.docker import require_docker_daemon
from pytest_bdd_testing.tool.pytest_results import attach_command_result_outputs

if TYPE_CHECKING:
    from collections.abc import Generator


@given("a cucumber messages NDJSON file with one passing scenario")
def cucumber_messages_ndjson_one_passing(tmp_path):
    """Create a minimal valid NDJSON file with one passing scenario."""
    ndjson_content = [
        {
            "meta": {
                "protocolVersion": "messages",
                "implementation": {"name": "pytest-bdd", "version": "1.0.0"},
                "runtime": {"name": "python", "version": "3.12.0"},
                "suite": {"uri": "features/login.feature"},
            },
            "source": {
                "uri": "features/login.feature",
                "data": "Feature: Login\n  Scenario: Successful login\n    Given I am on the login page\n    When I enter valid credentials\n    Then I should be logged in",  # noqa: E501  # embedded test fixture data
                "mediaType": "text/x.cucumber.gherkin+plain",
            },
        },
        {
            "gherkinDocument": {
                "uri": "features/login.feature",
                "feature": {
                    "tags": [],
                    "location": {"line": 1, "column": 1},
                    "keyword": "Feature",
                    "name": "Login",
                    "description": "",
                    "children": [
                        {
                            "scenario": {
                                "tags": [],
                                "location": {"line": 2, "column": 1},
                                "keyword": "Scenario",
                                "name": "Successful login",
                                "description": "",
                                "steps": [
                                    {
                                        "location": {"line": 3, "column": 3},
                                        "keyword": "Given ",
                                        "text": "I am on the login page",
                                        "docString": None,
                                        "dataTable": None,
                                    },
                                    {
                                        "location": {"line": 4, "column": 3},
                                        "keyword": "When ",
                                        "text": "I enter valid credentials",
                                        "docString": None,
                                        "dataTable": None,
                                    },
                                    {
                                        "location": {"line": 5, "column": 3},
                                        "keyword": "Then ",
                                        "text": "I should be logged in",
                                        "docString": None,
                                        "dataTable": None,
                                    },
                                ],
                                "examples": [],
                            },
                        },
                    ],
                },
                "comments": [],
            },
            "pickle": {
                "id": "pickle-001",
                "uri": "features/login.feature",
                "name": "Successful login",
                "source": {"location": {"line": 2, "column": 1}},
                "steps": [
                    {
                        "id": "step-001",
                        "source": {"location": {"line": 3, "column": 3}},
                        "type": "Step",
                        "keyword": "Given ",
                        "text": "I am on the login page",
                    },
                    {
                        "id": "step-002",
                        "source": {"location": {"line": 4, "column": 3}},
                        "type": "Step",
                        "keyword": "When ",
                        "text": "I enter valid credentials",
                    },
                    {
                        "id": "step-003",
                        "source": {"location": {"line": 5, "column": 3}},
                        "type": "Step",
                        "keyword": "Then ",
                        "text": "I should be logged in",
                    },
                ],
                "tags": [],
            },
        },
        {
            "testCaseStarted": {
                "id": "test-case-started-001",
                "testCaseId": "pickle-001",
                "timestamp": {"seconds": 1000000, "nanos": 0},
            },
        },
        {
            "testStepStarted": {
                "id": "test-step-started-001",
                "testCaseStartedId": "test-case-started-001",
                "pickleStepId": "step-001",
                "timestamp": {"seconds": 1000000, "nanos": 0},
            },
        },
        {
            "testStepFinished": {
                "id": "test-step-finished-001",
                "testCaseStartedId": "test-case-started-001",
                "pickleStepId": "step-001",
                "testStepId": "step-001",
                "timestamp": {"seconds": 1000001, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 100000000},
                "result": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 100000000}},
            },
        },
        {
            "testStepStarted": {
                "id": "test-step-started-002",
                "testCaseStartedId": "test-case-started-001",
                "pickleStepId": "step-002",
                "timestamp": {"seconds": 1000001, "nanos": 0},
            },
        },
        {
            "testStepFinished": {
                "id": "test-step-finished-002",
                "testCaseStartedId": "test-case-started-001",
                "pickleStepId": "step-002",
                "testStepId": "step-002",
                "timestamp": {"seconds": 1000002, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 50000000},
                "result": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 50000000}},
            },
        },
        {
            "testStepStarted": {
                "id": "test-step-started-003",
                "testCaseStartedId": "test-case-started-001",
                "pickleStepId": "step-003",
                "timestamp": {"seconds": 1000002, "nanos": 0},
            },
        },
        {
            "testStepFinished": {
                "id": "test-step-finished-003",
                "testCaseStartedId": "test-case-started-001",
                "pickleStepId": "step-003",
                "testStepId": "step-003",
                "timestamp": {"seconds": 1000003, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 50000000},
                "result": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 50000000}},
            },
        },
        {
            "testCaseFinished": {
                "id": "test-case-finished-001",
                "testCaseStartedId": "test-case-started-001",
                "timestamp": {"seconds": 1000003, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 200000000},
                "status": {"status": "PASSED"},
            },
        },
    ]
    ndjson_path = tmp_path / "messages.ndjson"
    with Path(ndjson_path).open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(entry) + "\n" for entry in ndjson_content)
    return ndjson_path


@given("a cucumber messages NDJSON file with two scenarios")
def cucumber_messages_ndjson_two_scenarios(tmp_path):
    """Create an NDJSON file with two scenarios."""
    ndjson_content = [
        {
            "meta": {
                "protocolVersion": "messages",
                "implementation": {"name": "pytest-bdd", "version": "1.0.0"},
                "runtime": {"name": "python", "version": "3.12.0"},
                "suite": {"uri": "features/login.feature"},
            },
            "source": {
                "uri": "features/login.feature",
                "data": "Feature: Login\n  Scenario: Successful login\n    Given I am on the login page\n    When I enter valid credentials\n    Then I should be logged in\n  Scenario: Failed login\n    Given I am on the login page\n    When I enter invalid credentials\n    Then I should see an error",  # noqa: E501  # embedded test fixture data
                "mediaType": "text/x.cucumber.gherkin+plain",
            },
        },
        {
            "gherkinDocument": {
                "uri": "features/login.feature",
                "feature": {
                    "tags": [],
                    "location": {"line": 1, "column": 1},
                    "keyword": "Feature",
                    "name": "Login",
                    "description": "",
                    "children": [
                        {
                            "scenario": {
                                "tags": [],
                                "location": {"line": 2, "column": 1},
                                "keyword": "Scenario",
                                "name": "Successful login",
                                "description": "",
                                "steps": [
                                    {
                                        "location": {"line": 3, "column": 3},
                                        "keyword": "Given ",
                                        "text": "I am on the login page",
                                    },
                                    {
                                        "location": {"line": 4, "column": 3},
                                        "keyword": "When ",
                                        "text": "I enter valid credentials",
                                    },
                                    {
                                        "location": {"line": 5, "column": 3},
                                        "keyword": "Then ",
                                        "text": "I should be logged in",
                                    },
                                ],
                                "examples": [],
                            },
                        },
                        {
                            "scenario": {
                                "tags": [],
                                "location": {"line": 7, "column": 1},
                                "keyword": "Scenario",
                                "name": "Failed login",
                                "description": "",
                                "steps": [
                                    {
                                        "location": {"line": 8, "column": 3},
                                        "keyword": "Given ",
                                        "text": "I am on the login page",
                                    },
                                    {
                                        "location": {"line": 9, "column": 3},
                                        "keyword": "When ",
                                        "text": "I enter invalid credentials",
                                    },
                                    {
                                        "location": {"line": 10, "column": 3},
                                        "keyword": "Then ",
                                        "text": "I should see an error",
                                    },
                                ],
                                "examples": [],
                            },
                        },
                    ],
                },
                "comments": [],
            },
            "pickle": {
                "id": "pickle-001",
                "uri": "features/login.feature",
                "name": "Successful login",
                "source": {"location": {"line": 2, "column": 1}},
                "steps": [
                    {
                        "id": "step-001",
                        "source": {"location": {"line": 3}},
                        "type": "Step",
                        "keyword": "Given ",
                        "text": "I am on the login page",
                    },
                    {
                        "id": "step-002",
                        "source": {"location": {"line": 4}},
                        "type": "Step",
                        "keyword": "When ",
                        "text": "I enter valid credentials",
                    },
                    {
                        "id": "step-003",
                        "source": {"location": {"line": 5}},
                        "type": "Step",
                        "keyword": "Then ",
                        "text": "I should be logged in",
                    },
                ],
                "tags": [],
            },
        },
        {
            "pickle": {
                "id": "pickle-002",
                "uri": "features/login.feature",
                "name": "Failed login",
                "source": {"location": {"line": 7, "column": 1}},
                "steps": [
                    {
                        "id": "step-004",
                        "source": {"location": {"line": 8}},
                        "type": "Step",
                        "keyword": "Given ",
                        "text": "I am on the login page",
                    },
                    {
                        "id": "step-005",
                        "source": {"location": {"line": 9}},
                        "type": "Step",
                        "keyword": "When ",
                        "text": "I enter invalid credentials",
                    },
                    {
                        "id": "step-006",
                        "source": {"location": {"line": 10}},
                        "type": "Step",
                        "keyword": "Then ",
                        "text": "I should see an error",
                    },
                ],
                "tags": [],
            },
        },
        {
            "testCaseStarted": {
                "id": "tcs-001",
                "testCaseId": "pickle-001",
                "timestamp": {"seconds": 1000000, "nanos": 0},
            },
        },
        {
            "testStepStarted": {
                "id": "tss-001",
                "testCaseStartedId": "tcs-001",
                "pickleStepId": "step-001",
                "timestamp": {"seconds": 1000000, "nanos": 0},
            },
        },
        {
            "testStepFinished": {
                "id": "tsf-001",
                "testCaseStartedId": "tcs-001",
                "pickleStepId": "step-001",
                "testStepId": "step-001",
                "timestamp": {"seconds": 1000001, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 100000000},
                "result": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 100000000}},
            },
        },
        {
            "testStepStarted": {
                "id": "tss-002",
                "testCaseStartedId": "tcs-001",
                "pickleStepId": "step-002",
                "timestamp": {"seconds": 1000001, "nanos": 0},
            },
        },
        {
            "testStepFinished": {
                "id": "tsf-002",
                "testCaseStartedId": "tcs-001",
                "pickleStepId": "step-002",
                "testStepId": "step-002",
                "timestamp": {"seconds": 1000002, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 50000000},
                "result": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 50000000}},
            },
        },
        {
            "testStepStarted": {
                "id": "tss-003",
                "testCaseStartedId": "tcs-001",
                "pickleStepId": "step-003",
                "timestamp": {"seconds": 1000002, "nanos": 0},
            },
        },
        {
            "testStepFinished": {
                "id": "tsf-003",
                "testCaseStartedId": "tcs-001",
                "pickleStepId": "step-003",
                "testStepId": "step-003",
                "timestamp": {"seconds": 1000003, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 50000000},
                "result": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 50000000}},
            },
        },
        {
            "testCaseFinished": {
                "id": "tcf-001",
                "testCaseStartedId": "tcs-001",
                "timestamp": {"seconds": 1000003, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 200000000},
                "status": {"status": "PASSED"},
            },
        },
        {
            "testCaseStarted": {
                "id": "tcs-002",
                "testCaseId": "pickle-002",
                "timestamp": {"seconds": 1000010, "nanos": 0},
            },
        },
        {
            "testStepStarted": {
                "id": "tss-004",
                "testCaseStartedId": "tcs-002",
                "pickleStepId": "step-004",
                "timestamp": {"seconds": 1000010, "nanos": 0},
            },
        },
        {
            "testStepFinished": {
                "id": "tsf-004",
                "testCaseStartedId": "tcs-002",
                "pickleStepId": "step-004",
                "testStepId": "step-004",
                "timestamp": {"seconds": 1000011, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 100000000},
                "result": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 100000000}},
            },
        },
        {
            "testStepStarted": {
                "id": "tss-005",
                "testCaseStartedId": "tcs-002",
                "pickleStepId": "step-005",
                "timestamp": {"seconds": 1000011, "nanos": 0},
            },
        },
        {
            "testStepFinished": {
                "id": "tsf-005",
                "testCaseStartedId": "tcs-002",
                "pickleStepId": "step-005",
                "testStepId": "step-005",
                "timestamp": {"seconds": 1000012, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 50000000},
                "result": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 50000000}},
            },
        },
        {
            "testStepStarted": {
                "id": "tss-006",
                "testCaseStartedId": "tcs-002",
                "pickleStepId": "step-006",
                "timestamp": {"seconds": 1000012, "nanos": 0},
            },
        },
        {
            "testStepFinished": {
                "id": "tsf-006",
                "testCaseStartedId": "tcs-002",
                "pickleStepId": "step-006",
                "testStepId": "step-006",
                "timestamp": {"seconds": 1000013, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 50000000},
                "result": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 50000000}},
            },
        },
        {
            "testCaseFinished": {
                "id": "tcf-002",
                "testCaseStartedId": "tcs-002",
                "timestamp": {"seconds": 1000013, "nanos": 0},
                "duration": {"seconds": 0, "nanos": 200000000},
                "status": {"status": "PASSED"},
            },
        },
    ]
    ndjson_path = tmp_path / "messages.ndjson"
    with Path(ndjson_path).open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(entry) + "\n" for entry in ndjson_content)
    return ndjson_path


@given("an empty cucumber messages NDJSON file")
def empty_cucumber_messages_ndjson(tmp_path):
    """Create an empty NDJSON file."""
    ndjson_path = tmp_path / "messages.ndjson"
    ndjson_path.touch()
    return ndjson_path


@given("a nonexistent NDJSON file path")
def nonexistent_ndjson_path(tmp_path):
    """Return a path to a nonexistent file."""
    return tmp_path / "nonexistent.ndjson"


@when("the allure-cucumber converter processes the file")
def process_with_converter(tmp_path, request, cucumber_messages_ndjson_one_passing):  # noqa: ARG001  # fixture injection
    """Process the NDJSON file with the converter."""
    output_dir = tmp_path / "allure-results"
    output_dir.mkdir()
    convert(str(cucumber_messages_ndjson_one_passing), str(output_dir))
    return output_dir


@when(parsers.parse("the allure-cucumber converter processes the file"))
def process_with_converter(tmp_path, request, cucumber_messages_ndjson):  # pylint: disable=function-redefined  # noqa: ARG001, F811  # fixture injection, overloaded step
    """Process the NDJSON file with the converter."""
    output_dir = tmp_path / "allure-results"
    output_dir.mkdir()
    convert(str(cucumber_messages_ndjson), str(output_dir))
    return output_dir


@when("the allure-cucumber CLI is invoked with that path")
def invoke_cli(nonexistent_ndjson_path):
    """Invoke the CLI with a nonexistent file."""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest_bdd.plugin.allure_formatter.cli",
            str(nonexistent_ndjson_path),
            "--output",
            str(nonexistent_ndjson_path.parent / "output"),
        ],
        capture_output=True,
        check=False,
        text=True,
    )


@then("an Allure result JSON file is created")
def check_result_file_created(tmp_path):
    """Check that a result JSON file was created."""
    output_dir = tmp_path / "allure-results"
    result_files = list(output_dir.glob("*-result.json"))
    assert_that(result_files, is_(greater_than(0)), f"No result files found in {output_dir}")


@then("the result JSON validates against the Allure3 events schema")
def check_schema_validation(tmp_path):
    """Validate the result JSON against the Allure3 schema."""
    import jsonschema

    schema_path = tmp_path.parent.parent.parent / "docs" / "allure3-events.schema.json"
    if not schema_path.exists():
        schema_path = tmp_path.parent.parent.parent.parent / "docs" / "allure3-events.schema.json"

    output_dir = tmp_path / "allure-results"
    result_files = list(output_dir.glob("*-result.json"))

    if schema_path.exists():
        with Path(schema_path).open(encoding="utf-8") as f:
            schema = json.load(f)

        for result_file in result_files:
            with Path(result_file).open(encoding="utf-8") as f:
                data = json.load(f)
            jsonschema.validate(data, schema)


@then(parsers.parse('the result has status "{expected_status}"'))
def check_result_status(tmp_path, expected_status):
    """Check that the result has the expected status."""
    output_dir = tmp_path / "allure-results"
    result_files = list(output_dir.glob("*-result.json"))

    for result_file in result_files:
        with Path(result_file).open(encoding="utf-8") as f:
            data = json.load(f)
        assert_that(
            data.get("status"),
            equal_to(expected_status),
            f"Expected status {expected_status}, got {data.get('status')}",
        )


@then("two Allure result JSON files are created")
def check_two_result_files(tmp_path):
    """Check that two result JSON files were created."""
    output_dir = tmp_path / "allure-results"
    result_files = list(output_dir.glob("*-result.json"))
    assert_that(result_files, has_length(2), f"Expected 2 result files, got {len(result_files)}")


@then("a container JSON file references both results")
def check_container_file(tmp_path):
    """Check that a container JSON file references both results."""
    output_dir = tmp_path / "allure-results"
    container_files = list(output_dir.glob("*-container.json"))
    assert_that(container_files, is_(greater_than(0)), "No container files found")

    for container_file in container_files:
        with Path(container_file).open(encoding="utf-8") as f:
            data = json.load(f)
        assert_that(data, contains_string("children"), "Container file missing children field")
        assert_that(data["children"], has_length(2), f"Expected 2 children, got {len(data['children'])}")


@then("no error occurs")
def check_no_error(tmp_path):
    """Verify no error occurred (test passes if we reach this point)."""


@then("the CLI exits with a non-zero code")
def check_cli_nonzero(nonexistent_ndjson_path):
    """Check that the CLI exited with a non-zero code."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest_bdd.plugin.allure_formatter.cli",
            str(nonexistent_ndjson_path),
            "--output",
            str(nonexistent_ndjson_path.parent / "output"),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert_that(result.returncode, is_not(equal_to(0)), f"Expected non-zero exit code, got {result.returncode}")


# --- Shared NDJSON content for runtime and CLI scenarios ---

PASSING_SCENARIO_NDJSON = [
    {
        "meta": {
            "protocolVersion": "messages",
            "implementation": {"name": "pytest-bdd", "version": "1.0.0"},
            "runtime": {"name": "python", "version": "3.12.0"},
            "suite": {"uri": "features/sample.feature"},
        },
        "source": {
            "uri": "features/sample.feature",
            "data": "Feature: Sample\n  Scenario: Passing\n    Given a passing step\n",
            "mediaType": "text/x.cucumber.gherkin+plain",
        },
    },
    {
        "gherkinDocument": {
            "uri": "features/sample.feature",
            "feature": {
                "tags": [],
                "location": {"line": 1, "column": 1},
                "keyword": "Feature",
                "name": "Sample",
                "description": "",
                "children": [
                    {
                        "scenario": {
                            "tags": [],
                            "location": {"line": 2, "column": 1},
                            "keyword": "Scenario",
                            "name": "Passing",
                            "description": "",
                            "steps": [
                                {
                                    "location": {"line": 3, "column": 3},
                                    "keyword": "Given ",
                                    "text": "a passing step",
                                },
                            ],
                            "examples": [],
                        },
                    },
                ],
            },
            "comments": [],
        },
        "pickle": {
            "id": "pickle-001",
            "uri": "features/sample.feature",
            "name": "Passing",
            "source": {"location": {"line": 2, "column": 1}},
            "steps": [
                {
                    "id": "step-001",
                    "source": {"location": {"line": 3, "column": 3}},
                    "type": "Step",
                    "keyword": "Given ",
                    "text": "a passing step",
                },
            ],
            "tags": [],
        },
    },
    {
        "testCaseStarted": {
            "id": "tcs-001",
            "testCaseId": "pickle-001",
            "timestamp": {"seconds": 1000000, "nanos": 0},
        },
    },
    {
        "testStepStarted": {
            "id": "tss-001",
            "testCaseStartedId": "tcs-001",
            "pickleStepId": "step-001",
            "timestamp": {"seconds": 1000000, "nanos": 0},
        },
    },
    {
        "testStepFinished": {
            "id": "tsf-001",
            "testCaseStartedId": "tcs-001",
            "pickleStepId": "step-001",
            "testStepId": "step-001",
            "timestamp": {"seconds": 1000001, "nanos": 0},
            "duration": {"seconds": 0, "nanos": 100000000},
            "result": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 100000000}},
        },
    },
    {
        "testCaseFinished": {
            "id": "tcf-001",
            "testCaseStartedId": "tcs-001",
            "timestamp": {"seconds": 1000001, "nanos": 0},
            "duration": {"seconds": 0, "nanos": 100000000},
            "status": {"status": "PASSED"},
        },
    },
]


def _write_ndjson_file(path: Path, content: list) -> None:
    """Write NDJSON content to a file."""
    with Path(path).open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(entry) + "\n" for entry in content)


def _testdir_path(testdir, path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(testdir.tmpdir.strpath) / candidate


def _load_json_files(directory: Path, pattern: str) -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(directory.glob(pattern))]


def _scenario_result_payloads(output_dir: Path) -> list[dict]:
    return [
        payload
        for payload in _load_json_files(output_dir, "*-result.json")
        if not str(payload.get("name", "")).startswith("Test Run")
    ]


def _schema_path() -> Path:
    candidates = [
        Path(__file__).parent.parent.parent.parent / "docs" / "allure3-events.schema.json",
        Path(__file__).parent.parent.parent.parent.parent / "docs" / "allure3-events.schema.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    msg = "Allure3 events schema not found"
    raise AssertionError(msg)


def _collect_named_lists(payload: object, name: str) -> list[dict]:
    found: list[dict] = []
    if isinstance(payload, dict):
        value = payload.get(name)
        if isinstance(value, list):
            found.extend(item for item in value if isinstance(item, dict))
        for child in payload.values():
            found.extend(_collect_named_lists(child, name))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_collect_named_lists(item, name))
    return found


def _objects_for_group(payloads: list[dict], group: str) -> list[dict]:
    if group in {"result", "container"}:
        return payloads
    if group == "statusDetails":
        return [item for payload in payloads if isinstance(item := payload.get("statusDetails"), dict)]
    if group.endswith("[]"):
        key = group[:-2]
        return [item for payload in payloads for item in _collect_named_lists(payload, key)]
    msg = f"Unsupported Allure JSON field group: {group}"
    raise AssertionError(msg)


def _assert_json_field_groups(payloads: list[dict], step) -> None:
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    missing: list[str] = []
    for row in data_table.rows[1:]:
        group = row.cells[0].value
        fields = [field.strip() for field in row.cells[1].value.split(",") if field.strip()]
        objects = _objects_for_group(payloads, group)
        missing.extend(f"{group}.{field}" for field in fields if not any(field in item for item in objects))
    assert_that(missing, is_(empty()), f"Missing Allure JSON fields: {missing!r}")


@given(re.compile(r'File "(?P<file_path>(?:[^"]*[\\/][^"]+|[^"]*-[^"]*))" with content:'))
def write_path_file_with_content(testdir, file_path: str, step) -> None:
    """Write a testdir file whose path contains directories or hyphenated names."""
    output_path = _testdir_path(testdir, file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(step.argument.doc_string.content, encoding="utf-8")


@given(parsers.parse('File "{filename}" with Cucumber Messages content for one passing scenario'))
def create_messages_ndjson(testdir, filename):
    """Create an NDJSON file with Cucumber Messages content for one passing scenario."""
    ndjson_path = Path(testdir.tmpdir.strpath) / filename
    _write_ndjson_file(ndjson_path, PASSING_SCENARIO_NDJSON)
    return ndjson_path


@then(parsers.parse('Directory "{dirname}" contains Allure result JSON files'))
def check_directory_has_results(testdir, dirname):
    """Check that a directory contains Allure result JSON files."""
    output_dir = Path(testdir.tmpdir.strpath) / dirname
    assert_that(output_dir.exists(), is_(True), f"Directory does not exist: {output_dir}")
    result_files = list(output_dir.glob("*-result.json"))
    assert_that(result_files, is_(greater_than(0)), f"No result files found in {output_dir}")


@then(parsers.parse('Directory "{dirname}" contains "{expected_count:d}" Allure result JSON files'))
def check_directory_has_result_count(testdir, dirname: str, expected_count: int) -> None:
    """Check that a directory contains expected Allure result JSON file count."""
    output_dir = Path(testdir.tmpdir.strpath) / dirname
    if expected_count == 0 and not output_dir.exists():
        return
    assert_that(output_dir.exists(), is_(True), f"Directory does not exist: {output_dir}")
    result_files = _scenario_result_payloads(output_dir)
    assert_that(
        result_files,
        has_length(expected_count),
        f"Expected {expected_count} result files, got {len(result_files)}",
    )


@then("Allure result files validate against the Allure3 events schema")
def check_results_validate_schema(testdir):
    """Validate Allure result files against the Allure3 schema."""
    import jsonschema

    schema_path = Path(__file__).parent.parent.parent.parent / "docs" / "allure3-events.schema.json"
    if not schema_path.exists():
        schema_path = Path(__file__).parent.parent.parent.parent.parent / "docs" / "allure3-events.schema.json"

    # Check all directories that might contain results
    testdir_path = Path(testdir.tmpdir.strpath)
    result_files = list(testdir_path.rglob("*-result.json"))

    if schema_path.exists() and result_files:
        with Path(schema_path).open(encoding="utf-8") as f:
            schema = json.load(f)

        for result_file in result_files:
            with Path(result_file).open(encoding="utf-8") as f:
                data = json.load(f)
            jsonschema.validate(data, schema)


@then(parsers.parse('Directory "{dirname}" contains a container JSON file referencing the results'))
def check_directory_has_container(testdir, dirname):
    """Check that a directory contains a container JSON file referencing results."""
    output_dir = Path(testdir.tmpdir.strpath) / dirname
    assert_that(output_dir.exists(), is_(True), f"Directory does not exist: {output_dir}")
    container_files = list(output_dir.glob("*-container.json"))
    assert_that(container_files, is_(greater_than(0)), f"No container files found in {output_dir}")

    for container_file in container_files:
        with Path(container_file).open(encoding="utf-8") as f:
            data = json.load(f)
        assert_that(data, contains_string("children"), "Container file missing children field")
        assert_that(data["children"], is_(greater_than(0)), "Container has no children")


@then(parsers.parse("renderer command exits with code {return_code:d}"))
def check_renderer_command_exit_code(renderer_result, return_code: int) -> None:
    """Assert standalone command exit code."""
    assert_that(renderer_result.returncode, equal_to(return_code))


@then("renderer command exits with non-zero code")
def check_renderer_command_nonzero(renderer_result) -> None:
    """Assert standalone command failed."""
    assert_that(renderer_result.returncode, is_not(equal_to(0)))


@then(parsers.parse('Allure result files in "{dirname}" include scenario statuses:'))
def check_allure_result_statuses(testdir, dirname: str, step) -> None:
    """Assert generated Allure result files include expected scenario statuses."""
    output_dir = _testdir_path(testdir, dirname)
    payloads = _scenario_result_payloads(output_dir)
    statuses = {payload.get("name"): payload.get("status") for payload in payloads}
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    for row in data_table.rows[1:]:
        scenario = row.cells[0].value
        status = row.cells[1].value
        assert_that(statuses.get(scenario), equal_to(status), statuses)


@then(parsers.parse('Allure result files in "{dirname}" contain JSON field groups:'))
def check_allure_result_json_field_groups(testdir, dirname: str, step) -> None:
    """Assert generated Allure result files expose expected schema field groups."""
    output_dir = _testdir_path(testdir, dirname)
    payloads = _load_json_files(output_dir, "*-result.json")
    assert_that(payloads, is_(True), f"No result files found in {output_dir}")
    _assert_json_field_groups(payloads, step)


@then(parsers.parse('Allure container files in "{dirname}" validate against the Allure3 events schema'))
def check_allure_container_files_validate_schema(testdir, dirname: str) -> None:
    """Validate generated Allure container files against the Allure3 schema."""
    import jsonschema

    output_dir = _testdir_path(testdir, dirname)
    payloads = _load_json_files(output_dir, "*-container.json")
    assert_that(payloads, is_(True), f"No container files found in {output_dir}")
    schema = json.loads(_schema_path().read_text(encoding="utf-8"))
    for payload in payloads:
        jsonschema.validate(payload, schema)


@then(parsers.parse('Allure container files in "{dirname}" contain JSON field groups:'))
def check_allure_container_json_field_groups(testdir, dirname: str, step) -> None:
    """Assert generated Allure container files expose expected schema field groups."""
    output_dir = _testdir_path(testdir, dirname)
    payloads = _load_json_files(output_dir, "*-container.json")
    assert_that(payloads, is_(True), f"No container files found in {output_dir}")
    _assert_json_field_groups(payloads, step)


@then(parsers.parse('Allure container files in "{dirname}" reference all result UUIDs'))
def check_allure_container_references_result_uuids(testdir, dirname: str) -> None:
    """Assert container children include every generated result UUID."""
    output_dir = _testdir_path(testdir, dirname)
    results = _load_json_files(output_dir, "*-result.json")
    containers = _load_json_files(output_dir, "*-container.json")
    result_uuids = {str(result["uuid"]) for result in results}
    child_uuids = {str(child) for container in containers for child in container.get("children", [])}
    assert_that(result_uuids, is_(True))
    assert_that(
        result_uuids.issubset(child_uuids),
        is_(True),
        f"Missing container children: {result_uuids - child_uuids}",
    )


# --- Docker and HTML report validation steps ---


ALLURE_DOCKER_IMAGE = "allure3-local:latest"


@contextmanager
def _serve_directory(directory: Path) -> "Generator[str, None, None]":
    """
    Serve a directory over HTTP on a random port.

    Yields:
        Base URL for the served directory.

    """

    class _QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def log_message(self, format: str, *args) -> None:  # noqa: A002  # override stdlib signature
            _ = (format, args)

    server = ThreadingHTTPServer(("127.0.0.1", 0), _QuietHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def _resolve_playwright_browsers_path() -> Path | None:
    """
    Resolve Playwright browser installation path.

    Returns:
        Browser installation path, or None when unavailable.

    """
    configured_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if configured_path and configured_path != "0":
        path = Path(configured_path)
        if path.exists():
            return path

    if os.name == "posix":
        import pwd  # pylint: disable=import-error  # posix-only module

        user_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
        if sys.platform == "darwin":
            path = user_home / "Library/Caches/ms-playwright"
        else:
            path = user_home / ".cache/ms-playwright"
        return path if path.exists() else None

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        path = Path(local_app_data) / "ms-playwright"
        if path.exists():
            return path

    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        path = Path(user_profile) / "AppData/Local/ms-playwright"
        return path if path.exists() else None
    return None


def _allure_result_files(output_dir: Path) -> list[Path]:
    """
    List scenario result files, excluding synthetic run-level results.

    Returns:
        Scenario result JSON paths.

    """
    result_files = []
    for result_file in output_dir.glob("*-result.json"):
        result = json.loads(result_file.read_text(encoding="utf-8"))
        if not str(result.get("name", "")).startswith("Test Run"):
            result_files.append(result_file)
    return result_files


@then(parsers.parse('the local allure-cucumber plugin generated results for "{expected_count:d}" scenarios'))
def check_local_plugin_result_count(testdir, expected_count: int) -> None:
    """Assert local plugin generated expected scenario result count."""
    output_dir = Path(testdir.tmpdir.strpath) / "allure-full-results"
    result_files = _allure_result_files(output_dir)
    assert_that(
        result_files,
        has_length(expected_count),
        f"Expected {expected_count} result files, got {len(result_files)}",
    )


@when("run docker", target_fixture="docker_result")
def run_docker(testdir, step, attach):
    """
    Run a Docker container with parameters from a data table.

    Expects a data table with columns:
      - image: Docker image to use (required)
      - command: Command to run in the container (optional)
      - volume: Volume mount in format host_path:container_path[:options] (repeatable)
      - env: Environment variable in format KEY=VALUE (repeatable)
      - timeout: Timeout in seconds (optional, default 120)

    Example:
      When run docker
        | image   | allure3-local:latest |
        | command | allure generate /allure-results --clean -o /allure-report   |
        | volume  | allure-results:/allure-results:ro          |
        | volume  | allure-report:/allure-report                |

    """
    data_table = getattr(step.argument, "data_table", None) if getattr(step, "argument", None) else None
    if data_table is None:
        raise ValueError("run docker requires a data table with at least 'image' column")  # noqa: EM101, TRY003  # BDD step validation

    options_dict: dict[str, list[str]] = {}
    for row in data_table.rows:
        key = row.cells[0].value
        options_dict.setdefault(key, []).extend(cell.value for cell in row.cells[1:])

    image = options_dict.get("image", [None])[0]
    if not image:
        raise ValueError("run docker requires 'image' column in data table")  # noqa: EM101, TRY003  # BDD step validation

    command_parts = options_dict.get("command", [])
    volumes = options_dict.get("volume", [])
    env_vars = options_dict.get("env", [])
    timeout_str = options_dict.get("timeout", ["120"])[0]
    timeout = int(timeout_str)

    require_docker_daemon()
    if image == "allure3-local:latest":
        from pytest_bdd_testing.tool.docker.docker import ensure_allure3_image

        ensure_allure3_image()

    docker_args = ["docker", "run", "--rm"]

    results_path = Path(testdir.tmpdir.strpath)
    for vol in volumes:
        volume_parts = str(vol).split(":")
        if volume_parts and volume_parts[0] and not Path(volume_parts[0]).is_absolute():
            volume_parts[0] = (results_path / volume_parts[0]).as_posix()
        docker_args.extend(["-v", ":".join(volume_parts)])

    for env in env_vars:
        docker_args.extend(["-e", str(env)])

    docker_args.append(image)

    if command_parts:
        for part in command_parts:
            docker_args.extend(part.split())

    result = subprocess.run(
        docker_args,
        check=False,
        text=True,
        timeout=timeout,
        cwd=str(results_path),
    )

    attach_command_result_outputs(
        attach,
        result,
        label="docker-run",
        command=" ".join(docker_args),
    )

    return result


@then(parsers.parse('Directory "{dirname}" contains Allure HTML report with index.html'))
def check_directory_has_html_report(testdir, dirname):
    """Check that a directory contains an Allure HTML report."""
    report_dir = Path(testdir.tmpdir.strpath) / dirname
    assert_that(report_dir.exists(), is_(True), f"Report directory does not exist: {report_dir}")
    index_html = report_dir / "index.html"
    assert_that(index_html.exists(), is_(True), f"index.html not found in {report_dir}")
    content = index_html.read_text(encoding="utf-8")
    assert_that(content, is_(greater_than(0)), "index.html is empty")


@then(parsers.parse('Allure HTML report contains scenario name "{scenario_name}"'))
def check_html_report_contains_scenario(testdir, scenario_name):
    """Check that the Allure HTML report contains a specific scenario name."""
    testdir_path = Path(testdir.tmpdir.strpath)
    report_files = [*testdir_path.rglob("index.html"), *testdir_path.rglob("*.json")]
    assert_that(report_files, is_(True), "No Allure report files found")

    for report_file in report_files:
        content = report_file.read_text(encoding="utf-8")
        if scenario_name in content:
            return

    pytest.fail(f"Scenario name '{scenario_name}' not found in any Allure HTML report")


@when("the Allure report is opened in a browser", target_fixture="allure_report_data")
def open_allure_report_in_browser(testdir):
    """Open Docker-generated Allure report in Playwright and load user-visible report data."""
    playwright_sync_api = pytest.importorskip("playwright.sync_api")
    browsers_path = _resolve_playwright_browsers_path()
    if browsers_path is None:
        pytest.skip("Playwright browsers are unavailable; run `python -m playwright install chromium`.")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)

    report_dir = Path(testdir.tmpdir.strpath) / "allure-full-report"
    assert_that((report_dir / "index.html").exists(), is_(True), f"Allure report index.html not found in {report_dir}")

    page_errors: list[str] = []
    console_errors: list[str] = []
    with (
        _serve_directory(report_dir) as base_url,
        playwright_sync_api.sync_playwright() as playwright,
        closing(playwright.chromium.launch()) as browser,
    ):
        page = browser.new_page()
        page.on("pageerror", lambda exception: page_errors.append(str(exception)))
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.goto(f"{base_url}/index.html", wait_until="load")
        page.wait_for_timeout(2000)
        assert_that(page.title(), is_(True))
        results_by_name = page.evaluate(
            """async () => {
                const indexResponse = await fetch("./widgets/search-index.json");
                if (!indexResponse.ok) {
                    throw new Error(`Cannot read Allure search index: ${indexResponse.status}`);
                }
                const index = await indexResponse.json();
                const entries = index.filter((item) => !item.name.startsWith("Test Run "));
                const results = {};
                for (const entry of entries) {
                    const resultResponse = await fetch(`./data/test-results/${entry.id}.json`);
                    if (!resultResponse.ok) {
                        throw new Error(`Cannot read Allure result ${entry.id}: ${resultResponse.status}`);
                    }
                    const result = await resultResponse.json();
                    results[result.name] = result;
                }
                return results;
            }""",
        )

    assert_that(page_errors, equal_to([]))
    assert_that(console_errors, equal_to([]))
    return results_by_name


@then(parsers.parse('the Allure report shows "{expected_count:d}" tests'))
def check_allure_report_test_count(allure_report_data: dict, expected_count: int) -> None:
    """Assert browser-loaded Allure report shows expected test count."""
    assert_that(allure_report_data, has_length(expected_count))


@then("the Allure report shows scenario statuses:")
def check_allure_report_statuses(allure_report_data: dict, step) -> None:
    """Assert browser-loaded Allure report shows expected scenario statuses."""
    data_table = getattr(step.argument, "data_table", None)
    for row in data_table.rows[1:]:
        scenario = row.cells[0].value
        status = row.cells[1].value
        assert_that(allure_report_data[scenario]["status"], equal_to(status))


@then("the Allure report shows step counts:")
def check_allure_report_step_counts(allure_report_data: dict, step) -> None:
    """Assert browser-loaded Allure report shows expected step counts."""
    data_table = getattr(step.argument, "data_table", None)
    for row in data_table.rows[1:]:
        scenario = row.cells[0].value
        expected_steps = int(row.cells[1].value)
        actual_steps = len([item for item in allure_report_data[scenario]["steps"] if item.get("type") == "step"])
        assert_that(actual_steps, equal_to(expected_steps))


@then("the Allure report shows tags:")
def check_allure_report_tags(allure_report_data: dict, step) -> None:
    """Assert browser-loaded Allure report shows expected tags."""
    data_table = getattr(step.argument, "data_table", None)
    for row in data_table.rows[1:]:
        scenario = row.cells[0].value
        expected_tags = {tag.strip() for tag in row.cells[1].value.split(",") if tag.strip()}
        actual_tags = set(allure_report_data[scenario]["groupedLabels"]["tag"])
        assert_that(expected_tags.issubset(actual_tags), is_(True))


@then("the Allure report shows attachments:")
def check_allure_report_attachments(allure_report_data: dict, step) -> None:
    """Assert browser-loaded Allure report shows expected attachment counts."""
    data_table = getattr(step.argument, "data_table", None)
    for row in data_table.rows[1:]:
        scenario = row.cells[0].value
        expected_attachments = int(row.cells[1].value)
        assert_that(allure_report_data[scenario]["attachments"], has_length(expected_attachments))


@then("the Allure report shows descriptions and structured arguments")
def check_allure_report_descriptions_and_arguments(allure_report_data: dict) -> None:
    """Assert browser-loaded Allure report shows descriptions, tables, and doc strings."""
    passed = allure_report_data["Passing full surface"]
    assert_that(passed["descriptionHtml"], contains_string("Feature description propagated to Allure."))
    assert_that(passed["descriptionHtml"], contains_string("Rule description propagated to Allure."))
    assert_that(passed["descriptionHtml"], contains_string("Scenario description propagated to Allure."))
    assert_that(passed["steps"][4]["parameters"][0]["value"], contains_string("foo"))
    assert_that(passed["steps"][4]["parameters"][0]["value"], contains_string("bar"))
    assert_that(passed["steps"][5]["parameters"][0]["value"], contains_string("pass docstring"))
    outline = allure_report_data["Outline status surface"]
    assert_that(outline["descriptionHtml"], contains_string("Outline description propagated to Allure."))


@then("the Allure report shows failure messages:")
def check_allure_report_failure_messages(allure_report_data: dict, step) -> None:
    """Assert browser-loaded Allure report shows expected failure messages."""
    data_table = getattr(step.argument, "data_table", None)
    for row in data_table.rows[1:]:
        scenario = row.cells[0].value
        message = row.cells[1].value
        assert_that(allure_report_data[scenario]["error"]["message"], contains_string(message))
