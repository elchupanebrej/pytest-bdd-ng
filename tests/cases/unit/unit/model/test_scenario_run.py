"""Unit tests for ScenarioRun class — per-scenario execution state."""

from __future__ import annotations

import pytest

from pytest_bdd.model.run import (
    ActiveObjectSet,
    ContextErrorState,
    HookPhase,
    LifecycleObjectRef,
    NoPreviousStep,
    Run,
    RunStage,
    RunStatus,
)
from pytest_bdd.model.scenario_run import RunNode, ScenarioRun, StepRun

pytestmark = [pytest.mark.unit]


def _build_run(**kwargs) -> Run:
    return Run(
        id="run-1",
        run_ref=LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True),
        status=RunStatus.ok,
        **kwargs,
    )


def _build_scenario_run(run: Run | None = None, **kwargs) -> ScenarioRun:
    if run is None:
        run = _build_run()
    run_ref = run.run_ref
    feature_ref = LifecycleObjectRef(kind="feature", object_id="feature-1", name="Feature", is_active=True)
    scenario_ref = LifecycleObjectRef(kind="scenario", object_id="scenario-1", name="Scenario", is_active=True)

    defaults = {
        "id": "ctx-1",
        "run_ref": run_ref,
        "active_hook": HookPhase.before_scenario,
        "stage": RunStage.idle,
        "status": RunStatus.ok,
        "active_set": ActiveObjectSet(
            run=run_ref,
            feature=feature_ref,
            scenario=scenario_ref,
            captured_at_stage=RunStage.idle,
        ),
        "run": run,
        "feature_ref": feature_ref,
        "scenario_ref": scenario_ref,
        "feature_node": RunNode(
            id="feature-node-1",
            parent_id=run.id,
            kind="feature",
            object_ref=feature_ref,
            is_active=True,
            opened_at_transition=0,
        ),
        "scenario_node": RunNode(
            id="scenario-node-1",
            parent_id="feature-node-1",
            kind="scenario",
            object_ref=scenario_ref,
            is_active=True,
            opened_at_transition=0,
        ),
    }
    defaults.update(kwargs)
    return ScenarioRun(**defaults)


class TestScenarioRunConstruction:
    """Tests for ScenarioRun construction and default state."""

    def test_construction_with_required_fields(self) -> None:
        """ScenarioRun can be constructed with required fields."""
        run = _build_run()
        sr = _build_scenario_run(run=run)
        assert sr.id == "ctx-1"
        assert sr.status == RunStatus.ok
        assert sr.stage == RunStage.idle

    def test_default_transition_index_is_zero(self) -> None:
        """New ScenarioRun starts with transition_index of 0."""
        sr = _build_scenario_run()
        assert sr.transition_index == 0

    def test_default_active_hook(self) -> None:
        """Default active_hook is before_scenario."""
        sr = _build_scenario_run()
        assert sr.active_hook == HookPhase.before_scenario

    def test_default_step_ref_is_inactive(self) -> None:
        """step_ref defaults to inactive step."""
        sr = _build_scenario_run()
        assert sr.step_ref.is_active is False
        assert sr.step_ref.empty_state_reason == "idle"

    def test_default_previous_step_ref_is_no_previous(self) -> None:
        """previous_step_ref defaults to no_previous_step."""
        sr = _build_scenario_run()
        assert sr.previous_step_ref.empty_state_reason == "no_previous_step"


class TestScenarioRunAdvanceTransition:
    """Tests for ScenarioRun.advance_transition()."""

    def test_advance_transition_increments_index(self) -> None:
        """advance_transition increments transition_index by 1."""
        sr = _build_scenario_run()
        assert sr.transition_index == 0
        sr.advance_transition()
        assert sr.transition_index == 1

    def test_multiple_advances(self) -> None:
        """Multiple advances increment correctly."""
        sr = _build_scenario_run()
        for _ in range(3):
            sr.advance_transition()
        assert sr.transition_index == 3


class TestScenarioRunRecordContextError:
    """Tests for ScenarioRun.record_context_error()."""

    def test_creates_and_stores_error(self) -> None:
        """record_context_error creates a ContextErrorState and stores it."""
        sr = _build_scenario_run()
        error = sr.record_context_error(
            code="object_inactive",
            message="Step unavailable",
            hook_name="pytest_bdd_before_step",
            requested_kind="step",
        )
        assert isinstance(error, ContextErrorState)
        assert error.code == "object_inactive"
        assert error.message == "Step unavailable"
        assert error.hook_name == "pytest_bdd_before_step"
        assert error.stage == RunStage.idle
        assert error.requested_kind == "step"

    def test_error_propagates_to_run(self) -> None:
        """Error is also stored on the parent Run's last_error."""
        run = _build_run()
        sr = _build_scenario_run(run=run)
        sr.record_context_error(
            code="transition_order_violation",
            message="Wrong order",
            hook_name="pytest_bdd_after_scenario",
        )
        assert run.last_error is not None
        assert run.last_error.code == "transition_order_violation"

    def test_return_type_is_context_error_state(self) -> None:
        """Returns ContextErrorState instance."""
        sr = _build_scenario_run()
        result = sr.record_context_error(
            code="context_not_initialized",
            message="Not ready",
            hook_name="pytest_bdd_run_scenario",
        )
        assert isinstance(result, ContextErrorState)


class TestScenarioRunSetActiveSet:
    """Tests for ScenarioRun.set_active_set()."""

    def test_replaces_active_set(self) -> None:
        """set_active_set replaces the current active set."""
        sr = _build_scenario_run()
        original_feature = sr.active_set.feature
        new_ref = LifecycleObjectRef.inactive("feature", reason="cancelled")
        new_set = ActiveObjectSet(run=sr.active_set.run, feature=new_ref, captured_at_stage=RunStage.scenario_setup)
        sr.set_active_set(new_set)
        assert sr.active_set.feature is new_ref
        assert sr.active_set.captured_at_stage == RunStage.scenario_setup

    def test_updates_internal_index(self) -> None:
        """Internal _active_kind_index is updated."""
        sr = _build_scenario_run()
        new_feature = LifecycleObjectRef.inactive("feature", reason="idle")
        new_set = ActiveObjectSet(run=sr.active_set.run, feature=new_feature, captured_at_stage=RunStage.idle)
        sr.set_active_set(new_set)
        assert sr._active_kind_index["feature"] is new_feature


class TestScenarioRunGetActiveObject:
    """Tests for ScenarioRun.get_active_object()."""

    def test_returns_active_ref(self) -> None:
        """Returns the LifecycleObjectRef when active."""
        sr = _build_scenario_run()
        run_ref = sr.get_active_object("run")
        assert run_ref is not None
        assert run_ref.is_active is True
        assert run_ref.kind == "run"

    def test_returns_none_for_inactive(self) -> None:
        """Returns None when the object is inactive."""
        from pytest_bdd.model.run import ActiveObjectSet, LifecycleObjectRef

        run = _build_run()
        inactive_feature = LifecycleObjectRef.inactive("feature", reason="idle")
        inactive_scenario = LifecycleObjectRef.inactive("scenario", reason="idle")

        active_set = ActiveObjectSet(
            run=run.run_ref,
            feature=inactive_feature,
            scenario=inactive_scenario,
            captured_at_stage=RunStage.idle,
        )
        sr = ScenarioRun(
            id="ctx-test",
            run_ref=run.run_ref,
            active_hook=HookPhase.before_scenario,
            stage=RunStage.idle,
            status=RunStatus.ok,
            active_set=active_set,
            run=run,
            feature_ref=inactive_feature,
            scenario_ref=inactive_scenario,
        )
        assert sr.get_active_object("feature") is None
        assert sr.get_active_object("scenario") is None
        assert sr.get_active_object("step") is None

    def test_returns_none_for_unknown_kind(self) -> None:
        """Returns None for unknown lifecycle kind."""
        sr = _build_scenario_run()
        assert sr.get_active_object("unknown_kind") is None


class TestScenarioRunRequireFeatureBinding:
    """Tests for ScenarioRun.require_feature_binding()."""

    def test_raises_when_no_binding(self) -> None:
        """Raises RuntimeError when feature binding is unavailable."""
        sr = _build_scenario_run()
        with pytest.raises(RuntimeError, match="Feature runtime binding is unavailable"):
            sr.require_feature_binding(hook_name="pytest_bdd_before_scenario")

    def test_raises_includes_hook_name_and_stage(self) -> None:
        """Error message includes hook_name and stage info."""
        sr = _build_scenario_run()
        hook_name = "pytest_bdd_after_scenario"
        with pytest.raises(RuntimeError, match=hook_name):
            sr.require_feature_binding(hook_name=hook_name)


class TestScenarioRunRequireMethods:
    """Tests for require_gherkin_document, require_pickle, require_step_object."""

    def test_require_gherkin_document_raises_when_missing(self) -> None:
        """require_gherkin_document raises when no binding or document."""
        sr = _build_scenario_run()
        with pytest.raises(RuntimeError, match="Feature object is unavailable"):
            sr.require_gherkin_document(hook_name="pytest_bdd_before_scenario")

    def test_require_pickle_raises_when_missing(self) -> None:
        """require_pickle raises when pickle is None."""
        sr = _build_scenario_run()
        with pytest.raises(RuntimeError, match="Pickle object is unavailable"):
            sr.require_pickle(hook_name="pytest_bdd_before_scenario")

    def test_require_step_object_raises_when_missing(self) -> None:
        """require_step_object raises when step_object is None."""
        sr = _build_scenario_run()
        with pytest.raises(RuntimeError, match="Step object is unavailable"):
            sr.require_step_object(hook_name="pytest_bdd_before_step")


class TestScenarioRunEnsureFinishedForCleanup:
    """Tests for ScenarioRun.ensure_finished_for_cleanup()."""

    def test_marks_all_nodes_finished(self) -> None:
        """All active nodes are marked inactive and closed_at_transition is set."""
        sr = _build_scenario_run()
        sr.ensure_finished_for_cleanup(at_transition=10)

        assert sr.feature_node.is_active is False
        assert sr.feature_node.closed_at_transition == 10
        assert sr.scenario_node.is_active is False
        assert sr.scenario_node.closed_at_transition == 10
        assert sr.step_node is None  # Was already None

        assert sr.feature_ref.is_active is False
        assert sr.scenario_ref.is_active is False
        assert sr.step_ref.is_active is False
        assert sr.previous_step_ref.is_active is False

    def test_sets_stage_to_finished(self) -> None:
        """Stage is set to finished."""
        sr = _build_scenario_run()
        sr.ensure_finished_for_cleanup(at_transition=5)
        assert sr.stage == RunStage.finished

    def test_creates_fresh_active_set(self) -> None:
        """Creates a new ActiveObjectSet with finished refs."""
        sr = _build_scenario_run()
        sr.ensure_finished_for_cleanup(at_transition=3)
        assert sr.active_set.captured_at_stage == RunStage.finished
        assert sr.active_set.feature.empty_state_reason == "finished"
        assert sr.active_set.scenario.empty_state_reason == "finished"
        assert sr.active_set.step.empty_state_reason == "finished"


class TestScenarioRunFeatureBinding:
    """Tests for the feature_binding property."""

    def test_returns_none_when_no_uri_or_document(self) -> None:
        """Returns None when neither feature_uri nor gherkin_document set."""
        sr = _build_scenario_run()
        sr.feature_uri = None
        sr.gherkin_document = None
        # Clear any bindings from the run
        sr.run.feature_bindings_by_uri.clear()
        assert sr.feature_binding is None

    def test_returns_none_for_nonexistent_uri_binding(self) -> None:
        """Returns None when feature_uri doesn't match any binding."""
        sr = _build_scenario_run()
        sr.feature_uri = "file:features/nonexistent.feature"
        assert sr.feature_binding is None


class TestScenarioRunAsDict:
    """Tests for ScenarioRun.as_dict() serialization."""

    def test_contains_expected_keys(self) -> None:
        """Serialized dict contains all expected top-level keys."""
        sr = _build_scenario_run()
        d = sr.as_dict()
        assert "id" in d
        assert "run_ref" in d
        assert "feature_ref" in d
        assert "scenario_ref" in d
        assert "step_ref" in d
        assert "previous_step_ref" in d
        assert "active_hook" in d
        assert "stage" in d
        assert "status" in d
        assert "active_set" in d
        assert "transition_index" in d
        assert "feature_uri" in d
        assert "last_error" in d
        assert "run" in d
        assert "feature_node" in d
        assert "scenario_node" in d
        assert "step_node" in d
        assert "reference_resolver" in d

    def test_active_hook_is_string(self) -> None:
        """active_hook is serialized as string value."""
        sr = _build_scenario_run()
        d = sr.as_dict()
        assert d["active_hook"] == "pytest_bdd_before_scenario"


class TestStepRun:
    """Tests for StepRun data class."""

    def test_default_construction(self) -> None:
        """StepRun can be created with defaults."""
        step_run = StepRun()
        assert step_run.step is None
        assert step_run.keyword is None
        assert not step_run.text
        assert step_run.parameters == {}
        assert step_run.status == RunStatus.ok
        assert step_run.duration is None
        assert step_run.attachments == []

    def test_construction_with_values(self) -> None:
        """StepRun accepts custom values."""
        step_run = StepRun(
            text="Given something",
            keyword="Given",
            status=RunStatus.failed,
            parameters={"x": 1},
        )
        assert step_run.text == "Given something"
        assert step_run.keyword == "Given"
        assert step_run.status == RunStatus.failed
        assert step_run.parameters == {"x": 1}


class TestRunNode:
    """Tests for RunNode data class."""

    def test_construction(self) -> None:
        """RunNode can be constructed."""
        ref = LifecycleObjectRef(kind="scenario", object_id="s-1", name="S")
        node = RunNode(
            id="n1",
            parent_id="parent",
            kind="scenario",
            object_ref=ref,
            is_active=True,
            opened_at_transition=0,
        )
        assert node.id == "n1"
        assert node.parent_id == "parent"
        assert node.kind == "scenario"
        assert node.is_active is True
        assert node.opened_at_transition == 0
        assert node.closed_at_transition is None

    def test_close_marks_inactive(self) -> None:
        """close() sets is_active False and records transition index."""
        ref = LifecycleObjectRef(kind="scenario", object_id="s-1", name="S")
        node = RunNode(
            id="n1",
            parent_id="parent",
            kind="scenario",
            object_ref=ref,
            is_active=True,
            opened_at_transition=0,
        )
        node.close(at_transition=5)
        assert node.is_active is False
        assert node.closed_at_transition == 5

    def test_as_dict_shape(self) -> None:
        """as_dict returns expected structure."""
        ref = LifecycleObjectRef(kind="scenario", object_id="s-1", name="S")
        node = RunNode(
            id="n1",
            parent_id="parent",
            kind="scenario",
            object_ref=ref,
            is_active=True,
            opened_at_transition=3,
        )
        d = node.as_dict()
        assert d["id"] == "n1"
        assert d["parent_id"] == "parent"
        assert d["kind"] == "scenario"
        assert d["is_active"] is True
        assert d["opened_at_transition"] == 3
        assert d["closed_at_transition"] is None


class TestScenarioRunRequireWithBinding:
    """Tests for require_* methods when binding IS present."""

    def test_require_feature_binding_returns_binding(self) -> None:
        """require_feature_binding returns binding when available."""
        from cucumber_messages import Feature as FeatureMessage
        from cucumber_messages import GherkinDocument, Location, Source

        run = _build_run()
        doc = GherkinDocument(
            comments=[],
            feature=FeatureMessage(
                children=[],
                description="",
                keyword="Feature",
                language="en",
                location=Location(line=1, column=1),
                name="Feature",
                tags=[],
            ),
            uri="file:test.feature",
        )
        source = Source(uri="file:test.feature", data="Feature: Test", media_type="text/x.cucumber.gherkin+plain")
        binding = run.ensure_feature_binding(gherkin_document=doc, source=source)
        sr = _build_scenario_run(run=run)
        sr.feature_uri = "file:test.feature"
        result = sr.require_feature_binding(hook_name="test")
        assert result is binding

    def test_require_gherkin_document_returns_document(self) -> None:
        """require_gherkin_document returns document when set directly."""
        from cucumber_messages import GherkinDocument

        sr = _build_scenario_run()
        sr.gherkin_document = GherkinDocument(comments=[], uri="file:test.feature")
        result = sr.require_gherkin_document(hook_name="test")
        assert isinstance(result, GherkinDocument)

    def test_require_pickle_returns_pickle(self) -> None:
        """require_pickle returns pickle when set."""
        from cucumber_messages import Pickle

        sr = _build_scenario_run()
        pickle = Pickle(
            id="p1",
            uri="file:test.feature",
            ast_node_ids=[],
            language="en",
            name="Test",
            steps=[],
            tags=[],
        )
        sr.pickle = pickle
        result = sr.require_pickle(hook_name="test")
        assert result is pickle

    def test_require_step_object_returns_step(self) -> None:
        """require_step_object returns step_object when set."""
        from cucumber_messages import PickleStep

        sr = _build_scenario_run()
        step = PickleStep(id="s1", type=1, text="a step", ast_node_ids=[])
        sr.step_object = step
        result = sr.require_step_object(hook_name="test")
        assert result is step


class TestScenarioRunEnsureFinishedWithStepNode:
    """Tests for ensure_finished_for_cleanup with active step node."""

    def test_closes_active_step_node(self) -> None:
        """ensure_finished_for_cleanup closes active step_node."""
        from pytest_bdd.model.scenario_run import RunNode

        sr = _build_scenario_run()
        step_ref = LifecycleObjectRef(kind="step", object_id="step-1", name="Step", is_active=True)
        sr.step_node = RunNode(
            id="step-node-1",
            parent_id="scenario-node-1",
            kind="step",
            object_ref=step_ref,
            is_active=True,
            opened_at_transition=0,
        )
        sr.ensure_finished_for_cleanup(at_transition=5)
        assert sr.step_node.is_active is False
        assert sr.step_node.closed_at_transition == 5

    def test_ensures_finished_resets_step_object(self) -> None:
        """ensure_finished_for_cleanup resets step_object and previous_step_object."""
        from cucumber_messages import PickleStep

        sr = _build_scenario_run()
        sr.step_object = PickleStep(id="s1", type=1, text="step", ast_node_ids=[])
        sr.ensure_finished_for_cleanup(at_transition=3)
        assert sr.step_object is None
        assert isinstance(sr.previous_step_object, NoPreviousStep)


class TestScenarioRunFeatureBindingProperty:
    """Tests for feature_binding property with feature_uri."""

    def test_feature_binding_returns_via_uri(self) -> None:
        """feature_binding looks up binding via feature_uri."""
        from cucumber_messages import Feature as FeatureMessage
        from cucumber_messages import GherkinDocument, Location, Source

        run = _build_run()
        doc = GherkinDocument(
            comments=[],
            feature=FeatureMessage(
                children=[],
                description="",
                keyword="Feature",
                language="en",
                location=Location(line=1, column=1),
                name="Feature",
                tags=[],
            ),
            uri="file:bound.feature",
        )
        source = Source(uri="file:bound.feature", data="Feature: Bound", media_type="text/x.cucumber.gherkin+plain")
        binding = run.ensure_feature_binding(gherkin_document=doc, source=source)
        sr = _build_scenario_run(run=run)
        sr.feature_uri = "file:bound.feature"
        result = sr.feature_binding
        assert result is binding


class TestScenarioRunAsDictWithError:
    """Tests for ScenarioRun.as_dict() with error state."""

    def test_as_dict_with_last_error(self) -> None:
        """as_dict serializes last_error when present."""
        sr = _build_scenario_run()
        sr.record_context_error(
            code="object_inactive",
            message="Test error",
            hook_name="test",
            requested_kind="step",
        )
        d = sr.as_dict()
        assert d["last_error"] is not None
        assert d["last_error"]["code"] == "object_inactive"
        assert d["last_error"]["message"] == "Test error"


class TestStepRunAsDict:
    """Tests for StepRun as_dict if it exists."""

    def test_step_run_with_all_values(self) -> None:
        """StepRun can be constructed with all fields."""
        from cucumber_messages import PickleStep

        step = PickleStep(id="s1", type=1, text="step", ast_node_ids=[])
        step_run = StepRun(
            step=step,
            keyword="Given",
            text="a step",
            parameters={"x": 1},
            status=RunStatus.failed,
            duration=0.5,
            attachments=["att1"],
            doc_string="doc",
            data_table="table",
            line_number=5,
        )
        assert step_run.step is step
        assert step_run.keyword == "Given"
        assert step_run.duration == pytest.approx(0.5)
        assert step_run.line_number == 5
