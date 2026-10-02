"""Reporting functionality.

Collection of the scenario execution statuses, timing and other information
that enriches the pytest test reporting.
"""

from __future__ import annotations

import time
from collections import Counter
from typing import TYPE_CHECKING, Any

import pytest
from attr import Factory, attrib, attrs

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from messages import Pickle, PickleStep
    from pytest_cuke.compatibility.pytest import CallInfo, FixtureRequest, Item, Parser, TerminalReporter
    from pytest_cuke.model import Feature


class StepReport:
    """Step execution report."""

    failed: bool = False
    stopped: float | None = None

    def __init__(self, step: PickleStep) -> None:
        """Step report constructor.

        :param step: PickleStep.
        """
        self.step = step
        self.started = time.perf_counter()

    def serialize(self, feature: Feature) -> dict[str, Any]:
        """Serialize the step execution report.

        :return: Serialized step execution report.
        """
        step_type = getattr(self.step, "type", None) or (
            feature._get_step_prefix(self.step)
            if hasattr(feature, "_get_step_prefix")
            else getattr(self.step, "prefix", "")
        )
        step_kw = getattr(self.step, "keyword", "") or (
            feature._get_step_keyword(self.step) if hasattr(feature, "_get_step_keyword") else ""
        )
        step_line = getattr(self.step, "line", 0) or (
            feature._get_step_line_number(self.step) if hasattr(feature, "_get_step_line_number") else 0
        )
        return {
            "name": getattr(self.step, "name", getattr(self.step, "text", "")),
            "type": step_type,
            "keyword": step_kw,
            "line_number": step_line,
            "failed": self.failed,
            "duration": self.duration,
        }

    def finalize(self, failed: bool) -> None:
        """Stop collecting information and finalize the report.

        :param failed: Whether the step execution failed.
        """
        self.stopped = time.perf_counter()
        self.failed = failed

    @property
    def duration(self) -> float:
        """Step execution duration.

        :return: Step execution duration in seconds.
        """
        if self.stopped is None:
            return 0.0

        return self.stopped - self.started


@attrs
class ScenarioReport:
    """Pickle execution report."""

    feature: Feature = attrib()
    scenario: Pickle = attrib()
    step_reports: list[StepReport] = attrib(default=Factory(list))

    @property
    def current_step_report(self) -> StepReport:
        """Get current step report."""
        return self.step_reports[-1]

    def add_step_report(self, step_report: StepReport) -> None:
        """Add new step report."""
        self.step_reports.append(step_report)

    def serialize(self) -> dict[str, Any]:
        """Serialize scenario execution report in order to transfer reporting from nodes in the distributed mode."""
        pickle = self.scenario
        feature: Feature = self.feature
        pickle_line = getattr(pickle, "line", 0) or (
            feature._get_pickle_line_number(pickle) if hasattr(feature, "_get_pickle_line_number") else 0
        )
        pickle_tags = getattr(pickle, "tag_names", ()) or ()
        feature_tags = getattr(feature, "tag_names", ()) or ()

        feat_rel = getattr(feature, "rel_filename", None)
        if not feat_rel:
            uri = feature.uri or ""
            feat_rel = uri[5:] if uri.startswith("file:") else (uri or feature.filename or "")

        steps_data = (
            [step_report.serialize(self.feature) for step_report in self.step_reports]
            if self.step_reports
            else [
                {
                    "name": getattr(s, "name", getattr(s, "text", "")),
                    "type": getattr(s, "type", None)
                    or (
                        feature._get_step_prefix(s)
                        if hasattr(feature, "_get_step_prefix")
                        else getattr(s, "prefix", "")
                    ),
                    "keyword": getattr(s, "keyword", "")
                    or (feature._get_step_keyword(s) if hasattr(feature, "_get_step_keyword") else ""),
                    "line_number": getattr(s, "line", 0)
                    or (feature._get_step_line_number(s) if hasattr(feature, "_get_step_line_number") else 0),
                    "failed": False,
                    "duration": 0.0,
                }
                for s in getattr(pickle, "steps", ())
            ]
        )

        return {
            "steps": steps_data,
            "name": pickle.name,
            "line_number": pickle_line,
            "tags": sorted(set(pickle_tags).difference(feature_tags)),
            "feature": {
                "name": feature.name,
                "filename": feature.filename or feature.uri,
                "rel_filename": feat_rel,
                "line_number": getattr(feature, "line", getattr(feature, "line_number", 0)),
                "description": getattr(feature, "description", ""),
                "tags": feature_tags,
            },
        }

    def fail(self) -> None:
        """Stop collecting information and finalize the report as failed."""
        self.current_step_report.finalize(failed=True)
        remaining_steps = self.scenario.steps[len(self.step_reports) :]

        # Fail the rest of the steps and make reports.
        for step in remaining_steps:
            report = StepReport(step=step)
            report.finalize(failed=True)
            self.add_step_report(report)


class ScenarioReporterPlugin:
    def __init__(self) -> None:
        self.current_report: ScenarioReport | None = None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call: CallInfo[Any]) -> Generator[Any, Any, None]:
        outcome = yield
        rep = outcome.get_result()
        if call.when != "setup":
            scenario_report: ScenarioReport | None = self.current_report
            if scenario_report is not None:
                rep.scenario = scenario_report.serialize()
                rep.item = {"name": item.name}
        elif rep.skipped:
            callspec = getattr(item, "callspec", None)
            params = getattr(callspec, "params", {}) if callspec else {}
            feature = params.get("feature") or getattr(item, "feature", None)
            scenario = params.get("scenario") or getattr(item, "scenario", None)
            if feature is not None and scenario is not None:
                rep.scenario = ScenarioReport(feature=feature, scenario=scenario).serialize()
                rep.item = {"name": item.name}

    @pytest.hookimpl(tryfirst=True)
    def pytest_cuke_before_scenario(self, request: FixtureRequest, feature: Feature, scenario: Pickle) -> None:
        """Create scenario report for the item."""
        self.current_report = ScenarioReport(feature=feature, scenario=scenario)

    @pytest.hookimpl(tryfirst=True)
    def pytest_cuke_step_error(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Pickle,
        step: PickleStep,
        step_func: Callable[..., Any],
        step_func_args: dict[str, Any],
        exception: Exception,
    ) -> None:
        """Finalize the step report as failed."""
        if self.current_report is not None:
            self.current_report.fail()

    @pytest.hookimpl(tryfirst=True)
    def pytest_cuke_before_step(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Pickle,
        step: PickleStep,
        step_func: Callable[..., Any],
    ) -> None:
        """Store step start time."""
        if self.current_report is not None:
            self.current_report.add_step_report(StepReport(step=step))

    @pytest.hookimpl(tryfirst=True)
    def pytest_cuke_after_step(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Pickle,
        step: PickleStep,
        step_func: Callable[..., Any],
        step_func_args: dict[str, Any],
    ) -> None:
        """Finalize the step report as successful."""
        if self.current_report is not None:
            self.current_report.current_step_report.finalize(failed=False)


def add_summary_options(parser: Parser) -> None:
    """Register the optional final scenario summary setting."""
    group = parser.getgroup("cuke reporting", "Scenario summary")
    group.addoption(
        "--cuke-summary",
        action="store_true",
        dest="cuke_summary",
        default=None,
        help="print the final passed, failed, and skipped scenario counts",
    )
    parser.addini("cuke_summary", "Show a scenario summary after the run.", default=False, type="bool")


class ScenarioSummaryPlugin:
    """Print counts for completed BDD scenarios at the end of a pytest run."""

    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        scenario_reports = [
            report
            for outcome in ("passed", "failed", "skipped")
            for report in terminalreporter.stats.get(outcome, ())
            if hasattr(report, "scenario") and getattr(report, "when", None) == "call"
        ]
        if not scenario_reports:
            return

        counts = Counter(report.outcome for report in scenario_reports)
        terminalreporter.write_sep("=", "pytest-cuke scenarios")
        terminalreporter.write_line(
            f"{counts['passed']} passed BDD scenarios, {counts['failed']} failed, {counts['skipped']} skipped"
        )
