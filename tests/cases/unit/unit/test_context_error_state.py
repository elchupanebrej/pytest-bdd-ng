"""Unit tests for ContextErrorState and remaining model helpers.

Direct-instantiation tests for small helper classes and enum-like types
in run.py that do not need a full Run fixture.
"""

from __future__ import annotations

import pytest

from pytest_bdd.model.run import (
    ActiveObjectSet,
    ContextErrorState,
    ExternalApiCompatibilityRecord,
    LifecycleObjectRef,
    NoPreviousStep,
    ReferenceResolverState,
    ReportingContextSnapshot,
    ReportingLifecycleState,
    RunStage,
    _finished_feature_ref,
    _finished_previous_step_ref,
    _finished_scenario_ref,
    _finished_step_ref,
    _inactive_feature_ref,
    _inactive_scenario_ref,
    _inactive_step_ref,
    _no_previous_step_ref,
)

pytestmark = [pytest.mark.unit]


# ── ContextErrorState ───────────────────────────────────────────────────────


class TestContextErrorState:
    """Tests for ContextErrorState class."""

    def test_as_dict_returns_all_fields(self):
        """as_dict returns all fields correctly."""
        error = ContextErrorState(
            code="object_inactive",
            message="Object is not active",
            hook_name="before_scenario",
            stage=RunStage.scenario_running,
            requested_kind="scenario",
        )
        result = error.as_dict()
        assert result["code"] == "object_inactive"
        assert result["message"] == "Object is not active"
        assert result["hook_name"] == "before_scenario"
        assert result["stage"] == "scenario_running"
        assert result["requested_kind"] == "scenario"

    def test_as_dict_with_none_requested_kind(self):
        """as_dict handles None requested_kind."""
        error = ContextErrorState(
            code="context_not_initialized",
            message="Context missing",
            hook_name="before_feature",
            stage=RunStage.idle,
        )
        result = error.as_dict()
        assert result["requested_kind"] is None

    def test_error_code_object_inactive(self):
        """ContextErrorState with object_inactive error code."""
        error = ContextErrorState(
            code="object_inactive",
            message="Feature is inactive",
            hook_name="before_step",
            stage=RunStage.step_running,
            requested_kind="feature",
        )
        assert error.code == "object_inactive"
        assert error.as_dict()["code"] == "object_inactive"

    def test_error_code_transition_order_violation(self):
        """ContextErrorState with transition_order_violation error code."""
        error = ContextErrorState(
            code="transition_order_violation",
            message="Cannot close before opening",
            hook_name="after_scenario",
            stage=RunStage.finished,
            requested_kind="scenario",
        )
        assert error.code == "transition_order_violation"

    def test_error_code_context_not_initialized(self):
        """ContextErrorState with context_not_initialized error code."""
        error = ContextErrorState(
            code="context_not_initialized",
            message="Run not started",
            hook_name="before_run",
            stage=RunStage.idle,
        )
        assert error.code == "context_not_initialized"

    def test_error_code_binding_missing(self):
        """ContextErrorState with binding_missing error code."""
        error = ContextErrorState(
            code="binding_missing",
            message="Feature binding unavailable",
            hook_name="before_scenario",
            stage=RunStage.scenario_setup,
            requested_kind="feature",
        )
        assert error.code == "binding_missing"


# ── NoPreviousStep ──────────────────────────────────────────────────────────


class TestNoPreviousStep:
    """Tests for NoPreviousStep sentinel class."""

    def test_default_id(self):
        """NoPreviousStep has expected default id."""
        nps = NoPreviousStep()
        assert nps.id == "step:no_previous_step"

    def test_default_text(self):
        """NoPreviousStep has empty default text."""
        nps = NoPreviousStep()
        assert not nps.text

    def test_default_keyword(self):
        """NoPreviousStep has empty default keyword."""
        nps = NoPreviousStep()
        assert not nps.keyword

    def test_custom_values(self):
        """NoPreviousStep accepts custom values."""
        nps = NoPreviousStep(id="custom", text="hello", keyword="Given")
        assert nps.id == "custom"
        assert nps.text == "hello"
        assert nps.keyword == "Given"


# ── Helper reference functions ──────────────────────────────────────────────


class TestReferenceHelpers:
    """Tests for _inactive_* and _finished_* helper functions."""

    def test_inactive_feature_ref(self):
        """_inactive_feature_ref produces inactive feature reference."""
        ref = _inactive_feature_ref()
        assert ref.kind == "feature"
        assert not ref.is_active
        assert ref.empty_state_reason == "idle"

    def test_inactive_scenario_ref(self):
        """_inactive_scenario_ref produces inactive scenario reference."""
        ref = _inactive_scenario_ref()
        assert ref.kind == "scenario"
        assert not ref.is_active
        assert ref.empty_state_reason == "idle"

    def test_inactive_step_ref(self):
        """_inactive_step_ref produces inactive step reference with fail_fast."""
        ref = _inactive_step_ref()
        assert ref.kind == "step"
        assert not ref.is_active
        assert ref.empty_state_reason == "idle"
        assert ref.fail_fast_code == "object_inactive"

    def test_no_previous_step_ref(self):
        """_no_previous_step_ref produces no_previous_step reference."""
        ref = _no_previous_step_ref()
        assert ref.kind == "step"
        assert not ref.is_active
        assert ref.empty_state_reason == "no_previous_step"

    def test_finished_feature_ref(self):
        """_finished_feature_ref produces finished feature reference."""
        ref = _finished_feature_ref()
        assert ref.kind == "feature"
        assert not ref.is_active
        assert ref.empty_state_reason == "finished"

    def test_finished_scenario_ref(self):
        """_finished_scenario_ref produces finished scenario reference."""
        ref = _finished_scenario_ref()
        assert ref.kind == "scenario"
        assert not ref.is_active
        assert ref.empty_state_reason == "finished"

    def test_finished_step_ref(self):
        """_finished_step_ref produces finished step reference."""
        ref = _finished_step_ref()
        assert ref.kind == "step"
        assert not ref.is_active
        assert ref.empty_state_reason == "finished"
        assert ref.fail_fast_code == "object_inactive"

    def test_finished_previous_step_ref(self):
        """_finished_previous_step_ref produces finished previous step reference."""
        ref = _finished_previous_step_ref()
        assert ref.kind == "step"
        assert not ref.is_active
        assert ref.empty_state_reason == "finished"


# ── ReportingLifecycleState ─────────────────────────────────────────────────


class TestReportingLifecycleState:
    """Tests for ReportingLifecycleState serialization."""

    def test_as_dict_serialization(self):
        """as_dict serializes all fields correctly."""
        state = ReportingLifecycleState(
            run_started_id="run-1",
            test_run_hook_started_id="hook-1",
            active_test_case_id="case-1",
            active_test_case_started_id="case-start-1",
            active_test_step_id="step-1",
            runtime_step_to_pickle_step_id={1: "pickle-1", 2: "pickle-2"},
            scenario_attempt_context={"attempt": 1, "scenario": "s1"},
            step_started_timestamp=1000.0,
            step_finished_timestamp=2000.0,
        )
        result = state.as_dict()
        assert result["run_started_id"] == "run-1"
        assert result["test_run_hook_started_id"] == "hook-1"
        assert result["active_test_case_id"] == "case-1"
        assert result["active_test_case_started_id"] == "case-start-1"
        assert result["active_test_step_id"] == "step-1"
        assert result["runtime_step_to_test_step_id"] == {"1": "pickle-1", "2": "pickle-2"}
        assert result["scenario_attempt_context"] == {"attempt": 1, "scenario": "s1"}
        assert result["step_started_timestamp"] == pytest.approx(1000.0)
        assert result["step_finished_timestamp"] == pytest.approx(2000.0)

    def test_as_dict_with_none_values(self):
        """as_dict handles None values correctly."""
        state = ReportingLifecycleState()
        result = state.as_dict()
        assert result["run_started_id"] is None
        assert result["active_test_case_id"] is None
        assert result["runtime_step_to_test_step_id"] == {}
        assert result["scenario_attempt_context"] is None

    def test_reset_scenario_scope(self):
        """reset_scenario_scope clears scenario-level state."""
        state = ReportingLifecycleState(
            active_test_case_id="case-1",
            active_test_case_started_id="start-1",
            active_test_step_id="step-1",
            runtime_step_to_pickle_step_id={1: "p1"},
            scenario_attempt_context={"a": 1},
            step_started_timestamp=100.0,
            step_finished_timestamp=200.0,
        )
        state.reset_scenario_scope()
        assert state.active_test_case_id is None
        assert state.active_test_case_started_id is None
        assert state.active_test_step_id is None
        assert state.runtime_step_to_pickle_step_id == {}
        assert state.scenario_attempt_context is None
        assert state.step_started_timestamp is None
        assert state.step_finished_timestamp is None

    def test_as_dict_preserves_run_level_ids(self):
        """as_dict preserves run-level IDs after scenario reset."""
        state = ReportingLifecycleState(
            run_started_id="run-1",
            test_run_hook_started_id="hook-1",
        )
        state.reset_scenario_scope()
        result = state.as_dict()
        assert result["run_started_id"] == "run-1"
        assert result["test_run_hook_started_id"] == "hook-1"


# ── ReportingContextSnapshot ────────────────────────────────────────────────


class TestReportingContextSnapshot:
    """Tests for ReportingContextSnapshot serialization."""

    def test_as_dict_serialization(self):
        """as_dict serializes all fields correctly."""
        run_ref = LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True)
        active_set = ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.scenario_running)
        snapshot = ReportingContextSnapshot(
            run_id="run-1",
            active_set=active_set,
            stage=RunStage.scenario_running,
            resolved_from_hierarchy=True,
            fallback_reason=None,
        )
        result = snapshot.as_dict()
        assert result["run_id"] == "run-1"
        assert result["stage"] == "scenario_running"
        assert result["resolved_from_hierarchy"] is True
        assert result["fallback_reason"] is None
        assert "active_set" in result

    def test_as_dict_with_fallback_reason(self):
        """as_dict includes fallback_reason when set."""
        run_ref = LifecycleObjectRef(kind="run", object_id="run-1", name="run", is_active=True)
        active_set = ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.idle)
        snapshot = ReportingContextSnapshot(
            run_id="run-1",
            active_set=active_set,
            stage=RunStage.idle,
            resolved_from_hierarchy=False,
            fallback_reason="no active scenario",
        )
        result = snapshot.as_dict()
        assert result["fallback_reason"] == "no active scenario"
        assert result["resolved_from_hierarchy"] is False


# ── ExternalApiCompatibilityRecord ──────────────────────────────────────────


class TestExternalApiCompatibilityRecord:
    """Tests for ExternalApiCompatibilityRecord serialization."""

    def test_as_dict_serialization(self):
        """as_dict serializes all fields correctly."""
        record = ExternalApiCompatibilityRecord(
            api_surface_id="pytest_bdd.steps",
            baseline_reference="v0.1.0",
            changed_symbols=["given", "when"],
            removed_symbols=["old_step"],
            renamed_symbols=["old_then"],
            additive_symbols=["new_step"],
            consumer_migration_required=True,
        )
        result = record.as_dict()
        assert result["api_surface_id"] == "pytest_bdd.steps"
        assert result["baseline_reference"] == "v0.1.0"
        assert result["changed_symbols"] == ["given", "when"]
        assert result["removed_symbols"] == ["old_step"]
        assert result["renamed_symbols"] == ["old_then"]
        assert result["additive_symbols"] == ["new_step"]
        assert result["consumer_migration_required"] is True

    def test_as_dict_with_empty_lists(self):
        """as_dict handles empty symbol lists."""
        record = ExternalApiCompatibilityRecord(
            api_surface_id="pytest_bdd.parsers",
            baseline_reference="v0.2.0",
            changed_symbols=[],
            removed_symbols=[],
            renamed_symbols=[],
            additive_symbols=[],
            consumer_migration_required=False,
        )
        result = record.as_dict()
        assert result["changed_symbols"] == []
        assert result["removed_symbols"] == []
        assert result["consumer_migration_required"] is False


# ── ReferenceResolverState ──────────────────────────────────────────────────


class TestReferenceResolverState:
    """Tests for ReferenceResolverState."""

    def test_as_dict_serialization(self):
        """as_dict serializes missing_reference_diagnostics."""
        state = ReferenceResolverState()
        state.add_missing_reference("Feature not found")
        state.add_missing_reference("Scenario missing")
        result = state.as_dict()
        assert result["missing_reference_diagnostics"] == ["Feature not found", "Scenario missing"]

    def test_clear_removes_all_diagnostics(self):
        """clear removes all accumulated diagnostics."""
        state = ReferenceResolverState()
        state.add_missing_reference("test")
        state.clear()
        assert state.as_dict()["missing_reference_diagnostics"] == []

    def test_initial_state_empty(self):
        """Initial state has empty diagnostics list."""
        state = ReferenceResolverState()
        assert state.as_dict()["missing_reference_diagnostics"] == []
