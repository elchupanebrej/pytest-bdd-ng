"""Cucumber json output formatter."""

from __future__ import annotations

import json
import math
import os
import time
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast, runtime_checkable

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Config as BaseConfig
    from pytest_bdd.compatibility.pytest import Parser, TerminalReporter, TestReport

    @runtime_checkable
    class LogBDDCucumberJSONProtocol(Protocol):
        _bddcucumberjson: LogBDDCucumberJSON

    class Config(BaseConfig, LogBDDCucumberJSONProtocol):  # type: ignore[misc]
        pass


def add_options(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Cucumber JSON")
    group.addoption(
        "--cucumberjson",
        "--cucumber-json",
        action="store",
        dest="cucumber_json_path",
        metavar="path",
        default=None,
        help="create cucumber json style report file at given path.",
    )


def configure(config: Config | BaseConfig) -> None:
    cucumber_json_path = config.option.cucumber_json_path
    # prevent opening json log on worker nodes (xdist)
    if cucumber_json_path and not hasattr(config, "workerinput"):
        cast("Config", config)._bddcucumberjson = LogBDDCucumberJSON(cucumber_json_path)
        config.pluginmanager.register(cast("Config", config)._bddcucumberjson)


def unconfigure(config: Config | BaseConfig) -> None:
    xml = getattr(config, "_bddcucumberjson", None)
    if xml is not None:
        _config = cast("Config", config)
        del _config._bddcucumberjson
        config.pluginmanager.unregister(xml)


class ElementType(str, Enum):
    background = "background"
    scenario = "scenario"


class Argument(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    value: str | None = None
    offset: float | None = None


class Status(str, Enum):
    passed = "passed"
    failed = "failed"
    skipped = "skipped"
    undefined = "undefined"
    pending = "pending"
    unknown = "unknown"


class DocString(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    line: float | None = None
    value: str | None = None
    content_type: str | None = None


class DataTableRow(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    cells: list[str]


class Tag(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    name: str
    line: float | None = None


class Match(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    location: str | None = None
    arguments: list[Argument] | None = None


class Result(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    duration: float | None = None
    status: Status
    error_message: str | None = None


class Step(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    keyword: str | None = None
    line: float | None = None
    match: Match | None = None
    name: str | None = None
    result: Result | None = None
    doc_string: DocString | None = None
    rows: list[DataTableRow] | None = None


class Hook(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    match: Match | None = None
    result: Result


class Element(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    start_timestamp: str | None = None
    line: float | None = None
    id: str | None = None
    type: ElementType | None = None
    keyword: str | None = None
    name: str | None = None
    description: str | None = None
    before: list[Hook] | None = None
    steps: list[Step] | None = None
    after: list[Hook] | None = None
    tags: list[Tag] | None = None


class Feature(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    uri: str | None = None
    id: str | None = None
    line: float | None = None
    keyword: str | None = None
    name: str | None = None
    description: str | None = None
    elements: list[Element] | None = None
    tags: list[Tag] | None = None


class CucumberJson(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    implementation: str | None = None
    features: list[Feature] | None = None


class LogBDDCucumberJSON:
    """Logging plugin for cucumber like json output."""

    def __init__(self, logfile: str | Path) -> None:
        logfile_str = os.path.expanduser(os.path.expandvars(str(logfile)))
        self.logfile = os.path.normpath(os.path.abspath(logfile_str))
        self.features: dict[str, dict[str, Any]] = {}
        self.suite_start_time: float = 0.0

    def _get_result(self, step: dict[str, Any], report: TestReport, error_message: bool = False) -> dict[str, Any]:
        """Get scenario test run result.

        :param step: Step dict we get result for
        :param report: pytest `TestReport` object
        :param error_message: whether to include error message
        :return: `dict` in form {"status": "<passed|failed|skipped>", ["error_message": "<error_message>"]}
        """
        result: dict[str, Any] = {}
        if report.skipped:
            result = {"status": "skipped"}
        elif report.failed and step.get("failed", False):
            result = {"status": "failed", "error_message": str(report.longrepr) if error_message else ""}
        elif report.passed or not step.get("failed", False):  # ignore setup/teardown
            result = {"status": "passed"}
        else:
            result = {"status": "unknown"}
        result["duration"] = math.floor((10**9) * step.get("duration", 0.0))  # nanosec
        return result

    def _serialize_tags(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        """Serialize item's tags.

        :param item: json-serialized `Scenario` or `Feature`.
        :return: `list` of `dict`
        """
        return [{"name": tag, "line": item["line_number"] - 1} for tag in item.get("tags", [])]

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        try:
            scenario = report.scenario
        except AttributeError:
            # skip reporting for non-bdd tests
            return

        if not scenario.get("steps") or report.when != "call":
            # skip if there isn't a result or scenario has no steps
            return

        def stepmap(step: dict[str, Any]) -> dict[str, Any]:
            error_message = False
            if step.get("failed") and not scenario.setdefault("failed", False):
                scenario["failed"] = True
                error_message = True

            step_name = step["name"]

            return {
                "keyword": step.get("keyword", ""),
                "name": step_name,
                "line": step.get("line_number"),
                "match": {"location": ""},
                "result": self._get_result(step, report, error_message),
            }

        feature_info = scenario["feature"]
        filename = feature_info["filename"]
        if filename not in self.features:
            self.features[filename] = {
                "keyword": "Feature",
                "uri": feature_info["rel_filename"],
                "name": feature_info["name"] or feature_info["rel_filename"],
                "id": feature_info["rel_filename"].lower().replace(" ", "-"),
                "line": feature_info["line_number"],
                "description": feature_info.get("description", ""),
                "tags": self._serialize_tags(feature_info),
                "elements": [],
            }

        item_name = getattr(report, "item", {}).get("name", scenario["name"])
        self.features[filename]["elements"].append(
            {
                "keyword": "Scenario",
                "id": item_name,
                "name": scenario["name"],
                "line": scenario["line_number"],
                "description": "",
                "tags": self._serialize_tags(scenario),
                "type": "scenario",
                "steps": [stepmap(step) for step in scenario["steps"]],
            }
        )

    def pytest_sessionstart(self) -> None:
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self) -> None:
        Path(self.logfile).parent.mkdir(parents=True, exist_ok=True)
        with open(self.logfile, "w", encoding="utf-8") as logfile:
            for feature in self.features.values():
                Feature.model_validate(feature)
            logfile.write(json.dumps(list(self.features.values())))

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        terminalreporter.write_sep("-", f"generated json file: {self.logfile}")
