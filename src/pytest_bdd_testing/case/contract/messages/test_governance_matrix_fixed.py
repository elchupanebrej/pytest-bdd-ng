"""Release-readiness governance matrix tests."""

import pytest

from pytest_bdd.model.message_outcome_mapping import (
    ObservedOutcome,
    validate_outcome_mappings,
)
from pytest_bdd_testing.tool.message.capability_fixtures import make_mapping_rule

pytestmark = [pytest.mark.contract]


def _fixed_rules() -> list:
    """Return the hardcoded set of 5 OutcomeMappingRule objects for release-readiness matrix."""
    return [
        make_mapping_rule(
            "rule-passed",
            outcome_scope="scenario",
            outcome_status="passed",
            capability_ids=("cap-pass",),
        ),
        make_mapping_rule(
            "rule-failed",
            outcome_scope="scenario",
            outcome_status="failed",
            capability_ids=("cap-fail",),
        ),
        make_mapping_rule(
            "rule-skipped",
            outcome_scope="scenario",
            outcome_status="skipped",
            capability_ids=("cap-skip",),
        ),
        make_mapping_rule(
            "rule-undefined",
            outcome_scope="scenario",
            outcome_status="undefined",
            capability_ids=("cap-undef",),
        ),
        make_mapping_rule(
            "rule-interrupted",
            outcome_scope="scenario",
            outcome_status="interrupted",
            capability_ids=("cap-interrupt",),
        ),
    ]


def test_messages_fixed_release_readiness_matrix_is_valid() -> None:
    """Assert the fixed governance matrix passes validation with all required outcomes present."""
    observed_outcomes = [
        ObservedOutcome(outcome_scope="scenario", outcome_status="passed", is_parallel_worker=True),
        ObservedOutcome(outcome_scope="scenario", outcome_status="failed", is_retry=True),
        ObservedOutcome(outcome_scope="scenario", outcome_status="skipped"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="undefined"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="interrupted"),
    ]
    result = validate_outcome_mappings(_fixed_rules(), observed_outcomes)
    assert result.status == "pass", f"expected pass status, got {result.status}"


def test_messages_fixed_release_readiness_matrix_rejects_missing_parallel_worker_scenario() -> None:
    """Assert the governance matrix rejects outcomes missing the parallel-worker variant."""
    observed_outcomes = [
        ObservedOutcome(outcome_scope="scenario", outcome_status="passed"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="failed", is_retry=True),
        ObservedOutcome(outcome_scope="scenario", outcome_status="skipped"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="undefined"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="interrupted"),
    ]
    result = validate_outcome_mappings(_fixed_rules(), observed_outcomes)
    assert result.status == "fail", f"expected fail status, got {result.status}"
    assert "missing_parallel_worker_scenario" in result.missing_required_matrix_cases, (
        f"expected missing_parallel_worker_scenario in {result.missing_required_matrix_cases}"
    )
