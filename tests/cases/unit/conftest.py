"""Shared factory fixtures for unit tests."""

from __future__ import annotations

import pytest

from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
from pytest_bdd.model.run import ActiveObjectSet, HookPhase, LifecycleObjectRef, Run, RunStage, RunStatus
from pytest_bdd.model.scenario_run import RunNode, ScenarioRun


def _build_run(**kwargs) -> Run:
    """Build a minimal Run instance with sensible defaults."""
    defaults = {
        "id": "run-1",
        "run_ref": LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True),
        "status": RunStatus.ok,
    }
    defaults.update(kwargs)
    return Run(**defaults)


def _build_scenario_run(**kwargs) -> ScenarioRun:
    """Build a minimal ScenarioRun instance with sensible defaults."""
    run = _build_run()
    run_ref = run.run_ref
    feature_ref = LifecycleObjectRef(kind="feature", object_id="feature-1", name="Feature", is_active=True)
    scenario_ref = LifecycleObjectRef(kind="scenario", object_id="scenario-1", name="Scenario", is_active=True)

    defaults = {
        "id": "ctx-1",
        "run_ref": run_ref,
        "active_hook": HookPhase.before_scenario,
        "stage": RunStage.idle,
        "status": RunStatus.ok,
        "active_set": ActiveObjectSet(
            run=run_ref,
            feature=feature_ref,
            scenario=scenario_ref,
            captured_at_stage=RunStage.idle,
        ),
        "run": run,
        "feature_ref": feature_ref,
        "scenario_ref": scenario_ref,
        "feature_node": RunNode(
            id="feature-node-1",
            parent_id=run.id,
            kind="feature",
            object_ref=feature_ref,
            is_active=True,
            opened_at_transition=0,
        ),
        "scenario_node": RunNode(
            id="scenario-node-1",
            parent_id="feature-node-1",
            kind="scenario",
            object_ref=scenario_ref,
            is_active=True,
            opened_at_transition=0,
        ),
    }
    defaults.update(kwargs)
    return ScenarioRun(**defaults)


def _build_feature_binding(**kwargs) -> FeatureRuntimeBinding:
    """Build a minimal FeatureRuntimeBinding with required fields set to empty/None."""
    from types import SimpleNamespace

    defaults = {
        "feature": None,
        "filename": "features/example.feature",
        "source": SimpleNamespace(uri="file:features/example.feature", data="", media_type=""),
        "gherkin_document": None,
        "scenario_asts": [],
        "examples_tables": [],
        "rule": None,
        "is_empty": True,
    }
    defaults.update(kwargs)
    return FeatureRuntimeBinding(**defaults)


@pytest.fixture
def run() -> Run:
    """Return a default Run instance."""
    return _build_run()


@pytest.fixture
def scenario_run() -> ScenarioRun:
    """Return a default ScenarioRun instance."""
    return _build_scenario_run()


@pytest.fixture
def feature_binding() -> FeatureRuntimeBinding:
    """Return a default FeatureRuntimeBinding instance."""
    return _build_feature_binding()
