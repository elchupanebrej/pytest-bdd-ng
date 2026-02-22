import json
import math
import os
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter

from pytest_bdd.plugin.cucumber_json.model import Feature


class LogBDDCucumberJSON:
    """Logging plugin for cucumber like json output."""

    def __init__(self, logfile: str) -> None:
        self.logfile = Path(os.path.expandvars(logfile)).expanduser().resolve()
        self.features: dict[str, dict] = {}

    def _get_result(self, step: dict[str, Any], report: TestReport, *, error_message: bool = False) -> dict[str, Any]:
        """Get scenario test run result.

        :param step: `Step` step we get result for
        :param report: pytest `Report` object
        :return: `dict` in form {"status": "<passed|failed|skipped>", ["error_message": "<error_message>"]}
        """
        result: dict[str, Any] = {}
        if report.passed or not step["failed"]:  # ignore setup/teardown
            result = {"status": "passed"}
        elif report.failed and step["failed"]:
            result = {
                "status": "failed",
                "error_message": str(report.longrepr) if error_message else "",
            }
        elif report.skipped:
            result = {"status": "skipped"}
        result["duration"] = math.floor((10**9) * step["duration"])  # nanosec
        return result

    def _serialize_tags(self, item: dict[str, Any]) -> Sequence[dict[str, Any]]:
        """Serialize item's tags.

        :param item: json-serialized `Scenario` or `Feature`.
        :return: `list` of `dict` in the form of:
            [
                {
                    "name": "<tag>",
                    "line": 2,
                }
            ]
        """
        return [{"name": tag, "line": item["line_number"] - 1} for tag in item["tags"]]

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        try:
            scenario = report.scenario
        except AttributeError:
            # skip reporting for non-bdd tests
            return

        if not scenario["steps"] or report.when != "call":
            # skip if there isn't a result or scenario has no steps
            return

        def stepmap(step: dict[str, Any]) -> dict[str, Any]:
            error_message = False
            if step["failed"] and not scenario.setdefault("failed", False):
                scenario["failed"] = True
                error_message = True

            step_name = step["name"]

            return {
                "keyword": step["keyword"],
                "name": step_name,
                "line": step["line_number"],
                "match": {"location": ""},
                "result": self._get_result(step, report, error_message=error_message),
            }

        if scenario["feature"]["filename"] not in self.features:
            self.features[scenario["feature"]["filename"]] = {
                "keyword": "Feature",
                "uri": scenario["feature"]["rel_filename"],
                "name": scenario["feature"]["name"] or scenario["feature"]["rel_filename"],
                "id": scenario["feature"]["rel_filename"].lower().replace(" ", "-"),
                "line": scenario["feature"]["line_number"],
                "description": scenario["feature"]["description"],
                "tags": self._serialize_tags(scenario["feature"]),
                "elements": [],
            }

        self.features[scenario["feature"]["filename"]]["elements"].append(
            {
                "keyword": "Scenario",
                "id": report.item["name"],
                "name": scenario["name"],
                "line": scenario["line_number"],
                "description": "",
                "tags": self._serialize_tags(scenario),
                "type": "scenario",
                "steps": [stepmap(step) for step in scenario["steps"]],
            },
        )

    def pytest_sessionstart(self) -> None:
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self) -> None:
        for feature in self.features.values():
            Feature.model_validate(feature)
        Path(self.logfile).write_text(json.dumps(list(self.features.values())), encoding="utf-8")

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        terminalreporter.write_sep("-", f"generated json file: {self.logfile}")
