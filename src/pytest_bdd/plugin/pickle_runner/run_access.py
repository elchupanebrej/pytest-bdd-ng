"""Provide run access helpers."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from cucumber_messages import GherkinDocument, Pickle, PickleStep, Source

    from pytest_bdd.compatibility.pytest import FixtureRequest
    from pytest_bdd.types.protocol import Identifiable


def resolve_feature_binding(run: Run) -> FeatureRuntimeBinding | None:
    """
    Resolve feature binding from run.

    Args:
        run: Current run.

    Returns:
        Feature binding or None.

    """
    scenario_run = run.active_scenario_run
    return scenario_run.feature_binding if scenario_run is not None else None


def require_feature_binding(run: Run, *, hook_name: str) -> FeatureRuntimeBinding:
    """
    Require feature binding from run.

    Args:
        run: Current run.
        hook_name: Name of the hook calling this.

    Returns:
        Feature binding.

    """
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_feature_binding(hook_name=hook_name)


def require_feature_object(run: Run, *, hook_name: str) -> GherkinDocument:
    """
    Require feature object from run.

    Args:
        run: Current run.
        hook_name: Name of the hook calling this.

    Returns:
        Gherkin document.

    """
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_gherkin_document(hook_name=hook_name)


def require_pickle_object(run: Run, *, hook_name: str) -> Pickle:
    """
    Require pickle object from run.

    Args:
        run: Current run.
        hook_name: Name of the hook calling this.

    Returns:
        Pickle object.

    """
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_pickle(hook_name=hook_name)


def require_step_object(run: Run, *, hook_name: str) -> PickleStep:
    """
    Require step object from run.

    Args:
        run: Current run.
        hook_name: Name of the hook calling this.

    Returns:
        Step object.

    """
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_step_object(hook_name=hook_name)


def resolve_feature_object(run: Run) -> GherkinDocument | None:
    """
    Resolve feature object from run.

    Args:
        run: Current run.

    Returns:
        Gherkin document or None.

    """
    binding = run.active_feature_binding
    if binding is not None:
        return binding.gherkin_document
    scenario_run = run.active_scenario_run
    return scenario_run.gherkin_document if scenario_run is not None else None


def resolve_feature_source(run: Run) -> Source | None:
    """
    Resolve feature source from run.

    Args:
        run: Current run.

    Returns:
        Source or None.

    """
    binding = run.active_feature_binding
    if binding is not None:
        return binding.source
    scenario_run = run.active_scenario_run
    return scenario_run.feature_source if scenario_run is not None else None


def resolve_pickle_object(run: Run) -> Pickle | None:
    """
    Resolve pickle object.

    Returns:
        Pickle object or None.

    """
    scenario_run = run.active_scenario_run
    return scenario_run.pickle if scenario_run is not None else None


def resolve_step_object(run: Run) -> PickleStep | None:
    """
    Resolve step object.

    Returns:
        Pickle step or None.

    """
    scenario_run = run.active_scenario_run
    return scenario_run.step_object if scenario_run is not None else None


def resolve_previous_step_object(run: Run) -> PickleStep | object | None:
    """
    Resolve previous step object.

    Returns:
        Previous step object or None.

    """
    scenario_run = run.active_scenario_run
    return scenario_run.previous_step_object if scenario_run is not None else None


def resolve_active_object_or_error(
    *,
    hook_name: str,
    scenario_run: ScenarioRun,
    requested_kind: LifecycleKind,
) -> tuple[LifecycleObjectRef | None, ContextErrorState | None]:
    """
    Resolve active object or error.

    Returns:
        Tuple of (active object, error state).

    """
    active_object = scenario_run.get_active_object(requested_kind)
    if active_object is not None:
        return active_object, None

    inactive_candidate = {
        "run": scenario_run.active_set.run,
        "feature": scenario_run.active_set.feature,
        "scenario": scenario_run.active_set.scenario,
        "step": scenario_run.active_set.step,
    }[requested_kind]
    message = (
        f"Lifecycle object '{requested_kind}' is unavailable during {hook_name} at stage '{scenario_run.stage.value}'"
    )
    if inactive_candidate.empty_state_reason is not None:
        message = f"{message} (empty state: {inactive_candidate.empty_state_reason})"
    error = scenario_run.record_context_error(
        code="object_inactive",
        message=message,
        hook_name=hook_name,
        requested_kind=requested_kind,
    )
    return None, error


def _fallback_reporting_snapshot(
    request: FixtureRequest,
    *,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot:
    run_root = Run.find_in_stash(request.config.stash).value_or(None)
    if run_root is None:
        run_ref = build_lifecycle_ref("run", getattr(request, "session", None), is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)
        run_id = f"run-{id(getattr(request, 'session', request))}"
    else:
        run_ref = run_root.run_ref
        run_id = run_root.id

    return ReportingContextSnapshot(
        run_id=run_id,
        active_set=ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.idle),
        stage=RunStage.idle,
        resolved_from_hierarchy=False,
        fallback_reason=fallback_reason or "hierarchy_not_available",
    )


def build_reporting_context_snapshot(
    *,
    request: FixtureRequest,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot:
    """
    Build reporting context snapshot.

    Returns:
        Reporting context snapshot.

    """
    run = Run.find_in_stash(request.config.stash).value_or(None)

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
            active_set=ActiveObjectSet(run=run.run_ref, captured_at_stage=RunStage.idle),
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
) -> Identifiable | None:
    """
    Resolve registry node.

    Returns:
        Identifiable node or None.

    """
    node = None
    if feature_binding is not None:
        with suppress(KeyError):
            node = feature_binding.resolve_node(ast_node_id)

    if node is None and scenario_run is not None:
        scenario_run.reference_resolver.add_missing_reference(f"Missing AST node id: {ast_node_id}")
    return node


def resolve_scenario_description(
    *,
    pickle: Pickle,
    feature_binding: FeatureRuntimeBinding | None = None,
    scenario_run: ScenarioRun | None = None,
) -> str | None:
    """
    Resolve scenario description.

    Returns:
        Scenario description or None.

    """
    ast_node_ids = getattr(pickle, "ast_node_ids", None) or ()
    if not ast_node_ids:
        if scenario_run is not None:
            scenario_run.reference_resolver.add_missing_reference("Pickle has no ast_node_ids")
        return None
    ast_node_id = str(ast_node_ids[0])
    effective_binding = feature_binding or (scenario_run.feature_binding if scenario_run is not None else None)
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
    step: PickleStep,
    feature_binding: FeatureRuntimeBinding | None = None,
    scenario_run: ScenarioRun | None = None,
) -> dict[str, object]:
    """
    Resolve step runtime enrichment.

    Returns:
        Step runtime enrichment dictionary.

    """
    effective_binding = feature_binding or (scenario_run.feature_binding if scenario_run is not None else None)
    model_step = effective_binding.pickle_step_ast_step(step) if effective_binding is not None else None
    if model_step is None:
        if scenario_run is not None:
            scenario_run.reference_resolver.add_missing_reference(
                f"Missing pickle step mapping: {getattr(step, 'id', 'unknown')}",
            )
        return {
            "keyword": None,
            "prefix": None,
            "line_number": None,
            "doc_string": None,
            "data_table": None,
            "state": "unresolved",
            "reason": "missing_pickle_step_mapping",
        }
    return {
        "keyword": effective_binding.step_keyword(step) if effective_binding is not None else None,
        "prefix": effective_binding.step_prefix(step) if effective_binding is not None else None,
        "line_number": effective_binding.step_line_number(step) if effective_binding is not None else None,
        "doc_string": effective_binding.step_doc_string(step) if effective_binding is not None else None,
        "data_table": effective_binding.step_data_table(step) if effective_binding is not None else None,
        "state": "resolved",
        "reason": None,
    }
