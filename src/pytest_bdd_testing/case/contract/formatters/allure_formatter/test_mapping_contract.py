"""Mapping contract tests: validate every Cucumber→Allure field mapping with real NDJSON.

Each test creates a minimal NDJSON that exercises exactly one mapping requirement,
converts it, and asserts the correct field value in the output. No mocks — real
converter pipeline, real dataclass payloads, semantic value assertions.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from pytest_bdd.plugin.allure_formatter.converter import convert

pytestmark = [pytest.mark.contract]


def _write_ndjson(path: Path, lines: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")


def _load_result(output: Path, uuid: str = "case-1") -> dict:
    """Load a specific result file by UUID from output directory."""
    result_files = list(output.glob("*-result.json"))
    for f in result_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("uuid") == uuid:
            return data
    # Fallback: return first result if UUID not found
    assert len(result_files) >= 1, f"Expected at least 1 result, got {len(result_files)}"
    return json.loads(result_files[0].read_text(encoding="utf-8"))


def _load_results(output: Path) -> list[dict]:
    """Load all result files from output directory."""
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(output.glob("*-result.json"))]


def test_step_name_matches_pickle_step_text(tmp_path: Path) -> None:
    """REQ-01: Step name is resolved from PickleStep.text through TestCase→Pickle lookup chain."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            # Structural: Pickle with step text
            {
                "pickle": {
                    "id": "pk-1",
                    "name": "Login",
                    "language": "en",
                    "astNodeIds": [],
                    "tags": [],
                    "uri": "features/login.feature",
                    "steps": [
                        {"id": "ps-1", "type": "Action", "text": "I enter valid credentials", "astNodeIds": []},
                    ],
                },
            },
            # Structural: TestCase linking pickle to test steps
            {"testCase": {"id": "tc-1", "pickleId": "pk-1", "testSteps": [{"id": "ts-1", "pickleStepId": "ps-1"}]}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepStarted": {
                    "testStepId": "ts-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepFinished": {
                    "testStepId": "ts-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 1, "nanos": 0}},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    assert len(result["steps"]) == 1
    assert result["steps"][0]["name"] == "I enter valid credentials"


def test_test_case_name_matches_pickle_name(tmp_path: Path) -> None:
    """REQ-02: Test case name is resolved from Pickle.name through TestCase→Pickle lookup chain."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "pickle": {
                    "id": "pk-1",
                    "name": "Successful Login",
                    "language": "en",
                    "astNodeIds": [],
                    "tags": [],
                    "uri": "features/login.feature",
                    "steps": [],
                },
            },
            {"testCase": {"id": "tc-1", "pickleId": "pk-1", "testSteps": []}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    assert result["name"] == "Successful Login"


def test_step_status_from_finished_event(tmp_path: Path) -> None:
    """REQ-03: Step status is correctly mapped from TestStepFinished.test_step_result.status."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepStarted": {
                    "testStepId": "step-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepFinished": {
                    "testStepId": "step-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "testStepResult": {"status": "FAILED", "duration": {"seconds": 1, "nanos": 0}},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": False, "timestamp": {"seconds": 3, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    assert result["steps"][0]["status"] == "failed"


def test_step_start_time_populated(tmp_path: Path) -> None:
    """REQ-04: Step start time is populated from TestStepStarted.timestamp (emitted as milliseconds)."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepStarted": {
                    "testStepId": "step-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 10, "nanos": 0},
                },
            },
            {
                "testStepFinished": {
                    "testStepId": "step-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 20, "nanos": 0},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 10, "nanos": 0}},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 20, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 30, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    step = result["steps"][0]
    # Emitter converts seconds to milliseconds: 10 * 1000 = 10000
    assert step.get("start") == 10000, f"Expected step start=10000, got {step.get('start')}"


def test_step_stop_time_populated(tmp_path: Path) -> None:
    """REQ-05: Step stop time is populated from TestStepFinished.timestamp (emitted as milliseconds)."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepStarted": {
                    "testStepId": "step-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 10, "nanos": 0},
                },
            },
            {
                "testStepFinished": {
                    "testStepId": "step-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 20, "nanos": 0},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 10, "nanos": 0}},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 20, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 30, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    step = result["steps"][0]
    # Emitter converts seconds to milliseconds: 20 * 1000 = 20000
    assert step.get("stop") == 20000, f"Expected step stop=20000, got {step.get('stop')}"


def test_result_start_time_populated(tmp_path: Path) -> None:
    """REQ-06: Result start time is populated from TestCaseStarted.timestamp (emitted as milliseconds)."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 5, "nanos": 0},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 10, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 15, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    # 5 * 1000 = 5000 milliseconds
    assert result["start"] == 5000, f"Expected start=5000, got {result['start']}"


def test_result_stop_time_populated(tmp_path: Path) -> None:
    """REQ-07: Result stop time is populated from TestCaseFinished.timestamp (emitted as milliseconds)."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 5, "nanos": 0},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 10, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 15, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    # 10 * 1000 = 10000 milliseconds
    assert result["stop"] == 10000, f"Expected stop=10000, got {result['stop']}"


def test_run_failure_sets_failed_status(tmp_path: Path) -> None:
    """REQ-08: TestRunFinished with success=false sets run-level result status to failed."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": False, "timestamp": {"seconds": 3, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    # Run-level events go to a separate run-level result
    results = _load_results(output)
    run_results = [r for r in results if r["name"].startswith("Test Run")]
    assert len(run_results) >= 1, f"Expected run-level result, got {[r['name'] for r in results]}"
    assert run_results[0]["status"] == "failed"


def test_run_error_message_propagated(tmp_path: Path) -> None:
    """REQ-09: TestRunFinished message is propagated to run-level statusDetails.message."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {
                "testRunFinished": {
                    "success": False,
                    "timestamp": {"seconds": 3, "nanos": 0},
                    "message": "2 scenarios failed, 1 passed",
                },
            },
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    # Run-level message goes to run-level result
    results = _load_results(output)
    run_results = [r for r in results if r["name"].startswith("Test Run")]
    assert len(run_results) >= 1
    assert run_results[0]["statusDetails"]["message"] == "2 scenarios failed, 1 passed"


def test_attachment_name_from_file_name(tmp_path: Path) -> None:
    """REQ-10: Attachment name is populated from file_name field."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "attachment": {
                    "testCaseStartedId": "case-1",
                    "fileName": "screenshot.png",
                    "mediaType": "image/png",
                    "source": "attachments/screenshot.png",
                    "body": {"data": "base64data"},
                    "contentEncoding": "BASE64",
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    assert len(result["attachments"]) >= 1
    att = result["attachments"][0]
    assert att["name"] == "screenshot.png"


def test_attachment_source_populated(tmp_path: Path) -> None:
    """REQ-11: Attachment source is populated from Attachment.source field."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "attachment": {
                    "testCaseStartedId": "case-1",
                    "fileName": "log.txt",
                    "mediaType": "text/plain",
                    "source": "attachments/log.txt",
                    "body": {"data": "base64data"},
                    "contentEncoding": "BASE64",
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    att = result["attachments"][0]
    assert att["source"] == "attachments/log.txt"


def test_attachment_type_from_media_type(tmp_path: Path) -> None:
    """REQ-12: Attachment type is populated from media_type field."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "attachment": {
                    "testCaseStartedId": "case-1",
                    "fileName": "screenshot.png",
                    "mediaType": "image/png",
                    "source": "attachments/screenshot.png",
                    "body": {"data": "base64data"},
                    "contentEncoding": "BASE64",
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    att = result["attachments"][0]
    assert att["type"] == "image/png"


def test_hook_name_from_hook_lookup(tmp_path: Path) -> None:
    """REQ-13: Hook step name is resolved from Hook.name through lookup chain."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            # Structural: Hook definition
            {
                "hook": {
                    "id": "hk-1",
                    "name": "setUp",
                    "sourceReference": {"uri": "features/conftest.py", "location": {"line": 10}},
                },
            },
            # Run-level hook started (links to hook via hook_id and run via testRunStartedId)
            {
                "testRunHookStarted": {
                    "id": "rkh-1",
                    "hookId": "hk-1",
                    "testRunStartedId": "run-1",
                    "timestamp": {"seconds": 0, "nanos": 500000000},
                },
            },
            {
                "testRunHookFinished": {
                    "testRunHookStartedId": "rkh-1",
                    "timestamp": {"seconds": 1, "nanos": 0},
                    "result": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 500000000}},
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 2, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    results = _load_results(output)
    # Hook events go to run-level group
    all_steps = [s for r in results for s in r.get("steps", [])]
    hook_steps = [s for s in all_steps if s["name"] == "setUp"]
    assert len(hook_steps) >= 1, f"Expected hook step named 'setUp', got step names: {[s['name'] for s in all_steps]}"


def test_pickle_id_parameter_added(tmp_path: Path) -> None:
    """REQ-14: Pickle ID is added as a parameter to the result."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "pickle": {
                    "id": "pk-42",
                    "name": "Test",
                    "language": "en",
                    "astNodeIds": [],
                    "tags": [],
                    "uri": "features/test.feature",
                    "steps": [],
                },
            },
            {"testCase": {"id": "tc-1", "pickleId": "pk-42", "testSteps": []}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    params = {p["name"]: p["value"] for p in result.get("parameters", [])}
    assert "pickleId" in params, f"Expected pickleId parameter, got {params}"
    assert params["pickleId"] == "pk-42"


def test_step_count_matches_pickle(tmp_path: Path) -> None:
    """REQ-15: Number of steps in result matches number of pickle steps."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "pickle": {
                    "id": "pk-1",
                    "name": "Multi-step",
                    "language": "en",
                    "astNodeIds": [],
                    "tags": [],
                    "uri": "features/test.feature",
                    "steps": [
                        {"id": "ps-1", "type": "Action", "text": "Step one", "astNodeIds": []},
                        {"id": "ps-2", "type": "Action", "text": "Step two", "astNodeIds": []},
                        {"id": "ps-3", "type": "Action", "text": "Step three", "astNodeIds": []},
                    ],
                },
            },
            {
                "testCase": {
                    "id": "tc-1",
                    "pickleId": "pk-1",
                    "testSteps": [
                        {"id": "ts-1", "pickleStepId": "ps-1"},
                        {"id": "ts-2", "pickleStepId": "ps-2"},
                        {"id": "ts-3", "pickleStepId": "ps-3"},
                    ],
                },
            },
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepStarted": {
                    "testStepId": "ts-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepFinished": {
                    "testStepId": "ts-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 1, "nanos": 500000000},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 500000000}},
                },
            },
            {
                "testStepStarted": {
                    "testStepId": "ts-2",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 1, "nanos": 500000000},
                },
            },
            {
                "testStepFinished": {
                    "testStepId": "ts-2",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 500000000}},
                },
            },
            {
                "testStepStarted": {
                    "testStepId": "ts-3",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                },
            },
            {
                "testStepFinished": {
                    "testStepId": "ts-3",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 500000000},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 500000000}},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 3, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 4, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    assert len(result["steps"]) == 3, f"Expected 3 steps, got {len(result['steps'])}"
    assert result["steps"][0]["name"] == "Step one"
    assert result["steps"][1]["name"] == "Step two"
    assert result["steps"][2]["name"] == "Step three"


def test_nested_steps_hierarchy(tmp_path: Path) -> None:
    """REQ-16: Multiple steps at different levels are all resolved correctly."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "pickle": {
                    "id": "pk-1",
                    "name": "Nested",
                    "language": "en",
                    "astNodeIds": [],
                    "tags": [],
                    "uri": "features/test.feature",
                    "steps": [
                        {"id": "ps-outer", "type": "Action", "text": "Outer step", "astNodeIds": []},
                        {"id": "ps-inner", "type": "Action", "text": "Inner step", "astNodeIds": []},
                    ],
                },
            },
            {
                "testCase": {
                    "id": "tc-1",
                    "pickleId": "pk-1",
                    "testSteps": [
                        {"id": "ts-outer", "pickleStepId": "ps-outer"},
                        {"id": "ts-inner", "pickleStepId": "ps-inner"},
                    ],
                },
            },
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepStarted": {
                    "testStepId": "ts-outer",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepStarted": {
                    "testStepId": "ts-inner",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 1, "nanos": 500000000},
                },
            },
            {
                "testStepFinished": {
                    "testStepId": "ts-inner",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 500000000}},
                },
            },
            {
                "testStepFinished": {
                    "testStepId": "ts-outer",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 1, "nanos": 0}},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 3, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 4, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result = _load_result(output)
    assert len(result["steps"]) == 2
    assert result["steps"][0]["name"] == "Outer step"
    assert result["steps"][1]["name"] == "Inner step"
    assert result["steps"][0]["status"] == "passed"
    assert result["steps"][1]["status"] == "passed"
