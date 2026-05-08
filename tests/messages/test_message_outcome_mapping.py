"""Provide test message outcome mapping helpers."""

from __future__ import annotations

from pytest_bdd.model.message_outcome_mapping import (
    MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1,
    ObservedOutcome,
    resolve_outcome_mapping,
    validate_outcome_mappings,
)

from .message_capability_fixtures import make_mapping_rule


def _fixed_matrix_rules():
    return [
        make_mapping_rule(
            "rule-passed", outcome_scope="scenario", outcome_status="passed", capability_ids=("cap-pass",)
        ),
        make_mapping_rule(
            "rule-failed", outcome_scope="scenario", outcome_status="failed", capability_ids=("cap-fail",)
        ),
        make_mapping_rule(
            "rule-skipped", outcome_scope="scenario", outcome_status="skipped", capability_ids=("cap-skip",)
        ),
        make_mapping_rule(
            "rule-undefined", outcome_scope="scenario", outcome_status="undefined", capability_ids=("cap-undef",)
        ),
        make_mapping_rule(
            "rule-interrupted",
            outcome_scope="scenario",
            outcome_status="interrupted",
            capability_ids=("cap-interrupt",),
        ),
    ]


def _fixed_matrix_outcomes():
    return [
        ObservedOutcome(outcome_scope="scenario", outcome_status="passed", is_parallel_worker=True),
        ObservedOutcome(outcome_scope="scenario", outcome_status="failed", is_retry=True),
        ObservedOutcome(outcome_scope="scenario", outcome_status="skipped"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="undefined"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="interrupted"),
    ]


def test_resolve_outcome_mapping_uses_priority_order() -> None:
    """Verify resolve outcome mapping uses priority order."""
    rules = [
        make_mapping_rule(
            "rule-high-priority",
            outcome_scope="scenario",
            outcome_status="failed",
            capability_ids=("cap-hi",),
            priority=0,
        ),
        make_mapping_rule(
            "rule-low-priority",
            outcome_scope="scenario",
            outcome_status="failed",
            capability_ids=("cap-low",),
            priority=10,
        ),
    ]

    selected, is_ambiguous = resolve_outcome_mapping(rules, outcome_scope="scenario", outcome_status="failed")

    assert is_ambiguous is False
    assert selected is not None
    assert selected.mapping_id == "rule-high-priority"


def test_resolve_outcome_mapping_reports_ambiguity_for_equal_priority() -> None:
    """Verify resolve outcome mapping reports ambiguity for equal priority."""
    rules = [
        make_mapping_rule(
            "rule-a",
            outcome_scope="scenario",
            outcome_status="failed",
            capability_ids=("cap-a",),
            priority=5,
        ),
        make_mapping_rule(
            "rule-b",
            outcome_scope="scenario",
            outcome_status="failed",
            capability_ids=("cap-b",),
            priority=5,
        ),
    ]

    selected, is_ambiguous = resolve_outcome_mapping(rules, outcome_scope="scenario", outcome_status="failed")

    assert selected is None
    assert is_ambiguous is True


def test_validate_outcome_mappings_passes_for_fixed_release_readiness_matrix() -> None:
    """Verify validate outcome mappings passes for fixed release readiness matrix."""
    result = validate_outcome_mappings(
        _fixed_matrix_rules(),
        _fixed_matrix_outcomes(),
        matrix_profile=MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1,
    )

    assert result.status == "pass"
    assert result.ambiguous_outcomes == ()
    assert result.unmapped_outcomes == ()
    assert result.missing_required_matrix_cases == ()


def test_validate_outcome_mappings_rejects_missing_retry_and_parallel() -> None:
    """Verify validate outcome mappings rejects missing retry and parallel."""
    outcomes = [
        ObservedOutcome(outcome_scope="scenario", outcome_status="passed"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="failed"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="skipped"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="undefined"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="interrupted"),
    ]

    result = validate_outcome_mappings(_fixed_matrix_rules(), outcomes)

    assert result.status == "fail"
    assert set(result.missing_required_matrix_cases) == {"missing_parallel_worker_scenario", "missing_retry_scenario"}


def test_validate_outcome_mappings_reports_unmapped_fixed_matrix_outcomes() -> None:
    """Verify validate outcome mappings reports unmapped fixed matrix outcomes."""
    result = validate_outcome_mappings(
        _fixed_matrix_rules()[:-1],
        _fixed_matrix_outcomes(),
        matrix_profile=MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1,
    )

    assert result.status == "fail"
    assert "scenario:interrupted" in result.unmapped_outcomes
