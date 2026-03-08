from __future__ import annotations

from typing import Any

from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    ContextErrorState,
    FeatureRuntimeBinding,
    LifecycleKind,
    LifecycleObjectRef,
    ReportingContextSnapshot,
    Run,
    RunStage,
    ScenarioRun,
)

from .run_transitions import build_lifecycle_ref


def resolve_feature_binding(run: Run) -> FeatureRuntimeBinding | None:
    scenario_run = run.active_scenario_run
    return scenario_run.feature_binding() if scenario_run is not None else None


def resolve_feature_object(run: Run) -> Any | None:
    binding = resolve_feature_binding(run)
    if binding is not None:
        return binding.gherkin_document
    scenario_run = run.active_scenario_run
    return scenario_run.gherkin_document if scenario_run is not None else None


def resolve_feature_source(run: Run) -> Any | None:
    binding = resolve_feature_binding(run)
    if binding is not None:
        return binding.source
    scenario_run = run.active_scenario_run
    return scenario_run.feature_source if scenario_run is not None else None


def resolve_pickle_object(run: Run) -> Any | None:
    scenario_run = run.active_scenario_run
    return scenario_run.pickle if scenario_run is not None else None


def resolve_step_object(run: Run) -> Any | None:
    scenario_run = run.active_scenario_run
    return scenario_run.step_object if scenario_run is not None else None


def resolve_previous_step_object(run: Run) -> Any | None:
    scenario_run = run.active_scenario_run
    return scenario_run.previous_step_object if scenario_run is not None else None


def resolve_active_object_or_error(
    *,
    hook_name: str,
    scenario_run: ScenarioRun,
    requested_kind: LifecycleKind,
) -> tuple[LifecycleObjectRef | None, ContextErrorState | None]:
    active_object = scenario_run.get_active_object(requested_kind)
    if active_object is not None:
        return active_object, None

    error = ContextErrorState(
        code="object_inactive",
        message=f"Requested lifecycle object '{requested_kind}' is not active",
        hook_name=hook_name,
        stage=scenario_run.stage,
        requested_kind=requested_kind,
    )
    scenario_run.last_error = error
    if scenario_run.run is not None:
        scenario_run.run.last_error = error
    return None, error


def _fallback_reporting_snapshot(
    request: Any,
    *,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot | None:
    run_root = Run.from_pytest_stash(request.config)
    if run_root is None:
        run_ref = build_lifecycle_ref("run", getattr(request, "session", None), is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)
        run_id = f"run-{id(getattr(request, 'session', request))}"
    else:
        run_ref = run_root.run_ref
        run_id = run_root.id

    fallback_active_set = ActiveObjectSet(
        run=run_ref,
        feature=None,
        scenario=None,
        step=None,
        previous_step=None,
        captured_at_stage=RunStage.idle,
    )
    return ReportingContextSnapshot(
        run_id=run_id,
        active_set=fallback_active_set,
        stage=RunStage.idle,
        resolved_from_hierarchy=False,
        fallback_reason=fallback_reason or "hierarchy_not_available",
    )


def build_reporting_context_snapshot(
    *,
    request: Any,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot | None:
    run = Run.from_pytest_stash(request.config)

    if run is not None and run.active_scenario_run is not None:
        active_scenario_run = run.active_scenario_run
        return ReportingContextSnapshot(
            run_id=run.id,
            active_set=active_scenario_run.active_set,
            stage=active_scenario_run.stage,
            resolved_from_hierarchy=True,
            fallback_reason=None,
        )
    if run is not None:
        return ReportingContextSnapshot(
            run_id=run.id,
            active_set=ActiveObjectSet(
                run=run.run_ref,
                feature=None,
                scenario=None,
                step=None,
                previous_step=None,
                captured_at_stage=RunStage.idle,
            ),
            stage=RunStage.idle,
            resolved_from_hierarchy=True,
            fallback_reason=fallback_reason or "run_has_no_active_scenario",
        )

    return _fallback_reporting_snapshot(request, fallback_reason=fallback_reason)


def resolve_registry_node(
    *,
    feature_binding: FeatureRuntimeBinding | None,
    ast_node_id: str,
    scenario_run: ScenarioRun | None = None,
) -> Any | None:
    node = feature_binding.resolve_node(ast_node_id) if feature_binding is not None else None
    if node is None and scenario_run is not None:
        scenario_run.reference_resolver.add_missing_reference(f"Missing AST node id: {ast_node_id}")
    return node


def resolve_scenario_description(
    *,
    pickle: Any,
    feature_binding: FeatureRuntimeBinding | None = None,
    scenario_run: ScenarioRun | None = None,
) -> str | None:
    ast_node_ids = getattr(pickle, "ast_node_ids", None) or ()
    if not ast_node_ids:
        if scenario_run is not None:
            scenario_run.reference_resolver.add_missing_reference("Pickle has no ast_node_ids")
        return None
    ast_node_id = str(ast_node_ids[0])
    effective_binding = feature_binding or (scenario_run.feature_binding() if scenario_run is not None else None)
    node = resolve_registry_node(
        feature_binding=effective_binding,
        ast_node_id=ast_node_id,
        scenario_run=scenario_run,
    )
    if node is None:
        return None
    description = getattr(node, "description", None)
    return str(description) if description is not None else None


def resolve_step_runtime_enrichment(
    *,
    step: Any,
    feature_binding: FeatureRuntimeBinding | None = None,
    scenario_run: ScenarioRun | None = None,
) -> dict[str, Any]:
    effective_binding = feature_binding or (scenario_run.feature_binding() if scenario_run is not None else None)
    model_step = effective_binding.pickle_step_ast_step(step) if effective_binding is not None else None
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
        "keyword": effective_binding.step_keyword(step) if effective_binding is not None else None,
        "prefix": effective_binding.step_prefix(step) if effective_binding is not None else None,
        "line_number": effective_binding.step_line_number(step) if effective_binding is not None else None,
        "doc_string": effective_binding.step_doc_string(step) if effective_binding is not None else None,
        "data_table": effective_binding.step_data_table(step) if effective_binding is not None else None,
    }
