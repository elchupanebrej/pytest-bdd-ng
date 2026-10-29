import json
from collections import Counter

import pytest

pytestmark = pytest.mark.integration


def test_messages_preserve_pickle_step_types_and_publish_unique_definitions(pytester):
    pytester.makeini("[pytest]\ncuke_features_dir = features\n")
    features = pytester.path / "features"
    features.mkdir()
    (features / "definitions.feature").write_text(
        "Feature: Definition catalog\n"
        "  Background:\n    Given stock 2\n"
        "  Scenario: First\n    When sell\n    Then done\n"
        "  Scenario: Second\n    When sell\n    Then done\n"
        "  Scenario Outline: Row <row>\n    When sell\n    Then done\n"
        "    Examples:\n      | row |\n      | one |\n      | two |\n",
        encoding="utf-8",
    )
    pytester.makeconftest(
        r"""
import json
from pathlib import Path
from pytest_cuke import given, when, then, parsers

conversions = []

def convert_amount(value):
    conversions.append(value)
    return value

def pytest_sessionfinish(session):
    Path("conversions.json").write_text(json.dumps(conversions))

@given(parsers.parse("stock {amount:d}"), converters={"amount": convert_amount})
def stock(amount):
    assert amount == 2

@when("sell")
def sell():
    pass

@then("done")
def done():
    pass
"""
    )
    result = pytester.runpytest_subprocess(
        "features/definitions.feature", "--cuke-messages-ndjson=messages.ndjson", "-q"
    )
    result.assert_outcomes(passed=4)
    assert json.loads((pytester.path / "conversions.json").read_text()) == [2, 2, 2, 2]
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    pickles = [event["pickle"] for event in events if "pickle" in event]
    definitions = [event["stepDefinition"] for event in events if "stepDefinition" in event]
    definition_counts = Counter(definition["id"] for definition in definitions)
    type_sequences = [[step.get("type") for step in pickle["steps"]] for pickle in pickles]
    violations = []
    if type_sequences != [["Context", "Action", "Outcome"]] * 4:
        violations.append(f"pickle step types: {type_sequences!r}")
    duplicates = {identifier: count for identifier, count in definition_counts.items() if count != 1}
    if duplicates:
        violations.append(f"repeated stepDefinition ids: {duplicates!r}")
    assert not violations, "\n".join(violations)
    custom_definitions = [
        definition for definition in definitions if definition["sourceReference"]["uri"].endswith("conftest.py")
    ]
    assert {definition["pattern"]["source"] for definition in custom_definitions} == {
        "stock {amount:d}",
        "sell",
        "done",
    }
    test_cases = [event["testCase"] for event in events if "testCase" in event]
    assert len(test_cases) == 4
    referenced_ids = [
        identifier
        for case in test_cases
        for step in case["testSteps"]
        for identifier in step.get("stepDefinitionIds", [])
    ]
    assert len(referenced_ids) == 12
    assert all(definition_counts[identifier] == 1 for identifier in referenced_ids)
    for case in test_cases:
        assert case["testSteps"][0]["stepMatchArgumentsLists"] == [
            {
                "stepMatchArguments": [
                    {
                        "parameterTypeName": "amount",
                        "group": {"children": [], "start": 6, "value": "2"},
                    }
                ],
            }
        ]


def test_message_capture_groups_and_ambiguous_match_diagnostics(pytester):
    pytester.makeini("[pytest]\ncuke_features_dir = features\n")
    features = pytester.path / "features"
    features.mkdir()
    (features / "captures.feature").write_text(
        'Feature: Capture groups\n  Scenario: Captures\n    Given expression value "red"\n    When ambiguous blue\n',
        encoding="utf-8",
    )
    pytester.makeconftest(
        r"""
from pytest_cuke import given, when, parsers

@given(parsers.cucumber_expression("expression value {string}"), anonymous_group_names=["value"])
def expression(value):
    assert value == "red"

@when(parsers.parse("ambiguous {value}"))
def first(value):
    assert value == "blue"

@when(parsers.parse("ambiguous {value}"))
def second(value):
    assert value == "blue"
"""
    )
    result = pytester.runpytest_subprocess("features/captures.feature", "--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(passed=1)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    case = next(event["testCase"] for event in events if "testCase" in event)
    arguments = case["testSteps"][0]["stepMatchArgumentsLists"][0]["stepMatchArguments"]
    assert len(arguments) == 1
    assert arguments[0]["parameterTypeName"] == "value"
    group = arguments[0]["group"]
    assert group["start"] == 17
    assert group["value"] == '"red"'
    assert any(child.get("value") == "red" for child in group["children"])
    assert "stepMatchArgumentsLists" not in case["testSteps"][1]
    assert "Alternative step definitions are found" in result.stdout.str()
