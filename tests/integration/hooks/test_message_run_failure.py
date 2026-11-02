import json

import pytest


@pytest.mark.parametrize("failure", ["step", "parse"])
def test_run_failure_preserves_the_exit_status_in_exception_fields(pytester, failure):
    pytester.makeini("[pytest]\ncuke_features_dir = .\ncuke_autoload = true\ncuke_parser = python\n")
    if failure == "parse":
        feature = "Feature: Invalid\n  Scenario: Broken\n    Given text\n    | one |\n    | two | three |\n"
    else:
        feature = "Feature: Failed\n  Scenario: Fails\n    Given a failing step\n"
        pytester.makeconftest(
            'from pytest_cuke import given\n@given("a failing step")\ndef failing():\n'
            '    raise ValueError("step failure")\n'
        )
    pytester.makefile(".feature", failure=feature)
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    assert result.ret == (2 if failure == "parse" else 1)
    envelopes = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    terminal = next(message["testRunFinished"] for message in envelopes if "testRunFinished" in message)
    assert terminal["success"] is False
    assert terminal["exception"] == {
        "type": "PytestExitCode",
        "message": str(int(result.ret)),
        "stackTrace": str(int(result.ret)),
    }
