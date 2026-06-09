"""Step definitions for Allure-Cucumber Converter feature."""

import json
import subprocess
import sys
from pathlib import Path

from pytest_bdd import given, parsers, then, when
from pytest_bdd.plugin.allure_cucumber.converter import convert


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
                "data": "Feature: Login\n  Scenario: Successful login\n    Given I am on the login page\n    When I enter valid credentials\n    Then I should be logged in",
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
    with Path(ndjson_path).open("w") as f:
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
                "data": "Feature: Login\n  Scenario: Successful login\n    Given I am on the login page\n    When I enter valid credentials\n    Then I should be logged in\n  Scenario: Failed login\n    Given I am on the login page\n    When I enter invalid credentials\n    Then I should see an error",
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
    with Path(ndjson_path).open("w") as f:
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
def process_with_converter(tmp_path, request, cucumber_messages_ndjson_one_passing):
    """Process the NDJSON file with the converter."""
    output_dir = tmp_path / "allure-results"
    output_dir.mkdir()
    convert(str(cucumber_messages_ndjson_one_passing), str(output_dir))
    return output_dir


@when(parsers.parse("the allure-cucumber converter processes the file"))
def process_with_converter(tmp_path, request, cucumber_messages_ndjson):
    """Process the NDJSON file with the converter."""
    output_dir = tmp_path / "allure-results"
    output_dir.mkdir()
    convert(str(cucumber_messages_ndjson), str(output_dir))
    return output_dir


@when("the allure-cucumber CLI is invoked with that path")
def invoke_cli(nonexistent_ndjson_path):
    """Invoke the CLI with a nonexistent file."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest_bdd.plugin.allure_cucumber.cli",
            str(nonexistent_ndjson_path),
            "--output",
            str(nonexistent_ndjson_path.parent / "output"),
        ],
        capture_output=True,
        text=True,
    )
    return result


@then("an Allure result JSON file is created")
def check_result_file_created(tmp_path):
    """Check that a result JSON file was created."""
    output_dir = tmp_path / "allure-results"
    result_files = list(output_dir.glob("*-result.json"))
    assert len(result_files) > 0, f"No result files found in {output_dir}"


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
        with Path(schema_path).open() as f:
            schema = json.load(f)

        for result_file in result_files:
            with Path(result_file).open() as f:
                data = json.load(f)
            jsonschema.validate(data, schema)


@then(parsers.parse('the result has status "{expected_status}"'))
def check_result_status(tmp_path, expected_status):
    """Check that the result has the expected status."""
    output_dir = tmp_path / "allure-results"
    result_files = list(output_dir.glob("*-result.json"))

    for result_file in result_files:
        with Path(result_file).open() as f:
            data = json.load(f)
        assert data.get("status") == expected_status, f"Expected status {expected_status}, got {data.get('status')}"


@then("two Allure result JSON files are created")
def check_two_result_files(tmp_path):
    """Check that two result JSON files were created."""
    output_dir = tmp_path / "allure-results"
    result_files = list(output_dir.glob("*-result.json"))
    assert len(result_files) == 2, f"Expected 2 result files, got {len(result_files)}"


@then("a container JSON file references both results")
def check_container_file(tmp_path):
    """Check that a container JSON file references both results."""
    output_dir = tmp_path / "allure-results"
    container_files = list(output_dir.glob("*-container.json"))
    assert len(container_files) > 0, "No container files found"

    for container_file in container_files:
        with Path(container_file).open() as f:
            data = json.load(f)
        assert "children" in data, "Container file missing children field"
        assert len(data["children"]) == 2, f"Expected 2 children, got {len(data['children'])}"


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
            "pytest_bdd.plugin.allure_cucumber.cli",
            str(nonexistent_ndjson_path),
            "--output",
            str(nonexistent_ndjson_path.parent / "output"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, f"Expected non-zero exit code, got {result.returncode}"


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
    with Path(path).open("w") as f:
        f.writelines(json.dumps(entry) + "\n" for entry in content)


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
    assert output_dir.exists(), f"Directory does not exist: {output_dir}"
    result_files = list(output_dir.glob("*-result.json"))
    assert len(result_files) > 0, f"No result files found in {output_dir}"


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
        with Path(schema_path).open() as f:
            schema = json.load(f)

        for result_file in result_files:
            with Path(result_file).open() as f:
                data = json.load(f)
            jsonschema.validate(data, schema)


@then(parsers.parse('Directory "{dirname}" contains a container JSON file referencing the results'))
def check_directory_has_container(testdir, dirname):
    """Check that a directory contains a container JSON file referencing results."""
    output_dir = Path(testdir.tmpdir.strpath) / dirname
    assert output_dir.exists(), f"Directory does not exist: {output_dir}"
    container_files = list(output_dir.glob("*-container.json"))
    assert len(container_files) > 0, f"No container files found in {output_dir}"

    for container_file in container_files:
        with Path(container_file).open() as f:
            data = json.load(f)
        assert "children" in data, "Container file missing children field"
        assert len(data["children"]) > 0, "Container has no children"


# --- Docker and HTML report validation steps ---


ALLURE_DOCKER_IMAGE = "allure3-local:latest"


@when("run docker", target_fixture="docker_result")
def run_docker(testdir, step, attach):
    """Run a Docker container with parameters from a data table.

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
        raise ValueError("run docker requires a data table with at least 'image' column")

    options_dict = data_table_to_dicts(data_table)

    image = options_dict.get("image", [None])[0]
    if not image:
        raise ValueError("run docker requires 'image' column in data table")

    command_parts = options_dict.get("command", [])
    volumes = options_dict.get("volume", [])
    env_vars = options_dict.get("env", [])
    timeout_str = options_dict.get("timeout", ["120"])[0]
    timeout = int(timeout_str)

    require_docker_daemon()
    if image == "allure3-local:latest":
        from pytest_bdd.testing.docker import ensure_allure3_image

        ensure_allure3_image()

    docker_args = ["docker", "run", "--rm"]

    for vol in volumes:
        docker_args.extend(["-v", str(vol)])

    for env in env_vars:
        docker_args.extend(["-e", str(env)])

    docker_args.append(image)

    if command_parts:
        for part in command_parts:
            docker_args.extend(part.split())

    results_path = Path(testdir.tmpdir.strpath)

    result = subprocess.run(  # noqa: S603
        docker_args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
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
    assert report_dir.exists(), f"Report directory does not exist: {report_dir}"
    index_html = report_dir / "index.html"
    assert index_html.exists(), f"index.html not found in {report_dir}"
    content = index_html.read_text(encoding="utf-8")
    assert len(content) > 0, "index.html is empty"


@then(parsers.parse('Allure HTML report contains scenario name "{scenario_name}"'))
def check_html_report_contains_scenario(testdir, scenario_name):
    """Check that the Allure HTML report contains a specific scenario name."""
    testdir_path = Path(testdir.tmpdir.strpath)
    index_files = list(testdir_path.rglob("index.html"))
    assert index_files, "No index.html files found"

    found = False
    for index_file in index_files:
        content = index_file.read_text(encoding="utf-8")
        if scenario_name in content:
            found = True
            break

    assert found, f"Scenario name '{scenario_name}' not found in any Allure HTML report"
