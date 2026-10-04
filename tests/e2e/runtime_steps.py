"""Acceptance assertions for session-owned runtime integration scenarios."""

from __future__ import annotations

import json
import re
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
    assert sum(name.startswith("Each outline row starts with clean step state for <label>") for name in scenario_names) == 2, rows
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
        "pytest_runtest_setup",
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
            ("running", "running"),
            ("step", "running"),
            ("step", "running"),
            ("step", "running"),
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
        assert row["steps"][1]["result"] == f'{row["row_value"]}:verified', row


@then(
    re.compile(
        r'consumer runtime artifact "(?P<relative_path>[^"]+)" should show failed teardown then clean BDD state'
    )
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
        r'should retain distinct terminal outcomes after cleanup'
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
        assert len(case["testSteps"]) == 1, case
        step_finished = [
            finish for finish in finishes if finish["testCaseStartedId"] == row["test_case_started_id"]
        ]
        assert len(step_finished) == 1, step_finished
        assert step_finished[0]["testStepResult"]["status"] == outcome["message_status"], step_finished


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
        all(step["result"]["status"].lower() == "passed" for step in element["steps"])
        for element in report_elements
    ), report_elements

    for observation in observations:
        case = cases[observation["test_case_id"]]
        pickle = pickles[case["pickleId"]]
        started = starts[observation["test_case_started_id"]]
        assert started["testCaseId"] == case["id"], (started, case)
        assert len(observation["steps"]) == len(case["testSteps"]) == len(pickle["steps"]) == 6
        assert [step["text"] for step in observation["steps"]] == [step["text"] for step in pickle["steps"]]
        assert [step["test_step_id"] for step in observation["steps"]] == [
            step["id"] for step in case["testSteps"]
        ]
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
        json_rows = [
            element
            for element in report_elements
            if any(step["name"] == action for step in element["steps"])
        ]
        assert len(json_rows) == 1, (action, report_elements)
        assert [step["name"] for step in json_rows[0]["steps"]] == [
            step["text"] for step in observation["steps"]
        ]
        assert json_rows[0]["name"] == observation["source_scenario_name"], (json_rows[0], observation)
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
        assert observation["pickle_id"] == pickle["id"], (observation, pickle)
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
                assert source_table is not None and pickle_argument is not None, (runtime_step, source_step, pickle_step)
                source_rows = source_table["rows"]
                assert [row["line"] for row in runtime_table["source_rows"]] == [
                    row["location"]["line"] for row in source_rows
                ], (runtime_table, source_table)
                assert runtime_table["source_line"] == source_table["location"]["line"], (
                    runtime_table,
                    source_table,
                )
                assert [
                    [cell["value"] for cell in row["cells"]] for row in runtime_table["source_rows"]
                ] == [[cell["value"] for cell in row["cells"]] for row in source_rows], (runtime_table, source_table)
                assert [
                    [cell["line"] for cell in row["cells"]] for row in runtime_table["source_rows"]
                ] == [
                    [cell["location"]["line"] for cell in row["cells"]] for row in source_rows
                ], (runtime_table, source_table)
                assert [
                    [cell["value"] for cell in row["cells"]] for row in runtime_table["rows"]
                ] == [
                    [cell["value"] for cell in row["cells"]]
                    for row in pickle_argument["dataTable"]["rows"]
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


@then(
    re.compile(
        r'consumer xdist runtime artifacts should show separate run roots in "(?P<messages_path>[^"]+)"'
    )
)
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
    started_ids = {
        envelope["testCaseStarted"]["id"]
        for envelope in envelopes
        if "testCaseStarted" in envelope
    }
    assert started_ids == {row["test_case_started_id"] for row in observations}, (started_ids, observations)


__all__ = [
    "consumer_plain_pytest_after_runtime_cleanup",
    "consumer_repeated_session_runtime_roots",
    "consumer_rule_background_runtime_links",
    "consumer_runtime_cleanup_isolation",
    "consumer_runtime_rows_are_isolated",
    "consumer_terminal_outcomes_after_cleanup",
    "consumer_xdist_runtime_roots",
]
