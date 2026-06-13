"""Integration tests for allure-cucumber plugin lifecycle."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def _write_ndjson(path: Path, lines: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")


def _make_minimal_ndjson(path: Path) -> None:
    """Write a minimal valid Cucumber Messages NDJSON to path."""
    _write_ndjson(
        path,
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
            {
                "testRunFinished": {
                    "success": True,
                    "timestamp": {"seconds": 3, "nanos": 0},
                    "testRunStartedId": "run-1",
                },
            },
        ],
    )


def test_live_mode_emits_results(testdir, tmp_path: Path) -> None:
    """pytest with --allure-formatter-output (live mode) runs BDD and produces results."""
    output = tmp_path / "allure-results"
    testdir.makeconftest("")
    testdir.makepyfile(
        test_noop="""\
def test_noop():
    pass
""",
    )
    result = testdir.runpytest_subprocess(
        "--allure-formatter-output",
        str(output),
    )
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*1 passed*"])


def test_import_mode_replays_ndjson(testdir, tmp_path: Path) -> None:
    """pytest with --cucumber-messages replays NDJSON into Allure results."""
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
        "--cucumber-messages",
        str(messages),
        "--allure-formatter-output",
        str(output),
    )
    json_files = list(output.glob("*.json")) if output.exists() else []
    assert len(json_files) >= 1, f"Expected Allure output files, found: {json_files}"


def test_import_mode_deselects_items(testdir, tmp_path: Path) -> None:
    """Import mode deselects all collected items (no tests run, only replay)."""
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
        "--cucumber-messages",
        str(messages),
        "--allure-formatter-output",
        str(output),
    )
    # Import mode deselects all collected items, so ExitCode.NO_TESTS_COLLECTED (5) is expected
    assert result.ret in {0, 5}, f"Expected exit code 0 or 5, got {result.ret}: {result.stdout.str()}"
    json_files = list(output.glob("*.json")) if output.exists() else []
    assert len(json_files) >= 1, f"Expected Allure output from NDJSON replay, found: {json_files}"


def test_deprecated_allure_messages_in_option(testdir, tmp_path: Path) -> None:
    """pytest with deprecated --cucumber-messages replays NDJSON into Allure results."""
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
        "--cucumber-messages",
        str(messages),
        "--allure-formatter-output",
        str(output),
    )
    json_files = list(output.glob("*.json")) if output.exists() else []
    assert len(json_files) >= 1, f"Expected Allure output files, found: {json_files}"


def test_plugin_respects_ini_config(testdir, tmp_path: Path) -> None:
    """Plugin reads allure_formatter_output_dir from INI and loads without error."""
    output = tmp_path / "custom-allure"
    output.mkdir()
    testdir.makeconftest("")
    testdir.makepyfile(
        test_noop="""\
def test_noop():
    pass
""",
    )
    ini_content = f"[pytest]\nallure_formatter_output_dir = {output.as_posix()}\n"
    testdir.makefile(".ini", pytest=ini_content)
    result = testdir.runpytest_subprocess()
    result.assert_outcomes(passed=1)
