from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict

from attrs import define

if TYPE_CHECKING:
    from pytest_bdd.model.scenario_run import StepRun

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


__all__ = [
    "RuntimeStepStatus",
    "ScenarioReportData",
    "StepReport",
    "StepReportData",
]
