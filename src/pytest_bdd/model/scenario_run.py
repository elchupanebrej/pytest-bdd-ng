from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from attrs import define

if TYPE_CHECKING:
    from pytest_bdd.model.step import Step


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


__all__ = ["StepRun"]
