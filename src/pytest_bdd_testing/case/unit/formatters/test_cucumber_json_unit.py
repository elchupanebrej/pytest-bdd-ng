"""
Unit tests for LogBDDCucumberJSON plugin.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

from pytest_bdd.plugin.cucumber_json.plugin import LogBDDCucumberJSON

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import TestReport


def test_cucumber_json_get_result_skipped() -> None:
    report = cast(
        "TestReport",
        SimpleNamespace(
            passed=False,
            failed=False,
            skipped=True,
            longrepr="Skipped: reason",
        ),
    )
    step: dict[str, Any] = {"failed": False, "duration": 0.05}
    result = LogBDDCucumberJSON._get_result(step, report)
    assert result["status"] == "skipped"
    assert result["duration"] == 50_000_000


def test_cucumber_json_get_result_passed() -> None:
    report = cast(
        "TestReport",
        SimpleNamespace(
            passed=True,
            failed=False,
            skipped=False,
        ),
    )
    step: dict[str, Any] = {"failed": False, "duration": 0.01}
    result = LogBDDCucumberJSON._get_result(step, report)
    assert result["status"] == "passed"


def test_cucumber_json_get_result_failed() -> None:
    report = cast(
        "TestReport",
        SimpleNamespace(
            passed=False,
            failed=True,
            skipped=False,
            longrepr="AssertionError: failed",
        ),
    )
    step: dict[str, Any] = {"failed": True, "duration": 0.02}
    result = LogBDDCucumberJSON._get_result(step, report, error_message=True)
    assert result["status"] == "failed"
    assert result["error_message"] == "AssertionError: failed"


def test_cucumber_json_logreport_setup_skipped(tmp_path) -> None:
    out_file = tmp_path / "cucumber.json"
    plugin = LogBDDCucumberJSON(str(out_file))

    scenario_data = {
        "feature": {
            "name": "Feature 1",
            "filename": "f.feature",
            "rel_filename": "f.feature",
            "line_number": 1,
            "description": "",
            "tags": [],
        },
        "name": "Skipped Scenario",
        "line_number": 2,
        "tags": ["skip"],
        "steps": [
            {
                "keyword": "Given",
                "name": "a step",
                "line_number": 3,
                "type": "given",
                "failed": False,
                "duration": 0.0,
            },
        ],
    }

    report = cast(
        "TestReport",
        SimpleNamespace(
            when="setup",
            passed=False,
            failed=False,
            skipped=True,
            scenario=scenario_data,
            longrepr="Skipped",
        ),
    )

    plugin.pytest_runtest_logreport(report)
    assert "f.feature" in plugin.features
    feature_entry = plugin.features["f.feature"]
    elements = feature_entry["elements"]
    assert len(elements) == 1
    assert elements[0]["name"] == "Skipped Scenario"
    assert elements[0]["steps"][0]["result"]["status"] == "skipped"
