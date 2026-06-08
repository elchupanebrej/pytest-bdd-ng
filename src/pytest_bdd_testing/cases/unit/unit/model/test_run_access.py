"""Unit tests for run access helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from cucumber_messages import Pickle, PickleStep

from pytest_bdd.model.run import ActiveObjectSet, LifecycleObjectRef, Run, RunStage, RunStatus
from pytest_bdd.model.run_access import (
    build_reporting_context_snapshot,
    resolve_active_object_or_error,
    resolve_pickle_object,
    resolve_previous_step_object,
    resolve_scenario_description,
    resolve_step_object,
    resolve_step_runtime_enrichment,
)
from pytest_bdd.model.scenario_run import ScenarioRun

pytestmark = [pytest.mark.unit]


def _build_run() -> Run:
    """Build a minimal run."""
    return Run(
        id="run-1",
        run_ref=LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True),
        status=RunStatus.ok,
    )


def _build_scenario_run(run: Run | None = None) -> ScenarioRun:
    """Build a minimal scenario run."""
    if run is None:
        run = _build_run()
    scenario = ScenarioRun(
        id="ctx-1",
        run_ref=run.run_ref,
        active_hook="pytest_bdd_before_scenario",
        stage=RunStage.scenario_setup,
        status=RunStatus.ok,
        active_set=ActiveObjectSet(
            run=run.run_ref,
            feature=LifecycleObjectRef.inactive("feature", reason="idle"),
            captured_at_stage=RunStage.scenario_setup,
        ),
        run=run,
    )
    run.active_scenario_run = scenario
    return scenario


def test_resolve_active_object_returns_error_for_inactive_slot() -> None:
    """resolve_active_object_or_error records context error for inactive objects."""
    scenario_run = _build_scenario_run()

    ref, error = resolve_active_object_or_error(
        hook_name="pytest_bdd_before_feature",
        scenario_run=scenario_run,
        requested_kind="feature",
    )

    assert ref is None
    assert error is not None
    assert error.code == "object_inactive"
    assert error.requested_kind == "feature"


def test_build_reporting_context_snapshot_uses_active_scenario_hierarchy() -> None:
    """Snapshot resolves from active scenario when available."""
    stash: dict[str, object] = {}
    run = Run.initialize_for_session(stash=stash, session=SimpleNamespace(name="session"))
    scenario_run = _build_scenario_run(run)
    request = SimpleNamespace(config=SimpleNamespace(stash=stash), session=SimpleNamespace(name="session"))

    snapshot = build_reporting_context_snapshot(request=request)

    assert snapshot.run_id == run.id
    assert snapshot.active_set is scenario_run.active_set
    assert snapshot.resolved_from_hierarchy is True


def test_build_reporting_context_snapshot_falls_back_without_run() -> None:
    """Snapshot falls back when run is missing from stash."""
    request = SimpleNamespace(config=SimpleNamespace(stash={}), session=SimpleNamespace(name="session"))

    snapshot = build_reporting_context_snapshot(request=request, fallback_reason="missing")

    assert snapshot.run_id.startswith("run-")
    assert snapshot.fallback_reason == "missing"
    assert snapshot.resolved_from_hierarchy is False


def test_resolve_objects_return_none_without_active_scenario() -> None:
    """Object resolvers return None when no scenario is active."""
    run = _build_run()

    assert resolve_pickle_object(run) is None
    assert resolve_step_object(run) is None
    assert resolve_previous_step_object(run) is None


def test_resolve_scenario_description_records_missing_ast_ids() -> None:
    """Scenario description resolver records missing pickle ast ids."""
    scenario_run = _build_scenario_run()
    pickle = Pickle(
        id="p1",
        uri="file:test.feature",
        ast_node_ids=[],
        language="en",
        name="Scenario",
        steps=[],
        tags=[],
    )

    assert resolve_scenario_description(pickle=pickle, scenario_run=scenario_run) is None
    assert "Pickle has no ast_node_ids" in scenario_run.reference_resolver.missing_reference_diagnostics


def test_resolve_step_runtime_enrichment_reports_unresolved_step() -> None:
    """Step runtime enrichment returns unresolved payload when no binding maps the step."""
    scenario_run = _build_scenario_run()
    step = PickleStep(id="step-1", type=1, text="a step", ast_node_ids=[])

    enrichment = resolve_step_runtime_enrichment(step=step, scenario_run=scenario_run)

    assert enrichment["state"] == "unresolved"
    assert enrichment["reason"] == "missing_pickle_step_mapping"
    assert "Missing pickle step mapping: step-1" in scenario_run.reference_resolver.missing_reference_diagnostics
