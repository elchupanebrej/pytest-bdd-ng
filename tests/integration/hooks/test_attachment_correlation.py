import json

import pytest


@pytest.mark.parametrize("late_hook", [False, True])
def test_attachment_retains_explicit_run_correlations_and_real_timestamp(pytester, late_hook):
    pytester.makeini("[pytest]\ncuke_features_dir = .\ncuke_parser = python\n")
    pytester.makefile(".feature", scope="Feature: Scope\n  Scenario: scope\n    Given attach log\n")
    pytester.makeconftest(
        """from pytest_cuke import given
state = {}
def pytest_cuke_message(message):
    if message.test_run_started:
        state["run"] = message.test_run_started.id
    if message.test_run_hook_started:
        state["hook"] = message.test_run_hook_started.id
@given("attach log")
def attach_log(attach):
    options = {"test_run_started_id": state["run"]}
    if LATE_HOOK:
        options["test_run_hook_started_id"] = state["hook"]
    attach("real run log", media_type="text/plain", **options)
""".replace("LATE_HOOK", repr(late_hook))
    )
    result = pytester.runpytest("--cuke-messages-ndjson=messages.ndjson", "-q")
    assert result.ret == (1 if late_hook else 0)
    rows = [json.loads(line) for line in (pytester.path / "messages.ndjson").read_text().splitlines()]
    run_ids = {row["testRunStarted"]["id"] for row in rows if "testRunStarted" in row}
    hook_ids = {row["testRunHookStarted"]["id"] for row in rows if "testRunHookStarted" in row}
    assert {row["testRunHookStarted"]["workerId"] for row in rows if "testRunHookStarted" in row} == {"master"}
    assert hook_ids
    if late_hook:
        assert "OUT_OF_ORDER_LIFECYCLE" in result.stdout.str() + result.stderr.str()
        assert not next(row["testRunFinished"] for row in rows if "testRunFinished" in row)["success"]
        return
    attachment = next(row["attachment"] for row in rows if row.get("attachment", {}).get("body") == "real run log")
    assert attachment["testRunStartedId"] in run_ids
    assert "testRunHookStartedId" not in attachment
    assert attachment["timestamp"]["seconds"] > 0
    assert 0 <= attachment["timestamp"]["nanos"] < 1_000_000_000
