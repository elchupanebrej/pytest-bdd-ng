from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import TestCase as CucumberTestCase  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import TestStep as CucumberTestStep

from pytest_bdd.model.execution_context import ExecutionStatus, LifecycleObjectRef, SessionExecutionContext
from pytest_bdd.plugin.scenario_runner.context_store import ExecutionContextStore


class _Stash:
    def __init__(self) -> None:
        self._items: dict[str, object] = {}

    def __contains__(self, key: object) -> bool:
        return key in self._items

    def __getitem__(self, key: str) -> object:
        return self._items[key]

    def __setitem__(self, key: str, value: object) -> None:
        self._items[key] = value


@dataclass(slots=True)
class _RuntimeObject:
    name: str
    id: str


def _build_session_root(suffix: str) -> SessionExecutionContext:
    return SessionExecutionContext(
        session_context_id=f"session-{suffix}",
        run_ref=LifecycleObjectRef(kind="run", object_id=f"run-{suffix}", is_active=True),
        status=ExecutionStatus.ok,
    )


def test_config_stash_lookup_supports_stash_without_get_method() -> None:
    config = SimpleNamespace(stash=_Stash())
    session_root = _build_session_root("stash")

    ExecutionContextStore.set_session_root_in_config(config, session_root)

    assert ExecutionContextStore.get_session_root_from_config(config) is session_root


def test_ensure_session_root_reuses_existing_stash_value() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    existing = _build_session_root("existing")
    ExecutionContextStore.set_session_root_in_config(config, existing)

    resolved = ExecutionContextStore.ensure_session_root_for_session(config=config, session=session)

    assert resolved is existing


def test_ensure_session_root_creates_and_stores_value_when_missing() -> None:
    config = SimpleNamespace()
    session = SimpleNamespace(config=config, name="run-session")

    resolved = ExecutionContextStore.ensure_session_root_for_session(config=config, session=session)

    assert resolved.status == ExecutionStatus.ok
    assert resolved.run_ref.kind == "run"
    assert resolved.run_ref.object_id == "run-session"
    assert ExecutionContextStore.get_session_root_from_config(config) is resolved


def test_get_session_root_prefers_config_stash_binding() -> None:
    store = ExecutionContextStore()
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::id"))

    store.initialize_session_root(session=session)
    preferred_root = _build_session_root("preferred")
    ExecutionContextStore.set_session_root_in_config(config, preferred_root)

    assert store.get_session_root(request) is preferred_root


def test_pop_clears_active_scenario_and_step_context_ids() -> None:
    store = ExecutionContextStore()
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::scenario"))
    feature = _RuntimeObject(name="Feature", id="feature-1")
    scenario = _RuntimeObject(name="Scenario", id="scenario-1")

    context = store.get_or_create(request, feature=feature, scenario=scenario)
    context.session_context.active_step_context_id = "step-ctx-1"

    popped = store.pop(request)

    assert popped is context
    assert context.session_context.active_scenario_context_id is None
    assert context.session_context.active_step_context_id is None


def test_get_or_create_copies_reporting_state_from_session_root() -> None:
    store = ExecutionContextStore()
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::scenario"))
    session_root = store.initialize_session_root(session=session)
    session_root.reporting_state.run_started_id = "run-started-42"
    session_root.reporting_state.test_run_hook_started_id = "hook-started-42"

    context = store.get_or_create(request)

    assert context.reporting_state.run_started_id == "run-started-42"
    assert context.reporting_state.test_run_hook_started_id == "hook-started-42"
    assert context.session_context.reporting_state.run_started_id == "run-started-42"


def test_context_is_shared_via_config_stash_across_store_instances() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::scenario"))
    writer_store = ExecutionContextStore()
    reader_store = ExecutionContextStore()

    context = writer_store.get_or_create(request)
    resolved = reader_store.get(request)

    assert resolved is context
    contexts = config.stash[ExecutionContextStore.CONTEXTS_STASH_KEY]
    assert contexts["node::scenario"] is context


def test_pop_removes_context_from_config_stash_registry() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::scenario"))
    store = ExecutionContextStore()
    store.get_or_create(request)

    popped = store.pop(request)

    assert popped is not None
    contexts = config.stash[ExecutionContextStore.CONTEXTS_STASH_KEY]
    assert "node::scenario" not in contexts


def test_get_or_create_binds_feature_object_when_feature_provided() -> None:
    store = ExecutionContextStore()
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::scenario"))
    feature = SimpleNamespace(uri="features/example.feature", gherkin_document=SimpleNamespace(feature=None))

    context = store.get_or_create(request, feature=feature)

    assert context.feature_object is feature


def test_ensure_session_root_initializes_envelope_registry_in_config_stash() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")

    _ = ExecutionContextStore.ensure_session_root_for_session(config=config, session=session)

    assert ExecutionContextStore.get_envelope_registry_from_config(config) is not None
    assert ExecutionContextStore.ENVELOPE_REGISTRY_STASH_KEY in config.stash


def test_register_envelope_indexes_identifiable_objects_by_protocol() -> None:
    config = SimpleNamespace(stash={})
    envelope = Message(
        test_case=CucumberTestCase(
            id="test-case-1",
            pickle_id="pickle-1",
            test_steps=[CucumberTestStep(id="test-step-1", pickle_step_id="pickle-step-1")],
        )
    )

    registry = ExecutionContextStore.register_envelope_in_config(config, envelope)

    assert registry.envelopes == [envelope]
    assert registry.resolve("test-case-1") is envelope.test_case
    assert registry.resolve("test-step-1") is envelope.test_case.test_steps[0]


def test_pop_resets_reporting_and_reference_states() -> None:
    store = ExecutionContextStore()
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::scenario"))
    context = store.get_or_create(request)
    context.reporting_state.active_test_case_started_id = "case-started-1"
    context.reporting_state.active_test_step_id = "step-1"
    context.reference_resolver.add_missing_reference("missing-step")

    popped = store.pop(request)

    assert popped is context
    assert context.reporting_state.active_test_case_started_id is None
    assert context.reporting_state.active_test_step_id is None
    assert context.reference_resolver.missing_reference_diagnostics == []
