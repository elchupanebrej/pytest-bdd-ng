from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

if TYPE_CHECKING:
    from pathlib import Path

from pytest_bdd.cucumber_json import LogBDDCucumberJSON

from pytest import mark

pytestmark = mark.unit


def test_log_bdd_cucumber_json_lifecycle_and_output(tmp_path: Path) -> None:
    out_file = tmp_path / "subdir" / "cucumber.json"
    logger = LogBDDCucumberJSON(str(out_file))
    logger.pytest_sessionstart()

    report = MagicMock()
    report.when = "call"
    report.passed = True
    report.failed = False
    report.skipped = False
    report.item = {"name": "test_scenario_1"}
    report.scenario = {
        "name": "My Scenario",
        "line_number": 3,
        "tags": ["smoke"],
        "steps": [
            {
                "keyword": "Given",
                "name": "step one",
                "line_number": 4,
                "failed": False,
                "duration": 0.01,
            },
        ],
        "feature": {
            "name": "My Feature",
            "filename": "/path/to/feature.feature",
            "rel_filename": "feature.feature",
            "line_number": 1,
            "description": "Feature desc",
            "tags": ["feature_tag"],
        },
    }

    logger.pytest_runtest_logreport(report)
    logger.pytest_sessionfinish()

    assert out_file.exists()
    content = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(content, list)
    assert len(content) == 1
    assert content[0]["name"] == "My Feature"
    assert len(content[0]["elements"]) == 1
    assert content[0]["elements"][0]["name"] == "My Scenario"

    terminalreporter = MagicMock()
    logger.pytest_terminal_summary(terminalreporter)
    terminalreporter.write_sep.assert_called_once()


def test_log_bdd_cucumber_json_status_fallback_and_stepless_scenario(tmp_path: Path) -> None:
    logger = LogBDDCucumberJSON(str(tmp_path / "cucumber.json"))

    report = MagicMock()
    report.skipped = False
    report.failed = False
    report.passed = False
    assert logger._get_result({"failed": True}, report) == {"status": "unknown", "duration": 0}

    step = {"keyword": "Given", "name": "irrelevant", "line_number": 1, "failed": False, "duration": 0.0}
    report.skipped = True
    assert logger._get_result(step, report) == {"status": "skipped", "duration": 0}

    report.skipped = False
    report.passed = True
    assert logger._get_result(step, report) == {"status": "passed", "duration": 0}

    step_without_steps = MagicMock()
    step_without_steps.scenario = {"name": "Empty", "steps": [], "feature": {"filename": "f.feature"}}
    logger.pytest_runtest_logreport(step_without_steps)
    assert logger.features == {}


def test_log_bdd_cucumber_json_strips_file_uri_from_relative_filename(tmp_path: Path) -> None:
    out_file = tmp_path / "cucumber.json"
    logger = LogBDDCucumberJSON(str(out_file))

    report = MagicMock()
    report.when = "call"
    report.passed = True
    report.failed = False
    report.skipped = False
    report.item = {"name": "test_case"}
    report.scenario = {
        "name": "Scenario",
        "line_number": 2,
        "tags": [],
        "steps": [{"keyword": "Given", "name": "step", "line_number": 3, "failed": False, "duration": 0.0}],
        "feature": {
            "name": "Feature",
            "filename": "/abs/features/feature.feature",
            "rel_filename": "file:features/feature.feature",
            "line_number": 1,
            "description": "",
            "tags": [],
        },
    }

    logger.pytest_runtest_logreport(report)
    logger.pytest_sessionfinish()

    content = json.loads(out_file.read_text(encoding="utf-8"))
    assert content[0]["uri"] == "features/feature.feature"
