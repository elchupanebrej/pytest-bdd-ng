import json

import pytest


def test_empty_scenario_without_allure_passes(pytester):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", empty="Feature: Empty\n  Scenario: Empty scenario\n")
    pytester.makepyfile(
        test_scenario="""
from pytest_cuke import scenario
@scenario("empty.feature", "Empty scenario", features_base_dir=".")
def test_empty():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(passed=1)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    assert any("testCaseFinished" in event for event in events)
    metadata = [
        json.loads(event["attachment"]["body"])
        for event in events
        if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.pytest-outcome+json"
    ]
    assert metadata == []


def test_empty_scenario_is_skipped_but_background_only_runs(pytester):
    pytest.importorskip("allure_commons")
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(
        ".feature",
        empty="Feature: Empty\n  Scenario: Empty scenario\n",
        background="Feature: Background\n  Background:\n    Given work\n  Scenario: Background only\n",
    )
    pytester.makeconftest("""
from pytest_cuke import given
@given("work")
def work():
    pass
""")
    pytester.makepyfile(
        test_scenarios="""
from pytest_cuke import scenario
@scenario("empty.feature", "Empty scenario", features_base_dir=".")
def test_empty():
    pass
@scenario("background.feature", "Background only", features_base_dir=".")
def test_background():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-allure=live", "--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(passed=2)
    replay = pytester.runpytest_subprocess("--cuke-allure-messages-in=messages.ndjson", "--cuke-allure=replay", "-q")
    assert replay.ret == 0
    for directory in ("live", "replay"):
        reports = [json.loads(path.read_text()) for path in (pytester.path / directory).glob("*-result.json")]
        assert {report["name"]: report["status"] for report in reports} == {
            "Empty scenario": "passed",
            "Background only": "passed",
        }
    diagnostic = pytester.runpytest_subprocess("--cuke-allure=diagnostic", "--cuke-skip-as-failed", "-q")
    diagnostic.assert_outcomes(passed=2)
    diagnostic_replay = pytester.runpytest_subprocess(
        "--cuke-allure-messages-in=messages.ndjson", "--cuke-allure=diagnostic-replay", "--cuke-skip-as-failed", "-q"
    )
    assert diagnostic_replay.ret == 0
    for directory in ("diagnostic", "diagnostic-replay"):
        reports = [json.loads(path.read_text()) for path in (pytester.path / directory).glob("*-result.json")]
        assert {report["name"]: report["status"] for report in reports} == {
            "Empty scenario": "passed",
            "Background only": "passed",
        }
