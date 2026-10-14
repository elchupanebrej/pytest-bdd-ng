"""Acceptance assertions for session-owned runtime integration scenarios."""

from __future__ import annotations

import json
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from pytest_cuke import then


def _runtime_artifact_path(relative_path: str, consumer: Any) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("consumer runtime artifact paths must stay inside the consumer project")
    project_root = consumer.path.resolve()
    artifact_path = (project_root / candidate).resolve()
    try:
        artifact_path.relative_to(project_root)
    except ValueError as exc:
        raise ValueError("consumer runtime artifact paths must stay inside the consumer project") from exc
    return artifact_path


def _jsonl_artifact_rows(relative_path: str, consumer: Any, artifact_name: str) -> list[dict[str, Any]]:
    artifact_path = _runtime_artifact_path(relative_path, consumer)
    assert artifact_path.is_file(), f"{artifact_name} {relative_path!r} does not exist"
    rows = [json.loads(line) for line in artifact_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert all(isinstance(row, dict) for row in rows), rows
    return rows


def _runtime_jsonl(relative_path: str, consumer: Any) -> list[dict[str, Any]]:
    return _jsonl_artifact_rows(relative_path, consumer, "consumer runtime artifact")


def _messages_envelopes(relative_path: str, consumer: Any) -> list[dict[str, Any]]:
    return _jsonl_artifact_rows(relative_path, consumer, "Messages artifact")


@then("the installed consumer should use the current PyPy 3.12 interpreter")
def installed_consumer_uses_current_pypy_312_interpreter(consumer: Any) -> None:
    expected_runtime = {
        "implementation": platform.python_implementation(),
        "version": [sys.version_info.major, sys.version_info.minor],
    }
    assert expected_runtime == {"implementation": "PyPy", "version": [3, 12]}, expected_runtime

    probe = (
        "import json, platform, sys; "
        "print(json.dumps({'implementation': platform.python_implementation(), "
        "'version': [sys.version_info.major, sys.version_info.minor]}))"
    )
    result = subprocess.run(
        [str(consumer.python), "-c", probe],
        cwd=consumer.path,
        env=consumer.env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"could not inspect installed consumer runtime:\n{result.stdout}\n{result.stderr}"
    actual_runtime = json.loads(result.stdout)
    assert actual_runtime == expected_runtime, (actual_runtime, expected_runtime)


@then(
    re.compile(
        r'consumer Messages artifact "(?P<relative_path>[^"]+)" should identify scenario "(?P<scenario_name>[^"]+)"'
    )
)
def consumer_messages_artifact_identifies_scenario(
    relative_path: str,
    scenario_name: str,
    consumer: Any,
) -> None:
    envelopes = _messages_envelopes(relative_path, consumer)
    pickles = [envelope["pickle"] for envelope in envelopes if isinstance(envelope.get("pickle"), dict)]
    assert len(pickles) == 1, pickles
    assert pickles[0].get("name") == scenario_name, pickles[0]


@then(
    re.compile(
        r'consumer runtime artifact "(?P<observation_path>[^"]+)" should match the run ID in Messages '
        r'"(?P<messages_path>[^"]+)"'
    )
)
def consumer_runtime_run_id_matches_messages(
    observation_path: str,
    messages_path: str,
    consumer: Any,
) -> None:
    observation = json.loads(_runtime_artifact_path(observation_path, consumer).read_text(encoding="utf-8"))
    run_id = observation.get("run_id")
    assert isinstance(run_id, str) and run_id, observation

    envelopes = _messages_envelopes(messages_path, consumer)
    run_started = [envelope["testRunStarted"] for envelope in envelopes if "testRunStarted" in envelope]
    assert len(run_started) == 1, run_started
    run_started_id = run_started[0].get("id")
    assert isinstance(run_started_id, str), run_started
    assert re.fullmatch(rf"{re.escape(run_id)}-\d+", run_started_id), (run_id, run_started_id)


def _single_messages_case(
    relative_path: str,
    consumer: Any,
    expected_step_count: int,
    problems: list[str],
) -> (
    tuple[
        dict[str, Any],
        dict[str, Any],
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]
    | None
):
    try:
        envelopes = _messages_envelopes(relative_path, consumer)
    except AssertionError as exc:
        problems.append(f"Messages artifact {relative_path!r} could not be read: {exc}")
        return None

    cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    starts = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    finishes = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    if len(cases) != 1:
        problems.append(f"expected one Messages TestCase, got {len(cases)}")
    if len(starts) != 1:
        problems.append(f"expected one Messages TestCaseStarted, got {len(starts)}")
    if len(finishes) != 1:
        problems.append(f"expected one Messages TestCaseFinished, got {len(finishes)}")
    if len(cases) != 1 or len(starts) != 1:
        return None

    case = cases[0]
    started = starts[0]
    test_steps = case.get("testSteps", [])
    if len(test_steps) != expected_step_count:
        problems.append(f"Messages TestCase has {len(test_steps)} test steps, expected {expected_step_count}")
    if started.get("testCaseId") != case.get("id"):
        problems.append("Messages TestCaseStarted does not reference its TestCase")
    if len(finishes) == 1 and finishes[0].get("testCaseStartedId") != started.get("id"):
        problems.append("Messages TestCaseFinished does not reference the interrupted TestCaseStarted")

    step_finishes = [
        envelope["testStepFinished"]
        for envelope in envelopes
        if "testStepFinished" in envelope and envelope["testStepFinished"].get("testCaseStartedId") == started.get("id")
    ]
    expected_step_ids = [step.get("id") for step in test_steps]
    finished_step_ids = [finish.get("testStepId") for finish in step_finishes]
    if finished_step_ids != expected_step_ids:
        problems.append(
            f"Messages finished step IDs={finished_step_ids!r}, expected scenario order {expected_step_ids!r}"
        )
    return case, started, test_steps, step_finishes, envelopes


def _split_messages_steps(
    test_steps: list[dict[str, Any]],
    step_finishes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    results_by_step_id = {finish.get("testStepId"): finish for finish in step_finishes}
    scenario_steps = [step for step in test_steps if "pickleStepId" in step]
    scenario_finishes = [results_by_step_id.get(step.get("id"), {}) for step in scenario_steps]
    hook_statuses = [
        str(results_by_step_id.get(step.get("id"), {}).get("testStepResult", {}).get("status", "")).lower()
        for step in test_steps
        if "hookId" in step
    ]
    return scenario_steps, scenario_finishes, hook_statuses


def _messages_hook_finishes(
    test_steps: list[dict[str, Any]],
    step_finishes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results_by_step_id = {finish.get("testStepId"): finish for finish in step_finishes}
    return [
        results_by_step_id.get(step.get("id"), {})
        for step in test_steps
        if "hookId" in step
    ]


def _split_json_report_steps(
    steps: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[tuple[str, str]]]:
    scenario_steps = [step for step in steps if step.get("keyword") not in {"Before", "After"}]
    hook_statuses = [
        (step.get("keyword", ""), str(step.get("result", {}).get("status", "")).lower())
        for step in steps
        if step.get("keyword") in {"Before", "After"}
    ]
    return scenario_steps, hook_statuses


def _json_hook_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [step for step in steps if step.get("keyword") in {"Before", "After"}]


def _normalize_outline_row_suffix(name: str) -> str:
    return re.sub(r"\s*\[table_rows:\[line:\s*\d+\]\]$", "", name)


def _source_uri_identity(uri: str) -> str:
    """Normalize consumer and parser URIs while keeping their feature-relative identity."""
    path = uri.removeprefix("file://").removeprefix("file:")
    marker = "/features/"
    if marker in path:
        path = path.split(marker, 1)[1]
    return path.lstrip("/")


def _single_json_scenario_steps(
    relative_path: str,
    consumer: Any,
    feature_basename: str,
    scenario_name: str,
    problems: list[str],
) -> list[dict[str, Any]] | None:
    try:
        report = json.loads(_runtime_artifact_path(relative_path, consumer).read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append(f"JSON report {relative_path!r} was not produced")
        return None

    features = [feature for feature in report if _uri_basename(feature.get("uri", "")) == feature_basename]
    if len(features) != 1:
        problems.append(f"expected one {feature_basename!r} feature in JSON report, got {len(features)}")
        return None
    scenarios = [element for element in features[0].get("elements", []) if element.get("name") == scenario_name]
    if len(scenarios) != 1:
        problems.append(f"expected one {scenario_name!r} scenario in JSON report, got {len(scenarios)}")
        return None
    return scenarios[0].get("steps", [])


@then(
    re.compile(
        r'consumer runtime artifact "(?P<relative_path>[^"]+)" should show isolated rows and monotonic hook phases'
    )
)
def consumer_runtime_rows_are_isolated(relative_path: str, consumer: Any) -> None:
    rows = _runtime_jsonl(relative_path, consumer)
    assert len(rows) == 4, rows
    scenario_names = [row["scenario_name"] for row in rows]
    assert scenario_names.count("The first ordinary scenario has clean step state") == 1, rows
    assert scenario_names.count("The second ordinary scenario starts with clean step state") == 1, rows
    assert (
        sum(name.startswith("Each outline row starts with clean step state for <label>") for name in scenario_names)
        == 2
    ), rows
    assert len({row["nodeid"] for row in rows}) == 4, rows
    for field in ("scenario_identity", "attempt_id", "test_case_id", "test_case_started_id"):
        values = [row[field] for row in rows]
        assert all(values) and len(set(values)) == 4, (field, values)

    assert len({row["run_id"] for row in rows}) == 1, rows
    assert len({row["binding_identity"] for row in rows}) == 1, rows
    assert len({row["feature_uri"] for row in rows}) == 1, rows
    expected_phases = [
        "setup",
        "pytest_cuke_before_scenario",
        "pytest_cuke_before_step",
        "pytest_cuke_before_step",
        "pytest_cuke_before_step",
        "pytest_cuke_after_scenario",
        "finished",
    ]
    expected_runtime_phases = [
        "pytest_cuke_match_step_definition_to_step",
        "pytest_cuke_before_scenario",
        "pytest_cuke_before_step",
        "pytest_cuke_before_step",
        "pytest_cuke_before_step",
        "pytest_cuke_after_scenario",
        "pytest_cuke_after_scenario",
    ]
    for row in rows:
        snapshots = row["snapshots"]
        assert [snapshot["hook_phase"] for snapshot in snapshots] == expected_phases, snapshots
        assert [snapshot["runtime_hook_phase"] for snapshot in snapshots] == expected_runtime_phases, snapshots
        indexes = [snapshot["transition_index"] for snapshot in snapshots]
        assert indexes == sorted(indexes), snapshots
        assert [(snapshot["stage"], snapshot["status"]) for snapshot in snapshots] == [
            ("setup", "running"),
            ("setup", "running"),
            ("step-running", "running"),
            ("step-running", "running"),
            ("step-running", "running"),
            ("finished", "passed"),
            ("finished", "passed"),
        ], snapshots
        assert all(snapshot["active_scenario"] for snapshot in snapshots), snapshots
        assert all(snapshot["scenario_identity"] == row["scenario_identity"] for snapshot in snapshots), snapshots
        assert [snapshot["scenario_status"] for snapshot in snapshots] == [
            "running",
            "running",
            "running",
            "running",
            "running",
            "passed",
            "passed",
        ], snapshots
        assert [snapshot["step_index"] for snapshot in snapshots[2:5]] == [0, 1, 2], snapshots
        assert row["status"] == "passed", row
        assert len(row["steps"]) == 3, row
        assert [step["status"] for step in row["steps"]] == ["passed", "passed", "passed"], row
        assert row["steps"][0]["result"] == row["row_value"], row
        assert row["steps"][1]["result"] == f"{row['row_value']}:verified", row


@then(
    re.compile(r'consumer runtime artifact "(?P<relative_path>[^"]+)" should show failed teardown then clean BDD state')
)
def consumer_runtime_cleanup_isolation(relative_path: str, consumer: Any) -> None:
    rows = _runtime_jsonl(relative_path, consumer)
    assert len(rows) == 4, rows
    failed_name = "Teardown failure happens before the next scenario"
    clean_name = "A fresh scenario follows a teardown failure"
    failed_call = next(row for row in rows if row["scenario_name"] == failed_name and row["phase"] == "call")
    failed_teardown = next(row for row in rows if row["scenario_name"] == failed_name and row["phase"] == "teardown")
    clean_call = next(row for row in rows if row["scenario_name"] == clean_name and row["phase"] == "call")
    clean_teardown = next(row for row in rows if row["scenario_name"] == clean_name and row["phase"] == "teardown")

    assert failed_call["status"] == "passed" and failed_call["active_scenario"] is True, failed_call
    assert failed_teardown["status"] == "failed", failed_teardown
    assert failed_teardown["active_scenario"] is False, failed_teardown
    assert failed_teardown["last_error"] == "runtime teardown failure sentinel", failed_teardown
    assert clean_call["status"] == "passed" and clean_call["active_scenario"] is True, clean_call
    assert clean_call["last_error"] is None, clean_call
    assert clean_teardown["status"] == "passed" and clean_teardown["active_scenario"] is False, clean_teardown
    assert clean_teardown["last_error"] is None, clean_teardown
    assert failed_teardown["run_id"] == clean_teardown["run_id"], rows
    assert failed_teardown["scenario_identity"] != clean_teardown["scenario_identity"], rows
    assert failed_teardown["attempt_id"] and clean_teardown["attempt_id"]
    assert failed_teardown["attempt_id"] != clean_teardown["attempt_id"], rows


@then(
    re.compile(
        r'consumer runtime snapshot "(?P<relative_path>[^"]+)" should show clean plain pytest state after BDD teardown'
    )
)
def consumer_plain_pytest_after_runtime_cleanup(relative_path: str, consumer: Any) -> None:
    snapshot = json.loads(_runtime_artifact_path(relative_path, consumer).read_text(encoding="utf-8"))
    assert snapshot == {
        "active_feature_binding": False,
        "active_scenario_run": False,
        "last_error": None,
        "scenario_count": 2,
        "status": "inactive",
    }, snapshot


@then(
    re.compile(
        r'consumer runtime artifacts "(?P<runtime_path>[^"]+)" and "(?P<messages_path>[^"]+)" '
        r"should retain distinct terminal outcomes after cleanup"
    )
)
def consumer_terminal_outcomes_after_cleanup(runtime_path: str, messages_path: str, consumer: Any) -> None:
    observations = _runtime_jsonl(runtime_path, consumer)
    envelopes = _messages_envelopes(messages_path, consumer)
    expected = {
        "Assertion failure is retained after teardown cleanup": {
            "scenario_status": "failed",
            "step_status": "failed",
            "exception_type": "AssertionError",
            "exception_message": "runtime assertion sentinel",
            "message_status": "FAILED",
        },
        "Undefined lookup is retained after teardown cleanup": {
            "scenario_status": "undefined",
            "step_status": "undefined",
            "exception_type": "StepDefinitionNotFoundError",
            "exception_message": "Step definition is not found",
            "message_status": "UNDEFINED",
        },
        "Skip is retained after teardown cleanup": {
            "scenario_status": "skipped",
            "step_status": "skipped",
            "exception_type": None,
            "exception_message": "runtime skip sentinel",
            "message_status": "SKIPPED",
        },
    }
    assert len(observations) == len(expected), observations
    by_name = {row["scenario_name"]: row for row in observations}
    assert set(by_name) == set(expected), by_name
    for scenario_name, outcome in expected.items():
        row = by_name[scenario_name]
        assert row["scenario_status"] == outcome["scenario_status"], row
        assert row["step_status"] == outcome["step_status"], row
        if outcome["exception_type"] is not None:
            assert row["exception_type"] == outcome["exception_type"], row
        assert outcome["exception_message"] in row["exception_message"], row
        assert row["root_status"] == "inactive", row
        assert row["root_stage"] == "inactive", row
        assert row["root_hook_phase"] == "inactive", row
        assert row["active_feature_binding"] is False, row
        assert row["active_scenario_run"] is False, row
        assert row["last_error_type"], row
        for field in ("run_id", "attempt_id", "test_case_id", "test_case_started_id"):
            assert row[field], (field, row)

    run_ids = {row["run_id"] for row in observations}
    assert len(run_ids) == 1, run_ids
    for field in ("attempt_id", "test_case_id", "test_case_started_id"):
        values = [row[field] for row in observations]
        assert len(set(values)) == len(expected), (field, values)

    pickles = {envelope["pickle"]["id"]: envelope["pickle"] for envelope in envelopes if "pickle" in envelope}
    cases = {envelope["testCase"]["id"]: envelope["testCase"] for envelope in envelopes if "testCase" in envelope}
    starts = {
        envelope["testCaseStarted"]["id"]: envelope["testCaseStarted"]
        for envelope in envelopes
        if "testCaseStarted" in envelope
    }
    finishes = [envelope["testStepFinished"] for envelope in envelopes if "testStepFinished" in envelope]
    case_finishes = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    run_finishes = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
    assert len(pickles) == len(cases) == len(starts) == len(case_finishes) == len(expected), envelopes
    assert len(run_finishes) == 1 and run_finishes[0]["success"] is False, run_finishes
    assert {finish["testCaseStartedId"] for finish in case_finishes} == set(starts), case_finishes

    for scenario_name, outcome in expected.items():
        row = by_name[scenario_name]
        case = cases[row["test_case_id"]]
        pickle = pickles[case["pickleId"]]
        started = starts[row["test_case_started_id"]]
        assert pickle["name"] == scenario_name, (pickle, row)
        assert started["testCaseId"] == case["id"], (started, case)
        pickle_step_ids = {
            step.get("id") for step in pickle.get("steps", []) if isinstance(step, dict) and isinstance(step.get("id"), str)
        }
        case_steps = [
            step
            for step in case["testSteps"]
            if isinstance(step, dict) and step.get("pickleStepId") in pickle_step_ids
        ]
        assert len(case_steps) == 1, case
        case_step_ids = {step["id"] for step in case_steps if isinstance(step.get("id"), str)}
        step_finished = [
            finish
            for finish in finishes
            if finish["testCaseStartedId"] == row["test_case_started_id"]
            and finish.get("testStepId") in case_step_ids
        ]
        assert len(step_finished) == 1, step_finished
        assert step_finished[0]["testStepResult"]["status"] == outcome["message_status"], step_finished


@then(
    re.compile(
        r'consumer runtime artifacts "(?P<messages_path>[^"]+)" and "(?P<json_path>[^"]+)" '
        r"should retain both step and teardown errors"
    )
)
def consumer_tolerant_step_and_teardown_failure_reporting(
    messages_path: str,
    json_path: str,
    consumer: Any,
) -> None:
    problems: list[str] = []
    scenario_name = "The tolerant failure and teardown error are both reported"
    step_names = ["the nonterminal tolerant step fails", "a later step passes"]
    assertion_message = "nonterminal tolerant assertion sentinel"
    teardown_message = "late teardown failure sentinel"

    messages_case = _single_messages_case(messages_path, consumer, len(step_names), problems)
    if messages_case is not None:
        case, _started, _test_steps, step_finishes, envelopes = messages_case
        pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
        if len(pickles) != 1:
            problems.append(f"expected one Messages Pickle, got {len(pickles)}")
        elif pickles[0].get("name") != scenario_name:
            problems.append(f"Messages Pickle name={pickles[0].get('name')!r}, expected {scenario_name!r}")
        if len(pickles) == 1 and case.get("pickleId") != pickles[0].get("id"):
            problems.append("Messages TestCase does not reference its Pickle")

        statuses = [finish.get("testStepResult", {}).get("status") for finish in step_finishes]
        if statuses != ["FAILED", "FAILED"]:
            problems.append(f"Messages test step statuses={statuses!r}, expected ['FAILED', 'FAILED']")
        if len(step_finishes) == len(step_names):
            first_result = step_finishes[0].get("testStepResult", {})
            first_exception = first_result.get("exception", {})
            if assertion_message not in str(first_exception.get("message")):
                problems.append(
                    f"tolerant Messages exception={first_exception!r}, expected to contain {assertion_message!r}"
                )
            terminal_result = step_finishes[-1].get("testStepResult", {})
            terminal_exception = terminal_result.get("exception", {})
            if teardown_message not in str(terminal_result.get("message")):
                problems.append(
                    f"terminal Messages message={terminal_result.get('message')!r}, "
                    f"expected to contain {teardown_message!r}"
                )
            if teardown_message not in str(terminal_exception.get("message")):
                problems.append(
                    f"terminal Messages exception={terminal_exception!r}, expected to contain {teardown_message!r}"
                )
        run_finishes = [envelope["testRunFinished"] for envelope in envelopes if "testRunFinished" in envelope]
        if len(run_finishes) != 1 or run_finishes[0].get("success") is not False:
            problems.append(f"Messages TestRunFinished should report failure, got {run_finishes!r}")

    json_steps = _single_json_scenario_steps(
        json_path,
        consumer,
        "tolerant-teardown-runtime.feature",
        scenario_name,
        problems,
    )
    if json_steps is not None:
        names = [step.get("name") for step in json_steps]
        statuses = [step.get("result", {}).get("status") for step in json_steps]
        if names != step_names:
            problems.append(f"JSON scenario steps={names!r}, expected {step_names!r}")
        if statuses != ["failed", "failed"]:
            problems.append(f"JSON step statuses={statuses!r}, expected ['failed', 'failed']")
        if len(json_steps) == len(step_names):
            first_error = json_steps[0].get("result", {}).get("error_message")
            if assertion_message not in str(first_error):
                problems.append(f"tolerant JSON error={first_error!r}, expected to contain {assertion_message!r}")
            terminal_error = json_steps[-1].get("result", {}).get("error_message")
            if teardown_message not in str(terminal_error):
                problems.append(f"terminal JSON error={terminal_error!r}, expected to contain {teardown_message!r}")

    assert not problems, "tolerant step and teardown failure reporting contract failed:\n- " + "\n- ".join(problems)


@then(
    re.compile(
        r'consumer runtime artifacts "(?P<runtime_path>[^"]+)", "(?P<messages_path>[^"]+)" and '
        r'"(?P<json_path>[^"]+)" should agree on Rule Background step links'
    )
)
def consumer_rule_background_runtime_links(
    runtime_path: str,
    messages_path: str,
    json_path: str,
    consumer: Any,
) -> None:
    observations = _runtime_jsonl(runtime_path, consumer)
    envelopes = _messages_envelopes(messages_path, consumer)
    report = json.loads(_runtime_artifact_path(json_path, consumer).read_text(encoding="utf-8"))
    assert len(observations) == 2, observations

    pickles = {envelope["pickle"]["id"]: envelope["pickle"] for envelope in envelopes if "pickle" in envelope}
    cases = {envelope["testCase"]["id"]: envelope["testCase"] for envelope in envelopes if "testCase" in envelope}
    starts = {
        envelope["testCaseStarted"]["id"]: envelope["testCaseStarted"]
        for envelope in envelopes
        if "testCaseStarted" in envelope
    }
    finishes = [envelope["testStepFinished"] for envelope in envelopes if "testStepFinished" in envelope]
    assert len(pickles) == len(cases) == len(starts) == 2, (pickles, cases, starts)
    assert len({row["feature_uri"] for row in observations}) == 1, observations
    assert len({row["test_case_started_id"] for row in observations}) == 2, observations
    assert len(finishes) == 12, finishes
    assert all(finish["testStepResult"]["status"] == "PASSED" for finish in finishes), finishes

    report_elements = [element for feature in report for element in feature["elements"]]
    assert len(report_elements) == 2, report_elements
    assert all(
        all(step["result"]["status"].lower() == "passed" for step in element["steps"]) for element in report_elements
    ), report_elements

    for observation in observations:
        case = cases[observation["test_case_id"]]
        pickle = pickles[case["pickleId"]]
        started = starts[observation["test_case_started_id"]]
        assert started["testCaseId"] == case["id"], (started, case)
        assert len(observation["steps"]) == len(case["testSteps"]) == len(pickle["steps"]) == 6
        assert [step["text"] for step in observation["steps"]] == [step["text"] for step in pickle["steps"]]
        assert [step["test_step_id"] for step in observation["steps"]] == [step["id"] for step in case["testSteps"]]
        assert all(step["status"] == "passed" and step["test_step_id"] for step in observation["steps"])
        assert [step["astNodeIds"] for step in pickle["steps"]] == [
            [step["source_step_id"]] for step in observation["steps"]
        ]
        step_finish_ids = {
            finish["testStepId"]
            for finish in finishes
            if finish["testCaseStartedId"] == observation["test_case_started_id"]
        }
        assert step_finish_ids == {step["test_step_id"] for step in observation["steps"]}
        action = observation["steps"][2]["text"]
        json_rows = [element for element in report_elements if any(step["name"] == action for step in element["steps"])]
        assert len(json_rows) == 1, (action, report_elements)
        assert [step["name"] for step in json_rows[0]["steps"]] == [step["text"] for step in observation["steps"]]
        assert _normalize_outline_row_suffix(json_rows[0]["name"]) == observation["source_scenario_name"], (
            json_rows[0],
            observation,
        )
        assert observation["scenario_name"] == pickle["name"], (observation, pickle)

        doc_step = next(step for step in observation["steps"] if step["doc_string"] is not None)
        table_step = next(step for step in observation["steps"] if step["data_table"] is not None)
        assert "<amount>" in observation["source_scenario_name"], observation
        assert observation["scenario_name"].startswith(observation["source_scenario_name"]), observation
        assert "<amount>" in doc_step["doc_string"]["source_content"], doc_step
        assert "<amount>" not in doc_step["doc_string"]["content"], doc_step
        assert "<amount>" in table_step["data_table"]["source_rows"][1]["cells"][1]["value"], table_step
        assert "<amount>" not in table_step["data_table"]["rows"][1]["cells"][1]["value"], table_step

    ast_steps: dict[str, dict[str, Any]] = {}

    def collect_ast_steps(value: Any) -> None:
        if isinstance(value, dict):
            if {"id", "keyword", "text", "location"}.issubset(value):
                ast_steps[value["id"]] = value
            for child in value.values():
                collect_ast_steps(child)
        elif isinstance(value, list):
            for child in value:
                collect_ast_steps(child)

    for envelope in envelopes:
        document = envelope.get("gherkinDocument")
        if isinstance(document, dict):
            collect_ast_steps(document.get("feature", {}))
    assert ast_steps, envelopes

    for observation in observations:
        case = cases[observation["test_case_id"]]
        pickle = pickles[case["pickleId"]]
        assert case["pickleId"] == pickle["id"], (case, pickle)
        assert observation["source_ast_node_ids"] == pickle["astNodeIds"], (observation, pickle)
        assert observation["scenario_name"] == pickle["name"], (observation, pickle)
        for runtime_step, pickle_step in zip(observation["steps"], pickle["steps"], strict=True):
            source_step = ast_steps[runtime_step["source_step_id"]]
            assert runtime_step["source_text"] == source_step["text"], (runtime_step, source_step)
            assert runtime_step["source_line"] == source_step["location"]["line"], (runtime_step, source_step)
            assert runtime_step["text"] == pickle_step["text"], (runtime_step, pickle_step)
            if "<amount>" in runtime_step["source_text"] or "<expected>" in runtime_step["source_text"]:
                assert "<amount>" not in runtime_step["text"] and "<expected>" not in runtime_step["text"], (
                    runtime_step,
                    pickle_step,
                )
            assert runtime_step["source_step_id"] in pickle_step["astNodeIds"], (runtime_step, pickle_step)

            source_doc = source_step.get("docString")
            source_table = source_step.get("dataTable")
            pickle_argument = pickle_step.get("argument")
            if runtime_step["doc_string"] is not None:
                runtime_doc = runtime_step["doc_string"]
                assert source_doc is not None and pickle_argument is not None, (runtime_step, source_step, pickle_step)
                assert runtime_doc["source_content"] == source_doc["content"], (runtime_doc, source_doc)
                assert runtime_doc["source_media_type"] == source_doc.get("mediaType"), (runtime_doc, source_doc)
                assert runtime_doc["source_line"] == source_doc["location"]["line"], (runtime_doc, source_doc)
                assert runtime_doc["content"] == pickle_argument["docString"]["content"], (
                    runtime_doc,
                    pickle_argument,
                )
                assert runtime_doc["media_type"] == pickle_argument["docString"].get("mediaType"), (
                    runtime_doc,
                    pickle_argument,
                )
            if runtime_step["data_table"] is not None:
                runtime_table = runtime_step["data_table"]
                assert source_table is not None and pickle_argument is not None, (
                    runtime_step,
                    source_step,
                    pickle_step,
                )
                source_rows = source_table["rows"]
                assert [row["line"] for row in runtime_table["source_rows"]] == [
                    row["location"]["line"] for row in source_rows
                ], (runtime_table, source_table)
                assert runtime_table["source_line"] == source_table["location"]["line"], (
                    runtime_table,
                    source_table,
                )
                assert [[cell["value"] for cell in row["cells"]] for row in runtime_table["source_rows"]] == [
                    [cell["value"] for cell in row["cells"]] for row in source_rows
                ], (runtime_table, source_table)
                assert [[cell["line"] for cell in row["cells"]] for row in runtime_table["source_rows"]] == [
                    [cell["location"]["line"] for cell in row["cells"]] for row in source_rows
                ], (runtime_table, source_table)
                assert [[cell["value"] for cell in row["cells"]] for row in runtime_table["rows"]] == [
                    [cell["value"] for cell in row["cells"]] for row in pickle_argument["dataTable"]["rows"]
                ], (runtime_table, pickle_argument)


@then(
    re.compile(
        r'consumer runtime artifacts "(?P<runtime_path>[^"]+)", "(?P<first_messages>[^"]+)" and '
        r'"(?P<second_messages>[^"]+)" should have independent run and scenario IDs'
    )
)
def consumer_repeated_session_runtime_roots(
    runtime_path: str,
    first_messages: str,
    second_messages: str,
    consumer: Any,
) -> None:
    observations = _runtime_jsonl(runtime_path, consumer)
    assert len(observations) == 2, observations
    assert len({row["run_id"] for row in observations}) == 2, observations
    for field in ("attempt_id", "test_case_id", "test_case_started_id"):
        values = [row[field] for row in observations]
        assert all(values) and len(set(values)) == 2, (field, values)

    for relative_path, observation in zip((first_messages, second_messages), observations, strict=True):
        envelopes = _messages_envelopes(relative_path, consumer)
        starts = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
        cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
        assert len(starts) == len(cases) == 1, (relative_path, starts, cases)
        assert starts[0]["id"] == observation["test_case_started_id"], (starts, observation)
        assert cases[0]["id"] == observation["test_case_id"], (cases, observation)
        assert starts[0]["testCaseId"] == cases[0]["id"], (starts, cases)


@then(re.compile(r'consumer xdist runtime artifacts should show separate run roots in "(?P<messages_path>[^"]+)"'))
def consumer_xdist_runtime_roots(messages_path: str, consumer: Any) -> None:
    artifact_root = _runtime_artifact_path(".", consumer)
    worker_artifacts = sorted(artifact_root.glob("runtime-gw*.jsonl"))
    assert len(worker_artifacts) == 2, worker_artifacts
    observations = [
        json.loads(line)
        for artifact in worker_artifacts
        for line in artifact.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(observations) == 2, observations
    assert {row["worker"] for row in observations} == {"gw0", "gw1"}, observations
    assert len({row["run_id"] for row in observations}) == 2, observations
    for field in ("attempt_id", "test_case_id", "test_case_started_id", "nodeid"):
        values = [row[field] for row in observations]
        assert all(values) and len(set(values)) == 2, (field, values)

    envelopes = _messages_envelopes(messages_path, consumer)
    started = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    assert len(started) == len(cases) == len(observations), (started, cases)
    expected_started = {
        (row["worker"], f"{row['worker']}:{row['test_case_started_id']}")
        for row in observations
    }
    actual_started = {(attempt.get("workerId"), attempt.get("id")) for attempt in started}
    assert actual_started == expected_started, (actual_started, expected_started)
    expected_case_ids = {f"{row['worker']}:{row['test_case_id']}" for row in observations}
    case_ids = {case.get("id") for case in cases}
    assert case_ids == expected_case_ids, (case_ids, expected_case_ids)

    started_by_worker = {attempt["workerId"]: attempt for attempt in started}
    assert len(started_by_worker) == len(started), started
    for row in observations:
        worker = row["worker"]
        attempt = started_by_worker[worker]
        assert attempt["id"] == f"{worker}:{row['attempt_id']}", (attempt, row)
        assert attempt["testCaseId"] == f"{worker}:{row['test_case_id']}", (attempt, row)


@then(
    re.compile(
        r'consumer runtime artifacts "(?P<runtime_path>[^"]+)", "(?P<plain_path>[^"]+)", '
        r'"(?P<messages_path>[^"]+)" and "(?P<json_path>[^"]+)" should exclude plain pytest from BDD reporting'
    )
)
def consumer_plain_reporting_does_not_reuse_bdd_identity(
    runtime_path: str,
    plain_path: str,
    messages_path: str,
    json_path: str,
    consumer: Any,
) -> None:
    observations = _runtime_jsonl(runtime_path, consumer)
    by_kind = {row["kind"]: row for row in observations}
    assert len(observations) == 1 and set(by_kind) == {"bdd"}, observations
    bdd = by_kind["bdd"]
    plain = json.loads(_runtime_artifact_path(plain_path, consumer).read_text(encoding="utf-8"))
    assert plain["run_context_identity"] == bdd["run_context_identity"], (bdd, plain)
    assert plain["run_id"] == bdd["run_id"], (bdd, plain)
    assert plain["run_status"] == plain["run_stage"] == plain["run_hook_phase"] == "inactive", plain
    assert plain["active_feature_binding"] is False, plain
    assert plain["active_scenario_run"] is False, plain
    assert plain["scenario_count"] == 1, plain
    assert plain["prior_nodeid"] == bdd["nodeid"], (bdd, plain)

    envelopes = _messages_envelopes(messages_path, consumer)
    pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    starts = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    finishes = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    assert len(pickles) == len(cases) == len(starts) == len(finishes) == 1, envelopes
    assert pickles[0]["name"] == bdd["scenario_name"], (pickles, bdd)
    assert cases[0]["id"] == bdd["test_case_id"], (cases, bdd)
    assert cases[0]["pickleId"] == pickles[0]["id"], (cases, pickles)
    assert starts[0]["id"] == bdd["test_case_started_id"], (starts, bdd)
    assert starts[0]["testCaseId"] == cases[0]["id"], (starts, cases)
    assert finishes[0]["testCaseStartedId"] == starts[0]["id"], (finishes, starts)
    finished_steps = [envelope["testStepFinished"] for envelope in envelopes if "testStepFinished" in envelope]
    assert {finish["testStepId"] for finish in finished_steps} == set(bdd["test_step_ids"]), (
        finished_steps,
        bdd,
    )
    assert all(finish["testCaseStartedId"] == starts[0]["id"] for finish in finished_steps), finished_steps

    report = json.loads(_runtime_artifact_path(json_path, consumer).read_text(encoding="utf-8"))
    report_elements = [element for feature in report for element in feature.get("elements", [])]
    assert len(report_elements) == 1, report_elements
    assert report_elements[0]["name"] == bdd["scenario_name"], (report_elements, bdd)
    assert all(step["result"]["status"].lower() == "passed" for step in report_elements[0]["steps"]), (report_elements,)


def _uri_basename(uri: str) -> str:
    return Path(uri.removeprefix("file:").replace("\\", "/")).name


@then(
    re.compile(
        r'consumer runtime artifacts "(?P<runtime_path>[^"]+)", "(?P<messages_path>[^"]+)" and '
        r'"(?P<json_path>[^"]+)" should keep source bindings and report identities separate'
    )
)
def consumer_distinct_source_identities(
    runtime_path: str,
    messages_path: str,
    json_path: str,
    consumer: Any,
) -> None:
    observations = _runtime_jsonl(runtime_path, consumer)
    assert len(observations) == 2, observations
    for field in (
        "feature_uri",
        "binding_identity",
        "registered_binding_identity",
        "test_case_id",
        "test_case_started_id",
    ):
        values = [row[field] for row in observations]
        assert all(values) and len(set(values)) == 2, (field, values)
    assert len({row["run_id"] for row in observations}) == 1, observations
    scenario_ast_identities = {(row["feature_uri"], row["source_scenario_id"]) for row in observations}
    assert len(scenario_ast_identities) == 2, scenario_ast_identities
    assert {row["scenario_name"] for row in observations} == {"The same scenario name executes"}, observations
    assert all(row["binding_identity"] == row["registered_binding_identity"] for row in observations), observations
    assert all(row["source_scenario_id"] == row["resolved_source_scenario_id"] for row in observations), observations
    source_step_ids = {(row["feature_uri"], row["steps"][0]["source_step_id"]) for row in observations}
    test_step_ids = [row["steps"][0]["test_step_id"] for row in observations]
    assert len(source_step_ids) == 2, source_step_ids
    assert all(test_step_ids) and len(set(test_step_ids)) == 2, test_step_ids
    assert all(len(row["steps"]) == 1 and row["steps"][0]["status"] == "passed" for row in observations), (
        observations,
    )
    assert {row["steps"][0]["name"] for row in observations} == {"the same source step name executes"}, observations

    envelopes = _messages_envelopes(messages_path, consumer)
    pickle_messages = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
    case_messages = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
    start_messages = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
    assert len(pickle_messages) == len(case_messages) == len(start_messages) == 2, envelopes
    assert len({pickle["id"] for pickle in pickle_messages}) == 2, pickle_messages
    assert len({case["id"] for case in case_messages}) == 2, case_messages
    assert len({case["pickleId"] for case in case_messages}) == 2, case_messages
    assert len({started["id"] for started in start_messages}) == 2, start_messages
    pickles = {pickle["id"]: pickle for pickle in pickle_messages}
    cases = {case["id"]: case for case in case_messages}
    starts = {started["id"]: started for started in start_messages}
    finishes = [envelope["testStepFinished"] for envelope in envelopes if "testStepFinished" in envelope]
    case_finishes = [envelope["testCaseFinished"] for envelope in envelopes if "testCaseFinished" in envelope]
    assert len(pickles) == len(cases) == len(starts) == len(case_finishes) == 2, envelopes
    assert len({pickle["uri"] for pickle in pickles.values()}) == 2, pickles
    assert len({finish["testStepId"] for finish in finishes}) == 2, finishes
    pickle_step_ids = [pickle_step["id"] for pickle in pickles.values() for pickle_step in pickle["steps"]]
    assert len(pickle_step_ids) == 2 and len(set(pickle_step_ids)) == 2, pickle_step_ids
    test_step_ids_from_cases = [test_step["id"] for case in cases.values() for test_step in case["testSteps"]]
    assert len(test_step_ids_from_cases) == 2 and len(set(test_step_ids_from_cases)) == 2, test_step_ids_from_cases

    documents = [
        envelope["gherkinDocument"]
        for envelope in envelopes
        if "gherkinDocument" in envelope and envelope["gherkinDocument"].get("feature") is not None
    ]
    assert len(documents) == 2, documents
    document_ids_by_uri: dict[str, set[str]] = {}

    def collect_ids(value: Any, ids: set[str]) -> None:
        if isinstance(value, dict):
            identifier = value.get("id")
            if isinstance(identifier, str):
                ids.add(identifier)
            for child in value.values():
                collect_ids(child, ids)
        elif isinstance(value, list):
            for child in value:
                collect_ids(child, ids)

    for document in documents:
        ids: set[str] = set()
        collect_ids(document.get("feature", {}), ids)
        document_ids_by_uri[_source_uri_identity(document["uri"])] = ids
    assert len(document_ids_by_uri) == 2, document_ids_by_uri

    for row in observations:
        case = cases[row["test_case_id"]]
        pickle = pickles[case["pickleId"]]
        started = starts[row["test_case_started_id"]]
        step = row["steps"][0]
        assert _source_uri_identity(pickle["uri"]) == _source_uri_identity(row["feature_uri"]), (pickle, row)
        assert pickle["name"] == row["scenario_name"], (pickle, row)
        assert row["source_scenario_id"] in pickle["astNodeIds"], (pickle, row)
        source_ids = document_ids_by_uri[_source_uri_identity(row["feature_uri"])]
        assert row["source_scenario_id"] in source_ids, (source_ids, row)
        assert step["source_step_id"] in source_ids, (source_ids, step)
        assert len(pickle["steps"]) == len(case["testSteps"]) == 1, (pickle, case)
        assert [test_step["pickleStepId"] for test_step in case["testSteps"]] == [
            pickle_step["id"] for pickle_step in pickle["steps"]
        ], (case, pickle)
        assert pickle["steps"][0]["astNodeIds"] == [step["source_step_id"]], (pickle, step)
        assert case["pickleId"] == pickle["id"], (case, pickle)
        assert [test_step["id"] for test_step in case["testSteps"]] == [step["test_step_id"]], (case, step)
        assert started["testCaseId"] == case["id"], (started, case)
        assert any(
            finish["testCaseStartedId"] == started["id"]
            and finish["testStepId"] == step["test_step_id"]
            and finish["testStepResult"]["status"] == "PASSED"
            for finish in finishes
        ), (finishes, started, step)
        assert any(finish["testCaseStartedId"] == started["id"] for finish in case_finishes), (case_finishes, started)

    report = json.loads(_runtime_artifact_path(json_path, consumer).read_text(encoding="utf-8"))
    assert len(report) == 2, report
    assert len({feature["uri"] for feature in report}) == 2, report
    report_by_uri = {feature["uri"]: feature for feature in report}
    report_by_uri_identity = {_source_uri_identity(feature["uri"]): feature for feature in report}
    observation_uri_identities = {_source_uri_identity(row["feature_uri"]) for row in observations}
    assert set(report_by_uri_identity) == observation_uri_identities, (
        report_by_uri,
        observations,
    )
    for row in observations:
        feature = report_by_uri_identity[_source_uri_identity(row["feature_uri"])]
        assert len(feature["elements"]) == 1, feature
        element = feature["elements"][0]
        assert element["name"] == row["scenario_name"], (element, row)
        assert len(element["steps"]) == 1, element
        assert element["steps"][0]["name"] == row["steps"][0]["name"], (element, row)
        assert element["steps"][0]["result"]["status"].lower() == "passed", element


@then(
    re.compile(
        r"the interrupted consumer should exit with code (?P<exit_code>\d+), retain runtime artifacts "
        r'"(?P<after_path>[^"]+)" and "(?P<history_path>[^"]+)", and report an UNKNOWN Messages step in '
        r'"(?P<messages_path>[^"]+)" and an UNKNOWN JSON result in "(?P<json_path>[^"]+)"'
    )
)
def consumer_interrupted_runtime_is_retained(
    exit_code: str,
    after_path: str,
    history_path: str,
    messages_path: str,
    json_path: str,
    consumer: Any,
) -> None:
    problems: list[str] = []
    result = getattr(consumer, "pytest_result", None)
    if result is None:
        problems.append("pytest did not run")
    elif result.returncode != int(exit_code):
        problems.append(
            f"pytest returned {result.returncode}, expected {exit_code}; stdout={result.stdout!r}; stderr={result.stderr!r}"
        )

    snapshots: dict[str, dict[str, Any]] = {}
    for label, relative_path in (("after-scenario", after_path), ("session-finish history", history_path)):
        try:
            snapshots[label] = json.loads(_runtime_artifact_path(relative_path, consumer).read_text(encoding="utf-8"))
        except FileNotFoundError:
            problems.append(f"{label} artifact {relative_path!r} was not produced")

    after = snapshots.get("after-scenario")
    if after is not None:
        for field, expected in (
            ("scenario_status", "interrupted"),
            ("exception_type", "KeyboardInterrupt"),
            ("exception_message", "runtime interrupt sentinel"),
            ("active_scenario_run", True),
        ):
            if after.get(field) != expected:
                problems.append(f"after-scenario {field}={after.get(field)!r}, expected {expected!r}")

        try:
            envelopes = _messages_envelopes(messages_path, consumer)
        except AssertionError as exc:
            problems.append(f"Messages artifact {messages_path!r} could not be read: {exc}")
        else:
            cases = [envelope["testCase"] for envelope in envelopes if "testCase" in envelope]
            starts = [envelope["testCaseStarted"] for envelope in envelopes if "testCaseStarted" in envelope]
            if len(cases) != 1:
                problems.append(f"expected one Messages TestCase, got {len(cases)}")
            if len(starts) != 1:
                problems.append(f"expected one Messages TestCaseStarted, got {len(starts)}")
            if len(cases) == 1 and len(starts) == 1:
                case = cases[0]
                started = starts[0]
                if case.get("id") != after.get("test_case_id"):
                    problems.append(
                        f"Messages TestCase id={case.get('id')!r}, expected runtime id={after.get('test_case_id')!r}"
                    )
                if started.get("id") != after.get("test_case_started_id"):
                    problems.append(
                        "Messages TestCaseStarted id="
                        f"{started.get('id')!r}, expected runtime id={after.get('test_case_started_id')!r}"
                    )
                if started.get("testCaseId") != case.get("id"):
                    problems.append("Messages TestCaseStarted does not reference the runtime TestCase")
                runtime_step_ids = after.get("test_step_ids")
                case_step_ids = [step.get("id") for step in case.get("testSteps", [])]
                if not runtime_step_ids or case_step_ids != runtime_step_ids:
                    problems.append(
                        f"Messages TestCase step IDs={case_step_ids!r}, expected runtime IDs={runtime_step_ids!r}"
                    )
                all_finished_steps = [
                    envelope["testStepFinished"]
                    for envelope in envelopes
                    if "testStepFinished" in envelope
                    and envelope["testStepFinished"].get("testCaseStartedId") == started.get("id")
                ]
                scenario_test_steps, finished_steps, hook_statuses = _split_messages_steps(
                    case.get("testSteps", []), all_finished_steps
                )
                if hook_statuses != ["passed", "passed"]:
                    problems.append(
                        f"Messages Before/After hook statuses={hook_statuses!r}, expected ['passed', 'passed']"
                    )
                if len(scenario_test_steps) != 1 or len(finished_steps) != 1:
                    problems.append(
                        "expected one finished scenario Messages step for the interrupted attempt, "
                        f"got {len(finished_steps)} scenario steps"
                    )
                else:
                    finished_step = finished_steps[0]
                    if finished_step.get("testStepId") != scenario_test_steps[0].get("id"):
                        problems.append(
                            "Messages interrupted TestStep does not reference the scenario step: "
                            f"{finished_step.get('testStepId')!r}"
                        )
                    wire_result = finished_step.get("testStepResult", {})
                    step_status = wire_result.get("status")
                    if step_status != "UNKNOWN":
                        problems.append(f"Messages interrupted TestStep status={step_status!r}, expected 'UNKNOWN'")
                    if wire_result.get("message") != "runtime interrupt sentinel":
                        problems.append(
                            "Messages interrupted TestStep message="
                            f"{wire_result.get('message')!r}, expected 'runtime interrupt sentinel'"
                        )
                    exception_message = wire_result.get("exception", {}).get("message")
                    if exception_message != "runtime interrupt sentinel":
                        problems.append(
                            "Messages interrupted TestStep exception message="
                            f"{exception_message!r}, expected 'runtime interrupt sentinel'"
                        )

    history = snapshots.get("session-finish history")
    if history is not None:
        for field, expected in (
            ("scenario_history_found", True),
            ("scenario_status", "interrupted"),
            ("exception_type", "KeyboardInterrupt"),
            ("exception_message", "runtime interrupt sentinel"),
            ("active_feature_binding", False),
            ("active_scenario_run", False),
            ("active_step", False),
            ("exit_status", int(exit_code)),
        ):
            if history.get(field) != expected:
                problems.append(f"session-finish history {field}={history.get(field)!r}, expected {expected!r}")

    try:
        report = json.loads(_runtime_artifact_path(json_path, consumer).read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append(f"JSON report {json_path!r} was not produced")
    else:
        features = [
            feature for feature in report if _uri_basename(feature.get("uri", "")) == "interrupted-runtime.feature"
        ]
        if len(features) != 1:
            problems.append(f"expected one interrupted feature in JSON report, got {len(features)}")
        else:
            scenarios = [
                element
                for element in features[0].get("elements", [])
                if element.get("name") == "KeyboardInterrupt leaves an interrupted runtime outcome"
            ]
            if len(scenarios) != 1:
                problems.append(f"expected one interrupted scenario in JSON report, got {len(scenarios)}")
            else:
                report_steps = scenarios[0].get("steps", [])
                steps, hook_statuses = _split_json_report_steps(report_steps)
                if hook_statuses != [("Before", "passed"), ("After", "passed")]:
                    problems.append(
                        "JSON Before/After hook statuses="
                        f"{hook_statuses!r}, expected [('Before', 'passed'), ('After', 'passed')]"
                    )
                if any(step.get("result", {}).get("error_message") is not None for step in _json_hook_steps(report_steps)):
                    problems.append("JSON Before/After hooks should omit error_message when they pass")
                if len(steps) != 1:
                    problems.append(f"expected one interrupted scenario step in JSON report, got {len(steps)}")
                else:
                    json_result = steps[0].get("result", {})
                    json_status = json_result.get("status")
                    if json_status != "unknown":
                        problems.append(f"JSON interrupted step status={json_status!r}, expected 'unknown'")
                    if json_result.get("error_message") is not None:
                        problems.append(
                            "JSON interrupted scenario step should omit error_message, got "
                            f"{json_result.get('error_message')!r}"
                        )

    assert not problems, "interrupted runtime contract failed:\n- " + "\n- ".join(problems)


@then(
    re.compile(
        r'consumer runtime artifacts "(?P<after_path>[^"]+)", "(?P<runtime_path>[^"]+)", '
        r'"(?P<messages_path>[^"]+)" and "(?P<json_path>[^"]+)" should retain the teardown interruption'
    )
)
def consumer_teardown_interrupt_is_retained(
    after_path: str,
    runtime_path: str,
    messages_path: str,
    json_path: str,
    consumer: Any,
) -> None:
    problems: list[str] = []
    result = getattr(consumer, "pytest_result", None)
    if result is None:
        problems.append("pytest did not run")
    elif result.returncode != 2:
        problems.append(
            f"pytest returned {result.returncode}, expected 2; stdout={result.stdout!r}; stderr={result.stderr!r}"
        )

    snapshots: dict[str, dict[str, Any]] = {}
    for label, relative_path in (("after-scenario", after_path), ("teardown runtime", runtime_path)):
        try:
            snapshots[label] = json.loads(_runtime_artifact_path(relative_path, consumer).read_text(encoding="utf-8"))
        except FileNotFoundError:
            problems.append(f"{label} artifact {relative_path!r} was not produced")

    after = snapshots.get("after-scenario")
    runtime = snapshots.get("teardown runtime")
    expected_scenario_name = "Fixture teardown interrupts a completed multi-step scenario"
    expected_step_names = [
        "the scenario arms a KeyboardInterrupt during fixture teardown",
        "the first runtime action completes",
        "the terminal runtime action completes before pytest teardown",
    ]
    expected_test_step_count = len(expected_step_names) + 2  # Cucumber Messages includes before/after hook steps.
    if after is not None:
        if after.get("scenario_name") != expected_scenario_name:
            problems.append(
                f"after-scenario scenario_name={after.get('scenario_name')!r}, expected {expected_scenario_name!r}"
            )
        step_ids = after.get("test_step_ids")
        if not isinstance(step_ids, list) or len(step_ids) != expected_test_step_count or not all(step_ids):
            problems.append(
                f"after-scenario test_step_ids={step_ids!r}, expected three scenario steps plus two hook steps"
            )

    if runtime is not None:
        for field, expected in (
            ("scenario_status", "interrupted"),
            ("exception_type", "KeyboardInterrupt"),
            ("exception_message", "teardown interrupt sentinel"),
            ("runtime_status", "inactive"),
            ("runtime_stage", "inactive"),
            ("active_feature_binding", False),
            ("active_scenario_run", False),
            ("exit_status", 2),
        ):
            if runtime.get(field) != expected:
                problems.append(f"teardown runtime {field}={runtime.get(field)!r}, expected {expected!r}")
        if len(runtime.get("test_step_ids", [])) != expected_test_step_count:
            problems.append(
                f"teardown runtime test_step_ids={runtime.get('test_step_ids')!r}, "
                "expected three scenario steps plus two hook steps"
            )
        if len(runtime.get("step_statuses", [])) != len(expected_step_names):
            problems.append(f"teardown runtime step_statuses={runtime.get('step_statuses')!r}, expected three steps")
        if after is not None:
            for field in ("test_case_id", "test_case_started_id", "test_step_ids"):
                if runtime.get(field) != after.get(field):
                    problems.append(
                        f"teardown runtime {field}={runtime.get(field)!r}, after-scenario has {after.get(field)!r}"
                    )

    messages_case = _single_messages_case(messages_path, consumer, expected_test_step_count, problems)
    if messages_case is not None:
        case, started, test_steps, step_finishes, _envelopes = messages_case
        if [step.get("id") for step in test_steps] != (after or {}).get("test_step_ids"):
            problems.append(
                f"Messages TestCase step IDs={[step.get('id') for step in test_steps]!r}, "
                f"after-scenario IDs={(after or {}).get('test_step_ids')!r}"
            )
        if runtime is not None and case.get("id") != runtime.get("test_case_id"):
            problems.append(f"Messages TestCase id={case.get('id')!r}, runtime id={runtime.get('test_case_id')!r}")
        if runtime is not None and started.get("id") != runtime.get("test_case_started_id"):
            problems.append(
                f"Messages TestCaseStarted id={started.get('id')!r}, runtime id={runtime.get('test_case_started_id')!r}"
            )
        if len(step_finishes) == expected_test_step_count:
            terminal_result = step_finishes[-1].get("testStepResult", {})
            if terminal_result.get("status") != "UNKNOWN":
                problems.append(
                    f"terminal Messages test step status={terminal_result.get('status')!r}, expected 'UNKNOWN'"
                )
            if terminal_result.get("message") != "teardown interrupt sentinel":
                problems.append(
                    f"terminal Messages message={terminal_result.get('message')!r}, expected 'teardown interrupt sentinel'"
                )
            if terminal_result.get("exception", {}).get("message") != "teardown interrupt sentinel":
                problems.append(
                    "terminal Messages exception.message="
                    f"{terminal_result.get('exception', {}).get('message')!r}, expected 'teardown interrupt sentinel'"
                )

    json_steps = _single_json_scenario_steps(
        json_path,
        consumer,
        "teardown-interrupted-runtime.feature",
        expected_scenario_name,
        problems,
    )
    if json_steps is not None:
        if len(json_steps) != expected_test_step_count:
            problems.append(
                f"JSON scenario has {len(json_steps)} report steps, expected three scenario steps plus two hooks"
            )
        else:
            before_hook, *scenario_steps, after_hook = json_steps
            if before_hook.get("keyword") != "Before" or before_hook.get("hidden") is not True:
                problems.append(f"first JSON report step should be a hidden Before hook: {before_hook!r}")
            if after_hook.get("keyword") != "After" or after_hook.get("hidden") is not True:
                problems.append(f"last JSON report step should be a hidden After hook: {after_hook!r}")
            if [step.get("name") for step in scenario_steps] != expected_step_names:
                problems.append(
                    f"JSON scenario steps={[step.get('name') for step in scenario_steps]!r}, "
                    f"expected {expected_step_names!r}"
                )
            terminal_result = after_hook.get("result", {})
            if terminal_result.get("status") != "unknown":
                problems.append(
                    f"terminal JSON after hook status={terminal_result.get('status')!r}, expected 'unknown'"
                )

    assert not problems, "teardown interruption reporting contract failed:\n- " + "\n- ".join(problems)


@then(
    re.compile(
        r'consumer artifacts "(?P<skip_path>[^"]+)", "(?P<messages_path>[^"]+)" and "(?P<json_path>[^"]+)" '
        r"should report the teardown interruption over the skipped terminal step"
    )
)
def consumer_teardown_interrupt_overrides_terminal_skip(
    skip_path: str,
    messages_path: str,
    json_path: str,
    consumer: Any,
) -> None:
    problems: list[str] = []
    result = getattr(consumer, "pytest_result", None)
    if result is None:
        problems.append("pytest did not run")
    elif result.returncode != 2:
        problems.append(
            f"pytest returned {result.returncode}, expected 2; stdout={result.stdout!r}; stderr={result.stderr!r}"
        )

    expected_scenario_name = "Fixture teardown interrupts after its terminal step skips"
    expected_step_names = [
        "the scenario arms teardown interruption after its terminal step",
        "the preliminary scenario action completes",
        "the terminal scenario step is skipped",
    ]
    expected_message = "teardown after skipped-step sentinel"

    try:
        skip_snapshot = json.loads(_runtime_artifact_path(skip_path, consumer).read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append(f"pre-teardown skip snapshot {skip_path!r} was not produced")
    else:
        for field, expected in (
            ("scenario_status", "skipped"),
            ("terminal_step_status", "skipped"),
            ("exception_message", "terminal scenario step skip sentinel"),
        ):
            if skip_snapshot.get(field) != expected:
                problems.append(
                    f"pre-teardown skip snapshot {field}={skip_snapshot.get(field)!r}, expected {expected!r}"
                )

    expected_test_step_count = len(expected_step_names) + 1
    messages_case = _single_messages_case(messages_path, consumer, expected_test_step_count, problems)
    if messages_case is not None:
        _case, _started, test_steps, step_finishes, _envelopes = messages_case
        scenario_steps, scenario_finishes, hook_statuses = _split_messages_steps(test_steps, step_finishes)
        if hook_statuses != ["unknown"]:
            problems.append(f"Messages After hook statuses={hook_statuses!r}, expected ['unknown']")
        scenario_statuses = [finish.get("testStepResult", {}).get("status") for finish in scenario_finishes]
        if scenario_statuses != ["PASSED", "PASSED", "SKIPPED"]:
            problems.append(
                f"Messages scenario step statuses={scenario_statuses!r}, expected ['PASSED', 'PASSED', 'SKIPPED']"
            )
        if len(scenario_steps) == len(expected_step_names):
            skipped_result = scenario_finishes[-1].get("testStepResult", {})
            if skipped_result.get("status") != "SKIPPED":
                problems.append(
                    f"terminal Messages scenario step status={skipped_result.get('status')!r}, expected 'SKIPPED'"
                )
            if skipped_result.get("message") != "terminal scenario step skip sentinel":
                problems.append(
                    "terminal Messages skipped-step message="
                    f"{skipped_result.get('message')!r}, expected 'terminal scenario step skip sentinel'"
                )
            after_result = _messages_hook_finishes(test_steps, step_finishes)[0].get("testStepResult", {})
            if after_result.get("message") != expected_message:
                problems.append(
                    f"Messages After hook message={after_result.get('message')!r}, expected {expected_message!r}"
                )
            exception = after_result.get("exception")
            exception_message = exception.get("message") if isinstance(exception, dict) else None
            if exception_message != expected_message:
                problems.append(
                    f"Messages After hook exception.message={exception_message!r}, expected {expected_message!r}"
                )

    json_steps = _single_json_scenario_steps(
        json_path,
        consumer,
        "terminal-skip-interrupted-runtime.feature",
        expected_scenario_name,
        problems,
    )
    if json_steps is not None:
        scenario_steps, hook_statuses = _split_json_report_steps(json_steps)
        if hook_statuses != [("After", "unknown")]:
            problems.append(f"JSON After hook statuses={hook_statuses!r}, expected [('After', 'unknown')]")
        step_names = [step.get("name") for step in scenario_steps]
        if step_names != expected_step_names:
            problems.append(f"JSON scenario steps={step_names!r}, expected {expected_step_names!r}")
        scenario_statuses = [step.get("result", {}).get("status") for step in scenario_steps]
        if scenario_statuses != ["passed", "passed", "skipped"]:
            problems.append(
                f"JSON scenario step statuses={scenario_statuses!r}, expected ['passed', 'passed', 'skipped']"
            )
        if len(scenario_steps) == len(expected_step_names):
            skipped_result = scenario_steps[-1].get("result", {})
            if skipped_result.get("status") != "skipped":
                problems.append(f"terminal JSON scenario step status={skipped_result.get('status')!r}, expected 'skipped'")
        after_hooks = _json_hook_steps(json_steps)
        after_hook = after_hooks[0] if after_hooks else {}
        if after_hook.get("result", {}).get("error_message") is not None:
            problems.append(
                "JSON After hook should omit error_message, got "
                f"{after_hook.get('result', {}).get('error_message')!r}"
            )

    assert not problems, "teardown interrupt must override terminal skip:\n- " + "\n- ".join(problems)


@then(
    re.compile(
        r'consumer runtime artifacts "(?P<before_path>[^"]+)", "(?P<runtime_path>[^"]+)", '
        r'"(?P<messages_path>[^"]+)" and "(?P<json_path>[^"]+)" '
        r"should retain both assertion reporting and the teardown error"
    )
)
def consumer_assertion_failure_and_teardown_interrupt_are_retained(
    before_path: str,
    runtime_path: str,
    messages_path: str,
    json_path: str,
    consumer: Any,
) -> None:
    problems: list[str] = []
    result = getattr(consumer, "pytest_result", None)
    if result is None:
        problems.append("pytest did not run")
    elif result.returncode != 2:
        problems.append(
            f"pytest returned {result.returncode}, expected 2; stdout={result.stdout!r}; stderr={result.stderr!r}"
        )

    expected_scenario_name = "Fixture teardown interrupts after a terminal assertion fails"
    expected_step_names = [
        "the scenario arms teardown interruption after its terminal assertion",
        "the preliminary assertion scenario action completes",
        "the terminal runtime assertion fails with its sentinel",
    ]
    assertion_message = "terminal assertion sentinel"
    teardown_message = "teardown after assertion sentinel"

    snapshots: dict[str, dict[str, Any]] = {}
    for label, relative_path in (("before-teardown", before_path), ("teardown runtime", runtime_path)):
        try:
            snapshots[label] = json.loads(_runtime_artifact_path(relative_path, consumer).read_text(encoding="utf-8"))
        except FileNotFoundError:
            problems.append(f"{label} artifact {relative_path!r} was not produced")

    before = snapshots.get("before-teardown")
    if before is not None:
        for field, expected in (
            ("scenario_status", "failed"),
            ("terminal_step_status", "failed"),
            ("terminal_step_exception_type", "AssertionError"),
        ):
            if before.get(field) != expected:
                problems.append(f"before-teardown {field}={before.get(field)!r}, expected {expected!r}")
        if assertion_message not in str(before.get("terminal_step_exception_message")):
            problems.append(
                "before-teardown terminal_step_exception_message="
                f"{before.get('terminal_step_exception_message')!r}, expected to contain {assertion_message!r}"
            )

    runtime = snapshots.get("teardown runtime")
    if runtime is not None:
        for field, expected in (
            ("scenario_status", "interrupted"),
            ("exception_type", "KeyboardInterrupt"),
            ("exception_message", teardown_message),
            ("runtime_status", "inactive"),
            ("runtime_stage", "inactive"),
            ("active_feature_binding", False),
            ("active_scenario_run", False),
            ("exit_status", 2),
        ):
            if runtime.get(field) != expected:
                problems.append(f"teardown runtime {field}={runtime.get(field)!r}, expected {expected!r}")
        expected_test_step_count = len(expected_step_names) + 2
        if len(runtime.get("test_step_ids", [])) != expected_test_step_count:
            problems.append(
                f"teardown runtime test_step_ids={runtime.get('test_step_ids')!r}, "
                "expected three scenario steps plus two hook steps"
            )
        if len(runtime.get("step_statuses", [])) != len(expected_step_names):
            problems.append(f"teardown runtime step_statuses={runtime.get('step_statuses')!r}, expected three steps")

    expected_test_step_count = len(expected_step_names) + 2
    messages_case = _single_messages_case(messages_path, consumer, expected_test_step_count, problems)
    if messages_case is not None:
        _case, _started, test_steps, step_finishes, _envelopes = messages_case
        scenario_steps, scenario_finishes, hook_statuses = _split_messages_steps(test_steps, step_finishes)
        if hook_statuses != ["passed", "unknown"]:
            problems.append(f"Messages Before/After hook statuses={hook_statuses!r}, expected ['passed', 'unknown']")
        if len(scenario_steps) == len(expected_step_names):
            terminal_result = scenario_finishes[-1].get("testStepResult", {})
            if terminal_result.get("status") != "FAILED":
                problems.append(
                    f"terminal Messages test step status={terminal_result.get('status')!r}, expected 'FAILED'"
                )
            if assertion_message not in str(terminal_result.get("message")):
                problems.append(
                    f"terminal Messages test step message={terminal_result.get('message')!r}, "
                    f"expected to contain {assertion_message!r}"
                )
            exception = terminal_result.get("exception")
            exception_message = exception.get("message") if isinstance(exception, dict) else None
            if assertion_message not in str(exception_message):
                problems.append(
                    f"terminal Messages exception.message={exception_message!r}, "
                    f"expected to contain {assertion_message!r}"
                )
        after_result = _messages_hook_finishes(test_steps, step_finishes)[-1].get("testStepResult", {})
        if teardown_message not in str(after_result.get("message")):
            problems.append(
                f"Messages After hook message={after_result.get('message')!r}, "
                f"expected to contain {teardown_message!r}"
            )
        if teardown_message not in str(after_result.get("exception", {}).get("message")):
            problems.append(
                f"Messages After hook exception={after_result.get('exception')!r}, "
                f"expected to contain {teardown_message!r}"
            )

    json_steps = _single_json_scenario_steps(
        json_path,
        consumer,
        "assertion-teardown-interrupted-runtime.feature",
        expected_scenario_name,
        problems,
    )
    if json_steps is not None:
        scenario_steps, hook_statuses = _split_json_report_steps(json_steps)
        if hook_statuses != [("Before", "passed"), ("After", "unknown")]:
            problems.append(
                "JSON Before/After hook statuses="
                f"{hook_statuses!r}, expected [('Before', 'passed'), ('After', 'unknown')]"
            )
        if any(step.get("result", {}).get("error_message") is not None for step in _json_hook_steps(json_steps)):
            problems.append("JSON Before/After hooks should omit error_message when no error is serialized")
        step_names = [step.get("name") for step in scenario_steps]
        if step_names != expected_step_names:
            problems.append(f"JSON scenario steps={step_names!r}, expected {expected_step_names!r}")
        if len(scenario_steps) == len(expected_step_names):
            terminal_result = scenario_steps[-1].get("result", {})
            if terminal_result.get("status") != "failed":
                problems.append(f"terminal JSON step status={terminal_result.get('status')!r}, expected 'failed'")
            if assertion_message not in str(terminal_result.get("error_message")):
                problems.append(
                    f"terminal JSON step error_message={terminal_result.get('error_message')!r}, "
                    f"expected to contain {assertion_message!r}"
                )

    assert not problems, "assertion report and teardown runtime contract failed:\n- " + "\n- ".join(problems)


@then(
    re.compile(
        r'consumer runtime artifacts "(?P<before_path>[^"]+)", "(?P<runtime_path>[^"]+)", '
        r'"(?P<messages_path>[^"]+)" and "(?P<json_path>[^"]+)" '
        r"should preserve skipped and interrupted step outcomes"
    )
)
def consumer_middle_skip_teardown_interrupt_preserves_reporting(
    before_path: str,
    runtime_path: str,
    messages_path: str,
    json_path: str,
    consumer: Any,
) -> None:
    problems: list[str] = []
    result = getattr(consumer, "pytest_result", None)
    if result is None:
        problems.append("pytest did not run")
    elif result.returncode != 2:
        problems.append(
            f"pytest returned {result.returncode}, expected 2; stdout={result.stdout!r}; stderr={result.stderr!r}"
        )

    expected_scenario_name = "Fixture teardown interrupts after the middle scenario step skips"
    expected_step_names = [
        "the scenario arms teardown interruption after its middle step",
        "the first scenario action completes",
        "the middle scenario step is skipped",
        "the final scenario step remains unstarted",
    ]
    expected_statuses = ["passed", "passed", "skipped", "skipped"]
    teardown_message = "teardown after middle skip sentinel"

    snapshots: dict[str, dict[str, Any]] = {}
    for label, relative_path in (("before-teardown", before_path), ("teardown runtime", runtime_path)):
        try:
            snapshots[label] = json.loads(_runtime_artifact_path(relative_path, consumer).read_text(encoding="utf-8"))
        except FileNotFoundError:
            problems.append(f"{label} artifact {relative_path!r} was not produced")

    before = snapshots.get("before-teardown")
    if before is not None:
        for field, expected in (
            ("scenario_status", "skipped"),
            ("scenario_step_count", len(expected_step_names)),
            ("executed_step_names", expected_step_names[:3]),
            ("executed_step_statuses", expected_statuses[:3]),
        ):
            if before.get(field) != expected:
                problems.append(f"before-teardown {field}={before.get(field)!r}, expected {expected!r}")

    runtime = snapshots.get("teardown runtime")
    if runtime is not None:
        for field, expected in (
            ("scenario_status", "interrupted"),
            ("exception_type", "KeyboardInterrupt"),
            ("exception_message", teardown_message),
            ("runtime_status", "inactive"),
            ("active_feature_binding", False),
            ("active_scenario_run", False),
            ("exit_status", 2),
        ):
            if runtime.get(field) != expected:
                problems.append(f"teardown runtime {field}={runtime.get(field)!r}, expected {expected!r}")

    expected_test_step_count = len(expected_step_names) + 2
    messages_case = _single_messages_case(messages_path, consumer, expected_test_step_count, problems)
    if messages_case is not None:
        case, _started, test_steps, step_finishes, envelopes = messages_case
        scenario_steps, scenario_finishes, hook_statuses = _split_messages_steps(test_steps, step_finishes)
        if hook_statuses != ["passed", "unknown"]:
            problems.append(f"Messages Before/After hook statuses={hook_statuses!r}, expected ['passed', 'unknown']")
        pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
        if len(pickles) != 1:
            problems.append(f"expected one Messages Pickle, got {len(pickles)}")
        else:
            pickle = pickles[0]
            pickle_steps = pickle.get("steps", [])
            if pickle.get("name") != expected_scenario_name:
                problems.append(f"Messages Pickle name={pickle.get('name')!r}, expected {expected_scenario_name!r}")
            if [step.get("text") for step in pickle_steps] != expected_step_names:
                problems.append(
                    f"Messages Pickle step texts={[step.get('text') for step in pickle_steps]!r}, "
                    f"expected {expected_step_names!r}"
                )
            if case.get("pickleId") != pickle.get("id"):
                problems.append("Messages TestCase does not reference its Pickle")
            if [step.get("pickleStepId") for step in scenario_steps] != [step.get("id") for step in pickle_steps]:
                problems.append("Messages TestCase step links do not match the Pickle step identities")

        message_statuses = [
            finish.get("testStepResult", {}).get("status", "").lower() for finish in scenario_finishes
        ]
        if message_statuses != expected_statuses:
            problems.append(f"Messages test step statuses={message_statuses!r}, expected {expected_statuses!r}")
        if len(scenario_finishes) == len(expected_step_names):
            terminal_result = scenario_finishes[-1].get("testStepResult", {})
            if terminal_result.get("message") is not None:
                problems.append(
                    f"unstarted Messages scenario step message={terminal_result.get('message')!r}, expected None"
                )
            after_result = _messages_hook_finishes(test_steps, step_finishes)[-1].get("testStepResult", {})
            if after_result.get("status") != "UNKNOWN":
                problems.append(f"Messages After hook status={after_result.get('status')!r}, expected 'UNKNOWN'")
            if teardown_message not in str(after_result.get("message")):
                problems.append(
                    f"Messages After hook message={after_result.get('message')!r}, "
                    f"expected to contain {teardown_message!r}"
                )
            exception = after_result.get("exception")
            exception_message = exception.get("message") if isinstance(exception, dict) else None
            if teardown_message not in str(exception_message):
                problems.append(
                    f"Messages After hook exception.message={exception_message!r}, "
                    f"expected to contain {teardown_message!r}"
                )

    json_steps = _single_json_scenario_steps(
        json_path,
        consumer,
        "middle-skip-interrupted-runtime.feature",
        expected_scenario_name,
        problems,
    )
    if json_steps is not None:
        scenario_json_steps, hook_statuses = _split_json_report_steps(json_steps)
        if hook_statuses != [("Before", "passed"), ("After", "unknown")]:
            problems.append(
                "JSON Before/After hook statuses="
                f"{hook_statuses!r}, expected [('Before', 'passed'), ('After', 'unknown')]"
            )
        json_step_names = [step.get("name") for step in scenario_json_steps]
        if json_step_names != expected_step_names:
            problems.append(f"JSON scenario steps={json_step_names!r}, expected {expected_step_names!r}")
        json_statuses = [step.get("result", {}).get("status") for step in scenario_json_steps]
        if json_statuses != expected_statuses:
            problems.append(f"JSON step statuses={json_statuses!r}, expected {expected_statuses!r}")
        if len(scenario_json_steps) == len(expected_step_names):
            terminal_result = scenario_json_steps[-1].get("result", {})
            if terminal_result.get("error_message") is not None:
                problems.append(
                    f"unstarted JSON scenario step error_message={terminal_result.get('error_message')!r}, "
                    "expected None"
                )
        after_hook = _json_hook_steps(json_steps)[-1]
        if after_hook.get("result", {}).get("error_message") is not None:
            problems.append(
                f"JSON After hook error_message={after_hook.get('result', {}).get('error_message')!r}, expected None"
            )

    assert not problems, "middle-step skip and teardown interruption contract failed:\n- " + "\n- ".join(problems)


@then(
    re.compile(
        r'consumer runtime artifacts "(?P<before_path>[^"]+)", "(?P<runtime_path>[^"]+)", '
        r'"(?P<messages_path>[^"]+)" and "(?P<json_path>[^"]+)" '
        r"should preserve the tolerant failure and interrupt sentinels"
    )
)
def consumer_tolerant_failure_teardown_interrupt_are_retained(
    before_path: str,
    runtime_path: str,
    messages_path: str,
    json_path: str,
    consumer: Any,
) -> None:
    problems: list[str] = []
    result = getattr(consumer, "pytest_result", None)
    if result is None:
        problems.append("pytest did not run")
    elif result.returncode != 2:
        problems.append(
            f"pytest returned {result.returncode}, expected 2; stdout={result.stdout!r}; stderr={result.stderr!r}"
        )

    assertion_message = "tolerant first-step assertion sentinel"
    teardown_message = "teardown after tolerant step sentinel"
    expected_scenario_name = "Tolerant failure stays failed while terminal pass becomes interrupted"
    expected_step_names = [
        "the tolerant first step raises an AssertionError and continues",
        "the terminal scenario step completes successfully",
    ]

    snapshots: dict[str, dict[str, Any]] = {}
    for label, relative_path in (("before-teardown", before_path), ("teardown runtime", runtime_path)):
        try:
            snapshots[label] = json.loads(_runtime_artifact_path(relative_path, consumer).read_text(encoding="utf-8"))
        except FileNotFoundError:
            problems.append(f"{label} artifact {relative_path!r} was not produced")

    before = snapshots.get("before-teardown")
    if before is not None:
        if before.get("scenario_status") != "passed":
            problems.append(f"before-teardown scenario_status={before.get('scenario_status')!r}, expected 'passed'")
        if before.get("step_statuses") != ["failed", "passed"]:
            problems.append(
                f"before-teardown step_statuses={before.get('step_statuses')!r}, expected ['failed', 'passed']"
            )
        first_step_error = before.get("step_exception_messages", [None])[0]
        if assertion_message not in str(first_step_error):
            problems.append(f"before-teardown first-step error={first_step_error!r}, expected {assertion_message!r}")

    runtime = snapshots.get("teardown runtime")
    if runtime is not None:
        for field, expected in (
            ("scenario_status", "interrupted"),
            ("exception_type", "KeyboardInterrupt"),
            ("exception_message", teardown_message),
            ("runtime_status", "inactive"),
            ("active_feature_binding", False),
            ("active_scenario_run", False),
            ("exit_status", 2),
        ):
            if runtime.get(field) != expected:
                problems.append(f"teardown runtime {field}={runtime.get(field)!r}, expected {expected!r}")

    expected_test_step_count = len(expected_step_names) + 2
    messages_case = _single_messages_case(messages_path, consumer, expected_test_step_count, problems)
    if messages_case is not None:
        case, _started, test_steps, step_finishes, _envelopes = messages_case
        _scenario_steps, scenario_finishes, hook_statuses = _split_messages_steps(test_steps, step_finishes)
        if case.get("pickleId") is None:
            problems.append("Messages TestCase is missing its Pickle identity")
        if hook_statuses != ["passed", "unknown"]:
            problems.append(f"Messages Before/After hook statuses={hook_statuses!r}, expected ['passed', 'unknown']")
        statuses = [finish.get("testStepResult", {}).get("status", "").lower() for finish in scenario_finishes]
        if statuses != ["failed", "passed"]:
            problems.append(f"Messages scenario step statuses={statuses!r}, expected ['failed', 'passed']")
        if len(scenario_finishes) == len(expected_step_names):
            first_result = scenario_finishes[0].get("testStepResult", {})
            first_exception = first_result.get("exception")
            first_exception_message = first_exception.get("message") if isinstance(first_exception, dict) else None
            if assertion_message not in str(first_exception_message):
                problems.append(
                    f"tolerant Messages exception.message={first_exception_message!r}, "
                    f"expected to contain {assertion_message!r}"
                )
            if scenario_finishes[-1].get("testStepResult", {}).get("message") is not None:
                problems.append("passed terminal Messages scenario step should omit message")
            after_result = _messages_hook_finishes(test_steps, step_finishes)[-1].get("testStepResult", {})
            if teardown_message not in str(after_result.get("message")):
                problems.append(
                    f"Messages After hook message={after_result.get('message')!r}, "
                    f"expected to contain {teardown_message!r}"
                )
            after_exception = after_result.get("exception")
            after_exception_message = after_exception.get("message") if isinstance(after_exception, dict) else None
            if teardown_message not in str(after_exception_message):
                problems.append(
                    f"Messages After hook exception.message={after_exception_message!r}, "
                    f"expected to contain {teardown_message!r}"
                )

    json_steps = _single_json_scenario_steps(
        json_path,
        consumer,
        "tolerant-teardown-interrupted-runtime.feature",
        expected_scenario_name,
        problems,
    )
    if json_steps is not None:
        scenario_json_steps, hook_statuses = _split_json_report_steps(json_steps)
        if hook_statuses != [("Before", "passed"), ("After", "unknown")]:
            problems.append(
                "JSON Before/After hook statuses="
                f"{hook_statuses!r}, expected [('Before', 'passed'), ('After', 'unknown')]"
            )
        if any(step.get("result", {}).get("error_message") is not None for step in _json_hook_steps(json_steps)):
            problems.append("JSON Before/After hooks should omit error_message when no error is serialized")
        names = [step.get("name") for step in scenario_json_steps]
        statuses = [step.get("result", {}).get("status") for step in scenario_json_steps]
        if names != expected_step_names:
            problems.append(f"JSON scenario steps={names!r}, expected {expected_step_names!r}")
        if statuses != ["failed", "passed"]:
            problems.append(f"JSON scenario step statuses={statuses!r}, expected ['failed', 'passed']")
        if len(scenario_json_steps) == len(expected_step_names):
            first_error = scenario_json_steps[0].get("result", {}).get("error_message")
            if assertion_message not in str(first_error):
                problems.append(f"tolerant JSON error={first_error!r}, expected to contain {assertion_message!r}")
            terminal_error = scenario_json_steps[-1].get("result", {}).get("error_message")
            if terminal_error is not None:
                problems.append(f"passed terminal JSON scenario step error_message={terminal_error!r}, expected None")

    assert not problems, "tolerant failure and teardown interruption contract failed:\n- " + "\n- ".join(problems)


@then(
    re.compile(
        r'consumer runtime artifacts "(?P<before_path>[^"]+)", "(?P<runtime_path>[^"]+)", '
        r'"(?P<messages_path>[^"]+)" and "(?P<json_path>[^"]+)" '
        r"should preserve the undefined step and final teardown interruption"
    )
)
def consumer_undefined_step_teardown_interrupt_are_retained(
    before_path: str,
    runtime_path: str,
    messages_path: str,
    json_path: str,
    consumer: Any,
) -> None:
    problems: list[str] = []
    result = getattr(consumer, "pytest_result", None)
    if result is None:
        problems.append("pytest did not run")
    elif result.returncode != 2:
        problems.append(
            f"pytest returned {result.returncode}, expected 2; stdout={result.stdout!r}; stderr={result.stderr!r}"
        )

    expected_scenario_name = "Teardown interruption follows an undefined step"
    expected_step_names = [
        "the scenario arms teardown interruption before an undefined step",
        "an undefined runtime step is encountered",
        "the middle runtime step remains unstarted",
        "the final runtime step remains unstarted",
    ]
    expected_statuses = ["passed", "undefined", "skipped", "skipped"]
    undefined_message = "Step definition is not found"
    teardown_message = "teardown after undefined-step sentinel"

    snapshots: dict[str, dict[str, Any]] = {}
    for label, relative_path in (("before-teardown", before_path), ("teardown runtime", runtime_path)):
        try:
            snapshots[label] = json.loads(_runtime_artifact_path(relative_path, consumer).read_text(encoding="utf-8"))
        except FileNotFoundError:
            problems.append(f"{label} artifact {relative_path!r} was not produced")

    before = snapshots.get("before-teardown")
    if before is not None:
        if before.get("scenario_status") != "undefined":
            problems.append(f"before-teardown scenario_status={before.get('scenario_status')!r}, expected 'undefined'")
        if before.get("step_names") != expected_step_names[:2]:
            problems.append(
                f"before-teardown step_names={before.get('step_names')!r}, expected {expected_step_names[:2]!r}"
            )
        if before.get("step_statuses") != expected_statuses[:2]:
            problems.append(
                f"before-teardown step_statuses={before.get('step_statuses')!r}, expected {expected_statuses[:2]!r}"
            )
        undefined_error = before.get("step_exception_messages", [None, None])[1]
        if undefined_message not in str(undefined_error):
            problems.append(
                f"before-teardown undefined error={undefined_error!r}, expected to contain {undefined_message!r}"
            )

    runtime = snapshots.get("teardown runtime")
    if runtime is not None:
        for field, expected in (
            ("scenario_status", "interrupted"),
            ("exception_type", "KeyboardInterrupt"),
            ("exception_message", teardown_message),
            ("runtime_status", "inactive"),
            ("active_feature_binding", False),
            ("active_scenario_run", False),
            ("exit_status", 2),
        ):
            if runtime.get(field) != expected:
                problems.append(f"teardown runtime {field}={runtime.get(field)!r}, expected {expected!r}")

    expected_test_step_count = len(expected_step_names) + 2
    messages_case = _single_messages_case(messages_path, consumer, expected_test_step_count, problems)
    if messages_case is not None:
        case, _started, test_steps, step_finishes, envelopes = messages_case
        scenario_steps, scenario_finishes, hook_statuses = _split_messages_steps(test_steps, step_finishes)
        if hook_statuses != ["passed", "unknown"]:
            problems.append(f"Messages Before/After hook statuses={hook_statuses!r}, expected ['passed', 'unknown']")
        pickles = [envelope["pickle"] for envelope in envelopes if "pickle" in envelope]
        if len(pickles) != 1:
            problems.append(f"expected one Messages Pickle, got {len(pickles)}")
        else:
            pickle = pickles[0]
            pickle_steps = pickle.get("steps", [])
            if pickle.get("name") != expected_scenario_name:
                problems.append(f"Messages Pickle name={pickle.get('name')!r}, expected {expected_scenario_name!r}")
            if [step.get("text") for step in pickle_steps] != expected_step_names:
                problems.append(
                    f"Messages Pickle step texts={[step.get('text') for step in pickle_steps]!r}, "
                    f"expected {expected_step_names!r}"
                )
            if case.get("pickleId") != pickle.get("id"):
                problems.append("Messages TestCase does not reference its Pickle")
            if [step.get("pickleStepId") for step in scenario_steps] != [step.get("id") for step in pickle_steps]:
                problems.append("Messages TestCase step links do not match the Pickle step identities")

        message_statuses = [
            finish.get("testStepResult", {}).get("status", "").lower() for finish in scenario_finishes
        ]
        if message_statuses != expected_statuses:
            problems.append(f"Messages test step statuses={message_statuses!r}, expected {expected_statuses!r}")
        if len(scenario_finishes) == len(expected_step_names):
            undefined_result = scenario_finishes[1].get("testStepResult", {})
            if undefined_message not in str(undefined_result.get("message")):
                problems.append(
                    f"undefined Messages message={undefined_result.get('message')!r}, "
                    f"expected to contain {undefined_message!r}"
                )
            terminal_result = scenario_finishes[-1].get("testStepResult", {})
            if terminal_result.get("message") is not None:
                problems.append(
                    f"unstarted Messages scenario step message={terminal_result.get('message')!r}, expected None"
                )
            after_result = _messages_hook_finishes(test_steps, step_finishes)[-1].get("testStepResult", {})
            if after_result.get("status") != "UNKNOWN":
                problems.append(f"Messages After hook status={after_result.get('status')!r}, expected 'UNKNOWN'")
            if teardown_message not in str(after_result.get("message")):
                problems.append(
                    f"Messages After hook message={after_result.get('message')!r}, "
                    f"expected to contain {teardown_message!r}"
                )
            after_exception = after_result.get("exception")
            after_exception_message = after_exception.get("message") if isinstance(after_exception, dict) else None
            if teardown_message not in str(after_exception_message):
                problems.append(
                    f"Messages After hook exception.message={after_exception_message!r}, "
                    f"expected to contain {teardown_message!r}"
                )

    json_steps = _single_json_scenario_steps(
        json_path,
        consumer,
        "undefined-teardown-interrupted-runtime.feature",
        expected_scenario_name,
        problems,
    )
    if json_steps is not None:
        scenario_json_steps, hook_statuses = _split_json_report_steps(json_steps)
        if hook_statuses != [("Before", "passed"), ("After", "unknown")]:
            problems.append(
                "JSON Before/After hook statuses="
                f"{hook_statuses!r}, expected [('Before', 'passed'), ('After', 'unknown')]"
            )
        if any(step.get("result", {}).get("error_message") is not None for step in _json_hook_steps(json_steps)):
            problems.append("JSON Before/After hooks should omit error_message when no error is serialized")
        json_names = [step.get("name") for step in scenario_json_steps]
        if json_names != expected_step_names:
            problems.append(f"JSON scenario steps={json_names!r}, expected {expected_step_names!r}")
        json_statuses = [step.get("result", {}).get("status") for step in scenario_json_steps]
        if json_statuses != expected_statuses:
            problems.append(f"JSON step statuses={json_statuses!r}, expected {expected_statuses!r}")
        if len(scenario_json_steps) == len(expected_step_names):
            undefined_error = scenario_json_steps[1].get("result", {}).get("error_message")
            if undefined_error is not None:
                problems.append(f"undefined JSON error_message={undefined_error!r}, expected None")
            terminal_error = scenario_json_steps[-1].get("result", {}).get("error_message")
            if terminal_error is not None:
                problems.append(f"unstarted JSON step error_message={terminal_error!r}, expected None")

    assert not problems, "undefined step and teardown interruption contract failed:\n- " + "\n- ".join(problems)


__all__ = [
    "consumer_assertion_failure_and_teardown_interrupt_are_retained",
    "consumer_distinct_source_identities",
    "consumer_interrupted_runtime_is_retained",
    "consumer_middle_skip_teardown_interrupt_preserves_reporting",
    "consumer_plain_pytest_after_runtime_cleanup",
    "consumer_plain_reporting_does_not_reuse_bdd_identity",
    "consumer_repeated_session_runtime_roots",
    "consumer_rule_background_runtime_links",
    "consumer_runtime_cleanup_isolation",
    "consumer_runtime_rows_are_isolated",
    "consumer_runtime_run_id_matches_messages",
    "consumer_teardown_interrupt_is_retained",
    "consumer_teardown_interrupt_overrides_terminal_skip",
    "consumer_terminal_outcomes_after_cleanup",
    "consumer_tolerant_failure_teardown_interrupt_are_retained",
    "consumer_tolerant_step_and_teardown_failure_reporting",
    "consumer_undefined_step_teardown_interrupt_are_retained",
    "consumer_xdist_runtime_roots",
]
