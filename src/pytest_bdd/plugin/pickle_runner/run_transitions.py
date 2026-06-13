"""
Implement plugin module operations for pytest-bdd.

Responsibility:
    Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
    consumed by the broader BDD infrastructure.

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion and serve as the information
    expert for its domain concepts.

Delegates:
    - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

Cohesion:
    All logic within this entity operates on a single responsibility domain with focused imports and control flow.

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

Main consumers:
    - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

State and side effects:
    None, keeps no persistent state beyond local scope.

Invariants:
    - All public API contracts defined by this entity must be honored by callers.

Architecture score:
    #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
    #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
    #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
    #arch-eval:cohesion=4  # Internal logic focus (1-5)
    #arch-eval:separation=4  # Distinctness from peers (1-5)
    #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
    #arch-eval:state_invariants=4  # Control of state mutations (1-5)
    #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
    #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    if value is None:
        return _inactive_ref(kind, reason=inactive_reason, fail_fast_code=fail_fast_code)
    lifecycle_ref = build_lifecycle_ref(kind, value, is_active=is_active)
    if lifecycle_ref is not None:
        return lifecycle_ref
    return _inactive_ref(kind, reason=inactive_reason, fail_fast_code=fail_fast_code)


def _resolve_transition_refs(  # noqa: PLR0913  -- suppressed warning
    scenario_run: ScenarioRun,
    *,
    hook_phase: HookPhase,
    gherkin_document: GherkinDocument | None,
    pickle: object | None,
    step: object | None,
    previous_step: object | None,
) -> tuple[LifecycleObjectRef, LifecycleObjectRef, LifecycleObjectRef, LifecycleObjectRef, LifecycleObjectRef]:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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


def apply_transition(  # noqa: PLR0913  -- suppressed warning
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
