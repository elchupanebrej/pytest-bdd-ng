from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, ClassVar

from attrs import define, field

from pytest_bdd.model.stash_access import StashBound

if TYPE_CHECKING:
    from pytest_bdd.model.scenario import Scenario
    from pytest_bdd.model.step import Step


@define(slots=True)
class ExecutionContext:
    parameters: dict[str, Any] = field(factory=dict)
    step_state: dict[str, Any] = field(factory=dict)
    user_data: dict[str, Any] = field(factory=dict)
    fixtures: dict[str, Any] = field(factory=dict)

    def get_param(self, name: str, default: Any = None) -> Any:
        return self.parameters.get(name, default)

    def set_param(self, name: str, value: Any) -> None:
        self.parameters[name] = value

    def get_step_result(self, step_id: str, default: Any = None) -> Any:
        return self.step_state.get(step_id, default)

    def set_step_result(self, step_id: str, value: Any) -> None:
        self.step_state[step_id] = value

    def clone(self) -> ExecutionContext:
        return ExecutionContext(
            parameters=dict(self.parameters),
            step_state=dict(self.step_state),
            user_data=dict(self.user_data),
            fixtures=dict(self.fixtures),
        )


@define(slots=True)
class StepRun:
    step: Step | Any | None = None
    status: str = "passed"
    start_time: float | None = None
    duration: float = 0.0
    result: Any = None
    exception: BaseException | None = None
    failure_reason: str | None = None
    id: str = ""
    test_step_id: str | None = None

    def start(self, timestamp: float | None = None) -> None:
        self.start_time = time.perf_counter() if timestamp is None else timestamp

    def finish(
        self,
        status: str = "passed",
        duration: float = 0.0,
        result: Any = None,
        exception: BaseException | None = None,
        failure_reason: str | None = None,
    ) -> None:
        self.status = status
        self.duration = duration
        self.result = result
        self.exception = exception
        self.failure_reason = failure_reason

    def fail(
        self,
        exception: BaseException,
        failure_reason: str | None = None,
        duration: float = 0.0,
    ) -> None:
        self.finish(
            status="failed",
            duration=duration,
            exception=exception,
            failure_reason=failure_reason or type(exception).__name__,
        )

    def pass_step(self, result: Any = None, duration: float = 0.0) -> None:
        self.finish(status="passed", duration=duration, result=result)

    def skip(self, reason: str | None = None, duration: float = 0.0) -> None:
        self.finish(status="skipped", duration=duration, failure_reason=reason)


@define(slots=True)
class ScenarioRun(StashBound):
    STASH_KEY: ClassVar[str] = "pytest_bdd_scenario_run"

    scenario: Scenario | Any | None = None
    steps: list[StepRun] = field(factory=list)
    context: ExecutionContext = field(factory=ExecutionContext)
    run_id: str = ""
    attempt: int = 0
    test_case_started_id: str = ""
    status: str = "pending"
    start_time: float | None = None
    duration: float = 0.0
    exception: BaseException | None = None

    def add_step_run(self, step_run: StepRun) -> StepRun:
        self.steps.append(step_run)
        return step_run

    def get_step_run(self, step_or_id: Any) -> StepRun | None:
        for s in self.steps:
            if step_or_id in (s.id, s.test_step_id) or s.step is step_or_id:
                return s
        return None

    def start(self, timestamp: float | None = None) -> None:
        self.start_time = time.perf_counter() if timestamp is None else timestamp
        self.status = "running"

    def finish(
        self,
        status: str = "passed",
        duration: float = 0.0,
        exception: BaseException | None = None,
    ) -> None:
        self.status = status
        self.duration = duration
        self.exception = exception

    def fail(self, exception: BaseException, duration: float = 0.0) -> None:
        self.finish(status="failed", duration=duration, exception=exception)

    def pass_scenario(self, duration: float = 0.0) -> None:
        self.finish(status="passed", duration=duration)

    def skip(self, duration: float = 0.0) -> None:
        self.finish(status="skipped", duration=duration)


__all__ = [
    "ExecutionContext",
    "ScenarioRun",
    "StepRun",
]
