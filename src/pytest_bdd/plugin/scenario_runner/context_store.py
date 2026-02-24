from __future__ import annotations

from typing import Any

from pytest_bdd.model.execution_context import (
    ExecutionContext,
    ExecutionContextNode,
    ExecutionStage,
    ExecutionStatus,
    HookPhase,
    LifecycleObjectRef,
    SessionExecutionContext,
)

from .context_transitions import (
    build_active_object_set,
    build_lifecycle_ref,
    initial_execution_context_id,
    runtime_object_id,
)


class ExecutionContextStore:
    """Store execution contexts per pytest node while keeping one session root."""

    CONTEXT_ATTR = "_pytest_bdd_execution_context"
    SESSION_CONTEXT_STASH_KEY = "_pytest_bdd_session_execution_context"

    def __init__(self) -> None:
        self._contexts: dict[str, ExecutionContext] = {}
        self._session_roots: dict[str, SessionExecutionContext] = {}

    @staticmethod
    def _get_config_stash(config: Any) -> Any:
        stash = getattr(config, "stash", None)
        if stash is None:
            stash = {}
            config.stash = stash
        return stash

    @classmethod
    def get_session_root_from_config(cls, config: Any) -> SessionExecutionContext | None:
        stash = cls._get_config_stash(config)
        if cls.SESSION_CONTEXT_STASH_KEY in stash:
            return stash[cls.SESSION_CONTEXT_STASH_KEY]
        return None

    @classmethod
    def set_session_root_in_config(cls, config: Any, session_root: SessionExecutionContext) -> None:
        stash = cls._get_config_stash(config)
        stash[cls.SESSION_CONTEXT_STASH_KEY] = session_root

    @classmethod
    def ensure_session_root_for_session(cls, *, config: Any, session: Any) -> SessionExecutionContext:
        existing = cls.get_session_root_from_config(config)
        if existing is not None:
            return existing

        run_ref = build_lifecycle_ref("run", session, is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)

        root = SessionExecutionContext(
            session_context_id=f"session-{id(session)}",
            run_ref=run_ref,
            status=ExecutionStatus.ok,
            transition_index=0,
        )
        cls.set_session_root_in_config(config, root)
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
            return f"session-{id(request)}"
        return str(id(session))

    def get(self, request: Any) -> ExecutionContext | None:
        key = self._request_key(request)
        context = self._contexts.get(key)
        if context is not None:
            return context

        node_context = getattr(request.node, self.CONTEXT_ATTR, None)
        if isinstance(node_context, ExecutionContext):
            self._contexts[key] = node_context
            return node_context
        return None

    def set(self, request: Any, context: ExecutionContext) -> None:
        self._contexts[self._request_key(request)] = context
        setattr(request.node, self.CONTEXT_ATTR, context)

    def get_session_root(self, request: Any) -> SessionExecutionContext | None:
        config = getattr(request, "config", None)
        if config is not None:
            root = self.get_session_root_from_config(config)
            if root is not None:
                self._session_roots[self._session_key(request)] = root
                return root
        return self._session_roots.get(self._session_key(request))

    def initialize_session_root(self, *, session: Any) -> SessionExecutionContext:
        root = self.ensure_session_root_for_session(config=session.config, session=session)
        self._session_roots[str(id(session))] = root
        return root

    def _get_or_create_session_root(self, request: Any, *, run_ref: LifecycleObjectRef) -> SessionExecutionContext:
        config = getattr(request, "config", None)
        if config is not None:
            by_config = self.get_session_root_from_config(config)
            if by_config is not None:
                self._session_roots[self._session_key(request)] = by_config
                return by_config

        key = self._session_key(request)
        existing = self._session_roots.get(key)
        if existing is not None:
            if config is not None:
                self.set_session_root_in_config(config, existing)
            return existing

        root = SessionExecutionContext(
            session_context_id=f"session-{key}",
            run_ref=run_ref,
            status=ExecutionStatus.ok,
            transition_index=0,
        )
        self._session_roots[key] = root
        if config is not None:
            self.set_session_root_in_config(config, root)
        return root

    def pop(self, request: Any) -> ExecutionContext | None:
        key = self._request_key(request)
        context = self._contexts.pop(key, None)
        if context is None:
            return None

        if hasattr(request.node, self.CONTEXT_ATTR):
            delattr(request.node, self.CONTEXT_ATTR)

        session_root = context.session_context
        if session_root is not None:
            if context.step_node is not None:
                context.step_node.close(session_root.transition_index)
            if context.scenario_node is not None:
                context.scenario_node.close(session_root.transition_index)
            if context.feature_node is not None:
                context.feature_node.close(session_root.transition_index)

            if session_root.active_scenario_context_id == context.context_id:
                session_root.active_scenario_context_id = None
            if session_root.active_step_context_id is not None:
                session_root.active_step_context_id = None

        return context

    def get_or_create(
        self, request: Any, *, feature: Any | None = None, scenario: Any | None = None
    ) -> ExecutionContext:
        existing = self.get(request)
        if existing is not None:
            return existing

        run_ref = build_lifecycle_ref("run", request.session, is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)

        session_root = self._get_or_create_session_root(request, run_ref=run_ref)

        feature_ref = build_lifecycle_ref("feature", feature, is_active=feature is not None)
        scenario_ref = build_lifecycle_ref("scenario", scenario, is_active=scenario is not None)
        active_set = build_active_object_set(
            stage=ExecutionStage.idle,
            run_ref=run_ref,
            feature_ref=feature_ref,
            scenario_ref=scenario_ref,
            step_ref=None,
            previous_step_ref=None,
        )

        context_id = initial_execution_context_id(request)
        feature_node = None
        if feature_ref is not None:
            feature_node = ExecutionContextNode(
                context_id=f"feature-{runtime_object_id(feature)}-{context_id}",
                parent_context_id=session_root.session_context_id,
                kind="feature",
                object_ref=feature_ref,
                is_active=True,
                opened_at_transition=session_root.transition_index,
            )
            session_root.active_feature_context_id = feature_node.context_id

        scenario_node = None
        if scenario_ref is not None:
            scenario_node = ExecutionContextNode(
                context_id=context_id,
                parent_context_id=feature_node.context_id
                if feature_node is not None
                else session_root.session_context_id,
                kind="scenario",
                object_ref=scenario_ref,
                is_active=True,
                opened_at_transition=session_root.transition_index,
            )
            session_root.active_scenario_context_id = scenario_node.context_id

        context = ExecutionContext(
            context_id=context_id,
            run_ref=run_ref,
            feature_ref=feature_ref,
            scenario_ref=scenario_ref,
            step_ref=None,
            previous_step_ref=None,
            active_hook=HookPhase.before_scenario,
            stage=ExecutionStage.idle,
            status=ExecutionStatus.ok,
            active_set=active_set,
            transition_index=0,
            session_context=session_root,
            feature_node=feature_node,
            scenario_node=scenario_node,
            step_node=None,
        )
        self.set(request, context)
        return context
