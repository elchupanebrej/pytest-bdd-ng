from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pytest_bdd.model.message_registry import EnvelopeRegistry
from pytest_bdd.model.scenario_run import (
    RunNode,
    RunStage,
    RunStatus,
    HookPhase,
    LifecycleObjectRef,
    Run,
    ScenarioRun,
)

from .run_transitions import (
    build_active_object_set,
    build_lifecycle_ref,
    initial_scenario_run_id,
    runtime_object_id,
)

if TYPE_CHECKING:
    from pytest_bdd.model.message_extension import EventEnvelope


class RunStore:
    """Store scenario runs per pytest node while keeping one run root."""

    SCENARIO_RUN_ATTR = "_pytest_bdd_scenario_run"
    RUN_ATTR = "_pytest_bdd_run"
    RUN_STASH_KEY = "_pytest_bdd_run"
    SCENARIO_RUNS_STASH_KEY = "_pytest_bdd_scenario_runs_by_request"
    ENVELOPE_REGISTRY_STASH_KEY = "_pytest_bdd_envelope_registry"

    def __init__(self) -> None:
        self._scenario_runs: dict[str, ScenarioRun] = {}
        self._runs: dict[str, Run] = {}

    @staticmethod
    def _get_config_stash(config: Any) -> Any:
        stash = getattr(config, "stash", None)
        if stash is None:
            stash = {}
            config.stash = stash
        return stash

    @classmethod
    def get_run_from_config(cls, config: Any) -> Run | None:
        stash = cls._get_config_stash(config)
        if cls.RUN_STASH_KEY in stash:
            run_root = stash[cls.RUN_STASH_KEY]
            if isinstance(run_root, Run):
                return run_root
        return None

    @classmethod
    def set_run_in_config(cls, config: Any, run_root: Run) -> None:
        stash = cls._get_config_stash(config)
        stash[cls.RUN_STASH_KEY] = run_root

    @classmethod
    def get_scenario_runs_from_config(cls, config: Any) -> dict[str, ScenarioRun] | None:
        stash = cls._get_config_stash(config)
        if cls.SCENARIO_RUNS_STASH_KEY in stash:
            scenario_runs = stash[cls.SCENARIO_RUNS_STASH_KEY]
            if isinstance(scenario_runs, dict):
                return scenario_runs
        return None

    @classmethod
    def get_envelope_registry_from_config(cls, config: Any) -> EnvelopeRegistry | None:
        stash = cls._get_config_stash(config)
        if cls.ENVELOPE_REGISTRY_STASH_KEY in stash:
            envelope_registry = stash[cls.ENVELOPE_REGISTRY_STASH_KEY]
            if isinstance(envelope_registry, EnvelopeRegistry):
                return envelope_registry
        return None

    @classmethod
    def ensure_envelope_registry_in_config(cls, config: Any) -> EnvelopeRegistry:
        existing = cls.get_envelope_registry_from_config(config)
        if existing is not None:
            return existing
        stash = cls._get_config_stash(config)
        envelope_registry = EnvelopeRegistry()
        stash[cls.ENVELOPE_REGISTRY_STASH_KEY] = envelope_registry
        return envelope_registry

    @classmethod
    def register_envelope_in_config(cls, config: Any, envelope: EventEnvelope) -> EnvelopeRegistry:
        envelope_registry = cls.ensure_envelope_registry_in_config(config)
        envelope_registry.add_envelope(envelope)
        return envelope_registry

    @classmethod
    def ensure_scenario_runs_in_config(cls, config: Any) -> dict[str, ScenarioRun]:
        existing = cls.get_scenario_runs_from_config(config)
        if existing is not None:
            return existing
        stash = cls._get_config_stash(config)
        scenario_runs: dict[str, ScenarioRun] = {}
        stash[cls.SCENARIO_RUNS_STASH_KEY] = scenario_runs
        return scenario_runs

    @classmethod
    def ensure_run_for_session(cls, *, config: Any, session: Any) -> Run:
        cls.ensure_envelope_registry_in_config(config)
        existing = cls.get_run_from_config(config)
        if existing is not None:
            return existing

        run_ref = build_lifecycle_ref("run", session, is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)

        root = Run(
            run_context_id=f"run-{id(session)}",
            run_ref=run_ref,
            status=RunStatus.ok,
            transition_index=0,
        )
        cls.set_run_in_config(config, root)
        return root

    @staticmethod
    def _request_key(request: Any) -> str:
        node = getattr(request, "node", None)
        node_id = getattr(node, "nodeid", None)
        if node_id is not None:
            return str(node_id)
        return f"request-{id(request)}"

    @staticmethod
    def _session_key(request: Any) -> str:
        session = getattr(request, "session", None)
        if session is None:
            return f"run-{id(request)}"
        return str(id(session))

    def get(self, request: Any) -> ScenarioRun | None:
        key = self._request_key(request)
        scenario_run = self._scenario_runs.get(key)
        if scenario_run is not None:
            return scenario_run

        config = getattr(request, "config", None)
        if config is not None:
            scenario_runs = self.get_scenario_runs_from_config(config)
            if scenario_runs is not None:
                scenario_run = scenario_runs.get(key)
                if isinstance(scenario_run, ScenarioRun):
                    self._scenario_runs[key] = scenario_run
                    setattr(request.node, self.SCENARIO_RUN_ATTR, scenario_run)
                    if scenario_run.run is not None:
                        scenario_run.run.active_scenario_run = scenario_run
                        setattr(request.node, self.RUN_ATTR, scenario_run.run)
                    return scenario_run

        node_scenario_run = getattr(request.node, self.SCENARIO_RUN_ATTR, None)
        if isinstance(node_scenario_run, ScenarioRun):
            self._scenario_runs[key] = node_scenario_run
            if node_scenario_run.run is not None:
                node_scenario_run.run.active_scenario_run = node_scenario_run
                setattr(request.node, self.RUN_ATTR, node_scenario_run.run)
            if config is not None:
                self.ensure_scenario_runs_in_config(config)[key] = node_scenario_run
            return node_scenario_run
        return None

    def set(self, request: Any, scenario_run: ScenarioRun) -> None:
        key = self._request_key(request)
        self._scenario_runs[key] = scenario_run
        setattr(request.node, self.SCENARIO_RUN_ATTR, scenario_run)
        if scenario_run.run is not None:
            scenario_run.run.active_scenario_run = scenario_run
            setattr(request.node, self.RUN_ATTR, scenario_run.run)
        config = getattr(request, "config", None)
        if config is not None:
            self.ensure_scenario_runs_in_config(config)[key] = scenario_run

    def get_run(self, request: Any) -> Run | None:
        config = getattr(request, "config", None)
        if config is not None:
            run_root = self.get_run_from_config(config)
            if run_root is not None:
                self._runs[self._session_key(request)] = run_root
                return run_root
        return self._runs.get(self._session_key(request))

    def initialize_run(self, *, session: Any) -> Run:
        run_root = self.ensure_run_for_session(config=session.config, session=session)
        self._runs[str(id(session))] = run_root
        return run_root

    def _get_or_create_run(self, request: Any, *, run_ref: LifecycleObjectRef) -> Run:
        config = getattr(request, "config", None)
        if config is not None:
            by_config = self.get_run_from_config(config)
            if by_config is not None:
                self._runs[self._session_key(request)] = by_config
                return by_config

        key = self._session_key(request)
        existing = self._runs.get(key)
        if existing is not None:
            if config is not None:
                self.set_run_in_config(config, existing)
            return existing

        root = Run(
            run_context_id=f"run-{key}",
            run_ref=run_ref,
            status=RunStatus.ok,
            transition_index=0,
        )
        self._runs[key] = root
        if config is not None:
            self.set_run_in_config(config, root)
        return root

    def pop(self, request: Any) -> ScenarioRun | None:  # noqa: C901
        key = self._request_key(request)
        scenario_run = self._scenario_runs.pop(key, None)
        config = getattr(request, "config", None)
        if config is not None:
            scenario_runs = self.get_scenario_runs_from_config(config)
            if scenario_runs is not None:
                stashed_scenario_run = scenario_runs.pop(key, None)
                if scenario_run is None and isinstance(stashed_scenario_run, ScenarioRun):
                    scenario_run = stashed_scenario_run
        if scenario_run is None:
            return None

        if hasattr(request.node, self.SCENARIO_RUN_ATTR):
            delattr(request.node, self.SCENARIO_RUN_ATTR)
        if hasattr(request.node, self.RUN_ATTR):
            delattr(request.node, self.RUN_ATTR)

        run_root = scenario_run.run
        if run_root is not None:
            if scenario_run.step_node is not None:
                scenario_run.step_node.close(run_root.transition_index)
            if scenario_run.scenario_node is not None:
                scenario_run.scenario_node.close(run_root.transition_index)
            if scenario_run.feature_node is not None:
                scenario_run.feature_node.close(run_root.transition_index)

            if run_root.active_scenario_context_id == scenario_run.context_id:
                run_root.active_scenario_context_id = None
            if run_root.active_scenario_run is scenario_run:
                run_root.active_scenario_run = None
            if run_root.active_step_context_id is not None:
                run_root.active_step_context_id = None
            run_root.reporting_state.reset_scenario_scope()

        scenario_run.reference_resolver.clear()

        return scenario_run

    def get_or_create(
        self, request: Any, *, feature: Any | None = None, scenario: Any | None = None
    ) -> ScenarioRun:
        existing = self.get(request)
        if existing is not None:
            return existing

        run_ref = build_lifecycle_ref("run", request.session, is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)

        run_root = self._get_or_create_run(request, run_ref=run_ref)

        feature_ref = build_lifecycle_ref("feature", feature, is_active=feature is not None)
        scenario_ref = build_lifecycle_ref("scenario", scenario, is_active=scenario is not None)
        active_set = build_active_object_set(
            stage=RunStage.idle,
            run_ref=run_ref,
            feature_ref=feature_ref,
            scenario_ref=scenario_ref,
            step_ref=None,
            previous_step_ref=None,
        )

        context_id = initial_scenario_run_id(request)
        feature_node = None
        if feature_ref is not None:
            feature_node = RunNode(
                context_id=f"feature-{runtime_object_id(feature)}-{context_id}",
                parent_context_id=run_root.run_context_id,
                kind="feature",
                object_ref=feature_ref,
                is_active=True,
                opened_at_transition=run_root.transition_index,
            )
            run_root.active_feature_context_id = feature_node.context_id

        scenario_node = None
        if scenario_ref is not None:
            scenario_node = RunNode(
                context_id=context_id,
                parent_context_id=feature_node.context_id
                if feature_node is not None
                else run_root.run_context_id,
                kind="scenario",
                object_ref=scenario_ref,
                is_active=True,
                opened_at_transition=run_root.transition_index,
            )
            run_root.active_scenario_context_id = scenario_node.context_id

        scenario_run = ScenarioRun(
            context_id=context_id,
            run_ref=run_ref,
            feature_ref=feature_ref,
            scenario_ref=scenario_ref,
            step_ref=None,
            previous_step_ref=None,
            active_hook=HookPhase.before_scenario,
            stage=RunStage.idle,
            status=RunStatus.ok,
            active_set=active_set,
            transition_index=0,
            run=run_root,
            feature_node=feature_node,
            scenario_node=scenario_node,
            step_node=None,
            feature_object=feature,
            scenario_object=scenario,
            step_object=None,
            previous_step_object=None,
        )
        run_root.active_scenario_run = scenario_run
        self.set(request, scenario_run)
        return scenario_run
