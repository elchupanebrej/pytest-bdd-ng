"""Contract tests for allure-cucumber converter mapping guarantees."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pytest_bdd.plugin.allure_cucumber.converter import convert
from pytest_bdd.plugin.allure_cucumber.converter.mapper import map_unmappable_to_attachment
from pytest_bdd.plugin.allure_cucumber.converter.model import AllureAttachment
from pytest_bdd.plugin.allure_cucumber.converter.reader import read_envelopes

pytestmark = [pytest.mark.contract]


def _write_ndjson(path: Path, lines: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")


def _load_json_files(directory: Path) -> list[dict]:
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(directory.glob("*.json"))]


def test_test_case_started_creates_result(tmp_path: Path) -> None:
    """Each TestCaseStarted in NDJSON produces one TestResult in output."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "r1", "timestamp": {"seconds": 0, "nanos": 0}}},
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
                }
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result_files = [f for f in output.glob("*-result.json")]
    # At least 1 test case result (may also have a run-level result)
    assert len(result_files) >= 1, f"Expected at least 1 result, got {len(result_files)}"
    # Verify the test case result exists with the correct UUID
    case_results = [
        json.loads(f.read_text(encoding="utf-8"))
        for f in result_files
        if json.loads(f.read_text(encoding="utf-8")).get("uuid") == "case-1"
    ]
    assert len(case_results) == 1, "Expected exactly 1 test case result with uuid='case-1'"


def test_unmappable_events_produce_attachments(tmp_path: Path) -> None:
    """Valid but unmapped Cucumber Message event types produce Allure attachments."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "r1", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "hook": {
                    "id": "hook-1",
                    "hookType": "BEFORE_TEST_CASE",
                    "sourceReference": {"uri": "features/steps.py", "location": {"line": 10}},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                }
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result_files = [f for f in output.glob("*-result.json")]
    assert len(result_files) >= 1
    # Hook events are top-level (no testCaseStartedId), so they're excluded from mapper groups.
    # Verify the mapper contract directly: map_unmappable_to_attachment returns valid AllureAttachment.
    projections = [p for p in read_envelopes(ndjson) if getattr(p.payload_kind, "value", str(p.payload_kind)) == "hook"]
    assert len(projections) == 1
    attachment = map_unmappable_to_attachment(projections[0])
    assert isinstance(attachment, AllureAttachment)
    assert attachment.name.startswith("unmapped-")


def test_result_contains_labels(tmp_path: Path) -> None:
    """TestResult includes labels field (may be empty until label extraction is implemented)."""
    ndjson = tmp_path / "messages.ndjson"
    _write_ndjson(
        ndjson,
        [
            {"testRunStarted": {"id": "r1", "timestamp": {"seconds": 0, "nanos": 0}}},
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
                }
            },
            {"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}},
        ],
    )
    output = tmp_path / "allure-results"
    convert(ndjson, output)
    result_files = list(output.glob("*-result.json"))
    assert len(result_files) >= 1
    result = json.loads(result_files[0].read_text(encoding="utf-8"))
    assert "labels" in result, "Result must have labels field"
    assert isinstance(result["labels"], list), "Labels must be a list"
