import json
import sys

import pytest
from pytest_cuke.formatter_api import FormatterRequest
from pytest_cuke.formatter_replay import replay_messages


@pytest.mark.parametrize("skip_flag,xfail_flag", [(False, False), (True, False), (False, True), (True, True)])
def test_skip_and_xfail_report_policies_are_independent(pytester, skip_flag, xfail_flag):
    pytest.importorskip("allure_commons")
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(
        ".feature",
        example="Feature: Example\n  Scenario: Ordinary\n    Given a step\n  Scenario: Expected\n    Given a step\n",
    )
    pytester.makeconftest("""
from pytest_cuke import given
@given("a step")
def step():
    raise AssertionError("must not execute")
""")
    pytester.makepyfile(
        test_cases="""
import pytest
from pytest_cuke import scenario
@pytest.mark.skip(reason="ordinary skip")
@scenario("example.feature", "Ordinary", features_base_dir=".")
def test_skip():
    pass
@pytest.mark.xfail(reason="expected skip", run=False)
@scenario("example.feature", "Expected", features_base_dir=".")
def test_xfail():
    pass
"""
    )
    flags = (["--cuke-skip-as-failed"] if skip_flag else []) + (["--cuke-xfail-as-failed"] if xfail_flag else [])
    result = pytester.runpytest_subprocess("--cuke-allure=live", "--cuke-messages-ndjson=messages.ndjson", *flags, "-q")
    result.assert_outcomes(skipped=1, xfailed=1)
    replay = pytester.runpytest_subprocess(
        "--cuke-allure-messages-in=messages.ndjson", "--cuke-allure=replay", *flags, "-q"
    )
    assert replay.ret == 0
    expected = {"Ordinary": "failed" if skip_flag else "skipped", "Expected": "failed" if xfail_flag else "skipped"}
    for directory in ("live", "replay"):
        reports = [json.loads(path.read_text()) for path in (pytester.path / directory).glob("*-result.json")]
        assert {report["name"]: report["status"] for report in reports} == expected
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    assert all(
        event["testStepFinished"]["testStepResult"]["status"] == "SKIPPED"
        for event in events
        if "testStepFinished" in event
    )


def test_strict_xpass_fails_live_and_replayed_allure_but_preserves_steps(pytester):
    pytest.importorskip("allure_commons")
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Unexpected pass\n    Given a step\n")
    pytester.makeconftest("""
from pytest_cuke import given
@given("a step")
def step():
    pass
""")
    pytester.makepyfile(
        test_xpass="""
import pytest
from pytest_cuke import scenario
@pytest.mark.xfail(reason="known issue", strict=True)
@scenario("example.feature", "Unexpected pass", features_base_dir=".")
def test_scenario():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-allure=live", "--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(failed=1)
    replay = pytester.runpytest_subprocess("--cuke-allure-messages-in=messages.ndjson", "--cuke-allure=replayed", "-q")
    assert replay.ret == 0
    for directory in ("live", "replayed"):
        reports = [json.loads(path.read_text()) for path in (pytester.path / directory).glob("*-result.json")]
        assert len(reports) == 1
        assert reports[0]["status"] == "failed"
        assert "known issue" in reports[0]["statusDetails"]["message"]
        assert [step["status"] for step in reports[0]["steps"]] == ["passed"]


def test_strict_xpass_outcome_is_preserved_in_messages(pytester):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Unexpected pass\n    Given a step\n")
    pytester.makeconftest("""
from pytest_cuke import given
@given("a step")
def step():
    pass
""")
    pytester.makepyfile(
        test_xpass="""
import pytest
from pytest_cuke import scenario
@pytest.mark.xfail(reason="known issue", strict=True)
@scenario("example.feature", "Unexpected pass", features_base_dir=".")
def test_scenario():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(failed=1)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    metadata = [
        json.loads(event["attachment"]["body"])
        for event in events
        if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.pytest-outcome+json"
    ]
    assert len(metadata) == 1
    assert metadata[0]["outcome"] == "xpass-strict"
    assert metadata[0]["reason"] == "known issue"
    assert metadata[0]["executed"] is True
    finished = [event["testStepFinished"] for event in events if "testStepFinished" in event]
    assert [step["testStepResult"]["status"] for step in finished] == ["PASSED"]


def test_unexpected_exception_is_not_mistaken_for_strict_xpass(pytester):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Unexpected failure\n    Given a step\n")
    pytester.makeconftest("""
from pytest_cuke import given
@given("a step")
def step():
    raise AssertionError("[XPASS(strict)] not a real xpass")
""")
    pytester.makepyfile(
        test_failure="""
import pytest
from pytest_cuke import scenario
@pytest.mark.xfail(reason="known issue", raises=ValueError, strict=True)
@scenario("example.feature", "Unexpected failure", features_base_dir=".")
def test_scenario():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(failed=1)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    assert not any(
        event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.pytest-outcome+json"
        for event in events
    )


@pytest.mark.parametrize(
    ("step_body", "expected"), [('raise AssertionError("actual failure")', "xfail"), ("pass", "xpass")]
)
def test_executed_xfail_outcome_is_preserved_in_messages(pytester, step_body, expected):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Expected failure\n    Given a step\n")
    pytester.makeconftest(f"""
from pytest_cuke import given
@given("a step")
def step():
    {step_body}
""")
    pytester.makepyfile(
        test_xfail="""
import pytest
from pytest_cuke import scenario
@pytest.mark.xfail(reason="known issue", strict=False)
@scenario("example.feature", "Expected failure", features_base_dir=".")
def test_scenario():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(**({"xfailed": 1} if expected == "xfail" else {"xpassed": 1}))
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    metadata = [
        json.loads(event["attachment"]["body"])
        for event in events
        if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.pytest-outcome+json"
    ]
    assert len(metadata) == 1
    assert metadata[0]["outcome"] == expected
    assert metadata[0]["executed"] is True
    assert "known issue" in metadata[0]["reason"]
    assert any(event.get("testCaseStarted", {}).get("id") == metadata[0]["testCaseStartedId"] for event in events)
    metadata_index = next(
        index
        for index, event in enumerate(events)
        if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.pytest-outcome+json"
    )
    finish_index = next(index for index, event in enumerate(events) if "testCaseFinished" in event)
    assert metadata_index < finish_index
    if expected == "xfail":
        assert any("actual failure" in json.dumps(event) for event in events)


@pytest.mark.parametrize("run", [False, True])
def test_xfail_is_reported_as_expected_skip(pytester, run):
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Expected failure\n    Given a failing step\n")
    pytester.makeconftest("""
from pytest_cuke import given
@given("a failing step")
def step():
    raise AssertionError("actual failure")
""")
    pytester.makepyfile(
        test_xfail=f"""
import pytest
from pytest_cuke import scenario
@pytest.mark.xfail(reason="known issue", run={run})
@scenario("example.feature", "Expected failure", features_base_dir=".")
def test_scenario():
    pass
"""
    )
    result = pytester.runpytest_subprocess("--cuke-messages-ndjson=messages.ndjson", "-q")
    result.assert_outcomes(xfailed=1)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    finished = [event["testStepFinished"] for event in events if "testStepFinished" in event]
    assert len(finished) == 1
    assert finished[0]["testStepResult"]["status"] == "SKIPPED"
    assert any("known issue" in json.dumps(event) for event in events)
    if run:
        assert any("actual failure" in json.dumps(event) for event in events)
    else:
        metadata = [
            json.loads(event["attachment"]["body"])
            for event in events
            if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.pytest-outcome+json"
        ]
        assert len(metadata) == 1
        assert metadata[0]["outcome"] == "xfail"
        assert metadata[0]["executed"] is False
        assert "known issue" in metadata[0]["reason"]


def test_not_run_xfail_is_visible_in_native_allure(pytester):
    pytest.importorskip("allure_commons")
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(".feature", example="Feature: Example\n  Scenario: Expected failure\n    Given a step\n")
    pytester.makeconftest("""
from pytest_cuke import given
@given("a step")
def step():
    raise AssertionError("step must not execute")
""")
    pytester.makepyfile(
        test_xfail="""
import pytest
from pytest_cuke import scenario
@pytest.mark.xfail(reason="known issue", run=False)
@scenario("example.feature", "Expected failure", features_base_dir=".")
def test_scenario():
    pass
"""
    )
    result = pytester.runpytest_subprocess(
        "--cuke-allure=allure-results", "--cuke-messages-ndjson=messages.ndjson", "-q"
    )
    result.assert_outcomes(xfailed=1)
    reports = [json.loads(path.read_text()) for path in (pytester.path / "allure-results").glob("*-result.json")]
    assert len(reports) == 1
    assert reports[0]["status"] == "skipped"
    assert "known issue" in reports[0]["statusDetails"]["message"]
    assert [(step["name"], step["status"]) for step in reports[0]["steps"]] == [("Given a step", "skipped")]
    assert all(
        attachment.get("type") != "application/vnd.pytest-cuke.pytest-outcome+json"
        for attachment in reports[0].get("attachments", [])
    )
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    assert any(
        event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.pytest-outcome+json"
        for event in events
    )
    replay = pytester.runpytest_subprocess("--cuke-allure-messages-in=messages.ndjson", "--cuke-allure=replayed", "-q")
    assert replay.ret == 0
    replayed = [json.loads(path.read_text()) for path in (pytester.path / "replayed").glob("*-result.json")]
    assert len(replayed) == 1
    assert replayed[0]["status"] == "skipped"
    assert all(
        attachment.get("type") != "application/vnd.pytest-cuke.pytest-outcome+json"
        for attachment in replayed[0].get("attachments", [])
    )


def test_executed_xfail_is_skipped_in_live_and_replayed_allure(pytester):
    pytest.importorskip("allure_commons")
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(
        ".feature",
        example="Feature: Example\n  Scenario: Expected failure\n    Given a failing step\n    And a later step\n",
    )
    pytester.makeconftest("""
from pytest_cuke import given
@given("a failing step")
def step():
    raise AssertionError("actual failure")
@given("a later step")
def later():
    raise AssertionError("later step must not run")
""")
    pytester.makepyfile(
        test_xfail="""
import pytest
from pytest_cuke import scenario
@pytest.mark.xfail(reason="known issue")
@scenario("example.feature", "Expected failure", features_base_dir=".")
def test_scenario():
    pass
"""
    )
    result = pytester.runpytest_subprocess(
        "--cuke-allure=allure-results", "--cuke-messages-ndjson=messages.ndjson", "-q"
    )
    result.assert_outcomes(xfailed=1)
    raw = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    assert all(
        event["testStepFinished"]["testStepResult"]["status"] == "SKIPPED"
        for event in raw
        if "testStepFinished" in event
    )
    metadata = [
        json.loads(event["attachment"]["body"])
        for event in raw
        if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.pytest-outcome+json"
    ]
    assert metadata[0]["actualStepResults"][0]["result"]["status"] == "FAILED"
    assert "actual failure" in json.dumps(metadata[0]["actualStepResults"])
    assert "AssertionError: actual failure" in metadata[0]["actualStepResults"][0]["result"]["exception"]["stackTrace"]
    formatter_output = pytester.path / "formatter.ndjson"
    replay_messages(
        pytester.path / "messages.ndjson",
        (
            FormatterRequest(
                name="probe",
                command=(sys.executable, "-c", "import sys; sys.stdout.write(sys.stdin.read())"),
                output_path=formatter_output,
                working_directory=pytester.path,
                timeout_seconds=5,
            ),
        ),
    )
    formatted = [json.loads(line) for line in formatter_output.read_text().splitlines()]
    assert any(
        event.get("testStepFinished", {}).get("testStepResult", {}).get("status") == "SKIPPED" for event in formatted
    )
    diagnostic_output = pytester.path / "diagnostic.ndjson"
    replay_messages(
        pytester.path / "messages.ndjson",
        (
            FormatterRequest(
                name="probe",
                command=(sys.executable, "-c", "import sys; sys.stdout.write(sys.stdin.read())"),
                output_path=diagnostic_output,
                working_directory=pytester.path,
                timeout_seconds=5,
            ),
        ),
        xfail_as_failed=True,
    )
    diagnostic = [json.loads(line) for line in diagnostic_output.read_text().splitlines()]
    assert any(
        event.get("testStepFinished", {}).get("testStepResult", {}).get("status") == "FAILED" for event in diagnostic
    )
    replay = pytester.runpytest_subprocess("--cuke-allure-messages-in=messages.ndjson", "--cuke-allure=replayed", "-q")
    assert replay.ret == 0
    for directory in ("allure-results", "replayed"):
        reports = [json.loads(path.read_text()) for path in (pytester.path / directory).glob("*-result.json")]
        assert len(reports) == 1
        assert reports[0]["status"] == "skipped"
        assert [step["status"] for step in reports[0]["steps"]] == ["skipped", "skipped"]
        assert "known issue" in reports[0]["steps"][0]["statusDetails"]["message"]
        assert "actual failure" in reports[0]["steps"][0]["statusDetails"]["message"]
    diagnostic_replay = pytester.runpytest_subprocess(
        "--cuke-allure-messages-in=messages.ndjson", "--cuke-allure=diagnostic-replay", "--cuke-xfail-as-failed", "-q"
    )
    assert diagnostic_replay.ret == 0
    diagnostic_live = pytester.runpytest_subprocess("--cuke-allure=diagnostic-live", "--cuke-xfail-as-failed", "-q")
    diagnostic_live.assert_outcomes(xfailed=1)
    for directory in ("diagnostic-replay", "diagnostic-live"):
        reports = [json.loads(path.read_text()) for path in (pytester.path / directory).glob("*-result.json")]
        assert len(reports) == 1
        assert reports[0]["status"] == "failed"
        assert reports[0]["steps"][0]["status"] == "failed"
        assert "actual failure" in reports[0]["steps"][0]["statusDetails"]["message"]


def test_xdist_xfail_metadata_references_the_correct_attempt(pytester):
    pytest.importorskip("xdist")
    pytest.importorskip("allure_commons")
    pytester.makeini("[pytest]\ncuke_parser = python\ncuke_autoload = false\n")
    pytester.makefile(
        ".feature",
        example=(
            "Feature: Example\n  Scenario: Expected failure\n    Given a failing step\n"
            "  Scenario: Unexpected success\n    Given a passing step\n"
        ),
    )
    pytester.makeconftest("""
from pytest_cuke import given
@given("a failing step")
def step():
    raise AssertionError("actual failure")
@given("a passing step")
def passing():
    pass
""")
    pytester.makepyfile(
        test_xfail="""
import pytest
from pytest_cuke import scenario
@pytest.mark.xfail(reason="known issue")
@scenario("example.feature", "Expected failure", features_base_dir=".")
def test_executed():
    pass
@pytest.mark.xfail(reason="not run", run=False)
@scenario("example.feature", "Expected failure", features_base_dir=".")
def test_not_run():
    pass
@pytest.mark.xfail(reason="strict issue", strict=True)
@scenario("example.feature", "Unexpected success", features_base_dir=".")
def test_strict_xpass():
    pass
"""
    )
    result = pytester.runpytest_subprocess(
        "-p", "xdist.plugin", "-n", "2", "--cuke-messages-ndjson=messages.ndjson", "--cuke-allure=allure-results", "-q"
    )
    result.assert_outcomes(xfailed=2, failed=1)
    events = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    started_ids = {event["testCaseStarted"]["id"] for event in events if "testCaseStarted" in event}
    metadata = [
        json.loads(event["attachment"]["body"])
        for event in events
        if event.get("attachment", {}).get("mediaType") == "application/vnd.pytest-cuke.pytest-outcome+json"
    ]
    assert {item["executed"] for item in metadata} == {True, False}
    assert sorted(item["outcome"] for item in metadata) == ["xfail", "xfail", "xpass-strict"]
    assert all(item["testCaseStartedId"] in started_ids for item in metadata)
    actual = next(item for item in metadata if item["outcome"] == "xfail" and item["executed"])
    actual_step = actual["actualStepResults"][0]
    assert actual_step["result"]["status"] == "FAILED"
    assert any(
        event.get("testStepFinished", {}).get("testStepId") == actual_step["testStepId"]
        and event["testStepFinished"]["testCaseStartedId"] == actual["testCaseStartedId"]
        and event["testStepFinished"]["testStepResult"]["status"] == "SKIPPED"
        for event in events
    )
    finished_at = {
        event["testCaseFinished"]["testCaseStartedId"]: index
        for index, event in enumerate(events)
        if "testCaseFinished" in event
    }
    for index, event in enumerate(events):
        attachment = event.get("attachment", {})
        if attachment.get("mediaType") == "application/vnd.pytest-cuke.pytest-outcome+json":
            attempt_id = attachment["testCaseStartedId"]
            assert json.loads(attachment["body"])["testCaseStartedId"] == attempt_id
            assert index < finished_at[attempt_id]
    reports = [json.loads(path.read_text()) for path in (pytester.path / "allure-results").glob("*-result.json")]
    assert len(reports) == 3
    assert [report["status"] for report in reports].count("skipped") == 2
    assert [report["status"] for report in reports].count("failed") == 1
    assert all(
        attachment.get("type") != "application/vnd.pytest-cuke.pytest-outcome+json"
        for report in reports
        for attachment in report.get("attachments", [])
    )
