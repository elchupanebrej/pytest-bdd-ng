"""Test cucumber json output."""

import json
from collections import Counter
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import pytest
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]
from cucumber_messages import TestStepFinished as _TestStepFinished  # type:ignore[attr-defined]

from pytest_bdd.model.message_converter import message_converter
from pytest_bdd.util.toolz_test import InstanceOfType

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import RunResult

MESSAGE_REPORTER_PLUGIN = "pytest_bdd.plugin.gherkin_message_reporter.entrypoint"
MESSAGE_REPORTER_PLUGIN_NAME = "pytest-bdd-gherkin-message-reporter"


def runandparse(testdir, *args: Any) -> tuple["RunResult", Sequence[dict[str, Any]]]:
    """Run tests in testdir and parse json output."""
    resultpath = testdir.tmpdir.join("cucumber.json")
    result = testdir.runpytest(f"--cucumberjson={resultpath}", "-s", *args)
    with resultpath.open() as f:
        jsonobject = json.load(f)
    return result, jsonobject


@pytest.mark.technical_nonconvertible
def test_step_trace(testdir):
    """Test step trace."""
    testdir.makefile(
        ".ini",
        pytest="""
        [pytest]
        markers =
            scenario-passing-tag
            scenario-failing-tag
            scenario-outline-passing-tag
            feature-tag
        """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        test="""\
        @feature-tag
        Feature: One passing scenario, one failing scenario

            @scenario-passing-tag
            Scenario: Passing
                Given a passing step
                And some other passing step

            @scenario-failing-tag
            Scenario: Failing
                Given a passing step
                And a failing step

            @scenario-outline-passing-tag
            Scenario Outline: Passing outline
                Given type <type> and value <value>

                Examples: example1
                | type    | value  |
                | str     | hello  |
                | int     | 42     |
                | float   | 1.0    |
        """,
    )
    testdir.makeconftest(
        # language=python
        """
        from pytest_bdd import given, parsers

        @given('a passing step')
        def a_passing_step():
            return 'pass'

        @given('some other passing step')
        def some_other_passing_step():
            return 'pass'

        @given('a failing step')
        def a_failing_step():
            raise Exception('Error')

        @given(parsers.parse('type {type} and value {value}'))
        def type_type_and_value_value():
            return 'pass'
        """,
    )
    result, jsonobject = runandparse(testdir)
    result.assert_outcomes(passed=4, failed=1)

    assert result.ret
    expected = [
        {
            "description": "",
            "elements": [
                {
                    "description": "",
                    "id": "test_scenarios[file:test.feature-One passing scenario, one failing scenario-Passing]",
                    "keyword": "Scenario",
                    "line": 5,
                    "name": "Passing",
                    "steps": [
                        {
                            "keyword": "Given",
                            "line": 6,
                            "match": {"location": ""},
                            "name": "a passing step",
                            "result": {"status": "passed", "duration": InstanceOfType(int)},
                        },
                        {
                            "keyword": "And",
                            "line": 7,
                            "match": {"location": ""},
                            "name": "some other passing step",
                            "result": {"status": "passed", "duration": InstanceOfType(int)},
                        },
                    ],
                    "tags": [{"name": "scenario-passing-tag", "line": 4}],
                    "type": "scenario",
                },
                {
                    "description": "",
                    "id": "test_scenarios[file:test.feature-One passing scenario, one failing scenario-Failing]",
                    "keyword": "Scenario",
                    "line": 10,
                    "name": "Failing",
                    "steps": [
                        {
                            "keyword": "Given",
                            "line": 11,
                            "match": {"location": ""},
                            "name": "a passing step",
                            "result": {"status": "passed", "duration": InstanceOfType(int)},
                        },
                        {
                            "keyword": "And",
                            "line": 12,
                            "match": {"location": ""},
                            "name": "a failing step",
                            "result": {
                                "error_message": InstanceOfType(str),
                                "status": "failed",
                                "duration": InstanceOfType(int),
                            },
                        },
                    ],
                    "tags": [{"name": "scenario-failing-tag", "line": 9}],
                    "type": "scenario",
                },
                {
                    "description": "",
                    "keyword": "Scenario",
                    "tags": [{"line": 14, "name": "scenario-outline-passing-tag"}],
                    "steps": [
                        {
                            "line": 16,
                            "match": {"location": ""},
                            "result": {"status": "passed", "duration": InstanceOfType(int)},
                            "keyword": "Given",
                            "name": "type str and value hello",
                        },
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": (
                        "test_scenarios["
                        "file:test.feature-One passing scenario, one failing scenario-"
                        "Passing outline[table_rows:[line: 20]]"
                        "]"
                    ),
                    "name": "Passing outline",
                },
                {
                    "description": "",
                    "keyword": "Scenario",
                    "tags": [{"line": 14, "name": "scenario-outline-passing-tag"}],
                    "steps": [
                        {
                            "line": 16,
                            "match": {"location": ""},
                            "result": {"status": "passed", "duration": InstanceOfType(int)},
                            "keyword": "Given",
                            "name": "type int and value 42",
                        },
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": (
                        "test_scenarios["
                        "file:test.feature-One passing scenario, one failing scenario-"
                        "Passing outline[table_rows:[line: 21]]"
                        "]"
                    ),
                    "name": "Passing outline",
                },
                {
                    "description": "",
                    "keyword": "Scenario",
                    "tags": [{"line": 14, "name": "scenario-outline-passing-tag"}],
                    "steps": [
                        {
                            "line": 16,
                            "match": {"location": ""},
                            "result": {"status": "passed", "duration": InstanceOfType(int)},
                            "keyword": "Given",
                            "name": "type float and value 1.0",
                        },
                    ],
                    "line": 15,
                    "type": "scenario",
                    "id": (
                        "test_scenarios["
                        "file:test.feature-One passing scenario, one failing scenario-"
                        "Passing outline[table_rows:[line: 22]]"
                        "]"
                    ),
                    "name": "Passing outline",
                },
            ],
            "id": "test.feature",
            "keyword": "Feature",
            "line": 2,
            "name": "One passing scenario, one failing scenario",
            "tags": [{"name": "feature-tag", "line": 1}],
            "uri": "test.feature",
        },
    ]

    assert jsonobject == expected


def test_cucumber_json_step_status_parity_with_canonical_messages(testdir, tmp_path):
    """Verify cucumber json step status parity with canonical messages."""
    resultpath = testdir.tmpdir.join("cucumber.json")
    ndjson_path = tmp_path / "cucumber-json-parity.ndjson"

    testdir.makefile(
        ".feature",
        # language=gherkin
        test="""\
        Feature: status parity

            Scenario: pass scenario
                Given a passing step

            Scenario: fail scenario
                Given a failing step
        """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given("a passing step")
        def passing_step():
            return "ok"

        @given("a failing step")
        def failing_step():
            raise RuntimeError("boom")
        """,
    )

    result = testdir.runpytest(
        "-p",
        f"no:{MESSAGE_REPORTER_PLUGIN_NAME}",
        "-p",
        MESSAGE_REPORTER_PLUGIN,
        f"--cucumberjson={resultpath}",
        "--messages-ndjson",
        str(ndjson_path),
        "-s",
    )
    result.assert_outcomes(passed=1, failed=1)

    with resultpath.open() as file:
        json_payload = json.load(file)
    json_statuses = Counter(
        step["result"]["status"]
        for feature in json_payload
        for scenario in feature["elements"]
        for step in scenario["steps"]
    )

    canonical_step_statuses: Counter[str] = Counter()
    for line in ndjson_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        envelope = message_converter.from_dict(json.loads(line), Message)
        payload = envelope.test_step_finished
        if isinstance(payload, _TestStepFinished):
            canonical_step_statuses[payload.test_step_result.status.value.lower()] += 1

    assert json_statuses["passed"] == canonical_step_statuses["passed"]
    assert json_statuses["failed"] == canonical_step_statuses["failed"]
