import json

import pytest


@pytest.mark.parametrize("workers", [None, 2])
def test_test_cases_reference_the_emitted_run(pytester, workers):
    pytester.makeini("[pytest]\ncuke_features_dir = .\ncuke_autoload = true\ncuke_parser = python\n")
    pytester.makefile(
        ".feature",
        parent="Feature: Run references\n  Scenario: First\n    Given a step\n  Scenario: Second\n    Given a step\n",
    )
    pytester.makeconftest('from pytest_cuke import given\n@given("a step")\ndef a_step():\n    pass\n')
    arguments = ["--cuke-messages-ndjson=messages.ndjson", "-q"]
    if workers is not None:
        arguments.extend(["-n", str(workers)])
    result = pytester.runpytest_subprocess(*arguments)
    result.assert_outcomes(passed=2)
    envelopes = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    run_ids = {message["testRunStarted"]["id"] for message in envelopes if "testRunStarted" in message}
    cases = [message["testCase"] for message in envelopes if "testCase" in message]
    assert cases
    assert all(case.get("testRunStartedId") in run_ids for case in cases), (cases, run_ids)
