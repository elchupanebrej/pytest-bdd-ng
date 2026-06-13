"""Golden file parity tests for allure-formatter converter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pytest_bdd.plugin.allure_formatter.converter import convert

pytestmark = [pytest.mark.contract]


def _write_ndjson(path: Path, lines: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")


def _load_json_files(directory: Path) -> list[dict]:
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(directory.glob("*.json"))]


def test_minimal_scenario_golden(tmp_path: Path) -> None:
    """Known minimal NDJSON produces Allure JSON with expected name, status, step count."""
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
                    "steps": [
                        {"id": "ps-1", "type": "Action", "text": "I enter valid credentials", "astNodeIds": []},
                    ],
                },
            },
            {
                "testCase": {
                    "id": "tc-1",
                    "pickleId": "pk-1",
                    "testSteps": [{"id": "ts-1", "pickleStepId": "ps-1"}],
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
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "testStepResult": {
                        "status": "PASSED",
                        "duration": {"seconds": 1, "nanos": 0},
                        "exception": None,
                        "message": None,
                    },
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
    result_files = list(output.glob("*-result.json"))
    # Find the test case result (may also have a run-level result)
    case_results = [
        json.loads(f.read_text(encoding="utf-8"))
        for f in result_files
        if json.loads(f.read_text(encoding="utf-8")).get("uuid") == "case-1"
    ]
    assert len(case_results) == 1
    result = case_results[0]
    assert result["name"] == "Successful Login"
    assert result["status"] == "passed"
    assert len(result.get("steps", [])) == 1
    assert result["steps"][0]["name"] == "I enter valid credentials"
    assert result["steps"][0]["status"] == "passed"


def test_container_references_children(tmp_path: Path) -> None:
    """Container.children UUIDs match the result file UUIDs."""
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
                "testCaseStarted": {
                    "id": "case-2",
                    "testCaseId": "tc-2",
                    "attempt": 0,
                    "timestamp": {"seconds": 3, "nanos": 0},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-2",
                    "timestamp": {"seconds": 4, "nanos": 0},
                    "willBeRetried": False,
                },
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 5, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result_files = list(output.glob("*-result.json"))
    container_files = list(output.glob("*-container.json"))
    # Filter to test case results only (may also have run-level result)
    case_results = []
    for f in result_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("uuid") in ("case-1", "case-2"):
            case_results.append(data)
    assert len(case_results) == 2, f"Expected 2 test case results, got {len(case_results)}"
    assert len(container_files) >= 1, f"Expected at least 1 container, got {len(container_files)}"
    result_uuids = {r["uuid"] for r in case_results}
    container = json.loads(container_files[0].read_text(encoding="utf-8"))
    container_children = set(container.get("children", []))
    # Container should contain at least the test case results
    assert result_uuids.issubset(container_children), (
        f"Container children {container_children} does not contain all result UUIDs {result_uuids}"
    )
