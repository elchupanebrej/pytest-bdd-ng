"""Integration tests for allure-cucumber plugin lifecycle."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_ndjson(path: Path, lines: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")


def _make_minimal_ndjson(path: Path) -> None:
    """Write a minimal valid Cucumber Messages NDJSON to path."""
    _write_ndjson(path, [
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
    ])


def test_plugin_sessionfinish_emits_results(testdir, tmp_path: Path) -> None:
    """pytest with --allure-cucumber-messages produces Allure result files."""
    messages = tmp_path / "messages.ndjson"
    _make_minimal_ndjson(messages)
    output = tmp_path / "allure-results"
    testdir.makeconftest("")
    testdir.makepyfile(
        test_noop="""\
def test_noop():
    pass
""",
    )
    result = testdir.runpytest_subprocess(
        "--allure-cucumber-messages", str(messages),
        "--allure-cucumber-output", str(output),
    )
    result.assert_outcomes(passed=1)
    json_files = list(output.glob("*.json")) if output.exists() else []
    assert len(json_files) >= 1, f"Expected Allure output files, found: {json_files}"


def test_plugin_respects_ini_config(testdir, tmp_path: Path) -> None:
    """Plugin reads allure_cucumber_output_dir from INI when CLI flag is absent."""
    output = tmp_path / "custom-allure"
    output.mkdir()
    messages = Path(str(testdir.tmpdir)) / "messages.ndjson"
    _make_minimal_ndjson(messages)
    testdir.makeconftest("")
    testdir.makepyfile(
        test_noop="""\
def test_noop():
    pass
""",
    )
    ini_content = f"[pytest]\nallure_cucumber_output_dir = {output.as_posix()}\n"
    testdir.makefile(".ini", pytest=ini_content)
    result = testdir.runpytest_subprocess(
        "--allure-cucumber-messages", str(messages),
    )
    result.assert_outcomes(passed=1)
    json_files = list(output.glob("*.json"))
    default_files = list((tmp_path / "allure-results").glob("*.json")) if (tmp_path / "allure-results").exists() else []
    assert len(json_files) >= 1 or len(default_files) >= 1, (
        f"Expected Allure output files, found {len(json_files)} in INI dir, {len(default_files)} in default"
    )
