"""
Provide run transitions helpers.

Responsibility:
    Provide run transitions helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.pickle_runner.run_transitions` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _inactive_ref: owns nested behavior below this boundary
    - _resolve_lifecycle_ref: owns nested behavior below this boundary
    - _resolve_transition_refs: owns nested behavior below this boundary
    - _sync_step_node: owns nested behavior below this boundary
    - _finalize_after_scenario: owns nested behavior below this boundary
    - apply_transition: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates run_ref, step_ref, previous_step_ref, step_is_active, feature_ref; depends on __future__.annotations,
    typing.TYPE_CHECKING, pytest_bdd.model.run.ActiveObjectSet, pytest_bdd.model.run.HookPhase,
    pytest_bdd.model.run.LifecycleKind.

Invariants:
    - `pytest_bdd.plugin.pickle_runner.run_transitions` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.model.run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleKind,
    LifecycleObjectRef,
    NoPreviousStep,
    RunStage,
    RunStatus,
)
from pytest_bdd.model.run.transitions import (
    build_lifecycle_ref,
)
from pytest_bdd.model.scenario_run import (
    RunNode,
    ScenarioRun,
)

if TYPE_CHECKING:
    from cucumber_messages import GherkinDocument


PHASE_TO_STAGE: dict[HookPhase, RunStage] = {
    HookPhase.before_scenario: RunStage.scenario_setup,
    HookPhase.run_scenario: RunStage.scenario_running,
    HookPhase.after_scenario: RunStage.scenario_teardown,
    HookPhase.run_step: RunStage.step_running,
    HookPhase.before_step: RunStage.step_running,
    HookPhase.before_step_call: RunStage.step_running,
    HookPhase.after_step: RunStage.scenario_running,
    HookPhase.step_error: RunStage.scenario_running,
    HookPhase.step_lookup_error: RunStage.scenario_running,
}


def _inactive_ref(kind: LifecycleKind, *, reason: str, fail_fast_code: str | None = None) -> LifecycleObjectRef:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.run_transitions._inactive_ref` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.run_transitions._inactive_ref`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - LifecycleObjectRef.inactive: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    return LifecycleObjectRef.inactive(kind, reason=reason, fail_fast_code=fail_fast_code)


def _resolve_lifecycle_ref(
    kind: LifecycleKind,
    value: object | None,
    *,
    is_active: bool,
    inactive_reason: str,
    fail_fast_code: str | None = None,
) -> LifecycleObjectRef:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.run_transitions._resolve_lifecycle_ref` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.run_transitions._resolve_lifecycle_ref` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - _inactive_ref: collaborator call used by this boundary
        - build_lifecycle_ref: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates lifecycle_ref.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.run_transitions._resolve_lifecycle_ref` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if value is None:
        return _inactive_ref(kind, reason=inactive_reason, fail_fast_code=fail_fast_code)
    lifecycle_ref = build_lifecycle_ref(kind, value, is_active=is_active)
    if lifecycle_ref is not None:
        return lifecycle_ref
    return _inactive_ref(kind, reason=inactive_reason, fail_fast_code=fail_fast_code)


def _resolve_transition_refs(  # noqa: PLR0913
    scenario_run: ScenarioRun,
    *,
    hook_phase: HookPhase,
    gherkin_document: GherkinDocument | None,
    pickle: object | None,
    step: object | None,
    previous_step: object | None,
) -> tuple[LifecycleObjectRef, LifecycleObjectRef, LifecycleObjectRef, LifecycleObjectRef, LifecycleObjectRef]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.run_transitions._resolve_transition_refs` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.run_transitions._resolve_transition_refs` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - _resolve_lifecycle_ref: collaborator call used by this boundary
        - _inactive_ref: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates run_ref, step_ref, previous_step_ref, scenario_is_active, feature_is_active.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.run_transitions._resolve_transition_refs` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    run_ref = scenario_run.run_ref
    if scenario_run.run is not None:
        run_ref = _resolve_lifecycle_ref("run", scenario_run.run, is_active=True, inactive_reason="idle")

    scenario_is_active = hook_phase not in {HookPhase.after_scenario, HookPhase.step_error, HookPhase.step_lookup_error}
    feature_is_active = scenario_is_active
    step_is_active = (
        hook_phase is HookPhase.run_step
        or hook_phase is HookPhase.before_step
        or hook_phase is HookPhase.before_step_call
    )

    feature_ref = _resolve_lifecycle_ref(
        "feature",
        gherkin_document,
        is_active=feature_is_active,
        inactive_reason="idle" if not feature_is_active else "unresolved_external",
    )
    scenario_ref = _resolve_lifecycle_ref(
        "scenario",
        pickle,
        is_active=scenario_is_active,
        inactive_reason="idle" if not scenario_is_active else "unresolved_external",
    )

    if hook_phase is HookPhase.after_scenario:
        step_ref = _inactive_ref("step", reason="finished", fail_fast_code="object_inactive")
        previous_step_ref = _inactive_ref("step", reason="finished")
    else:
        step_ref = _resolve_lifecycle_ref(
            "step",
            step,
            is_active=step_is_active,
            inactive_reason="idle",
            fail_fast_code="object_inactive",
        )
        previous_step_ref = _resolve_lifecycle_ref(
            "step",
            previous_step,
            is_active=previous_step is not None,
            inactive_reason="no_previous_step",
        )
    return run_ref, feature_ref, scenario_ref, step_ref, previous_step_ref


def _sync_step_node(
    scenario_run: ScenarioRun,
    *,
    step_ref: LifecycleObjectRef,
    step_is_active: bool,
) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.run_transitions._sync_step_node` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.run_transitions._sync_step_node`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - current_step_node.close: collaborator call used by this boundary
        - RunNode: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates scenario_run.step_node, next_transition, current_step_node, current_step_node.object_ref, parent_id.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.run_transitions._sync_step_node` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    next_transition = scenario_run.transition_index + 1
    current_step_node = scenario_run.step_node
    if step_ref.is_active and step_is_active:
        if current_step_node is not None and current_step_node.is_active:
            if current_step_node.object_ref.object_id == step_ref.object_id:
                current_step_node.object_ref = step_ref
                return
            current_step_node.close(next_transition)
        parent_id = scenario_run.scenario_node.id if scenario_run.scenario_node is not None else scenario_run.id
        scenario_run.step_node = RunNode(
            id=f"step-{step_ref.object_id}-{next_transition}",
            parent_id=parent_id,
            kind="step",
            object_ref=step_ref,
            is_active=True,
            opened_at_transition=next_transition,
        )
        return
    if current_step_node is not None and current_step_node.is_active:
        current_step_node.close(next_transition)
    scenario_run.step_node = None


def _finalize_after_scenario(scenario_run: ScenarioRun, *, run_ref: LifecycleObjectRef) -> None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.run_transitions._finalize_after_scenario` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.run_transitions._finalize_after_scenario` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - _inactive_ref: collaborator call used by this boundary
        - scenario_run.step_node.close: collaborator call used by this boundary
        - scenario_run.scenario_node.close: collaborator call used by this boundary
        - scenario_run.feature_node.close: collaborator call used by this boundary
        - NoPreviousStep: collaborator call used by this boundary
        - scenario_run.set_active_set: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates scenario_run.stage, scenario_run.step_object, scenario_run.previous_step_object,
        scenario_run.feature_ref, scenario_run.scenario_ref.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.run_transitions._finalize_after_scenario` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    if scenario_run.step_node is not None:
        scenario_run.step_node.close(scenario_run.transition_index)
    if scenario_run.scenario_node is not None:
        scenario_run.scenario_node.close(scenario_run.transition_index)
    if scenario_run.feature_node is not None:
        scenario_run.feature_node.close(scenario_run.transition_index)

    scenario_run.stage = RunStage.finished
    scenario_run.step_object = None
    scenario_run.previous_step_object = NoPreviousStep()
    scenario_run.feature_ref = _inactive_ref("feature", reason="finished")
    scenario_run.scenario_ref = _inactive_ref("scenario", reason="finished")
    scenario_run.step_ref = _inactive_ref("step", reason="finished", fail_fast_code="object_inactive")
    scenario_run.previous_step_ref = _inactive_ref("step", reason="finished")
    scenario_run.set_active_set(
        ActiveObjectSet(
            run=run_ref,
            feature=scenario_run.feature_ref,
            scenario=scenario_run.scenario_ref,
            step=scenario_run.step_ref,
            previous_step=scenario_run.previous_step_ref,
            captured_at_stage=RunStage.finished,
        ),
    )


def apply_transition(  # noqa: PLR0913
    scenario_run: ScenarioRun,
    *,
    hook_phase: HookPhase,
    gherkin_document: GherkinDocument | None = None,
    pickle: object | None = None,
    step: object | None = None,
    previous_step: object | None = None,
    status: RunStatus | None = None,
) -> ScenarioRun:
    """
    Apply transition to scenario run.

    Returns:
        Updated scenario run.

    Responsibility:
        Apply transition to scenario run. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.run_transitions.apply_transition`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _resolve_transition_refs: collaborator call used by this boundary
        - NoPreviousStep: collaborator call used by this boundary
        - _sync_step_node: collaborator call used by this boundary
        - scenario_run.set_active_set: collaborator call used by this boundary
        - ActiveObjectSet: collaborator call used by this boundary
        - scenario_run.advance_transition: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/__init__.py: imports or references `apply_transition`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `apply_transition`

    State and side effects:
        mutates scenario_run.status, run.active_feature_id, stage, run, run_ref.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.run_transitions.apply_transition` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    stage = PHASE_TO_STAGE[hook_phase]
    run = scenario_run.run
    run_ref, feature_ref, scenario_ref, step_ref, previous_step_ref = _resolve_transition_refs(
        scenario_run,
        hook_phase=hook_phase,
        gherkin_document=gherkin_document,
        pickle=pickle,
        step=step,
        previous_step=previous_step,
    )
    step_is_active = hook_phase in {HookPhase.run_step, HookPhase.before_step, HookPhase.before_step_call}

    scenario_run.active_hook = hook_phase
    scenario_run.stage = stage
    scenario_run.status = status or scenario_run.status
    if hook_phase in {HookPhase.step_error, HookPhase.step_lookup_error} and status is None:
        scenario_run.status = RunStatus.failed

    scenario_run.feature_ref = feature_ref
    scenario_run.scenario_ref = scenario_ref
    scenario_run.step_ref = step_ref
    scenario_run.previous_step_ref = previous_step_ref
    scenario_run.gherkin_document = gherkin_document
    scenario_run.pickle = pickle  # type: ignore[assignment]  # stash-sourced untyped object
    scenario_run.step_object = step  # type: ignore[assignment]  # stash-sourced untyped object
    scenario_run.previous_step_object = previous_step if previous_step is not None else NoPreviousStep()  # type: ignore[assignment]  # PickleStep | None vs PickleStep | NoPreviousStep

    _sync_step_node(scenario_run, step_ref=step_ref, step_is_active=step_is_active)

    scenario_run.set_active_set(
        ActiveObjectSet(
            run=run_ref,
            feature=feature_ref,
            scenario=scenario_ref,
            step=step_ref,
            previous_step=previous_step_ref,
            captured_at_stage=stage,
        ),
    )
    scenario_run.advance_transition()
    if hook_phase is HookPhase.after_scenario:
        _finalize_after_scenario(scenario_run, run_ref=run_ref)

    if run is not None:
        run.active_scenario_run = scenario_run
        run.advance_transition()
        run.status = scenario_run.status
        if hook_phase is HookPhase.after_scenario:
            run.active_feature_id = None
        else:
            run.active_feature_id = (
                scenario_run.feature_node.id
                if scenario_run.feature_node is not None and scenario_run.feature_node.is_active
                else None
            )

    return scenario_run
