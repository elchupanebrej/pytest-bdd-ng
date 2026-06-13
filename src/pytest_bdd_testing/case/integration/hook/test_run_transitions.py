"""

Provide test run transitions helpers.
"""

from __future__ import annotations

import pytest
from attrs import define

from pytest_bdd.model.run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleObjectRef,
    Run,
    RunStage,
    RunStatus,
)
from pytest_bdd.model.scenario_run import (
    RunNode,
    ScenarioRun,
)
from pytest_bdd.plugin.pickle_runner.plugin import PickleRunner
from pytest_bdd.plugin.pickle_runner.run_transitions import apply_transition


@define
class _Dummy:
    name: str
    id: str


@define
class _TransitionInputs:
    feature: _Dummy
    scenario: _Dummy
    step: _Dummy
    previous_step: _Dummy


def _build_context() -> ScenarioRun:
    run_ref = LifecycleObjectRef(kind="run", object_id="run", is_active=True)
    session = Run(
        id="run-1",
        run_ref=run_ref,
        status=RunStatus.ok,
    )
    scenario_node = RunNode(
        id="ctx",
        parent_id=session.id,
        kind="scenario",
        object_ref=LifecycleObjectRef(kind="scenario", object_id="s-1", is_active=True),
        is_active=True,
        opened_at_transition=0,
    )
    active_set = ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.idle)
    return ScenarioRun(
        id="ctx",
        run_ref=run_ref,
        active_hook=HookPhase.before_scenario,
        stage=RunStage.idle,
        status=RunStatus.ok,
        active_set=active_set,
        run=session,
        scenario_node=scenario_node,
    )


def _build_transition_inputs() -> _TransitionInputs:
    return _TransitionInputs(
        feature=_Dummy("feature", "f-1"),
        scenario=_Dummy("scenario", "s-1"),
        step=_Dummy("step", "st-1"),
        previous_step=_Dummy("previous-step", "st-0"),
    )


def test_transition_updates_stage_for_step_flow() -> None:
    """
    Verify transition updates stage for step flow.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    context = _build_context()
    inputs = _build_transition_inputs()

    apply_transition(
        context,
        hook_phase=HookPhase.before_step,
        gherkin_document=inputs.feature,
        pickle=inputs.scenario,
        step=inputs.step,
        previous_step=None,
    )

    assert context.stage == RunStage.step_running
    assert context.step_ref.object_id == "st-1"
    assert context.active_set.previous_step.empty_state_reason == "no_previous_step"


def test_transition_marks_failed_status_on_step_error() -> None:
    """
    Verify transition marks failed status on step error.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    context = _build_context()
    inputs = _build_transition_inputs()
    apply_transition(
        context,
        hook_phase=HookPhase.step_error,
        gherkin_document=inputs.feature,
        pickle=inputs.scenario,
        step=inputs.step,
        previous_step=None,
    )

    assert context.status == RunStatus.failed
    assert context.run.status == RunStatus.failed


def test_lookup_error_hook_name_maps_to_failed_transition() -> None:
    """
    Verify lookup-error pytest hook name transitions scenario run state.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    context = _build_context()
    inputs = _build_transition_inputs()

    apply_transition(
        context,
        hook_phase=HookPhase("pytest_bdd_step_func_lookup_error"),
        gherkin_document=inputs.feature,
        pickle=inputs.scenario,
        step=inputs.step,
        previous_step=None,
    )

    assert context.active_hook == HookPhase.step_lookup_error
    assert context.stage == RunStage.scenario_running
    assert context.status == RunStatus.failed
    assert context.run.status == RunStatus.failed


def test_transition_clears_scenario_objects_after_after_scenario() -> None:
    """
    Verify transition clears scenario objects after after scenario.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    context = _build_context()
    inputs = _build_transition_inputs()
    feature_node = RunNode(
        id="feature-node-1",
        parent_id=context.run.id,
        kind="feature",
        object_ref=LifecycleObjectRef(kind="feature", object_id="f-1", is_active=True),
        is_active=True,
        opened_at_transition=0,
    )
    context.feature_node = feature_node
    context.run.active_feature_id = feature_node.id
    context.run.reporting_state.active_test_case_started_id = "case-started-1"
    context.run.reporting_state.active_test_step_id = "step-1"
    context.reference_resolver.add_missing_reference("missing-ast-node")
    apply_transition(
        context,
        hook_phase=HookPhase.after_scenario,
        gherkin_document=inputs.feature,
        pickle=inputs.scenario,
        step=None,
        previous_step=None,
    )

    assert context.stage == RunStage.finished
    assert context.active_set.feature.is_active is False
    assert context.active_set.feature.empty_state_reason == "finished"
    assert context.active_set.scenario.is_active is False
    assert context.active_set.scenario.empty_state_reason == "finished"
    assert context.active_set.step.is_active is False
    assert context.active_set.step.empty_state_reason == "finished"
    assert context.feature_ref == context.active_set.feature
    assert context.scenario_ref == context.active_set.scenario
    assert context.step_ref == context.active_set.step
    assert context.previous_step_ref == context.active_set.previous_step
    assert context.run.active_feature_id is None
    with pytest.raises(AttributeError, match="No active scenario"):
        _ = context.run.active_scenario_id
    assert context.run.reporting_state.active_test_case_started_id == "case-started-1"
    assert context.run.reporting_state.active_test_step_id == "step-1"
    assert context.reference_resolver.missing_reference_diagnostics == ["missing-ast-node"]


def test_transition_reuses_active_step_node_for_same_step() -> None:
    """
    Verify repeated active hook phases preserve the current step node.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    context = _build_context()
    inputs = _build_transition_inputs()

    apply_transition(
        context,
        hook_phase=HookPhase.before_step,
        gherkin_document=inputs.feature,
        pickle=inputs.scenario,
        step=inputs.step,
        previous_step=None,
    )
    first_step_node = context.step_node

    apply_transition(
        context,
        hook_phase=HookPhase.before_step_call,
        gherkin_document=inputs.feature,
        pickle=inputs.scenario,
        step=inputs.step,
        previous_step=None,
    )

    assert context.step_node is first_step_node
    assert context.step_node is not None
    assert context.step_node.is_active is True
    assert context.step_node.closed_at_transition is None


def test_transition_closes_active_step_node_when_step_changes() -> None:
    """
    Verify replacing active step nodes closes the old node.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    context = _build_context()
    inputs = _build_transition_inputs()
    next_step = _Dummy("next-step", "st-2")

    apply_transition(
        context,
        hook_phase=HookPhase.before_step,
        gherkin_document=inputs.feature,
        pickle=inputs.scenario,
        step=inputs.step,
        previous_step=None,
    )
    first_step_node = context.step_node

    apply_transition(
        context,
        hook_phase=HookPhase.before_step,
        gherkin_document=inputs.feature,
        pickle=inputs.scenario,
        step=next_step,
        previous_step=inputs.step,
    )

    assert first_step_node is not None
    assert first_step_node.is_active is False
    assert first_step_node.closed_at_transition == 2
    assert context.step_node is not None
    assert context.step_node.object_ref.object_id == "st-2"
    assert context.step_node.is_active is True


def test_pickle_runner_raises_when_lifecycle_hook_has_no_active_scenario_run() -> None:
    """
    Verify pickle runner raises when lifecycle hook has no active scenario run.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    runner = PickleRunner()
    run_ref = LifecycleObjectRef(kind="run", object_id="run", is_active=True)
    run = Run(id="run-1", run_ref=run_ref, status=RunStatus.ok)
    config = type(
        "_Config",
        (),
        {
            "stash": {},
            "hook": type("_Hook", (), {"pytest_bdd_before_scenario": staticmethod(lambda **_kwargs: None)})(),
        },
    )()
    run.set_in_stash(config.stash)
    request = type("_Request", (), {"config": config})()

    with pytest.raises(RuntimeError, match=r"Active scenario run.*pytest_bdd_before_scenario"):
        runner._invoke_bdd_hook(
            hook_name="pytest_bdd_before_scenario",
            request=request,
            gherkin_document=_Dummy("feature", "f-1"),
            pickle=_Dummy("scenario", "s-1"),
        )
