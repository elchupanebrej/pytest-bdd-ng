"""

Characterization tests for scenario run runtime state.
"""

from __future__ import annotations

import pytest
from attrs import define

from pytest_bdd.model.run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleObjectRef,
    ReportingContextSnapshot,
    Run,
    RunStage,
    RunStatus,
)
from pytest_bdd.model.scenario_run import (
    RunNode,
    ScenarioRun,
)
from pytest_bdd.plugin.pickle_runner.run_transitions import PHASE_TO_STAGE, apply_transition

pytestmark = [pytest.mark.unit]


@define
class _RuntimeObject:
    name: str
    id: str


def _lifecycle_dict(
    *,
    kind: str,
    object_id: str,
    name: str | None = None,
    source: str | None = None,
    is_active: bool = True,
    empty_state_reason: str | None = None,
    fail_fast_code: str | None = None,
) -> dict[str, object]:
    return {
        "kind": kind,
        "object_id": object_id,
        "name": name,
        "source": source,
        "is_active": is_active,
        "empty_state_reason": empty_state_reason,
        "fail_fast_code": fail_fast_code,
    }


def _run_reporting_state_dict() -> dict[str, object]:
    return {
        "run_started_id": None,
        "test_run_hook_started_id": None,
        "active_test_case_id": None,
        "active_test_case_started_id": None,
        "active_test_step_id": None,
        "runtime_step_to_test_step_id": {},
        "scenario_attempt_context": None,
        "step_started_timestamp": None,
        "step_finished_timestamp": None,
    }


def _build_run() -> Run:
    return Run(
        id="run-1",
        run_ref=LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True),
        status=RunStatus.ok,
    )


def _build_scenario_run() -> ScenarioRun:
    run = _build_run()
    run_ref = run.run_ref
    feature_ref = LifecycleObjectRef(kind="feature", object_id="feature-1", name="Feature", is_active=True)
    scenario_ref = LifecycleObjectRef(kind="scenario", object_id="scenario-1", name="Scenario", is_active=True)
    scenario_run = ScenarioRun(
        id="ctx-1",
        run_ref=run_ref,
        active_hook=HookPhase.before_scenario,
        stage=RunStage.idle,
        status=RunStatus.ok,
        active_set=ActiveObjectSet(
            run=run_ref,
            feature=feature_ref,
            scenario=scenario_ref,
            captured_at_stage=RunStage.idle,
        ),
        run=run,
        feature_ref=feature_ref,
        scenario_ref=scenario_ref,
        feature_node=RunNode(
            id="feature-node-1",
            parent_id=run.id,
            kind="feature",
            object_ref=feature_ref,
            is_active=True,
            opened_at_transition=0,
        ),
        scenario_node=RunNode(
            id="scenario-node-1",
            parent_id="feature-node-1",
            kind="scenario",
            object_ref=scenario_ref,
            is_active=True,
            opened_at_transition=0,
        ),
    )
    run.active_scenario_run = scenario_run
    run.active_feature_id = "feature-node-1"
    run.active_feature_uri = "features/example.feature"
    return scenario_run


def test_lifecycle_object_ref_serialization_is_stable() -> None:
    """
    Verify lifecycle object refs serialize explicit active and inactive state.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    active_ref = LifecycleObjectRef(
        kind="scenario",
        object_id="scenario-1",
        name="Scenario",
        source="Pickle",
        is_active=True,
    )
    inactive_ref = LifecycleObjectRef.inactive("step", reason="idle", fail_fast_code="object_inactive")

    assert active_ref.as_dict() == _lifecycle_dict(
        kind="scenario",
        object_id="scenario-1",
        name="Scenario",
        source="Pickle",
    )
    assert inactive_ref.as_dict() == _lifecycle_dict(
        kind="step",
        object_id="step:idle",
        name="step",
        source="lifecycle-slot",
        is_active=False,
        empty_state_reason="idle",
        fail_fast_code="object_inactive",
    )


def test_active_object_set_serialization_is_stable() -> None:
    """
    Verify active object set serializes all lifecycle slots.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run_ref = LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True)
    active_set = ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.idle)

    assert active_set.as_dict() == {
        "run": _lifecycle_dict(kind="run", object_id="run-1", name="run"),
        "feature": _lifecycle_dict(
            kind="feature",
            object_id="feature:idle",
            name="feature",
            source="lifecycle-slot",
            is_active=False,
            empty_state_reason="idle",
        ),
        "scenario": _lifecycle_dict(
            kind="scenario",
            object_id="scenario:idle",
            name="scenario",
            source="lifecycle-slot",
            is_active=False,
            empty_state_reason="idle",
        ),
        "step": _lifecycle_dict(
            kind="step",
            object_id="step:idle",
            name="step",
            source="lifecycle-slot",
            is_active=False,
            empty_state_reason="idle",
            fail_fast_code="object_inactive",
        ),
        "previous_step": _lifecycle_dict(
            kind="step",
            object_id="step:no_previous_step",
            name="step",
            source="lifecycle-slot",
            is_active=False,
            empty_state_reason="no_previous_step",
        ),
        "captured_at_stage": "idle",
    }


def test_run_serialization_is_stable_for_idle_root() -> None:
    """
    Verify idle Run serialization shape is stable.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    run = _build_run()

    assert run.as_dict() == {
        "run_id": "run-1",
        "run_ref": _lifecycle_dict(kind="run", object_id="run-1", name="run"),
        "status": "ok",
        "transition_index": 0,
        "feature_bindings_by_uri": [],
        "active_feature_id": None,
        "active_feature_uri": None,
        "active_scenario_id": None,
        "active_step_id": None,
        "last_error": None,
        "reporting_state": _run_reporting_state_dict(),
    }


def test_scenario_run_serialization_is_stable() -> None:
    """
    Verify ScenarioRun serialization shape is stable.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    scenario_run = _build_scenario_run()

    assert scenario_run.as_dict() == {
        "id": "ctx-1",
        "run_ref": _lifecycle_dict(kind="run", object_id="run-1", name="run"),
        "feature_ref": _lifecycle_dict(kind="feature", object_id="feature-1", name="Feature"),
        "scenario_ref": _lifecycle_dict(kind="scenario", object_id="scenario-1", name="Scenario"),
        "step_ref": _lifecycle_dict(
            kind="step",
            object_id="step:idle",
            name="step",
            source="lifecycle-slot",
            is_active=False,
            empty_state_reason="idle",
            fail_fast_code="object_inactive",
        ),
        "previous_step_ref": _lifecycle_dict(
            kind="step",
            object_id="step:no_previous_step",
            name="step",
            source="lifecycle-slot",
            is_active=False,
            empty_state_reason="no_previous_step",
        ),
        "active_hook": "pytest_bdd_before_scenario",
        "stage": "idle",
        "status": "ok",
        "active_set": scenario_run.active_set.as_dict(),
        "transition_index": 0,
        "feature_uri": None,
        "last_error": None,
        "run": {
            "run_id": "run-1",
            "run_ref": _lifecycle_dict(kind="run", object_id="run-1", name="run"),
            "status": "ok",
            "transition_index": 0,
            "feature_bindings_by_uri": [],
            "active_feature_id": "feature-node-1",
            "active_feature_uri": "features/example.feature",
            "active_scenario_id": "scenario-node-1",
            "active_step_id": None,
            "last_error": None,
            "reporting_state": _run_reporting_state_dict(),
        },
        "feature_node": {
            "id": "feature-node-1",
            "parent_id": "run-1",
            "kind": "feature",
            "object_ref": _lifecycle_dict(kind="feature", object_id="feature-1", name="Feature"),
            "is_active": True,
            "opened_at_transition": 0,
            "closed_at_transition": None,
        },
        "scenario_node": {
            "id": "scenario-node-1",
            "parent_id": "feature-node-1",
            "kind": "scenario",
            "object_ref": _lifecycle_dict(kind="scenario", object_id="scenario-1", name="Scenario"),
            "is_active": True,
            "opened_at_transition": 0,
            "closed_at_transition": None,
        },
        "step_node": None,
        "reference_resolver": {"missing_reference_diagnostics": []},
    }


def test_context_error_and_reporting_snapshot_serialization_are_stable() -> None:
    """
    Verify diagnostics and reporting snapshots serialize stable dictionaries.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    scenario_run = _build_scenario_run()
    error = scenario_run.record_context_error(
        code="object_inactive",
        message="Step unavailable",
        hook_name="pytest_bdd_after_step",
        requested_kind="step",
    )
    snapshot = ReportingContextSnapshot(
        run_id=scenario_run.run.id,
        active_set=scenario_run.active_set,
        stage=RunStage.idle,
        resolved_from_hierarchy=True,
    )

    assert error.as_dict() == {
        "code": "object_inactive",
        "message": "Step unavailable",
        "hook_name": "pytest_bdd_after_step",
        "stage": "idle",
        "requested_kind": "step",
    }
    assert scenario_run.run.last_error is error
    assert snapshot.as_dict() == {
        "run_id": "run-1",
        "active_set": scenario_run.active_set.as_dict(),
        "stage": "idle",
        "resolved_from_hierarchy": True,
        "fallback_reason": None,
    }


@pytest.mark.parametrize(("hook_phase", "expected_stage"), list(PHASE_TO_STAGE.items()))
def test_apply_transition_characterizes_every_hook_phase(hook_phase: HookPhase, expected_stage: RunStage) -> None:
    """
    Verify every HookPhase maps to the characterized runtime state.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    scenario_run = _build_scenario_run()
    feature = _RuntimeObject("Feature", "feature-1")
    scenario = _RuntimeObject("Scenario", "scenario-1")
    step = _RuntimeObject("Step", "step-1")
    previous_step = _RuntimeObject("Previous", "step-0")

    apply_transition(
        scenario_run,
        hook_phase=hook_phase,
        gherkin_document=feature,
        pickle=scenario,
        step=step,
        previous_step=previous_step,
    )

    failure_hooks = {HookPhase.step_error, HookPhase.step_lookup_error}
    expected_status = RunStatus.failed if hook_phase in failure_hooks else RunStatus.ok
    assert scenario_run.active_hook == hook_phase
    assert scenario_run.stage == (RunStage.finished if hook_phase is HookPhase.after_scenario else expected_stage)
    assert scenario_run.status == expected_status
    assert scenario_run.run.status == expected_status
    assert scenario_run.transition_index == 1
    assert scenario_run.run.transition_index == 1
    assert scenario_run.active_set.captured_at_stage == scenario_run.stage
    assert scenario_run.active_set.run.kind == "run"

    if hook_phase is HookPhase.after_scenario:
        assert scenario_run.feature_node is not None
        assert scenario_run.feature_node.closed_at_transition == 1
        assert scenario_run.scenario_node is not None
        assert scenario_run.scenario_node.closed_at_transition == 1
        assert scenario_run.active_set.feature.empty_state_reason == "finished"
        assert scenario_run.active_set.scenario.empty_state_reason == "finished"
        assert scenario_run.active_set.step.empty_state_reason == "finished"
        assert scenario_run.active_set.previous_step.empty_state_reason == "finished"
        return

    scenario_is_active = hook_phase not in {HookPhase.step_error, HookPhase.step_lookup_error}
    step_is_active = hook_phase in {HookPhase.run_step, HookPhase.before_step, HookPhase.before_step_call}
    assert scenario_run.active_set.feature.is_active is scenario_is_active
    assert scenario_run.active_set.scenario.is_active is scenario_is_active
    assert scenario_run.active_set.step.is_active is step_is_active
    assert scenario_run.active_set.previous_step.object_id == "step-0"


def test_target_split_modules_expose_runtime_symbols() -> None:
    """
    Verify target split modules expose their owning runtime symbols.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
    from pytest_bdd.model.run import ActiveObjectSet as SplitActiveObjectSet
    from pytest_bdd.model.run import HookPhase as SplitHookPhase
    from pytest_bdd.model.run import LifecycleObjectRef as SplitLifecycleObjectRef
    from pytest_bdd.model.run import ReportingContextSnapshot as SplitReportingContextSnapshot
    from pytest_bdd.model.run import Run as SplitRun
    from pytest_bdd.model.run import RunStage as SplitRunStage
    from pytest_bdd.model.run import RunStatus as SplitRunStatus
    from pytest_bdd.model.scenario_run import RunNode, ScenarioRun, StepRun

    assert SplitRun is Run
    assert SplitRunStage is RunStage
    assert SplitHookPhase is HookPhase
    assert SplitRunStatus is RunStatus
    assert SplitLifecycleObjectRef is LifecycleObjectRef
    assert SplitActiveObjectSet is ActiveObjectSet
    assert SplitReportingContextSnapshot is ReportingContextSnapshot
    assert FeatureRuntimeBinding.__name__ == "FeatureRuntimeBinding"
    assert ScenarioRun.__name__ == "ScenarioRun"
    assert RunNode.__name__ == "RunNode"
    assert StepRun.__name__ == "StepRun"
