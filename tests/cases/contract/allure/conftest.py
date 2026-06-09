"""Shared fixtures for allure-cucumber contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def allure_schema_path() -> Path:
    """Path to committed Allure3 events JSON Schema."""
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / "docs" / "allure3-events.schema.json"


@pytest.fixture
def sample_valid_result() -> dict:
    """Minimal valid Allure3 TestResult dict."""
    return {
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "name": "sample test",
        "fullName": "com.example.SampleTest.sample",
        "historyId": "abc123",
        "testCaseId": "tc-001",
        "status": "passed",
        "stage": "finished",
        "start": 1000,
        "stop": 2000,
        "labels": [{"name": "suite", "value": "SampleSuite"}],
        "links": [],
        "steps": [],
        "attachments": [],
        "parameters": [],
    }


@pytest.fixture
def sample_valid_container() -> dict:
    """Minimal valid Allure3 TestResultContainer dict."""
    return {
        "uuid": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "name": "SampleSuite",
        "children": ["550e8400-e29b-41d4-a716-446655440000"],
        "befores": [],
        "afters": [],
        "links": [],
        "start": 900,
        "stop": 3000,
    }


@pytest.fixture
def sample_ndjson(tmp_path: Path) -> Path:
    """Create a minimal valid Cucumber Messages NDJSON file."""
    ndjson = tmp_path / "messages.ndjson"
    lines = [
        json.dumps({"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}}),
        json.dumps(
            {
                "testCaseStarted": {
                    "id": "case-1",
                    "testCaseId": "tc-1",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
        ),
        json.dumps(
            {
                "testStepStarted": {
                    "testStepId": "step-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
        ),
        json.dumps(
            {
                "testStepFinished": {
                    "testStepId": "step-1",
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
        ),
        json.dumps(
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                },
            },
        ),
        json.dumps({"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}}),
    ]
    ndjson.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ndjson


@pytest.fixture
def converter_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory for converter results."""
    output = tmp_path / "allure-results"
    output.mkdir(parents=True, exist_ok=True)
    return output
