import time
from typing import Any, Final, Literal

from attr import Factory, attrib, attrs
from cucumber_messages import Pickle, PickleStep  # type:ignore[import-untyped]

from pytest_bdd.model.scenario_run import ReportingContextSnapshot
from pytest_bdd.model.gherkin_document import Feature

RuntimeStepStatus = Literal["passed", "failed"]
CONTROLLED_RUNTIME_STEP_STATUSES: Final[tuple[RuntimeStepStatus, ...]] = ("passed", "failed")


def normalize_runtime_step_status(status: str | None, *, failed_fallback: bool) -> RuntimeStepStatus:
    normalized = (status or "").strip().lower()
    if normalized in CONTROLLED_RUNTIME_STEP_STATUSES:
        return normalized  # type: ignore[return-value]
    return "failed" if failed_fallback else "passed"


class StepReport:
    """Step execution report."""

    failed = False
    stopped = None

    def __init__(self, step: PickleStep) -> None:
        """Step report constructor.

        :param Step step: Step.
        """
        self.step = step
        self.started = time.perf_counter()

    def serialize(self, feature: Feature, *, config: Any | None = None) -> dict[str, Any]:
        """Serialize the step execution report.

        :return: Serialized step execution report.
        :rtype: dict
        """
        keyword = getattr(self.step, "keyword", None) or feature._get_step_keyword(self.step, config=config)
        line_number = getattr(self.step, "line_number", None)
        if line_number is None:
            line_number = feature._get_step_line_number(self.step, config=config)
        step_prefix = getattr(self.step, "prefix", None)
        if step_prefix is None:
            step_prefix = feature._get_step_prefix(self.step, config=config)
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
        """Stop collecting information and finalize the report.

        :param bool failed: Whether the step execution is failed.
        """
        self.stopped = time.perf_counter()
        self.failed = failed

    @property
    def duration(self) -> float:
        """Step execution duration.

        :return: Step execution duration.
        :rtype: float
        """
        if self.stopped is None:
            return 0

        return self.stopped - self.started


@attrs
class ScenarioReport:
    """Pickle execution report."""

    feature: Feature = attrib()
    scenario: Pickle = attrib()
    config: Any | None = attrib(default=None)
    step_reports: list[StepReport] = attrib(default=Factory(list))
    context_snapshot: ReportingContextSnapshot | None = attrib(default=None)

    @property
    def current_step_report(self) -> StepReport:
        """Get current step report.

        :return: Last or current step report.
        :rtype: pytest_bdd.reporting.StepReport
        """
        return self.step_reports[-1]

    def add_step_report(self, step_report: StepReport) -> None:
        """Add new step report.

        :param step_report: New current step report.
        :type step_report: pytest_bdd.reporting.StepReport
        """
        self.step_reports.append(step_report)

    def set_context_snapshot(self, context_snapshot: ReportingContextSnapshot | None) -> None:
        self.context_snapshot = context_snapshot

    def serialize(self) -> dict[str, Any]:
        """Serialize scenario execution report in order to transfer reporting from nodes in the distributed mode.

        :return: Serialized report.
        :rtype: dict
        """
        pickle = self.scenario
        feature: Feature = self.feature

        return {
            "steps": [step_report.serialize(self.feature, config=self.config) for step_report in self.step_reports],
            "name": pickle.name,
            "line_number": feature._get_pickle_line_number(pickle, config=self.config),
            "tags": sorted(set(feature.get_pickle_tag_names(pickle)).difference(feature.tag_names)),
            "feature": {
                "name": feature.name,
                "filename": feature.filename,
                "rel_filename": feature.rel_filename,
                "line_number": feature.line_number,
                "description": feature.description,
                "tags": feature.tag_names,
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
