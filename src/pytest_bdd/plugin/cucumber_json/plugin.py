import json
import math
import os
import time
from pathlib import Path
from typing import cast

from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter

from pytest_bdd.plugin.cucumber_json.model import Feature
from pytest_bdd.types.json import JSONArray, JSONObject


class LogBDDCucumberJSON:
    """Logging plugin for cucumber like json output."""

    def __init__(self, logfile: str) -> None:
        self.logfile = Path(os.path.expandvars(logfile)).expanduser().resolve()
        self.features: dict[str, JSONObject] = {}

    def _get_result(self, step: JSONObject, report: TestReport, *, error_message: bool = False) -> JSONObject:
        """Get scenario test run result.

        :param step: `Step` step we get result for
        :param report: pytest `Report` object
        :return: `dict` in form {"status": "<passed|failed|skipped>", ["error_message": "<error_message>"]}
        """
        result: JSONObject = {}
        if report.passed or not step["failed"]:  # ignore setup/teardown
            result = {"status": "passed"}
        elif report.failed and step["failed"]:
            result = {
                "status": "failed",
                "error_message": str(report.longrepr) if error_message else "",
            }
        elif report.skipped:
            result = {"status": "skipped"}
        raw_duration = step.get("duration", 0)
        duration = float(raw_duration) if isinstance(raw_duration, (str, int, float)) else 0.0
        result["duration"] = math.floor((10**9) * duration)  # nanosec
        return result

    def _serialize_tags(self, item: JSONObject) -> JSONArray:
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
        raw_tags = item.get("tags", [])
        tags = raw_tags if isinstance(raw_tags, list) else []
        line_number = item.get("line_number", 1)
        line = int(line_number) if isinstance(line_number, (str, int, float)) else 1
        return cast(JSONArray, [{"name": str(tag), "line": line - 1} for tag in tags])

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        try:
            scenario = cast(JSONObject, report.scenario)
        except AttributeError:
            # skip reporting for non-bdd tests
            return

        if not scenario["steps"] or report.when != "call":
            # skip if there isn't a result or scenario has no steps
            return

        def stepmap(step: JSONObject) -> JSONObject:
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

        feature = cast(JSONObject, scenario["feature"])
        feature_filename = str(feature["filename"])
        if feature_filename not in self.features:
            self.features[feature_filename] = {
                "keyword": "Feature",
                "uri": feature["rel_filename"],
                "name": feature["name"] or feature["rel_filename"],
                "id": str(feature["rel_filename"]).lower().replace(" ", "-"),
                "line": feature["line_number"],
                "description": feature["description"],
                "tags": self._serialize_tags(feature),
                "elements": [],
            }

        elements = cast(JSONArray, self.features[feature_filename]["elements"])
        raw_steps = scenario["steps"]
        steps = raw_steps if isinstance(raw_steps, list) else []
        elements.append(
            {
                "keyword": "Scenario",
                "id": report.item["name"],
                "name": scenario["name"],
                "line": scenario["line_number"],
                "description": "",
                "tags": self._serialize_tags(scenario),
                "type": "scenario",
                "steps": cast(JSONArray, [stepmap(cast(JSONObject, step)) for step in steps]),
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
