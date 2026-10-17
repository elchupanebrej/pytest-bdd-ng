from __future__ import annotations

import json
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from pytest_cuke.cucumber_json import LogBDDCucumberJSON


def test_log_bdd_cucumber_json_lifecycle_and_output(tmp_path: Path) -> None:
    pytest.importorskip("pydantic")

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
    logger.pytest_sessionfinish(SimpleNamespace(config=SimpleNamespace(stash={})))

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
