from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import TestCase as CucumberTestCase  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import TestStep as CucumberTestStep

import pytest_bdd.types.exception as exceptions
from pytest_bdd.model.message_registry import EnvelopeRegistry
from pytest_bdd.model.scenario_run import LifecycleObjectRef, Run, RunNode, RunStatus
from pytest_bdd.util.other import IdGenerator


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


def _build_run_root(suffix: str) -> Run:
    return Run(
        id=f"run-{suffix}",
        run_ref=LifecycleObjectRef(kind="run", object_id=f"run-{suffix}", is_active=True),
        status=RunStatus.ok,
    )


def test_config_stash_lookup_supports_stash_without_get_method() -> None:
    config = SimpleNamespace(stash=_Stash())
    run_root = _build_run_root("stash")

    run_root.set_in_stash(config.stash)

    assert Run.from_stash(config.stash) is run_root


def test_initialize_run_raises_when_run_is_already_initialized() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    existing = _build_run_root("existing")
    existing.initialize_in_stash(config.stash)
    EnvelopeRegistry(identifiable=existing.identifiable_registry).initialize_in_stash(config.stash)

    with pytest.raises(exceptions.PytestBDDStashAlreadyInitializedError, match="already initialized"):
        Run.initialize_for_session(stash=config.stash, session=session)


def test_initialize_run_creates_and_stores_value_when_missing() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="run-session")

    resolved = Run.initialize_for_session(stash=config.stash, session=session)

    assert resolved.status == RunStatus.ok
    assert resolved.run_ref.kind == "run"
    assert resolved.run_ref.object_id == "run-session"
    assert Run.from_stash(config.stash) is resolved


def test_id_generator_lookup_raises_when_missing() -> None:
    config = SimpleNamespace(stash={})

    with pytest.raises(exceptions.PytestBDDStashLookupError, match=r"unavailable in config\.stash"):
        IdGenerator.from_stash(config.stash)


def test_pop_clears_active_scenario_and_step_context_ids() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::scenario"))
    feature = _RuntimeObject(name="Feature", id="feature-1")
    scenario = _RuntimeObject(name="Scenario", id="scenario-1")
    run = Run.initialize_for_session(stash=config.stash, session=session)

    scenario_run = run.create_scenario_run(request, gherkin_document=feature, pickle=scenario)

    scenario_run.step_node = RunNode(
        id="step-ctx-1",
        parent_id="scenario-1",
        kind="step",
        object_ref=LifecycleObjectRef(kind="step", object_id="step-1"),
        is_active=True,
        opened_at_transition=0,
    )

    popped = Run.pop_scenario_run(request)

    assert popped is scenario_run
    with pytest.raises(AttributeError, match="No active scenario"):
        _ = scenario_run.run.active_scenario_id
    with pytest.raises(AttributeError, match="No active step"):
        _ = scenario_run.run.active_step_id


def test_create_scenario_run_reuses_run_root_reporting_state() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::scenario"))
    run = Run.initialize_for_session(stash=config.stash, session=session)
    run.reporting_state.run_started_id = "run-started-42"
    run.reporting_state.test_run_hook_started_id = "hook-started-42"

    scenario_run = run.create_scenario_run(request)

    assert scenario_run.run.reporting_state.run_started_id == "run-started-42"
    assert scenario_run.run.reporting_state.test_run_hook_started_id == "hook-started-42"


def test_scenario_run_not_stored_in_config_stash() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::scenario"))
    run = Run.initialize_for_session(stash=config.stash, session=session)

    scenario_run = run.create_scenario_run(request)
    resolved = Run.get_scenario_run(request)

    assert resolved is scenario_run
    assert "_pytest_bdd_scenario_runs_by_request" not in config.stash


def test_create_scenario_run_binds_feature_object_when_feature_provided() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::scenario"))
    feature = SimpleNamespace(uri="features/example.feature", gherkin_document=SimpleNamespace(feature=None))
    run = Run.initialize_for_session(stash=config.stash, session=session)

    scenario_run = run.create_scenario_run(request, gherkin_document=feature)

    assert scenario_run.gherkin_document is feature


def test_initialize_run_initializes_envelope_registry_in_config_stash() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")

    _ = Run.initialize_for_session(stash=config.stash, session=session)

    assert EnvelopeRegistry.from_stash(config.stash)
    assert EnvelopeRegistry.STASH_KEY in config.stash


def test_initialize_id_generator_initializes_in_config_stash_once() -> None:
    config = SimpleNamespace(stash={})

    id_generator = IdGenerator().initialize_in_stash(config.stash)

    assert id_generator is not None
    assert IdGenerator.STASH_KEY in config.stash
    assert not hasattr(config, "pytest_bdd_id_generator")


def test_initialize_id_generator_raises_on_repeated_initialization() -> None:
    config = SimpleNamespace(stash={})

    first = IdGenerator().initialize_in_stash(config.stash)

    with pytest.raises(exceptions.PytestBDDStashAlreadyInitializedError, match="already initialized"):
        IdGenerator().initialize_in_stash(config.stash)

    assert IdGenerator.from_stash(config.stash) is first


def test_register_envelope_indexes_identifiable_objects_by_protocol() -> None:
    config = SimpleNamespace(stash={})
    run = Run.initialize_for_config(stash=config.stash, config=config)
    envelope = Message(
        test_case=CucumberTestCase(
            id="test-case-1",
            pickle_id="pickle-1",
            test_steps=[CucumberTestStep(id="test-step-1", pickle_step_id="pickle-step-1")],
        )
    )

    registry = EnvelopeRegistry.register_envelope_in_pytest_stash(config.stash, envelope)

    assert registry.envelopes == [envelope]
    assert registry.resolve("test-case-1") is envelope.test_case
    assert registry.resolve("test-step-1") is envelope.test_case.test_steps[0]
    assert registry.identifiable is run.identifiable_registry


def test_pop_resets_reporting_and_reference_states() -> None:
    config = SimpleNamespace(stash={})
    session = SimpleNamespace(config=config, name="session")
    request = SimpleNamespace(config=config, session=session, node=SimpleNamespace(nodeid="node::scenario"))
    run = Run.initialize_for_session(stash=config.stash, session=session)
    scenario_run = run.create_scenario_run(request)
    scenario_run.run.reporting_state.active_test_case_started_id = "case-started-1"
    scenario_run.run.reporting_state.active_test_step_id = "step-1"
    scenario_run.reference_resolver.add_missing_reference("missing-step")

    popped = Run.pop_scenario_run(request)

    assert popped is scenario_run
    assert scenario_run.run.reporting_state.active_test_case_started_id is None
    assert scenario_run.run.reporting_state.active_test_step_id is None
    assert scenario_run.reference_resolver.missing_reference_diagnostics == []
