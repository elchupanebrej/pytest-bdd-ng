from __future__ import annotations

from typing import Any

from pytest_bdd.model.execution_context import (
    ContextErrorState,
    ExecutionContext,
    ExecutionStage,
    ExecutionStatus,
    HookInvocationContext,
    LifecycleKind,
    LifecycleObjectRef,
    ReportingContextSnapshot,
    ReportingLifecycleState,
    SessionExecutionContext,
)
from pytest_bdd.model.gherkin_document.core import _resolve_registry_for_feature
from pytest_bdd.model.gherkin_document.lookup import (
    get_pickle_step_model_step,
    get_step_data_table,
    get_step_doc_string,
    get_step_keyword,
    get_step_line_number,
    get_step_prefix,
)
from pytest_bdd.model.hook_parameter_model import ExecutionContextView, HookParameterModel

from .context_store import ExecutionContextStore
from .context_transitions import build_active_object_set, build_lifecycle_ref, phase_from_hook_name

HOOK_PARAMETER_MODEL_ATTR = "_pytest_bdd_hook_parameter_model"
EXECUTION_CONTEXT_VIEW_ATTR = "_pytest_bdd_execution_context_view"


def build_execution_context_view(execution_context: ExecutionContext) -> ExecutionContextView:
    session = execution_context.session_context
    if session is None:
        session = SessionExecutionContext(
            session_context_id=f"synthetic-{execution_context.context_id}",
            run_ref=execution_context.run_ref,
            status=ExecutionStatus.ok,
            transition_index=execution_context.transition_index,
        )

    return ExecutionContextView(
        session=session,
        context_id=execution_context.context_id,
        active_set=execution_context.active_set,
        active_hook=execution_context.active_hook,
        stage=execution_context.stage,
        status=execution_context.status,
        transition_index=execution_context.transition_index,
        node_context=execution_context,
    )


def _sync_execution_context_view(
    *,
    view: ExecutionContextView,
    execution_context: ExecutionContext,
) -> ExecutionContextView:
    session = execution_context.session_context
    if session is None:
        session = SessionExecutionContext(
            session_context_id=f"synthetic-{execution_context.context_id}",
            run_ref=execution_context.run_ref,
            status=ExecutionStatus.ok,
            transition_index=execution_context.transition_index,
        )

    view.session = session
    view.context_id = execution_context.context_id
    view.active_set = execution_context.active_set
    view.active_hook = execution_context.active_hook
    view.stage = execution_context.stage
    view.status = execution_context.status
    view.transition_index = execution_context.transition_index
    view.node_context = execution_context
    return view


def bind_request_execution_context(request: Any, execution_context: ExecutionContext) -> ExecutionContextView:
    setattr(request.node, ExecutionContextStore.CONTEXT_ATTR, execution_context)
    cached_view = getattr(request.node, EXECUTION_CONTEXT_VIEW_ATTR, None)
    if isinstance(cached_view, ExecutionContextView):
        context_view = _sync_execution_context_view(
            view=cached_view,
            execution_context=execution_context,
        )
    else:
        context_view = build_execution_context_view(execution_context)
        setattr(request.node, EXECUTION_CONTEXT_VIEW_ATTR, context_view)
    request.execution_context = context_view
    return context_view


def resolve_request_execution_context(request: Any) -> ExecutionContext | None:
    return ExecutionContextStore().get(request)


def resolve_execution_context(
    request: Any,
    *,
    context_store: ExecutionContextStore,
    feature: Any | None = None,
    scenario: Any | None = None,
) -> ExecutionContext:
    context = context_store.get(request)
    if context is None:
        context = context_store.get_or_create(request, feature=feature, scenario=scenario)
    bind_request_execution_context(request, context)
    return context


def bind_hook_parameter_model(
    *,
    request: Any,
    execution_context: ExecutionContext,
    feature: Any | None = None,
    scenario: Any | None = None,
    step: Any | None = None,
    previous_step: Any | None = None,
) -> HookParameterModel:
    context_view = bind_request_execution_context(request, execution_context)
    model = HookParameterModel(
        request=request,
        feature=feature,
        scenario=scenario,
        step=step,
        previous_step=previous_step,
        execution_context=context_view,
    )

    setattr(request.node, HOOK_PARAMETER_MODEL_ATTR, model)
    request.hook_parameters = model

    for obj in (feature, scenario, step, previous_step):
        if obj is not None:
            obj.execution_context = context_view

    return model


def clear_hook_parameter_model(model: HookParameterModel) -> None:
    request = model.request
    if hasattr(request, "execution_context"):
        delattr(request, "execution_context")
    if hasattr(request, "hook_parameters"):
        delattr(request, "hook_parameters")

    for obj in (model.feature, model.scenario, model.step, model.previous_step):
        if obj is not None and hasattr(obj, "execution_context"):
            delattr(obj, "execution_context")


def build_hook_invocation_context(
    *,
    hook_name: str,
    request: Any,
    execution_context: ExecutionContext,
) -> HookInvocationContext:
    phase = phase_from_hook_name(hook_name) or execution_context.active_hook
    node_id = getattr(request.node, "nodeid", str(id(request.node)))
    return HookInvocationContext(
        hook_name=hook_name,
        hook_phase=phase,
        execution_context_ref=execution_context,
        request_ref=node_id,
        resolved_objects=execution_context.active_set,
    )


def build_unavailable_object_error(
    *,
    hook_name: str,
    execution_context: ExecutionContext,
    requested_kind: LifecycleKind,
) -> ContextErrorState:
    return ContextErrorState(
        code="object_inactive",
        message=f"Requested lifecycle object '{requested_kind}' is not active",
        hook_name=hook_name,
        stage=execution_context.stage,
        requested_kind=requested_kind,
    )


def resolve_active_object_or_error(
    *,
    hook_name: str,
    execution_context: ExecutionContext,
    requested_kind: LifecycleKind,
) -> tuple[LifecycleObjectRef | None, ContextErrorState | None]:
    active_object = execution_context.get_active_object(requested_kind)
    if active_object is not None:
        return active_object, None

    error = build_unavailable_object_error(
        hook_name=hook_name,
        execution_context=execution_context,
        requested_kind=requested_kind,
    )
    execution_context.last_error = error
    if execution_context.session_context is not None:
        execution_context.session_context.last_error = error
    return None, error


def resolve_execution_context_for_hook(
    *,
    hook_name: str,
    request: Any,
    context_store: ExecutionContextStore,
    feature: Any | None = None,
    scenario: Any | None = None,
) -> tuple[ExecutionContext, HookInvocationContext]:
    execution_context = resolve_execution_context(
        request,
        context_store=context_store,
        feature=feature,
        scenario=scenario,
    )
    invocation_context = build_hook_invocation_context(
        hook_name=hook_name,
        request=request,
        execution_context=execution_context,
    )
    return execution_context, invocation_context


def _fallback_reporting_snapshot(
    request: Any,
    *,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot | None:
    session_root = ExecutionContextStore.get_session_root_from_config(request.config)
    if session_root is None:
        run_ref = build_lifecycle_ref("run", getattr(request, "session", None), is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)
        session_context_id = f"session-{id(getattr(request, 'session', request))}"
    else:
        run_ref = session_root.run_ref
        session_context_id = session_root.session_context_id

    fallback_active_set = build_active_object_set(
        stage=ExecutionStage.idle,
        run_ref=run_ref,
        feature_ref=None,
        scenario_ref=None,
        step_ref=None,
        previous_step_ref=None,
    )
    return ReportingContextSnapshot(
        session_context_id=session_context_id,
        active_set=fallback_active_set,
        stage=ExecutionStage.idle,
        resolved_from_hierarchy=False,
        fallback_reason=fallback_reason or "hierarchy_not_available",
    )


def build_reporting_context_snapshot(
    *,
    request: Any,
    execution_context: ExecutionContext | None = None,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot | None:
    context = execution_context
    if context is None:
        context = resolve_request_execution_context(request)
    if context is None:
        context_view = getattr(request, "execution_context", None)
        if isinstance(context_view, ExecutionContextView):
            node_context = context_view.node_context
            if isinstance(node_context, ExecutionContext):
                context = node_context

    if context is not None and context.session_context is not None:
        return ReportingContextSnapshot(
            session_context_id=context.session_context.session_context_id,
            active_set=context.active_set,
            stage=context.stage,
            resolved_from_hierarchy=True,
            fallback_reason=None,
        )

    return _fallback_reporting_snapshot(request, fallback_reason=fallback_reason)


def get_reporting_state(execution_context: ExecutionContext) -> ReportingLifecycleState:
    return execution_context.reporting_state


def get_session_reporting_state(execution_context: ExecutionContext) -> ReportingLifecycleState:
    session = execution_context.session_context
    if session is None:
        return execution_context.reporting_state
    return session.reporting_state


def map_runtime_step_to_test_step_id(
    *,
    execution_context: ExecutionContext,
    runtime_step: Any,
    test_step_id: str,
) -> None:
    execution_context.reporting_state.runtime_step_to_test_step_id[id(runtime_step)] = test_step_id


def resolve_test_step_id_for_runtime_step(
    *,
    execution_context: ExecutionContext,
    runtime_step: Any,
) -> str | None:
    mapped = execution_context.reporting_state.runtime_step_to_test_step_id.get(id(runtime_step))
    if mapped is not None:
        return mapped
    runtime_step_id = getattr(runtime_step, "id", None)
    if runtime_step_id is not None:
        runtime_step_id_text = str(runtime_step_id)
        for candidate in execution_context.reporting_state.runtime_step_to_test_step_id.values():
            if candidate == runtime_step_id_text:
                return candidate
    return execution_context.reporting_state.active_test_step_id


def _registry_from_feature(feature: Any, *, config: Any | None = None) -> dict[str, Any]:
    return _resolve_registry_for_feature(feature, config=config)


def resolve_registry_node(
    *,
    registry: dict[str, Any],
    ast_node_id: str,
    execution_context: ExecutionContext | None = None,
) -> Any | None:
    node = registry.get(ast_node_id)
    if node is None and execution_context is not None:
        execution_context.reference_resolver.add_missing_reference(f"Missing AST node id: {ast_node_id}")
    return node


def resolve_scenario_description(
    *,
    feature: Any,
    scenario: Any,
    execution_context: ExecutionContext | None = None,
    config: Any | None = None,
) -> str | None:
    ast_node_ids = getattr(scenario, "ast_node_ids", None) or ()
    if not ast_node_ids:
        if execution_context is not None:
            execution_context.reference_resolver.add_missing_reference("Scenario has no ast_node_ids")
        return None
    ast_node_id = str(ast_node_ids[0])
    node = resolve_registry_node(
        registry=_registry_from_feature(feature, config=config),
        ast_node_id=ast_node_id,
        execution_context=execution_context,
    )
    if node is None:
        return None
    description = getattr(node, "description", None)
    return str(description) if description is not None else None


def resolve_step_runtime_enrichment(
    *,
    feature: Any,
    step: Any,
    execution_context: ExecutionContext | None = None,
    config: Any | None = None,
) -> dict[str, Any]:
    registry = _registry_from_feature(feature, config=config)
    model_step = get_pickle_step_model_step(registry, step)
    if model_step is None:
        if execution_context is not None:
            execution_context.reference_resolver.add_missing_reference(
                f"Missing pickle step mapping: {getattr(step, 'id', 'unknown')}"
            )
        return {
            "keyword": None,
            "prefix": None,
            "line_number": None,
            "doc_string": None,
            "data_table": None,
        }
    return {
        "keyword": get_step_keyword(registry, step),
        "prefix": get_step_prefix(registry, step),
        "line_number": get_step_line_number(registry, step),
        "doc_string": get_step_doc_string(registry, step),
        "data_table": get_step_data_table(registry, step),
    }
