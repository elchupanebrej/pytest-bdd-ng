"""Reporting functionality.

Collection of the scenario execution statuses, timing and other information
that enriches the pytest test reporting.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import pytest
from attr import Factory, attrib, attrs

from pytest_cuke.model.execution_steps import execution_steps
from pytest_cuke.model.run_access import get_scenario_run

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from pytest_cuke.compatibility.pytest import CallInfo, Item
    from pytest_cuke.model import Feature, Scenario, Step
    from pytest_cuke.model.scenario_run import ScenarioRun


class StepReport:
    """Step execution report."""

    failed: bool = False
    skipped: bool = False
    stopped: float | None = None

    def __init__(self, step: Step) -> None:
        """Step report constructor.

        :param step: Scenario step.
        """
        self.step = step
        self.started = time.perf_counter()
        self.duration_override: float | None = None
        self.status = "passed"
        self.error_message: str | None = None

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
        serialized: dict[str, Any] = {
            "name": getattr(self.step, "name", getattr(self.step, "text", "")),
            "type": step_type,
            "keyword": step_kw,
            "line_number": step_line,
            "failed": self.failed,
            "skipped": self.skipped,
            "status": self.status,
            "duration": self.duration,
            "error_message": self.error_message,
        }
        return serialized

    def finalize(self, failed: bool, skipped: bool = False) -> None:
        """Stop collecting information and finalize the report.

        :param failed: Whether the step execution failed.
        """
        self.stopped = time.perf_counter()
        self.failed = failed
        self.skipped = skipped
        self.status = "failed" if failed else "skipped" if skipped else "passed"

    @property
    def duration(self) -> float:
        """Step execution duration.

        :return: Step execution duration in seconds.
        """
        if self.duration_override is not None:
            return self.duration_override
        if self.stopped is None:
            return 0.0

        return self.stopped - self.started


@attrs
class ScenarioReport:
    """Pickle execution report."""

    feature: Feature = attrib()
    scenario: Scenario = attrib()
    step_reports: list[StepReport] = attrib(default=Factory(list))
    run_id: str = attrib(default="")
    attempt: int = attrib(default=0)
    attempt_id: str = attrib(default="")
    error_message: str | None = attrib(default=None)

    @classmethod
    def from_scenario_run(cls, scenario_run: ScenarioRun) -> ScenarioReport:
        """Build the pytest report from the session-owned execution snapshot."""
        feature = scenario_run.feature
        scenario = scenario_run.scenario
        if feature is None or scenario is None:
            raise RuntimeError("ScenarioRun cannot be reported without its immutable feature and scenario.")
        report = cls(feature=feature, scenario=scenario)
        report.run_id = scenario_run.run_id
        report.attempt = scenario_run.attempt
        report.attempt_id = scenario_run.attempt_id
        report.error_message = str(scenario_run.exception) if scenario_run.exception is not None else None
        for step_run in scenario_run.steps:
            if step_run.step is None:
                continue
            step_report = StepReport(step=step_run.step)
            step_report.duration_override = step_run.duration
            step_report.failed = step_run.status in ("failed", "undefined")
            step_report.skipped = step_run.status == "skipped"
            step_report.status = "unknown" if step_run.status == "interrupted" else step_run.status
            step_report.error_message = (
                str(step_run.exception) if step_run.exception is not None else step_run.failure_reason
            )
            report.add_step_report(step_report)
        if scenario_run.status in ("failed", "undefined"):
            report.fail()
        elif scenario_run.status == "skipped":
            report.skip()
        elif scenario_run.status == "interrupted":
            report.interrupt()
        return report

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

        uri = feature.uri or ""
        if uri.startswith("file:"):
            feat_rel = uri[5:]
        else:
            feat_rel = getattr(feature, "rel_filename", None) or uri or feature.filename or ""

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
                for s in execution_steps(feature, pickle)
            ]
        )

        serialized = {
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
        if source := getattr(pickle, "external_example_source", None):
            serialized["external_examples_source"] = {
                "path": source.path,
                "marker_line": source.marker_line,
                "section_index": source.section_index,
                "row_index": source.row_index,
                "source_line": source.source_line,
            }
        return serialized

    def _skip_unstarted_steps(self, scenario_steps: Sequence[Step]) -> None:
        for step in scenario_steps[len(self.step_reports) :]:
            report = StepReport(step=step)
            report.finalize(failed=False, skipped=True)
            self.add_step_report(report)

    def fail(self) -> None:
        """Stop collecting information and finalize the report as failed."""
        scenario_steps = execution_steps(self.feature, self.scenario)
        if self.step_reports:
            if not any(report.failed for report in self.step_reports):
                self.current_step_report.finalize(failed=True)
                self.current_step_report.error_message = self.error_message
        elif scenario_steps:
            report = StepReport(step=scenario_steps[0])
            report.finalize(failed=True)
            report.error_message = self.error_message
            self.add_step_report(report)
        self._skip_unstarted_steps(scenario_steps)

    def skip(self) -> None:
        """Finalize the current step and all later steps as skipped."""
        scenario_steps = execution_steps(self.feature, self.scenario)
        if self.step_reports:
            self.current_step_report.finalize(failed=False, skipped=True)
        self._skip_unstarted_steps(scenario_steps)

    def interrupt(self) -> None:
        """Record interruption as unknown and keep other step outcomes intact."""
        scenario_steps = execution_steps(self.feature, self.scenario)
        if not self.step_reports and scenario_steps:
            report = StepReport(step=scenario_steps[0])
            report.status = "unknown"
            report.error_message = self.error_message
            self.add_step_report(report)
        elif self.step_reports and not any(report.status == "unknown" for report in self.step_reports):
            has_unstarted_steps = len(self.step_reports) < len(scenario_steps)
            if has_unstarted_steps:
                self._skip_unstarted_steps(scenario_steps)
            current_report = self.current_step_report
            if has_unstarted_steps or current_report.status in ("passed", "skipped"):
                current_report.status = "unknown"
                current_report.failed = False
                current_report.skipped = False
                current_report.error_message = self.error_message
                return
        self._skip_unstarted_steps(scenario_steps)


class ScenarioReporterPlugin:
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call: CallInfo[Any]) -> Generator[Any, Any, None]:
        outcome = yield
        rep = outcome.get_result()
        is_scenario = item.get_closest_marker("pytest_cuke_scenario") is not None
        if not is_scenario:
            return

        scenario_run = get_scenario_run(item)
        if scenario_run is not None and scenario_run.feature is not None and scenario_run.scenario is not None:
            scenario_report = ScenarioReport.from_scenario_run(scenario_run)
            if rep.skipped and scenario_run.status != "skipped":
                scenario_report.skip()
            elif rep.failed and scenario_run.status not in ("failed", "undefined", "interrupted"):
                scenario_report.fail()
            rep.scenario = scenario_report.serialize()
            rep.item = {"name": item.name}
        elif rep.skipped or rep.failed:
            callspec = getattr(item, "callspec", None)
            params = getattr(callspec, "params", {}) if callspec else {}
            feature = params.get("feature") or getattr(item, "feature", None)
            scenario = params.get("scenario") or getattr(item, "scenario", None)
            if feature is not None and scenario is not None:
                scenario_report = ScenarioReport(feature=feature, scenario=scenario)
                if rep.skipped:
                    scenario_report.skip()
                else:
                    scenario_report.fail()
                rep.scenario = scenario_report.serialize()
                rep.item = {"name": item.name}
