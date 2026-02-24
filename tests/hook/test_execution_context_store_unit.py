from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

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
