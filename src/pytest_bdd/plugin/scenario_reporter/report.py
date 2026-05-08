"""Provide report helpers."""

import time
from typing import Literal, TypedDict

from attrs import define, field
from cucumber_messages import Pickle, PickleStep  # type:ignore[import-untyped]

from pytest_bdd.model.scenario_run import FeatureRuntimeBinding, ReportingContextSnapshot

RuntimeStepStatus = Literal["passed", "failed"]


class StepReportData(TypedDict):
    """Represent step report data state."""

    name: str
    type: str | None
    keyword: str | None
    line_number: int | None
    failed: bool
    status: RuntimeStepStatus
    duration: float


class FeatureReportData(TypedDict):
    """Represent feature report data state."""

    name: str | None
    filename: str
    rel_filename: str | None
    line_number: int | None
    description: str | None
    tags: list[str]


class ScenarioReportData(TypedDict):
    """Represent scenario report data state."""

    steps: list[StepReportData]
    name: str
    line_number: int
    tags: list[str]
    feature: FeatureReportData


def normalize_runtime_step_status(status: str | None, *, failed_fallback: bool) -> RuntimeStepStatus:
    """Normalize runtime step status."""
    normalized = (status or "").strip().lower()
    if normalized == "passed":
        return "passed"
    if normalized == "failed":
        return "failed"
    return "failed" if failed_fallback else "passed"


@define(eq=False)
class StepReport:
    """Step execution report."""

    step: PickleStep = field()
    started: float = field(factory=time.perf_counter)
    failed: bool = field(default=False)
    stopped: float | None = field(default=None)

    def serialize(self, feature_binding: FeatureRuntimeBinding) -> StepReportData:
        """
        Serialize the step execution report.

        :return: Serialized step execution report.
        :rtype: dict
        """
        keyword = getattr(self.step, "keyword", None) or feature_binding.step_keyword(self.step)
        line_number = getattr(self.step, "line_number", None)
        if line_number is None:
            line_number = feature_binding.step_line_number(self.step)
        step_prefix = getattr(self.step, "prefix", None)
        if step_prefix is None:
            step_prefix = feature_binding.step_prefix(self.step)
        return {
            "name": self.step.text,
            "type": step_prefix,
            "keyword": keyword,
            "line_number": line_number,
            "failed": self.failed,
            "status": normalize_runtime_step_status(None, failed_fallback=self.failed),
            "duration": self.duration,
        }

    def finalize(self, *, failed: bool = False) -> None:
        """
        Stop collecting information and finalize the report.

        :param bool failed: Whether the step execution is failed.
        """
        self.stopped = time.perf_counter()
        self.failed = failed

    @property
    def duration(self) -> float:
        """
        Step execution duration.

        :return: Step execution duration.
        :rtype: float
        """
        if self.stopped is None:
            return 0.0

        return self.stopped - self.started


@define
class ScenarioReport:
    """Pickle execution report."""

    feature_binding: FeatureRuntimeBinding = field()
    pickle: Pickle = field()
    step_reports: list[StepReport] = field(factory=list)
    context_snapshot: ReportingContextSnapshot | None = field(default=None)

    @property
    def current_step_report(self) -> StepReport:
        """
        Get current step report.

        :return: Last or current step report.
        :rtype: pytest_bdd.reporting.StepReport
        """
        return self.step_reports[-1]

    def add_step_report(self, step_report: StepReport) -> None:
        """
        Add new step report.

        :param step_report: New current step report.
        :type step_report: pytest_bdd.reporting.StepReport
        """
        self.step_reports.append(step_report)

    def set_context_snapshot(self, context_snapshot: ReportingContextSnapshot | None) -> None:
        """Handle set context snapshot."""
        self.context_snapshot = context_snapshot

    def serialize(self) -> ScenarioReportData:
        """
        Serialize scenario execution report in order to transfer reporting from nodes in the distributed mode.

        :return: Serialized report.
        :rtype: dict
        """
        pickle = self.pickle
        feature_binding = self.feature_binding

        return {
            "steps": [step_report.serialize(self.feature_binding) for step_report in self.step_reports],
            "name": pickle.name,
            "line_number": feature_binding.pickle_line_number(pickle),
            "tags": sorted({tag.name.lstrip("@") for tag in pickle.tags}.difference(feature_binding.tag_names)),
            "feature": {
                "name": feature_binding.name,
                "filename": feature_binding.filename,
                "rel_filename": feature_binding.rel_filename,
                "line_number": feature_binding.line_number,
                "description": feature_binding.description,
                "tags": feature_binding.tag_names,
            },
        }

    def fail(self) -> None:
        """Stop collecting information and finalize the report as failed."""
        self.current_step_report.finalize(failed=True)
        remaining_steps = self.pickle.steps[len(self.step_reports) :]

        # Fail the rest of the steps and make reports.
        for step in remaining_steps:
            report = StepReport(step=step)
            report.finalize(failed=True)
            self.add_step_report(report)
