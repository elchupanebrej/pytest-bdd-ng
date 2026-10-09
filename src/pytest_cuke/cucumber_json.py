"""Cucumber json output formatter."""

from __future__ import annotations

import json
import math
import os
import time
from argparse import ArgumentTypeError
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Protocol, cast, runtime_checkable

from pydantic import BaseModel, ConfigDict

from pytest_cuke.model.session_run import RunContext
from pytest_cuke.reporting import ScenarioReport

if TYPE_CHECKING:  # pragma: no cover
    from pytest_cuke.compatibility.pytest import Config as BaseConfig
    from pytest_cuke.compatibility.pytest import Parser, TerminalReporter, TestReport

    @runtime_checkable
    class LogBDDCucumberJSONProtocol(Protocol):
        _bddcucumberjson: LogBDDCucumberJSON

    class Config(BaseConfig, LogBDDCucumberJSONProtocol):  # type: ignore[misc]  # The type-only adapter adds the optional reporter protocol to pytest Config.
        pass


DEFAULT_CUCUMBER_JSON_PATH = "cucumber.json"
CUCUMBER_JSON_BACKENDS = ("cucumber", "native")


def add_options(parser: Parser) -> None:
    """Add canonical JSON output and backend settings."""
    group = parser.getgroup("cuke", "Cucumber JSON")
    group.addoption(
        "--cuke-json",
        action="store",
        nargs="?",
        const=DEFAULT_CUCUMBER_JSON_PATH,
        dest="cuke_json",
        metavar="PATH",
        default=None,
        type=_required_output_path,
        help="write the message-driven Cucumber JSON report to PATH (default: cucumber.json)",
    )
    group.addoption(
        "--cuke-json-backend",
        action="store",
        choices=CUCUMBER_JSON_BACKENDS,
        dest="cuke_json_backend",
        metavar="BACKEND",
        default=None,
        help="select the Cucumber JSON backend: cucumber (default) or native",
    )
    parser.addini("cuke_json", "Cucumber JSON report path.", default="", type="string")
    parser.addini("cuke_json_backend", "Cucumber JSON backend (cucumber or native).", default="cucumber", type="string")


def configured_cucumber_json_output_value(config: BaseConfig) -> str | None:
    """Return the raw selected Cucumber JSON destination, if enabled."""
    option = getattr(getattr(config, "option", None), "cuke_json", None)
    if option is None:
        getini = getattr(config, "getini", None)
        option = getini("cuke_json") if callable(getini) else None
    if not isinstance(option, (str, Path)) or not option:
        return None
    return str(option)


def _required_output_path(value: str) -> str:
    if not value:
        raise ArgumentTypeError("Cucumber JSON output path must not be empty")
    return value


def configured_cucumber_json_backend(config: BaseConfig) -> str:
    """Return the selected Cucumber JSON backend, validating its ini value."""
    option = getattr(getattr(config, "option", None), "cuke_json_backend", None)
    if option is None:
        getini = getattr(config, "getini", None)
        option = getini("cuke_json_backend") if callable(getini) else None
    backend = option if isinstance(option, str) and option else "cucumber"
    if backend not in CUCUMBER_JSON_BACKENDS:
        from pytest import (  # noqa: PLC0415 -- standalone replay does not import pytest unless this live setting is invalid.
            UsageError,
        )

        choices = ", ".join(CUCUMBER_JSON_BACKENDS)
        raise UsageError(f"Invalid cuke_json_backend {backend!r}; expected one of: {choices}.")
    return backend


def normalize_cucumber_json_path(logfile: str | Path) -> Path:
    """Normalize a Cucumber JSON destination using the logger's path rules."""
    logfile_str = os.path.expanduser(os.path.expandvars(str(logfile)))
    return Path(os.path.normpath(os.path.abspath(logfile_str)))


def configured_cucumber_json_output_path(config: BaseConfig) -> Path | None:
    """Return the effective CLI/ini Cucumber JSON destination, if selected."""
    option = configured_cucumber_json_output_value(config)
    if option is None:
        return None
    return normalize_cucumber_json_path(option)


def configure(config: Config | BaseConfig) -> None:
    if configured_cucumber_json_output_value(config) is None:
        return
    if configured_cucumber_json_backend(config) != "native":
        return
    cucumber_json_path = configured_cucumber_json_output_path(config)
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


class ExternalExamplesRowSource(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    path: str
    marker_line: int
    section_index: int
    row_index: int
    source_line: int


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
    external_examples_source: ExternalExamplesRowSource | None = None


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
        self.logfile = str(normalize_cucumber_json_path(logfile))
        self.features: dict[str, dict[str, Any]] = {}
        self.reported_elements_by_nodeid: dict[str, dict[str, Any]] = {}
        self.suite_start_time: float = 0.0

    def _get_result(self, step: dict[str, Any], report: TestReport, error_message: bool = False) -> dict[str, Any]:
        """Get scenario test run result.

        :param step: Step dict we get result for
        :param report: pytest `TestReport` object
        :param error_message: whether to include error message
        :return: `dict` with the step status and an optional error message. Supported statuses are `passed`, `failed`,
            `skipped`, `undefined`, and `unknown`.
        """
        result: dict[str, Any] = {}
        if step.get("skipped", False) or step.get("status") == "skipped":
            result = {"status": "skipped"}
        elif step.get("status") == "undefined":
            result = {"status": "undefined"}
            if message := step.get("error_message"):
                result["error_message"] = message
        elif step.get("status") == "failed" or (report.failed and step.get("failed", False)):
            message = step.get("error_message")
            if not message and error_message:
                message = str(report.longrepr)
            result = {"status": "failed"}
            if message:
                result["error_message"] = message
        elif step.get("status") == "unknown":
            result = {"status": "unknown"}
            if message := step.get("error_message"):
                result["error_message"] = message
        elif report.skipped:
            result = {"status": "skipped"}
        elif step.get("status") == "passed" or report.passed or not step.get("failed", False):  # ignore setup/teardown
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

        if not scenario.get("steps"):
            # skip if scenario has no steps
            return

        if report.when not in ("call", "setup", "teardown") or (
            report.when == "setup" and not (report.skipped or report.failed)
        ):
            return
        nodeid = getattr(report, "nodeid", None)

        def stepmap(step: dict[str, Any]) -> dict[str, Any]:
            error_message = False
            if step.get("failed") and not scenario.setdefault("failed", False) and not report.passed:
                scenario["failed"] = True
                error_message = True

            step_name = step["name"]

            return {
                "keyword": step.get("keyword", "").strip(),
                "name": step_name,
                "line": step.get("line_number"),
                "match": {"location": ""},
                "result": self._get_result(step, report, error_message),
            }

        feature_info = scenario["feature"]
        filename = feature_info["filename"]
        rel_filename = feature_info.get("rel_filename") or feature_info.get("filename") or ""
        if rel_filename.startswith("file:"):
            rel_filename = rel_filename[5:]
        if filename not in self.features:
            self.features[filename] = {
                "keyword": "Feature",
                "uri": rel_filename,
                "name": feature_info["name"] or rel_filename,
                "id": rel_filename,
                "line": feature_info["line_number"],
                "description": feature_info.get("description", ""),
                "tags": self._serialize_tags(feature_info),
                "elements": [],
            }

        item_name = getattr(report, "item", {}).get("name", scenario["name"])
        sc_name = scenario["name"].split("[table_rows:")[0].split("[external_examples:")[0]
        element: dict[str, Any] = {
            "keyword": "Scenario",
            "id": item_name,
            "name": sc_name,
            "line": scenario["line_number"],
            "description": "",
            "tags": self._serialize_tags(scenario),
            "type": "scenario",
            "steps": [stepmap(step) for step in scenario["steps"]],
        }
        if external_source := scenario.get("external_examples_source"):
            element["external_examples_source"] = external_source
        existing_element = self.reported_elements_by_nodeid.get(nodeid) if isinstance(nodeid, str) else None
        if report.when == "teardown" and existing_element is not None:
            existing_element["steps"] = element["steps"]
        else:
            self.features[filename]["elements"].append(element)
            if isinstance(nodeid, str):
                self.reported_elements_by_nodeid[nodeid] = element

    def pytest_sessionstart(self) -> None:
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self, session: Any) -> None:
        """Reconcile scenario artifacts with their final runtime snapshots."""
        run_context = RunContext.find_in_config(session.config)
        if run_context is not None:
            for nodeid, scenario_run in run_context.scenario_runs_by_nodeid.items():
                if scenario_run.scenario is None or scenario_run.status not in (
                    "passed",
                    "failed",
                    "skipped",
                    "undefined",
                    "interrupted",
                ):
                    continue
                report = SimpleNamespace(
                    nodeid=nodeid,
                    when="teardown",
                    passed=scenario_run.status == "passed",
                    failed=scenario_run.status in ("failed", "undefined"),
                    skipped=scenario_run.status == "skipped",
                    item={"name": scenario_run.scenario.name},
                    scenario=ScenarioReport.from_scenario_run(scenario_run).serialize(),
                    longrepr=None,
                )
                self.pytest_runtest_logreport(cast("TestReport", report))

        Path(self.logfile).parent.mkdir(parents=True, exist_ok=True)
        with open(self.logfile, "w", encoding="utf-8") as logfile:
            for feature in self.features.values():
                Feature.model_validate(feature)
            logfile.write(json.dumps(list(self.features.values())))

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        terminalreporter.write_sep("-", f"generated json file: {self.logfile}")
