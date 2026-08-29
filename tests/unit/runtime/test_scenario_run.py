from __future__ import annotations

from pytest_bdd.model.scenario_run import StepRun


def test_step_run_lifecycle_and_status() -> None:
    step_run = StepRun(id="step-1")
    assert step_run.status == "passed"
    assert step_run.duration == 0.0

    step_run.start(timestamp=10.0)
    assert step_run.start_time == 10.0

    step_run.pass_step(result="ok", duration=1.5)
    assert step_run.status == "passed"
    assert step_run.result == "ok"
    assert step_run.duration == 1.5

    err = ValueError("boom")
    step_run.fail(exception=err, duration=0.2)
    assert step_run.status == "failed"
    assert step_run.exception is err
    assert step_run.failure_reason == "ValueError"

    step_run.skip(reason="not implemented", duration=0.0)
    assert step_run.status == "skipped"
    assert step_run.failure_reason == "not implemented"
