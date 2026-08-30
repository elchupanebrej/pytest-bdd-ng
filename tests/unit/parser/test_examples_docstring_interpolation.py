from __future__ import annotations


def test_examples_interpolation_in_docstring_and_datatable(testdir):
    testdir.makefile(
        ".feature",
        test_interp="""
Feature: Examples interpolation in docstring and data table
    Scenario Outline: Send payload to <endpoint>
        Given I send payload:
            \"\"\"
            {"user": "<username>", "dest": "<endpoint>"}
            \"\"\"
        And with parameters:
            | key      | value        |
            | target   | <endpoint>   |
            | author   | <username>   |
        Then verified payload for "<username>"

        Examples:
            | endpoint | username |
            | /api/v1  | alice    |
            | /api/v2  | bob      |
""",
    )
    testdir.makeconftest(
        """
import json
import pytest
from pytest_bdd import given, then
from pytest_bdd.testing_utils import data_table_to_dicts

captured = []

@given("I send payload:")
def send_payload(step):
    payload = json.loads(step.doc_string.content)
    captured.append(payload)

@given("with parameters:")
def with_params(step):
    params = data_table_to_dicts(step.data_table)
    captured.append(params)

@then('verified payload for "{username}"')
def verify_payload(username):
    assert any(p.get("user") == username for p in captured if isinstance(p, dict) and "user" in p)
"""
    )
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=2)
