import time
from typing import Any

from attr import Factory, attrib, attrs

from messages import Pickle, PickleStep
from pytest_bdd.model import Feature


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

    def serialize(self, feature: Feature) -> dict[str, Any]:
        """Serialize the step execution report.

        :return: Serialized step execution report.
        :rtype: dict
        """
        return {
            "name": self.step.text,
            "type": feature._get_step_prefix(self.step),
            "keyword": feature._get_step_keyword(self.step),
            "line_number": feature._get_step_line_number(self.step),
            "failed": self.failed,
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
    step_reports: list[StepReport] = attrib(default=Factory(list))

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

    def serialize(self) -> dict[str, Any]:
        """Serialize scenario execution report in order to transfer reporting from nodes in the distributed mode.

        :return: Serialized report.
        :rtype: dict
        """
        pickle = self.scenario
        feature: Feature = self.feature

        return {
            "steps": [step_report.serialize(self.feature) for step_report in self.step_reports],
            "name": pickle.name,
            "line_number": feature._get_pickle_line_number(pickle),
            "tags": sorted(set(feature._get_pickle_tag_names(pickle)).difference(feature.tag_names)),
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
