"""Integration test for before-step hook failure paired envelope and Cucumber JSON (G08)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.integration


def test_before_step_hook_failure_paired_envelope_and_cucumber_json(pytester) -> None:
    pytester.makeini(
        "[pytest]\n"
        "cuke_features_dir = .\n"
        "cuke_autoload = true\n"
        "cuke_parser = python\n"
    )
    feature_content = """\
Feature: Hook Failure Contract
  Scenario: Before step hook failure
    Given a working step
    When a skipped step
"""
    pytester.makefile(".feature", hook_failure=feature_content)
    conftest_content = """\
from pytest_cuke import given, when

def pytest_cuke_before_step(request, run, step_func):
    raise RuntimeError("intentional before_step hook failure")

@given("a working step")
def working_step():
    pass

@when("a skipped step")
def skipped_step():
    pass
"""
    pytester.makeconftest(conftest_content)

    result = pytester.runpytest_subprocess(
        "--cuke-messages-ndjson=messages.ndjson",
        "--cuke-json=cucumber.json",
        "--cuke-json-backend=native",
        "-q",
    )
    assert result.ret != 0

    # 1. Envelopes assertion: paired testStepStarted and testStepFinished
    messages_file = pytester.path / "messages.ndjson"
    assert messages_file.exists()
    envelopes = [json.loads(line) for line in messages_file.read_text(encoding="utf-8").splitlines()]

    step_started_events = [msg["testStepStarted"] for msg in envelopes if "testStepStarted" in msg]
    step_finished_events = [msg["testStepFinished"] for msg in envelopes if "testStepFinished" in msg]

    assert len(step_started_events) >= 1
    assert len(step_started_events) == len(step_finished_events)

    started_by_id = {event["testStepId"]: event for event in step_started_events}
    finished_by_id = {event["testStepId"]: event for event in step_finished_events}

    for step_id in started_by_id:
        assert step_id in finished_by_id, f"testStepStarted {step_id} has no matching testStepFinished"

    # The failing step must be marked FAILED with error details
    first_finished = step_finished_events[0]
    result_payload = first_finished["testStepResult"]
    assert result_payload["status"] == "FAILED"
    assert "intentional before_step hook failure" in (result_payload.get("message") or "")
    exception_payload = result_payload.get("exception")
    assert exception_payload is not None
    assert exception_payload.get("type") == "RuntimeError"
    assert "intentional before_step hook failure" in exception_payload.get("message", "")

    # 2. Cucumber JSON assertion: valid JSON with step formatted as failed
    cucumber_json_file = pytester.path / "cucumber.json"
    assert cucumber_json_file.exists()
    report = json.loads(cucumber_json_file.read_text(encoding="utf-8"))
    assert isinstance(report, list) and len(report) == 1
    feature_report = report[0]
    element = feature_report["elements"][0]
    steps = element["steps"]
    assert len(steps) == 2

    failed_step = steps[0]
    assert failed_step["result"]["status"] == "failed"
    assert "intentional before_step hook failure" in failed_step["result"].get("error_message", "")

    skipped_step = steps[1]
    assert skipped_step["result"]["status"] == "skipped"
