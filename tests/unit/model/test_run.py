"""Unit tests for Run class — session-level runtime state."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from cucumber_messages import Feature as FeatureMessage
from cucumber_messages import GherkinDocument, Location, Source

from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
from pytest_bdd.model.run import (
    ActiveObjectSet,
    HookPhase,
    LifecycleObjectRef,
    ReportingLifecycleState,
    Run,
    RunStage,
    RunStatus,
    _no_previous_step_ref,
)
from pytest_bdd.model.scenario_run import ScenarioRun


class TestRun:
    """Tests for Run class construction and basic state."""

    def test_run_construction_with_minimal_fields(self) -> None:
        """Run can be constructed with required fields only."""
        run = Run(
            id="test-run",
            run_ref=LifecycleObjectRef(kind="run", object_id="run-1", name="run"),
            status=RunStatus.ok,
        )
        assert run.id == "test-run"
        assert run.status == RunStatus.ok
        assert run.transition_index == 0

    def test_run_construction_with_full_fields(self) -> None:
        """Run can be constructed with all fields populated."""
        run = Run(
            id="test-run",
            run_ref=LifecycleObjectRef(kind="run", object_id="run-1", name="run"),
            status=RunStatus.failed,
            transition_index=5,
            active_feature_id="feature-1",
            active_feature_uri="features/test.feature",
        )
        assert run.id == "test-run"
        assert run.status == RunStatus.failed
        assert run.transition_index == 5
        assert run.active_feature_id == "feature-1"
        assert run.active_feature_uri == "features/test.feature"

    def test_run_default_identifiable_registry_is_empty(self) -> None:
        """New Run has an empty identifiable registry."""
        run = _build_run()
        # IdentifiableObjectRegistry doesn't support len(); check it has no entries via resolve
        from pytest_bdd.model.message_registry import IdentifiableObjectRegistry

        assert isinstance(run.identifiable_registry, IdentifiableObjectRegistry)

    def test_run_default_feature_bindings_empty(self) -> None:
        """New Run has no feature bindings."""
        run = _build_run()
        assert run.feature_bindings_by_uri == {}

    def test_run_default_active_scenario_is_none(self) -> None:
        """New Run has no active scenario."""
        run = _build_run()
        assert run.active_scenario_run is None

    def test_run_default_last_error_is_none(self) -> None:
        """New Run has no last error."""
        run = _build_run()
        assert run.last_error is None

    def test_run_default_reporting_state_initialized(self) -> None:
        """New Run has initialized reporting state."""
        run = _build_run()
        assert isinstance(run.reporting_state, ReportingLifecycleState)
        assert run.reporting_state.run_started_id is None
        assert run.reporting_state.active_test_case_id is None


class TestRunAdvanceTransition:
    """Tests for Run.advance_transition()."""

    def test_advance_transition_increments_index(self) -> None:
        """advance_transition increments transition_index by 1."""
        run = _build_run()
        assert run.transition_index == 0
        run.advance_transition()
        assert run.transition_index == 1

    def test_advance_transition_multiple_times(self) -> None:
        """advance_transition can be called multiple times."""
        run = _build_run()
        for _ in range(5):
            run.advance_transition()
        assert run.transition_index == 5


class TestRunActiveScenarioId:
    """Tests for Run.active_scenario_id property."""

    def test_active_scenario_id_raises_when_no_scenario(self) -> None:
        """active_scenario_id raises AttributeError when no active scenario."""
        run = _build_run()
        with pytest.raises(AttributeError, match="No active scenario"):
            _ = run.active_scenario_id

    def test_active_scenario_id_raises_when_scenario_inactive(self) -> None:
        """active_scenario_id raises when scenario node exists but is inactive."""
        run = _build_run()
        scenario_run = _build_scenario_run(run=run)
        run.active_scenario_run = scenario_run
        scenario_run.scenario_node.is_active = False
        with pytest.raises(AttributeError, match="No active scenario"):
            _ = run.active_scenario_id

    def test_active_scenario_id_returns_id_when_active(self) -> None:
        """active_scenario_id returns the scenario node ID when active."""
        run = _build_run()
        scenario_run = _build_scenario_run(run=run)
        run.active_scenario_run = scenario_run
        assert run.active_scenario_id == "scenario-node-1"


class TestRunActiveStepId:
    """Tests for Run.active_step_id property."""

    def test_active_step_id_raises_when_no_scenario(self) -> None:
        """active_step_id raises AttributeError when no active scenario."""
        run = _build_run()
        with pytest.raises(AttributeError, match="No active step"):
            _ = run.active_step_id

    def test_active_step_id_returns_id_when_active(self) -> None:
        """active_step_id returns the step node ID when active."""
        from pytest_bdd.model.scenario_run import RunNode

        run = _build_run()
        scenario_run = _build_scenario_run(run=run)
        run.active_scenario_run = scenario_run
        step_node = RunNode(
            id="step-1",
            parent_id="scenario-node-1",
            kind="step",
            object_ref=_no_previous_step_ref(),
            is_active=True,
            opened_at_transition=0,
        )
        scenario_run.step_node = step_node
        assert run.active_step_id == "step-1"


class TestRunRequireActiveScenarioRun:
    """Tests for Run.require_active_scenario_run()."""

    def test_raises_when_no_active_scenario(self) -> None:
        """Raises RuntimeError when no active scenario run exists."""
        run = _build_run()
        with pytest.raises(RuntimeError, match="Active scenario run is unavailable"):
            run.require_active_scenario_run(hook_name="pytest_bdd_before_scenario")

    def test_raises_with_correct_hook_name(self) -> None:
        """Error message includes the hook_name."""
        run = _build_run()
        hook_name = "pytest_bdd_after_scenario"
        with pytest.raises(RuntimeError, match=hook_name):
            run.require_active_scenario_run(hook_name=hook_name)

    def test_returns_scenario_run_when_active(self) -> None:
        """Returns the active ScenarioRun instance."""
        run = _build_run()
        scenario_run = _build_scenario_run(run=run)
        run.active_scenario_run = scenario_run
        result = run.require_active_scenario_run(hook_name="pytest_bdd_before_scenario")
        assert result is scenario_run


class TestRunStashOperations:
    """Tests for Run stash-bound operations."""

    def test_initialize_for_session_requires_stash(self) -> None:
        """initialize_for_session stores Run in stash."""
        stash: dict = {}
        session = SimpleNamespace(name="session")
        run = Run.initialize_for_session(stash=stash, session=session)
        assert stash["_pytest_bdd_run"] is run
        assert run.status == RunStatus.ok

    def test_initialize_for_config_requires_stash(self) -> None:
        """initialize_for_config stores Run in stash."""
        stash: dict = {}
        config = SimpleNamespace(name="config")
        run = Run.initialize_for_config(stash=stash, config=config)
        assert stash["_pytest_bdd_run"] is run

    def test_from_stash_retrieves_run(self) -> None:
        """Run can be retrieved from stash via from_stash."""
        stash: dict = {}
        session = SimpleNamespace(name="session")
        original = Run.initialize_for_session(stash=stash, session=session)
        retrieved = Run.from_stash(stash)
        assert retrieved is original

    def test_find_in_stash_returns_maybe(self) -> None:
        """find_in_stash returns Maybe with Run or Nothing."""
        stash: dict = {}
        session = SimpleNamespace()
        Run.initialize_for_session(stash=stash, session=session)
        from returns.maybe import Maybe

        result = Run.find_in_stash(stash)
        assert isinstance(result, Maybe)
        assert result.value_or(None) is not None

    def test_find_in_stash_empty_returns_nothing(self) -> None:
        """find_in_stash on empty stash returns Nothing."""
        stash: dict = {}
        result = Run.find_in_stash(stash)
        assert result.value_or(None) is None

    def test_build_for_owner_via_session(self) -> None:
        """Run built for a session-like owner gets named from owner."""
        session = SimpleNamespace(name="my-session")
        stash: dict = {}
        run = Run.initialize_for_session(stash=stash, session=session)
        assert run.id.startswith("run-")
        assert run.run_ref.name == "run"

    def test_build_for_owner_via_config(self) -> None:
        """Run built for a config-like owner gets named from owner."""
        config = SimpleNamespace(name="my-config")
        stash: dict = {}
        run = Run.initialize_for_config(stash=stash, config=config)
        assert run.id.startswith("run-")
        assert run.run_ref.name == "run"


class TestRunFeatureBindingLookups:
    """Tests for feature binding lookup methods on Run."""

    def test_feature_binding_for_uri_returns_none_when_empty(self) -> None:
        """feature_binding_for_uri returns None when no bindings registered."""
        run = _build_run()
        assert run.feature_binding_for_uri("file:features/test.feature") is None

    def test_feature_binding_for_uri_returns_binding(self) -> None:
        """feature_binding_for_uri returns matching binding."""
        run = _build_run()
        doc = _make_gherkin_document()
        binding = run.ensure_feature_binding(
            gherkin_document=doc,
            source=SimpleNamespace(
                uri="file:features/example.feature",
                data="Feature: Feature",
                media_type="text/x.cucumber.gherkin+plain",
            ),
        )
        result = run.feature_binding_for_uri("file:features/example.feature")
        assert result is binding

    def test_feature_binding_for_none_uri_returns_none(self) -> None:
        """feature_binding_for_uri returns None for None input."""
        run = _build_run()
        assert run.feature_binding_for_uri(None) is None

    def test_feature_binding_for_document_returns_none_when_empty(self) -> None:
        """feature_binding_for_document returns None when no bindings."""
        run = _build_run()
        assert run.feature_binding_for_document(None) is None


class TestRunScenarioRunManagement:
    """Tests for scenario run registration methods on Run."""

    def test_set_scenario_run_registers_and_activates(self) -> None:
        """set_scenario_run registers the scenario and sets it as active."""
        run = _build_run()
        scenario_run = _build_scenario_run(run=run)
        request = SimpleNamespace(config=SimpleNamespace(stash={}), node=SimpleNamespace(nodeid="test-1"))
        Run.set_scenario_run(request, scenario_run)
        assert run.active_scenario_run is scenario_run

    def test_pop_scenario_run_returns_none_when_not_registered(self) -> None:
        """pop_scenario_run returns None when no scenario registered for request key."""
        stash: dict = {}
        session = SimpleNamespace(name="session")
        run = Run.initialize_for_session(stash=stash, session=session)
        request = SimpleNamespace(config=SimpleNamespace(stash=stash), node=SimpleNamespace(nodeid="unknown"))
        result = Run.pop_scenario_run(request)
        assert result is None

    def test_get_scenario_run_returns_none_when_not_registered(self) -> None:
        """get_scenario_run returns None for unregistered request key."""
        run = _build_run()
        request = SimpleNamespace(config=SimpleNamespace(stash={}), node=SimpleNamespace(nodeid="unknown"))
        result = Run.get_scenario_run(request)
        assert result is None

    def test_set_and_pop_scenario_run_roundtrip(self) -> None:
        """Full roundtrip: set then pop returns same scenario_run and deactivates."""
        stash: dict = {}
        session = SimpleNamespace(name="session")
        run = Run.initialize_for_session(stash=stash, session=session)
        scenario_run = _build_scenario_run(run=run)
        request = SimpleNamespace(config=SimpleNamespace(stash=stash), node=SimpleNamespace(nodeid="test-1"))
        Run.set_scenario_run(request, scenario_run)
        assert run.active_scenario_run is scenario_run
        assert run.scenario_runs_by_request["test-1"] is scenario_run

        popped = Run.pop_scenario_run(request)
        assert popped is scenario_run
        assert run.active_scenario_run is None


class TestRunReporting:
    """Tests for Run reporting state tracking."""

    def test_map_runtime_step_to_test_step_id_records_mapping(self) -> None:
        """map_runtime_step_to_test_step_id stores the mapping."""
        run = _build_run()
        step = SimpleNamespace()
        run.map_runtime_step_to_test_step_id(pickle_step=step, test_step_id="step-42")
        assert run.reporting_state.runtime_step_to_pickle_step_id[id(step)] == "step-42"

    def test_resolve_test_step_id_returns_mapped_id(self) -> None:
        """resolve_test_step_id_for_runtime_step returns previously mapped ID."""
        run = _build_run()
        step = SimpleNamespace()
        run.map_runtime_step_to_test_step_id(pickle_step=step, test_step_id="step-42")
        result = run.resolve_test_step_id_for_runtime_step(pickle_step=step)
        assert result == "step-42"

    def test_resolve_test_step_id_returns_active_when_not_mapped(self) -> None:
        """resolve_test_step_id falls back to active_test_step_id."""
        run = _build_run()
        run.reporting_state.active_test_step_id = "active-step-1"
        step = SimpleNamespace()
        result = run.resolve_test_step_id_for_runtime_step(pickle_step=step)
        assert result == "active-step-1"


class TestRunAsDict:
    """Tests for Run.as_dict() serialization."""

    def test_serialization_shape(self) -> None:
        """as_dict returns expected top-level keys and types."""
        run = _build_run()
        d = run.as_dict()
        assert d["run_id"] == "run-1"
        assert d["status"] == "ok"
        assert d["transition_index"] == 0
        assert d["feature_bindings_by_uri"] == []
        assert d["active_feature_id"] is None
        assert d["active_feature_uri"] is None
        assert d["active_scenario_id"] is None
        assert d["active_step_id"] is None
        assert d["last_error"] is None
        assert "reporting_state" in d


class TestRunIndexing:
    """Tests for Run.index_identifiable_tree()."""

    def test_index_delegates_to_registry(self) -> None:
        """index_identifiable_tree calls identifiable_registry.index_tree."""
        run = _build_run()
        obj = SimpleNamespace()
        # Should not raise — registry accepts any object
        run.index_identifiable_tree(obj)


class TestRunEnsureFeatureBindingUpdate:
    """Tests for ensure_feature_binding update path."""

    def test_ensure_feature_binding_updates_existing(self) -> None:
        """ensure_feature_binding updates existing binding with new source/pickles."""
        run = _build_run()
        doc = _make_gherkin_document()
        source1 = Source(
            uri="file:features/example.feature",
            data="Feature: Original",
            media_type="text/x.cucumber.gherkin+plain",
        )
        first = run.ensure_feature_binding(gherkin_document=doc, source=source1)
        # Call again with updated source
        source2 = Source(
            uri="file:features/example.feature",
            data="Feature: Updated",
            media_type="text/x.cucumber.gherkin+plain",
        )
        second = run.ensure_feature_binding(gherkin_document=doc, source=source2)
        assert first is second
        assert second.source.data == "Feature: Updated"

    def test_ensure_feature_binding_updates_filename_when_empty(self) -> None:
        """ensure_feature_binding sets filename when it was empty."""
        run = _build_run()
        doc = _make_gherkin_document(uri="file:features/test.feature")
        binding = FeatureRuntimeBinding(
            uri="file:features/test.feature",
            filename="",
            gherkin_document=doc,
            run=run,
        )
        run.feature_bindings_by_uri["file:features/test.feature"] = binding
        # Call ensure_feature_binding which should update the existing binding
        result = run.ensure_feature_binding(gherkin_document=doc)
        # The binding should be the same object (reused)
        assert result is binding
        # filename should be updated from URI
        assert result.filename == "features/test.feature"


class TestRunFeatureBindingForDocument:
    """Tests for feature_binding_for_document."""

    def test_feature_binding_for_document_finds_by_uri(self) -> None:
        """feature_binding_for_document looks up binding via document URI."""
        run = _build_run()
        doc = _make_gherkin_document()
        source = Source(
            uri="file:features/example.feature",
            data="Feature: Feature",
            media_type="text/x.cucumber.gherkin+plain",
        )
        run.ensure_feature_binding(gherkin_document=doc, source=source)
        result = run.feature_binding_for_document(doc)
        assert result is not None
        assert result.uri == "file:features/example.feature"

    def test_feature_binding_for_document_returns_none_for_no_uri(self) -> None:
        """feature_binding_for_document returns None when document has no URI."""
        run = _build_run()
        doc = GherkinDocument(comments=[], uri=None)
        assert run.feature_binding_for_document(doc) is None


class TestRunResolveTestStepIdWithIdentifiable:
    """Tests for resolve_test_step_id with Identifiable step."""

    def test_resolve_by_identifiable_id_match(self) -> None:
        """resolve_test_step_id falls back to checking Identifiable.id."""

        run = _build_run()
        run.reporting_state.active_test_step_id = "fallback-step"
        # Register a mapping with a different id text
        run.reporting_state.runtime_step_to_pickle_step_id[999] = "mapped-step-42"
        # Create an Identifiable step with matching id text
        step = SimpleNamespace(id="mapped-step-42")
        # Should find the candidate match
        result = run.resolve_test_step_id_for_runtime_step(pickle_step=step)
        assert result == "mapped-step-42"


class TestRunAsDictWithActiveScenario:
    """Tests for Run.as_dict() with active scenario."""

    def test_as_dict_with_active_scenario(self) -> None:
        """as_dict includes active_scenario_id and active_step_id when present."""
        run = _build_run()
        scenario_run = _build_scenario_run(run=run)
        run.active_scenario_run = scenario_run
        d = run.as_dict()
        assert d["active_scenario_id"] == "scenario-node-1"
        assert d["active_step_id"] is None


class TestRunGetScenarioRunWithRegistered:
    """Tests for get_scenario_run with registered scenario."""

    def test_get_scenario_run_returns_registered(self) -> None:
        """get_scenario_run returns the registered ScenarioRun."""
        stash: dict = {}
        session = SimpleNamespace(name="session")
        run = Run.initialize_for_session(stash=stash, session=session)
        scenario_run = _build_scenario_run(run=run)
        request = SimpleNamespace(config=SimpleNamespace(stash=stash), node=SimpleNamespace(nodeid="test-1"))
        Run.set_scenario_run(request, scenario_run)
        result = Run.get_scenario_run(request)
        assert result is scenario_run


class TestRunRequestKeyWithoutNodeid:
    """Tests for _request_key edge cases."""

    def test_request_key_without_nodeid(self) -> None:
        """_request_key falls back to request id when no nodeid."""
        request = SimpleNamespace(config=SimpleNamespace(stash={}))
        key = Run._request_key(request)
        assert key.startswith("request-")


def _build_feature_binding(run: Run) -> FeatureRuntimeBinding:
    from cucumber_messages import Feature as FeatureMessage
    from cucumber_messages import GherkinDocument, Location

    feature_message = FeatureMessage(
        children=[],
        description="",
        keyword="Feature",
        language="en",
        location=Location(line=1, column=1),
        name="Feature",
        tags=[],
    )
    gherkin_document = GherkinDocument(
        comments=[],
        feature=feature_message,
        uri="file:features/example.feature",
    )
    source = Source(
        uri="file:features/example.feature",
        data="Feature: Feature",
        media_type="text/x.cucumber.gherkin+plain",
    )
    return FeatureRuntimeBinding.build(
        run=run,
        gherkin_document=gherkin_document,
        source=source,
    )


# Module-level helpers
def _make_gherkin_document(uri="file:features/example.feature", name="Feature"):
    """Create a minimal GherkinDocument for testing."""
    feature_message = FeatureMessage(
        children=[],
        description="Test feature",
        keyword="Feature",
        language="en",
        location=Location(line=1, column=1),
        name=name,
        tags=[],
    )
    return GherkinDocument(
        comments=[],
        feature=feature_message,
        uri=uri,
    )


def _build_run(**kwargs) -> Run:
    return Run(
        id="run-1",
        run_ref=LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True),
        status=RunStatus.ok,
        **kwargs,
    )


def _build_scenario_run(run: Run) -> ScenarioRun:
    from pytest_bdd.model.scenario_run import RunNode

    run_ref = run.run_ref
    feature_ref = LifecycleObjectRef(kind="feature", object_id="feature-1", name="Feature", is_active=True)
    scenario_ref = LifecycleObjectRef(kind="scenario", object_id="scenario-1", name="Scenario", is_active=True)
    return ScenarioRun(
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
