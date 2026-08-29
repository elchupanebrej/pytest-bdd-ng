from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal, TypedDict

from attrs import define, field

if TYPE_CHECKING:
    from pytest_bdd.model.scenario_run import ScenarioRun, StepRun

RuntimeStepStatus = Literal["passed", "failed", "skipped", "undefined"]


class StepReportData(TypedDict, total=False):
    name: str
    type: str | None
    keyword: str | None
    line_number: int | None
    failed: bool
    status: str
    duration: float
    error_message: str | None


class ScenarioReportData(TypedDict, total=False):
    scenario_name: str
    feature_name: str | None
    steps: list[StepReportData]
    failed: bool
    status: str
    duration: float
    error_message: str | None
    run_id: str
    attempt: int


@define(slots=True)
class StepReport:
    name: str = ""
    type: str | None = None
    keyword: str | None = None
    line_number: int | None = None
    failed: bool = False
    status: str = "passed"
    duration: float = 0.0
    error_message: str | None = None

    @classmethod
    def from_step_run(cls, step_run: StepRun) -> StepReport:
        step = step_run.step
        name = getattr(step, "name", getattr(step, "text", "")) if step is not None else ""
        keyword = getattr(step, "keyword", getattr(step, "type", None)) if step is not None else None
        line = getattr(step, "line", getattr(step, "line_number", None)) if step is not None else None
        step_type = getattr(step, "type", keyword) if step is not None else None
        failed = step_run.status == "failed"
        err_msg = str(step_run.exception) if step_run.exception is not None else step_run.failure_reason
        return cls(
            name=name,
            type=step_type,
            keyword=keyword,
            line_number=line,
            failed=failed,
            status=step_run.status,
            duration=step_run.duration,
            error_message=err_msg,
        )

    def to_dict(self) -> StepReportData:
        return {
            "name": self.name,
            "type": self.type,
            "keyword": self.keyword,
            "line_number": self.line_number,
            "failed": self.failed,
            "status": self.status,
            "duration": self.duration,
            "error_message": self.error_message,
        }

    def serialize(self) -> StepReportData:
        return self.to_dict()


@define(slots=True)
class ScenarioReport:
    scenario_name: str = ""
    feature_name: str | None = None
    steps: list[StepReport] = field(factory=list)
    failed: bool = False
    status: str = "passed"
    duration: float = 0.0
    error_message: str | None = None
    run_id: str = ""
    attempt: int = 0

    @classmethod
    def from_scenario_run(cls, scenario_run: ScenarioRun) -> ScenarioReport:
        scenario = scenario_run.scenario
        sc_name = getattr(scenario, "name", "") if scenario is not None else ""
        feature = getattr(scenario, "feature", None) if scenario is not None else None
        feat_name = getattr(feature, "name", None) if feature is not None else None

        steps = [StepReport.from_step_run(st) for st in scenario_run.steps]
        failed = scenario_run.status == "failed" or any(s.failed for s in steps)
        err_msg = str(scenario_run.exception) if scenario_run.exception is not None else None
        if not err_msg and any(s.error_message for s in steps if s.failed):
            err_msg = next(s.error_message for s in steps if s.failed and s.error_message)

        total_duration = scenario_run.duration or sum(s.duration for s in steps)
        status = "failed" if failed else scenario_run.status

        return cls(
            scenario_name=sc_name,
            feature_name=feat_name,
            steps=steps,
            failed=failed,
            status=status,
            duration=total_duration,
            error_message=err_msg,
            run_id=scenario_run.run_id,
            attempt=scenario_run.attempt,
        )

    def add_step_report(self, step_report: StepReport) -> StepReport:
        self.steps.append(step_report)
        if step_report.failed:
            self.failed = True
            self.status = "failed"
            if not self.error_message:
                self.error_message = step_report.error_message
        self.duration += step_report.duration
        return step_report

    def fail(self, error_message: str | None = None) -> None:
        self.failed = True
        self.status = "failed"
        self.error_message = error_message

    def to_dict(self) -> ScenarioReportData:
        return {
            "scenario_name": self.scenario_name,
            "feature_name": self.feature_name,
            "steps": [s.to_dict() for s in self.steps],
            "failed": self.failed,
            "status": self.status,
            "duration": self.duration,
            "error_message": self.error_message,
            "run_id": self.run_id,
            "attempt": self.attempt,
        }

    def serialize(self) -> ScenarioReportData:
        return self.to_dict()

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


__all__ = [
    "RuntimeStepStatus",
    "ScenarioReport",
    "ScenarioReportData",
    "StepReport",
    "StepReportData",
]
