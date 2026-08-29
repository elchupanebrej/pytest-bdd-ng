from __future__ import annotations

import json

from pytest_bdd.model.scenario import Scenario
from pytest_bdd.model.scenario_report import ScenarioReport, StepReport
from pytest_bdd.model.scenario_run import ExecutionContext, ScenarioRun, StepRun
from pytest_bdd.model.stash_access import SimpleStash
from pytest_bdd.model.step import Step


def test_seam4_pure_state_access_contract() -> None:
    st1 = Step(name="setup state", keyword="Given ", line=2, id="st-1")
    st2 = Step(name="perform action", keyword="When ", line=3, id="st-2")
    st3 = Step(name="verify outcome", keyword="Then ", line=4, id="st-3")
    sc = Scenario(name="Pure Execution", keyword="Scenario", line=1, id="sc-1", steps=(st1, st2, st3))

    ctx = ExecutionContext()
    ctx.set_param("auth_token", "secret123")
    ctx.set_param("user_id", 42)

    sc_run = ScenarioRun(scenario=sc, run_id="run-seam4-1", context=ctx)
    sc_run.start(timestamp=100.0)

    sr1 = sc_run.add_step_run(StepRun(step=st1, id="sr-1"))
    sr1.start(timestamp=100.1)
    sr1.pass_step(result={"status": "ready"}, duration=0.2)
    ctx.set_step_result("st-1", sr1.result)

    sr2 = sc_run.add_step_run(StepRun(step=st2, id="sr-2"))
    sr2.start(timestamp=100.3)
    sr2.pass_step(result={"items_count": 5}, duration=0.4)
    ctx.set_step_result("st-2", sr2.result)

    sr3 = sc_run.add_step_run(StepRun(step=st3, id="sr-3"))
    sr3.start(timestamp=100.7)
    sr3.pass_step(result=True, duration=0.1)
    ctx.set_step_result("st-3", sr3.result)

    sc_run.pass_scenario(duration=0.7)

    stash = SimpleStash()
    sc_run.set_in_stash(stash)
    retrieved = ScenarioRun.from_stash(stash)
    assert retrieved is sc_run
    assert retrieved.context.get_param("auth_token") == "secret123"
    assert retrieved.context.get_step_result("st-2") == {"items_count": 5}

    report = ScenarioReport.from_scenario_run(sc_run)
    assert report.scenario_name == "Pure Execution"
    assert report.status == "passed"
    assert len(report.steps) == 3
    assert all(isinstance(s, StepReport) for s in report.steps)
    assert not report.failed

    report_dict = report.serialize()
    json_str = report.to_json()
    assert json.loads(json_str)["scenario_name"] == "Pure Execution"
    assert not any("pytest" in k.lower() or "_pytest" in k.lower() for k in report_dict)


def test_seam4_execution_context_isolation() -> None:
    ctx1 = ExecutionContext()
    ctx1.set_param("shared_key", "value_1")

    ctx2 = ExecutionContext()
    ctx2.set_param("shared_key", "value_2")

    assert ctx1.get_param("shared_key") == "value_1"
    assert ctx2.get_param("shared_key") == "value_2"
    assert ctx1.clone().get_param("shared_key") == "value_1"
