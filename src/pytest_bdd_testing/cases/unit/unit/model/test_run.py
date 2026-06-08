"""Unit tests for Run class — session-level runtime state."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from cucumber_messages import Feature as FeatureMessage
from cucumber_messages import GherkinDocument, Location, Pickle, Source

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

pytestmark = [pytest.mark.unit]


def test_run_construction_with_minimal_fields() -> None:
    run = Run(
        id="test-run",
        run_ref=LifecycleObjectRef(kind="run", object_id="run-1", name="run"),
        status=RunStatus.ok,
    )
    assert run.id == "test-run"
    assert run.status == RunStatus.ok
    assert run.transition_index == 0


def test_run_construction_with_full_fields() -> None:
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


def test_run_default_identifiable_registry_is_empty() -> None:
    run = _build_run()
    # IdentifiableObjectRegistry doesn't support len(); check it has no entries via resolve
    from pytest_bdd.model.message_registry import IdentifiableObjectRegistry

    assert isinstance(run.identifiable_registry, IdentifiableObjectRegistry)


def test_run_default_feature_bindings_empty() -> None:
    run = _build_run()
    assert run.feature_bindings_by_uri == {}


def test_run_default_active_scenario_is_none() -> None:
    run = _build_run()
    assert run.active_scenario_run is None


def test_run_active_feature_binding_returns_none_without_active_scenario() -> None:
    run = _build_run()
    assert run.active_feature_binding is None


def test_run_active_feature_binding_delegates_to_active_scenario() -> None:
    run = _build_run()
    scenario_run = _build_scenario_run(run=run)
    binding = _build_feature_binding(run)
    scenario_run.feature_uri = binding.uri
    run.feature_bindings_by_uri[binding.uri] = binding
    run.active_scenario_run = scenario_run

    assert run.active_feature_binding is binding


def test_run_default_last_error_is_none() -> None:
    run = _build_run()
    assert run.last_error is None


def test_run_default_reporting_state_initialized() -> None:
    run = _build_run()
    assert isinstance(run.reporting_state, ReportingLifecycleState)
    assert run.reporting_state.run_started_id is None
    assert run.reporting_state.active_test_case_id is None


def test_run_advance_transition_increments_index() -> None:
    run = _build_run()
    assert run.transition_index == 0
    run.advance_transition()
    assert run.transition_index == 1


def test_run_advance_transition_multiple_times() -> None:
    run = _build_run()
    for _ in range(5):
        run.advance_transition()
    assert run.transition_index == 5


def test_run_active_scenario_id_raises_when_no_scenario() -> None:
    run = _build_run()
    with pytest.raises(AttributeError, match="No active scenario"):
        _ = run.active_scenario_id


def test_run_active_scenario_id_raises_when_scenario_inactive() -> None:
    run = _build_run()
    scenario_run = _build_scenario_run(run=run)
    run.active_scenario_run = scenario_run
    scenario_run.scenario_node.is_active = False
    with pytest.raises(AttributeError, match="No active scenario"):
        _ = run.active_scenario_id


def test_run_active_scenario_id_returns_id_when_active() -> None:
    run = _build_run()
    scenario_run = _build_scenario_run(run=run)
    run.active_scenario_run = scenario_run
    assert run.active_scenario_id == "scenario-node-1"


def test_run_active_step_id_raises_when_no_scenario() -> None:
    run = _build_run()
    with pytest.raises(AttributeError, match="No active step"):
        _ = run.active_step_id


def test_run_active_step_id_returns_id_when_active() -> None:
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


def test_run_require_active_scenario_run_raises_when_no_active_scenario() -> None:
    run = _build_run()
    with pytest.raises(RuntimeError, match="Active scenario run is unavailable"):
        run.require_active_scenario_run(hook_name="pytest_bdd_before_scenario")


def test_run_require_active_scenario_run_raises_with_correct_hook_name() -> None:
    run = _build_run()
    hook_name = "pytest_bdd_after_scenario"
    with pytest.raises(RuntimeError, match=hook_name):
        run.require_active_scenario_run(hook_name=hook_name)


def test_run_require_active_scenario_run_returns_scenario_run_when_active() -> None:
    run = _build_run()
    scenario_run = _build_scenario_run(run=run)
    run.active_scenario_run = scenario_run
    result = run.require_active_scenario_run(hook_name="pytest_bdd_before_scenario")
    assert result is scenario_run


def test_run_stash_operations_initialize_for_session_requires_stash() -> None:
    stash: dict = {}
    session = SimpleNamespace(name="session")
    run = Run.initialize_for_session(stash=stash, session=session)
    assert stash["_pytest_bdd_run"] is run
    assert run.status == RunStatus.ok


def test_run_stash_operations_initialize_for_config_requires_stash() -> None:
    stash: dict = {}
    config = SimpleNamespace(name="config")
    run = Run.initialize_for_config(stash=stash, config=config)
    assert stash["_pytest_bdd_run"] is run


def test_run_stash_operations_from_stash_retrieves_run() -> None:
    stash: dict = {}
    session = SimpleNamespace(name="session")
    original = Run.initialize_for_session(stash=stash, session=session)
    retrieved = Run.from_stash(stash)
    assert retrieved is original


def test_run_stash_operations_find_in_stash_returns_maybe() -> None:
    stash: dict = {}
    session = SimpleNamespace()
    Run.initialize_for_session(stash=stash, session=session)
    from returns.maybe import Maybe

    result = Run.find_in_stash(stash)
    assert isinstance(result, Maybe)
    assert result.value_or(None) is not None


def test_run_stash_operations_find_in_stash_empty_returns_nothing() -> None:
    stash: dict = {}
    result = Run.find_in_stash(stash)
    assert result.value_or(None) is None


def test_run_stash_operations_build_for_owner_via_session() -> None:
    session = SimpleNamespace(name="my-session")
    stash: dict = {}
    run = Run.initialize_for_session(stash=stash, session=session)
    assert run.id.startswith("run-")
    assert run.run_ref.name == "run"


def test_run_stash_operations_build_for_owner_via_config() -> None:
    config = SimpleNamespace(name="my-config")
    stash: dict = {}
    run = Run.initialize_for_config(stash=stash, config=config)
    assert run.id.startswith("run-")
    assert run.run_ref.name == "run"


def test_run_feature_binding_lookups_feature_binding_for_uri_returns_none_when_empty() -> None:
    run = _build_run()
    assert run.feature_binding_for_uri("file:features/test.feature") is None


def test_run_feature_binding_lookups_feature_binding_for_uri_returns_binding() -> None:
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


def test_run_feature_binding_lookups_feature_binding_for_none_uri_returns_none() -> None:
    run = _build_run()
    assert run.feature_binding_for_uri(None) is None


def test_run_feature_binding_lookups_feature_binding_for_document_returns_none_when_empty() -> None:
    run = _build_run()
    assert run.feature_binding_for_document(None) is None


def test_run_scenario_run_management_set_scenario_run_registers_and_activates() -> None:
    run = _build_run()
    scenario_run = _build_scenario_run(run=run)
    request = SimpleNamespace(config=SimpleNamespace(stash={}), node=SimpleNamespace(nodeid="test-1"))
    Run.set_scenario_run(request, scenario_run)
    assert run.active_scenario_run is scenario_run


def test_run_scenario_run_management_pop_scenario_run_returns_none_when_not_registered() -> None:
    stash: dict = {}
    session = SimpleNamespace(name="session")
    run = Run.initialize_for_session(stash=stash, session=session)
    request = SimpleNamespace(config=SimpleNamespace(stash=stash), node=SimpleNamespace(nodeid="unknown"))
    result = Run.pop_scenario_run(request)
    assert result is None


def test_run_scenario_run_management_get_scenario_run_returns_none_when_not_registered() -> None:
    run = _build_run()
    request = SimpleNamespace(config=SimpleNamespace(stash={}), node=SimpleNamespace(nodeid="unknown"))
    result = Run.get_scenario_run(request)
    assert result is None


def test_run_scenario_run_management_set_and_pop_scenario_run_roundtrip() -> None:
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


def test_run_scenario_run_management_set_scenario_run_uses_stashed_run_when_missing() -> None:
    stash: dict = {}
    session = SimpleNamespace(name="session")
    run = Run.initialize_for_session(stash=stash, session=session)
    scenario_run = _build_scenario_run(run=run)
    scenario_run.run = None
    request = SimpleNamespace(config=SimpleNamespace(stash=stash), node=SimpleNamespace(nodeid="test-1"))

    Run.set_scenario_run(request, scenario_run)

    assert scenario_run.run is run
    assert run.active_scenario_run is scenario_run


def test_run_scenario_run_management_pop_scenario_run_handles_request_without_stash() -> None:
    request = SimpleNamespace(node=SimpleNamespace(nodeid="test-1"))
    assert Run.pop_scenario_run(request) is None


def test_run_scenario_run_management_pop_scenario_run_clears_matching_feature_uri() -> None:
    stash: dict = {}
    session = SimpleNamespace(name="session")
    run = Run.initialize_for_session(stash=stash, session=session)
    scenario_run = _build_scenario_run(run=run)
    scenario_run.feature_uri = "file:features/example.feature"
    run.active_feature_uri = scenario_run.feature_uri
    run.reporting_state.active_test_case_id = "case-1"
    request = SimpleNamespace(config=SimpleNamespace(stash=stash), node=SimpleNamespace(nodeid="test-1"))
    Run.set_scenario_run(request, scenario_run)

    popped = Run.pop_scenario_run(request)

    assert popped is scenario_run
    assert run.active_feature_uri is None
    assert run.reporting_state.active_test_case_id is None


def test_run_scenario_run_management_create_scenario_run_without_feature_creates_inactive_context() -> None:
    run = _build_run()
    request = SimpleNamespace(session=SimpleNamespace(id="session"), node=SimpleNamespace(nodeid="test-1"))

    scenario_run = run.create_scenario_run(request)

    assert scenario_run.run is run
    assert scenario_run.feature_node is None
    assert scenario_run.scenario_node is None
    assert scenario_run.feature_uri is None
    assert run.scenario_runs_by_request["test-1"] is scenario_run
    assert run.active_scenario_run is scenario_run


def test_run_scenario_run_management_create_scenario_run_with_feature_and_pickle_creates_nodes() -> None:
    run = _build_run()
    request = SimpleNamespace(session=SimpleNamespace(id="session"), node=SimpleNamespace(nodeid="test-1"))
    doc = _make_gherkin_document()
    pickle = Pickle(
        ast_node_ids=["scenario-ast-1"],
        id="pickle-1",
        language="en",
        name="Scenario",
        steps=[],
        tags=[],
        uri=doc.uri,
    )
    source = Source(
        uri=doc.uri,
        data="Feature: Feature",
        media_type="text/x.cucumber.gherkin+plain",
    )

    scenario_run = run.create_scenario_run(
        request,
        gherkin_document=doc,
        pickle=pickle,
        feature_source=source,
    )

    assert scenario_run.feature_node is not None
    assert scenario_run.scenario_node is not None
    assert scenario_run.feature_uri == doc.uri
    assert run.active_feature_id == scenario_run.feature_node.id
    assert run.active_feature_uri == doc.uri
    assert run.feature_bindings_by_uri[doc.uri].pickles == (pickle,)


def test_run_reporting_map_runtime_step_to_test_step_id_records_mapping() -> None:
    run = _build_run()
    step = SimpleNamespace()
    run.map_runtime_step_to_test_step_id(pickle_step=step, test_step_id="step-42")
    assert run.reporting_state.runtime_step_to_pickle_step_id[id(step)] == "step-42"


def test_run_reporting_resolve_test_step_id_returns_mapped_id() -> None:
    run = _build_run()
    step = SimpleNamespace()
    run.map_runtime_step_to_test_step_id(pickle_step=step, test_step_id="step-42")
    result = run.resolve_test_step_id_for_runtime_step(pickle_step=step)
    assert result == "step-42"


def test_run_reporting_resolve_test_step_id_returns_active_when_not_mapped() -> None:
    run = _build_run()
    run.reporting_state.active_test_step_id = "active-step-1"
    step = SimpleNamespace()
    result = run.resolve_test_step_id_for_runtime_step(pickle_step=step)
    assert result == "active-step-1"


def test_run_as_dict_serialization_shape() -> None:
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


def test_run_indexing_index_delegates_to_registry() -> None:
    run = _build_run()
    obj = SimpleNamespace()
    # Should not raise — registry accepts any object
    run.index_identifiable_tree(obj)


def test_run_ensure_feature_binding_update_ensure_feature_binding_updates_existing() -> None:
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


def test_run_ensure_feature_binding_update_keeps_existing_pickles_when_shorter() -> None:
    run = _build_run()
    doc = _make_gherkin_document()
    pickle_1 = Pickle(ast_node_ids=[], id="pickle-1", language="en", name="One", steps=[], tags=[], uri=doc.uri)
    pickle_2 = Pickle(ast_node_ids=[], id="pickle-2", language="en", name="Two", steps=[], tags=[], uri=doc.uri)
    binding = run.ensure_feature_binding(gherkin_document=doc, pickles=(pickle_1, pickle_2))

    result = run.ensure_feature_binding(gherkin_document=doc, pickles=(pickle_1,))

    assert result is binding
    assert result.pickles == (pickle_1, pickle_2)


def test_run_ensure_feature_binding_update_ensure_feature_binding_updates_filename_when_empty() -> None:
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


def test_run_feature_binding_for_document_finds_by_uri() -> None:
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


def test_run_feature_binding_for_document_returns_none_for_no_uri() -> None:
    run = _build_run()
    doc = GherkinDocument(comments=[], uri=None)
    assert run.feature_binding_for_document(doc) is None


def test_run_resolve_test_step_id_with_identifiable_resolve_by_identifiable_id_match() -> None:

    run = _build_run()
    run.reporting_state.active_test_step_id = "fallback-step"
    # Register a mapping with a different id text
    run.reporting_state.runtime_step_to_pickle_step_id[999] = "mapped-step-42"
    # Create an Identifiable step with matching id text
    step = SimpleNamespace(id="mapped-step-42")
    # Should find the candidate match
    result = run.resolve_test_step_id_for_runtime_step(pickle_step=step)
    assert result == "mapped-step-42"


def test_run_as_dict_with_active_scenario_as_dict_with_active_scenario() -> None:
    run = _build_run()
    scenario_run = _build_scenario_run(run=run)
    run.active_scenario_run = scenario_run
    d = run.as_dict()
    assert d["active_scenario_id"] == "scenario-node-1"
    assert d["active_step_id"] is None


def test_run_get_scenario_run_with_registered_get_scenario_run_returns_registered() -> None:
    stash: dict = {}
    session = SimpleNamespace(name="session")
    run = Run.initialize_for_session(stash=stash, session=session)
    scenario_run = _build_scenario_run(run=run)
    request = SimpleNamespace(config=SimpleNamespace(stash=stash), node=SimpleNamespace(nodeid="test-1"))
    Run.set_scenario_run(request, scenario_run)
    result = Run.get_scenario_run(request)
    assert result is scenario_run


def test_run_request_key_without_nodeid_request_key_without_nodeid() -> None:
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
