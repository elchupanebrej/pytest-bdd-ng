"""
Lifecycle stage and status enumerations for the run model.

Responsibility:
    Lifecycle stage and status enumerations for the run model. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.run.stages` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - HookPhase: owns nested behavior below this boundary
    - RunStage: owns nested behavior below this boundary
    - RunStatus: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/run/__init__.py: imports or references `stages`
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `stages`
    - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `stages`
    - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `stages`

State and side effects:
    mutates before_scenario, run_scenario, after_scenario, run_step, before_step; depends on __future__.annotations,
    pytest_bdd.compatibility.enum.StrEnum.

Invariants:
    - `pytest_bdd.model.run.stages` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from pytest_bdd.compatibility.enum import StrEnum


class HookPhase(StrEnum):
    """
    Represent hook phase state.

    Responsibility:
        Represent hook phase state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.stages.HookPhase` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `HookPhase`
        - src/pytest_bdd/model/run/__init__.py: imports or references `HookPhase`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `HookPhase`
        - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `HookPhase`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `HookPhase`

    State and side effects:
        mutates before_scenario, run_scenario, after_scenario, run_step, before_step.

    Invariants:
        - `pytest_bdd.model.run.stages.HookPhase` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

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
    """
    Represent run stage state.

    Responsibility:
        Represent run stage state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.stages.RunStage` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `RunStage`
        - src/pytest_bdd/model/run/__init__.py: imports or references `RunStage`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `RunStage`
        - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `RunStage`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `RunStage`

    State and side effects:
        mutates idle, scenario_setup, scenario_running, step_running, scenario_teardown.

    Invariants:
        - `pytest_bdd.model.run.stages.RunStage` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    idle = "idle"
    scenario_setup = "scenario_setup"
    scenario_running = "scenario_running"
    step_running = "step_running"
    scenario_teardown = "scenario_teardown"
    finished = "finished"


class RunStatus(StrEnum):
    """
    Contain state changes related to a scenario run's execution progression.

    Responsibility:
        Contain state changes related to a scenario run's execution progression. It directly owns the observable
        contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.stages.RunStatus` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `RunStatus`
        - src/pytest_bdd/model/run/__init__.py: imports or references `RunStatus`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `RunStatus`
        - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `RunStatus`
        - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `RunStatus`

    State and side effects:
        mutates ok, failed, interrupted.

    Invariants:
        - `pytest_bdd.model.run.stages.RunStatus` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    ok = "ok"
    failed = "failed"
    interrupted = "interrupted"
