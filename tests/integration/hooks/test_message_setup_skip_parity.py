import json

import pytest


@pytest.mark.parametrize(
    "marker", ['pytest.mark.skip(reason="intentional skip")', 'pytest.mark.skipif(True, reason="intentional skip")']
)
def test_explicit_skip_remains_a_reported_skip(pytester, marker):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Skipped scenario\n    Given a working step\n")
    pytester.makeconftest("""
from pathlib import Path
from pytest_cuke import given
@given("a working step")
def step():
    Path("step-executed").touch()
""")
    pytester.makepyfile(
        test_skip=f"""
import pytest
from pytest_cuke import scenario
@{marker}
@scenario("example.feature", "Skipped scenario", features_base_dir=".")
def test_skip():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(skipped=1)
    assert not (pytester.path / "step-executed").exists()
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    started = [event["testStepStarted"] for event in events if "testStepStarted" in event]
    finished = [event["testStepFinished"] for event in events if "testStepFinished" in event]
    assert len(started) == len(finished) == 1
    assert finished[0]["testStepResult"]["status"] == "SKIPPED"
    assert started[0]["testStepId"] == finished[0]["testStepId"]
    assert any("testCaseFinished" in event for event in events)


@pytest.mark.parametrize("feature", ["Feature: Empty\n", "Feature: Other\n  Scenario: Other\n    Given a step\n"])
def test_missing_scenario_remains_skipped_with_messages(pytester, feature):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example=feature)
    pytester.makepyfile(
        test_missing="""
from pytest_cuke import scenario
@scenario("example.feature", "Missing", features_base_dir=".")
def test_missing():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(skipped=1)


def test_setup_failure_is_not_replaced_by_reporting_error(pytester):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Failure\n    Given a step\n")
    pytester.makeconftest("""
import pytest
from pytest_cuke import given

@given("a step")
def step():
    pass

@pytest.fixture(autouse=True)
def broken_setup():
    raise RuntimeError("original setup failure")
""")
    pytester.makepyfile(
        test_failure="""
from pytest_cuke import scenario
@scenario("example.feature", "Failure", features_base_dir=".")
def test_failure():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*RuntimeError: original setup failure*"])


def test_skipped_scenario_does_not_affect_following_scenario(pytester):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(
        ".feature",
        example="Feature: Example\n  Scenario: Skipped\n    Given a step\n  Scenario: Passed\n    Given a step\n",
    )
    pytester.makeconftest("""
from pytest_cuke import given
@given("a step")
def step():
    pass
""")
    pytester.makepyfile(
        test_scenarios="""
import pytest
from pytest_cuke import scenario
@pytest.mark.skip(reason="intentional skip")
@scenario("example.feature", "Skipped", features_base_dir=".")
def test_a_skipped():
    pass
@scenario("example.feature", "Passed", features_base_dir=".")
def test_b_passed():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(passed=1, skipped=1)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    statuses = [
        event["testStepFinished"]["testStepResult"]["status"] for event in events if "testStepFinished" in event
    ]
    assert statuses == ["SKIPPED", "PASSED"]


def test_fixture_skip_is_reported_without_running_steps(pytester):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Fixture skip\n    Given a step\n")
    pytester.makeconftest("""
import pytest
from pytest_cuke import given
@pytest.fixture(autouse=True)
def skip_setup():
    pytest.skip("unavailable dependency")
@given("a step")
def step():
    raise AssertionError("step must not execute")
""")
    pytester.makepyfile(
        test_scenario="""
from pytest_cuke import scenario
@scenario("example.feature", "Fixture skip", features_base_dir=".")
def test_scenario():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(skipped=1)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    finished = [event["testStepFinished"] for event in events if "testStepFinished" in event]
    assert len(finished) == 1
    assert finished[0]["testStepResult"]["status"] == "SKIPPED"


def test_setup_skip_is_visible_in_native_allure(pytester):
    pytest.importorskip("allure_commons")
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Skipped\n    Given a step\n")
    pytester.makeconftest("""
from pytest_cuke import given
@given("a step")
def step():
    raise AssertionError("step must not execute")
""")
    pytester.makepyfile(
        test_scenario="""
import pytest
from pytest_cuke import scenario
@pytest.mark.skip(reason="intentional skip")
@scenario("example.feature", "Skipped", features_base_dir=".")
def test_scenario():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-allure=allure-results", "-q")
    result.assert_outcomes(skipped=1)
    reports = [json.loads(path.read_text()) for path in (pytester.path / "allure-results").glob("*-result.json")]
    assert len(reports) == 1
    assert reports[0]["name"] == "Skipped"
    assert reports[0]["status"] == "skipped"
    assert [(step["name"], step["status"]) for step in reports[0]["steps"]] == [("Given a step", "skipped")]
