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
from pytest_bdd.model.scenario_run import (
    ActiveObjectSet,
    ContextErrorState,
    RunStage,
    LifecycleKind,
    LifecycleObjectRef,
    ReportingContextSnapshot,
    ReportingLifecycleState,
    Run,
    ScenarioRun,
)
from .run_transitions import build_lifecycle_ref


def resolve_feature_object(run: Run) -> Any | None:
    scenario_run = run.active_scenario_run
    return scenario_run.feature_object if scenario_run is not None else None


def resolve_pickle_object(run: Run) -> Any | None:
    scenario_run = run.active_scenario_run
    return scenario_run.scenario_object if scenario_run is not None else None


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
    scenario_run = Run.get_scenario_run(request)

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
