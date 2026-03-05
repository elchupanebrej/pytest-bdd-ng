from __future__ import annotations

from typing import Any

from pytest_bdd.model.gherkin_document.core import _resolve_registry_for_feature
from pytest_bdd.model.gherkin_document.lookup import (
    get_pickle_step_model_step,
    get_step_data_table,
    get_step_doc_string,
    get_step_keyword,
    get_step_line_number,
    get_step_prefix,
)
from pytest_bdd.model.hook_parameter_model import HookParameterModel, ScenarioRunView
from pytest_bdd.model.scenario_run import (
    ContextErrorState,
    RunStage,
    RunStatus,
    HookInvocationContext,
    LifecycleKind,
    LifecycleObjectRef,
    ReportingContextSnapshot,
    ReportingLifecycleState,
    Run,
    ScenarioRun,
)

from .run_store import RunStore
from .run_transitions import build_active_object_set, build_lifecycle_ref, phase_from_hook_name

HOOK_PARAMETER_MODEL_ATTR = "_pytest_bdd_hook_parameter_model"
SCENARIO_RUN_VIEW_ATTR = "_pytest_bdd_scenario_run_view"


def build_scenario_run_view(scenario_run: ScenarioRun) -> ScenarioRunView:
    run = scenario_run.run
    if run is None:
        run = Run(
            run_context_id=f"synthetic-{scenario_run.context_id}",
            run_ref=scenario_run.run_ref,
            status=RunStatus.ok,
            transition_index=scenario_run.transition_index,
        )

    return ScenarioRunView(
        run=run,
        context_id=scenario_run.context_id,
        active_set=scenario_run.active_set,
        active_hook=scenario_run.active_hook,
        stage=scenario_run.stage,
        status=scenario_run.status,
        transition_index=scenario_run.transition_index,
        node_context=scenario_run,
    )


def _sync_scenario_run_view(
    *,
    view: ScenarioRunView,
    scenario_run: ScenarioRun,
) -> ScenarioRunView:
    run = scenario_run.run
    if run is None:
        run = Run(
            run_context_id=f"synthetic-{scenario_run.context_id}",
            run_ref=scenario_run.run_ref,
            status=RunStatus.ok,
            transition_index=scenario_run.transition_index,
        )

    view.run = run
    view.context_id = scenario_run.context_id
    view.active_set = scenario_run.active_set
    view.active_hook = scenario_run.active_hook
    view.stage = scenario_run.stage
    view.status = scenario_run.status
    view.transition_index = scenario_run.transition_index
    view.node_context = scenario_run
    return view


def bind_request_scenario_run(request: Any, scenario_run: ScenarioRun) -> ScenarioRunView:
    setattr(request.node, RunStore.SCENARIO_RUN_ATTR, scenario_run)
    if scenario_run.run is not None:
        setattr(request.node, RunStore.RUN_ATTR, scenario_run.run)
    cached_view = getattr(request.node, SCENARIO_RUN_VIEW_ATTR, None)
    if isinstance(cached_view, ScenarioRunView):
        context_view = _sync_scenario_run_view(
            view=cached_view,
            scenario_run=scenario_run,
        )
    else:
        context_view = build_scenario_run_view(scenario_run)
        setattr(request.node, SCENARIO_RUN_VIEW_ATTR, context_view)
    request.scenario_run = scenario_run
    if scenario_run.run is not None:
        request.run = scenario_run.run
    return context_view


def resolve_request_scenario_run(request: Any) -> ScenarioRun | None:
    return RunStore().get(request)


def resolve_request_run(request: Any) -> Run | None:
    run = getattr(request, "run", None)
    if isinstance(run, Run):
        return run
    run = getattr(getattr(request, "node", None), RunStore.RUN_ATTR, None)
    if isinstance(run, Run):
        return run
    scenario_run = resolve_request_scenario_run(request)
    if scenario_run is not None and scenario_run.run is not None:
        return scenario_run.run
    config = getattr(request, "config", None)
    if config is None:
        return None
    return RunStore.get_run_from_config(config)


def resolve_active_scenario_run(run: Run) -> ScenarioRun | None:
    return run.active_scenario_run


def resolve_feature_object(run: Run) -> Any | None:
    scenario_run = resolve_active_scenario_run(run)
    return scenario_run.feature_object if scenario_run is not None else None


def resolve_pickle_object(run: Run) -> Any | None:
    scenario_run = resolve_active_scenario_run(run)
    return scenario_run.scenario_object if scenario_run is not None else None


def resolve_step_object(run: Run) -> Any | None:
    scenario_run = resolve_active_scenario_run(run)
    return scenario_run.step_object if scenario_run is not None else None


def resolve_previous_step_object(run: Run) -> Any | None:
    scenario_run = resolve_active_scenario_run(run)
    return scenario_run.previous_step_object if scenario_run is not None else None


def resolve_scenario_run(
    request: Any,
    *,
    run_store: RunStore,
    feature: Any | None = None,
    scenario: Any | None = None,
) -> ScenarioRun:
    scenario_run = run_store.get(request)
    if scenario_run is None:
        scenario_run = run_store.get_or_create(request, feature=feature, scenario=scenario)
    bind_request_scenario_run(request, scenario_run)
    return scenario_run


def bind_hook_parameter_model(
    *,
    request: Any,
    scenario_run: ScenarioRun,
    feature: Any | None = None,
    scenario: Any | None = None,
    step: Any | None = None,
    previous_step: Any | None = None,
) -> HookParameterModel:
    context_view = bind_request_scenario_run(request, scenario_run)
    model = HookParameterModel(
        request=request,
        feature=feature,
        scenario=scenario,
        step=step,
        previous_step=previous_step,
        scenario_run_view=context_view,
    )

    setattr(request.node, HOOK_PARAMETER_MODEL_ATTR, model)
    request.hook_parameters = model

    for obj in (feature, scenario, step, previous_step):
        if obj is not None:
            obj.scenario_run = scenario_run

    return model


def clear_hook_parameter_model(model: HookParameterModel) -> None:
    request = model.request
    if hasattr(request, "scenario_run"):
        delattr(request, "scenario_run")
    if hasattr(request, "run"):
        delattr(request, "run")
    if hasattr(request, "hook_parameters"):
        delattr(request, "hook_parameters")

    for obj in (model.feature, model.scenario, model.step, model.previous_step):
        if obj is not None and hasattr(obj, "scenario_run"):
            delattr(obj, "scenario_run")


def build_hook_invocation_context(
    *,
    hook_name: str,
    request: Any,
    scenario_run: ScenarioRun,
) -> HookInvocationContext:
    phase = phase_from_hook_name(hook_name) or scenario_run.active_hook
    node_id = getattr(request.node, "nodeid", str(id(request.node)))
    return HookInvocationContext(
        hook_name=hook_name,
        hook_phase=phase,
        scenario_run_ref=scenario_run,
        request_ref=node_id,
        resolved_objects=scenario_run.active_set,
    )


def build_unavailable_object_error(
    *,
    hook_name: str,
    scenario_run: ScenarioRun,
    requested_kind: LifecycleKind,
) -> ContextErrorState:
    return ContextErrorState(
        code="object_inactive",
        message=f"Requested lifecycle object '{requested_kind}' is not active",
        hook_name=hook_name,
        stage=scenario_run.stage,
        requested_kind=requested_kind,
    )


def resolve_active_object_or_error(
    *,
    hook_name: str,
    scenario_run: ScenarioRun,
    requested_kind: LifecycleKind,
) -> tuple[LifecycleObjectRef | None, ContextErrorState | None]:
    active_object = scenario_run.get_active_object(requested_kind)
    if active_object is not None:
        return active_object, None

    error = build_unavailable_object_error(
        hook_name=hook_name,
        scenario_run=scenario_run,
        requested_kind=requested_kind,
    )
    scenario_run.last_error = error
    if scenario_run.run is not None:
        scenario_run.run.last_error = error
    return None, error


def resolve_scenario_run_for_hook(
    *,
    hook_name: str,
    request: Any,
    run_store: RunStore,
    feature: Any | None = None,
    scenario: Any | None = None,
) -> tuple[ScenarioRun, HookInvocationContext]:
    scenario_run = resolve_scenario_run(
        request,
        run_store=run_store,
        feature=feature,
        scenario=scenario,
    )
    invocation_context = build_hook_invocation_context(
        hook_name=hook_name,
        request=request,
        scenario_run=scenario_run,
    )
    return scenario_run, invocation_context


def _fallback_reporting_snapshot(
    request: Any,
    *,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot | None:
    run_root = RunStore.get_run_from_config(request.config)
    if run_root is None:
        run_ref = build_lifecycle_ref("run", getattr(request, "session", None), is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)
        run_context_id = f"run-{id(getattr(request, 'session', request))}"
    else:
        run_ref = run_root.run_ref
        run_context_id = run_root.run_context_id

    fallback_active_set = build_active_object_set(
        stage=RunStage.idle,
        run_ref=run_ref,
        feature_ref=None,
        scenario_ref=None,
        step_ref=None,
        previous_step_ref=None,
    )
    return ReportingContextSnapshot(
        run_context_id=run_context_id,
        active_set=fallback_active_set,
        stage=RunStage.idle,
        resolved_from_hierarchy=False,
        fallback_reason=fallback_reason or "hierarchy_not_available",
    )


def build_reporting_context_snapshot(
    *,
    request: Any,
    run: Run | None = None,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot | None:
    resolved_run = run
    if resolved_run is None:
        resolved_run = resolve_request_run(request)
    if resolved_run is None:
        resolved_scenario_run = resolve_request_scenario_run(request)
        if resolved_scenario_run is not None:
            resolved_run = resolved_scenario_run.run
    if resolved_run is None:
        request_scenario_run = getattr(request, "scenario_run", None)
        if isinstance(request_scenario_run, ScenarioRun):
            resolved_run = request_scenario_run.run

    if resolved_run is not None and resolved_run.active_scenario_run is not None:
        active_scenario_run = resolved_run.active_scenario_run
        return ReportingContextSnapshot(
            run_context_id=resolved_run.run_context_id,
            active_set=active_scenario_run.active_set,
            stage=active_scenario_run.stage,
            resolved_from_hierarchy=True,
            fallback_reason=None,
        )
    if resolved_run is not None:
        return ReportingContextSnapshot(
            run_context_id=resolved_run.run_context_id,
            active_set=build_active_object_set(
                stage=RunStage.idle,
                run_ref=resolved_run.run_ref,
                feature_ref=None,
                scenario_ref=None,
                step_ref=None,
                previous_step_ref=None,
            ),
            stage=RunStage.idle,
            resolved_from_hierarchy=True,
            fallback_reason=fallback_reason or "run_has_no_active_scenario",
        )

    return _fallback_reporting_snapshot(request, fallback_reason=fallback_reason)


def map_runtime_step_to_test_step_id(
    *,
    run: Run,
    runtime_step: Any,
    test_step_id: str,
) -> None:
    run.reporting_state.runtime_step_to_test_step_id[id(runtime_step)] = test_step_id


def resolve_test_step_id_for_runtime_step(
    *,
    run: Run,
    runtime_step: Any,
) -> str | None:
    reporting_state: ReportingLifecycleState = run.reporting_state
    mapped = reporting_state.runtime_step_to_test_step_id.get(id(runtime_step))
    if mapped is not None:
        return mapped
    runtime_step_id = getattr(runtime_step, "id", None)
    if runtime_step_id is not None:
        runtime_step_id_text = str(runtime_step_id)
        for candidate in reporting_state.runtime_step_to_test_step_id.values():
            if candidate == runtime_step_id_text:
                return candidate
    return reporting_state.active_test_step_id

def resolve_registry_node(
    *,
    registry: dict[str, Any],
    ast_node_id: str,
    scenario_run: ScenarioRun | None = None,
) -> Any | None:
    node = registry.get(ast_node_id)
    if node is None and scenario_run is not None:
        scenario_run.reference_resolver.add_missing_reference(f"Missing AST node id: {ast_node_id}")
    return node


def resolve_scenario_description(
    *,
    feature: Any,
    scenario: Any,
    scenario_run: ScenarioRun | None = None,
    config: Any | None = None,
) -> str | None:
    ast_node_ids = getattr(scenario, "ast_node_ids", None) or ()
    if not ast_node_ids:
        if scenario_run is not None:
            scenario_run.reference_resolver.add_missing_reference("Scenario has no ast_node_ids")
        return None
    ast_node_id = str(ast_node_ids[0])
    node = resolve_registry_node(
        registry=_resolve_registry_for_feature(feature, config=config),
        ast_node_id=ast_node_id,
        scenario_run=scenario_run,
    )
    if node is None:
        return None
    description = getattr(node, "description", None)
    return str(description) if description is not None else None


def resolve_step_runtime_enrichment(
    *,
    feature: Any,
    step: Any,
    scenario_run: ScenarioRun | None = None,
    config: Any | None = None,
) -> dict[str, Any]:
    registry = _resolve_registry_for_feature(feature, config=config)
    model_step = get_pickle_step_model_step(registry, step)
    if model_step is None:
        if scenario_run is not None:
            scenario_run.reference_resolver.add_missing_reference(
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
