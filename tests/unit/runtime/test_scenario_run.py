from __future__ import annotations

from pytest_bdd.model.scenario_run import ExecutionContext, ScenarioRun, StepRun
from pytest_bdd.model.stash_access import SimpleStash


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


def test_execution_context_and_scenario_run() -> None:
    ctx = ExecutionContext()
    ctx.set_param("x", 42)
    ctx.set_step_result("st-1", "result-1")
    assert ctx.get_param("x") == 42
    assert ctx.get_step_result("st-1") == "result-1"

    cloned = ctx.clone()
    cloned.set_param("x", 99)
    assert ctx.get_param("x") == 42
    assert cloned.get_param("x") == 99

    sc_run = ScenarioRun(run_id="run-1", context=ctx)
    assert sc_run.status == "pending"

    st_run = StepRun(id="step-1")
    sc_run.add_step_run(st_run)
    assert sc_run.get_step_run("step-1") is st_run
    assert sc_run.get_step_run("missing") is None

    sc_run.start(timestamp=100.0)
    assert sc_run.status == "running"
    assert sc_run.start_time == 100.0

    sc_run.pass_scenario(duration=2.0)
    assert sc_run.status == "passed"
    assert sc_run.duration == 2.0

    stash = SimpleStash()
    sc_run.set_in_stash(stash)
    assert ScenarioRun.find_in_stash(stash) is sc_run
