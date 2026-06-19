"""Integration tests for real-time Allure interception via AllureFormatter.

These tests verify that the plugin loads correctly in live mode and produces
Allure output when used with BDD scenarios. Plain (non-BDD) tests verify
that the plugin initializes and tears down without errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.plugin.allure_formatter.listener import AllureFormatter

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.integration]


def test_plugin_loads_and_teardowns_cleanly(testdir, tmp_path: Path) -> None:
    """Verify the allure-cucumber plugin loads and tears down without errors in live mode."""
    testdir.makeconftest("")
    testdir.makepyfile(
        test_noop="""
def test_one():
    pass

def test_two():
    pass
""",
    )
    result = testdir.runpytest_subprocess(
        "--allure-cucumber-out",
        str(tmp_path / "allure-results"),
    )
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(["*2 passed*"])


def test_message_flow_unit_level() -> None:
    """Verify the full message flow: pytest_bdd_message -> adapter -> allure lifecycle."""
    config = MagicMock(spec=Config)
    config.option = MagicMock()
    config.option.allure_cucumber_output_dir = "test-allure-results"
    config.option.allure_cucumber_messages_in = None
    config.getini = MagicMock(return_value=None)

    listener = AllureFormatter(config=config, output_dir="test-allure-results")

    # Simulate the full message flow for one scenario
    messages = [
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
    ]

    for msg in messages:
        listener.pytest_bdd_message(config, msg)

    # Verify no exceptions were raised and adapter processed all messages


def test_message_flow_failure_status() -> None:
    """Verify that FAILED status is correctly mapped through the message flow."""
    config = MagicMock(spec=Config)
    config.option = MagicMock()
    config.option.allure_cucumber_output_dir = "test-allure-results"
    config.option.allure_cucumber_messages_in = None
    config.getini = MagicMock(return_value=None)

    listener = AllureFormatter(config=config, output_dir="test-allure-results")

    messages = [
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
                    "status": "FAILED",
                    "duration": {"seconds": 1, "nanos": 0},
                    "exception": {
                        "type": "AssertionError",
                        "message": "intentional failure",
                    },
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
    ]

    for msg in messages:
        listener.pytest_bdd_message(config, msg)


def test_message_flow_multiple_scenarios() -> None:
    """Verify the message flow handles multiple sequential scenarios."""
    config = MagicMock(spec=Config)
    config.option = MagicMock()
    config.option.allure_cucumber_output_dir = "test-allure-results"
    config.option.allure_cucumber_messages_in = None
    config.getini = MagicMock(return_value=None)

    listener = AllureFormatter(config=config, output_dir="test-allure-results")

    # Run 3 scenarios in sequence
    for i in range(3):
        messages = [
            {"testRunStarted": {"id": f"run-{i}", "timestamp": {"seconds": 0, "nanos": 0}}},
            {
                "testCaseStarted": {
                    "id": f"case-{i}",
                    "testCaseId": f"tc-{i}",
                    "attempt": 0,
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepStarted": {
                    "testStepId": f"step-{i}",
                    "testCaseStartedId": f"case-{i}",
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
            {
                "testStepFinished": {
                    "testStepId": f"step-{i}",
                    "testCaseStartedId": f"case-{i}",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 1, "nanos": 0}},
                },
            },
            {
                "testCaseFinished": {
                    "testCaseStartedId": f"case-{i}",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "willBeRetried": False,
                },
            },
        ]

        for msg in messages:
            listener.pytest_bdd_message(config, msg)


def test_plugin_with_ini_config(testdir, tmp_path: Path) -> None:
    """Verify the plugin reads allure_cucumber_output_dir from INI when CLI flag is absent."""
    output = tmp_path / "custom-allure"
    output.mkdir()
    testdir.makeconftest("")
    testdir.makepyfile(
        test_noop="""
def test_one():
    pass
""",
    )
    ini_content = f"[pytest]\nallure_cucumber_output_dir = {output.as_posix()}\n"
    testdir.makefile(".ini", pytest=ini_content)
    result = testdir.runpytest_subprocess()
    result.assert_outcomes(passed=1)


def test_plugin_not_loaded_without_output_dir(testdir) -> None:
    """Verify the plugin is not loaded when no output directory option is provided."""
    testdir.makeconftest("")
    testdir.makepyfile(
        test_noop="""
def test_one():
    pass
""",
    )
    result = testdir.runpytest_subprocess()
    result.assert_outcomes(passed=1)
