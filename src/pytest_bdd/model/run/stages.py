"""Lifecycle stage and status enumerations for the run model."""

from __future__ import annotations

from pytest_bdd.compatibility.enum import StrEnum


class HookPhase(StrEnum):
    """Represent hook phase state."""

    before_scenario = "pytest_bdd_before_scenario"
    run_scenario = "pytest_bdd_run_scenario"
    after_scenario = "pytest_bdd_after_scenario"
    run_step = "pytest_bdd_run_step"
    before_step = "pytest_bdd_before_step"
    before_step_call = "pytest_bdd_before_step_call"
    after_step = "pytest_bdd_after_step"
    step_error = "pytest_bdd_step_error"
    step_lookup_error = "pytest_bdd_step_func_lookup_error"


class RunStage(StrEnum):
    """Represent run stage state."""

    idle = "idle"
    scenario_setup = "scenario_setup"
    scenario_running = "scenario_running"
    step_running = "step_running"
    scenario_teardown = "scenario_teardown"
    finished = "finished"


class RunStatus(StrEnum):
    """Contain state changes related to a scenario run's execution progression."""

    ok = "ok"
    failed = "failed"
    interrupted = "interrupted"
