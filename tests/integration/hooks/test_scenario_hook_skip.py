import json

import pytest


def _messages(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _hook_result(events):
    test_case = next(event["testCase"] for event in events if "testCase" in event)
    hook_steps = [step for step in test_case["testSteps"] if "hookId" in step]
    assert len(hook_steps) == 1, hook_steps
    hook_step_id = hook_steps[0]["id"]
    finished = [
        event["testStepFinished"]["testStepResult"]
        for event in events
        if "testStepFinished" in event and event["testStepFinished"]["testStepId"] == hook_step_id
    ]
    assert len(finished) == 1, finished
    return finished[0]


@pytest.mark.parametrize("phase", ["before", "after"])
def test_scenario_hook_skip_reports_a_skipped_hook_step(pytester, phase):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Hook skips\n    Given a working step\n")
    pytester.makepyfile(
        test_scenario="""
from pytest_cuke import scenario
@scenario("example.feature", "Hook skips", features_base_dir=".")
def test_hook_skip():
    pass
"""
    )
    pytester.makeconftest(f"""
import pytest
from pytest_cuke import given

@given("a working step")
def step():
    pass

def pytest_cuke_{phase}_scenario(request, run):
    pytest.skip("{phase} hook skip sentinel")
""")
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(skipped=1)

    hook_result = _hook_result(_messages(pytester.path / "messages.ndjson"))
    assert hook_result["status"] == "SKIPPED"
    assert hook_result["message"] == f"{phase} hook skip sentinel"
    assert "exception" not in hook_result
