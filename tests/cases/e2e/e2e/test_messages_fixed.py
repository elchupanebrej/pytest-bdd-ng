"""E2E tests for messages fixed release readiness matrix."""

from types import SimpleNamespace

import pytest
from contract.messages.message_capability_fixtures import make_mapping_rule

from pytest_bdd.model.message_outcome_mapping import ObservedOutcome, validate_outcome_mappings

pytestmark = [pytest.mark.e2e]


def _fixed_rules():
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
    """Verify messages fixed release readiness matrix is valid."""
    observed_outcomes = [
        ObservedOutcome(outcome_scope="scenario", outcome_status="passed", is_parallel_worker=True),
        ObservedOutcome(outcome_scope="scenario", outcome_status="failed", is_retry=True),
        ObservedOutcome(outcome_scope="scenario", outcome_status="skipped"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="undefined"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="interrupted"),
    ]

    result = validate_outcome_mappings(_fixed_rules(), observed_outcomes)

    assert result.status == "pass"


def test_messages_fixed_release_readiness_matrix_rejects_missing_parallel_worker_scenario() -> None:
    """Verify messages fixed release readiness matrix rejects missing parallel worker scenario."""
    observed_outcomes = [
        ObservedOutcome(outcome_scope="scenario", outcome_status="passed"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="failed", is_retry=True),
        ObservedOutcome(outcome_scope="scenario", outcome_status="skipped"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="undefined"),
        ObservedOutcome(outcome_scope="scenario", outcome_status="interrupted"),
    ]

    result = validate_outcome_mappings(_fixed_rules(), observed_outcomes)

    assert result.status == "fail"
    assert "missing_parallel_worker_scenario" in result.missing_required_matrix_cases


def test_default_bdd_filter_excludes_tagged_slow_scenarios() -> None:
    """Verify default bdd filter excludes tagged slow scenarios."""

    from ._bdd_filter import exclude_default_bdd_features

    def _tag(name: str):
        return SimpleNamespace(name=name)

    def _document(*, name: str, tags: list[str], uri: str = "file:test.feature"):
        return SimpleNamespace(
            uri=uri,
            feature=SimpleNamespace(
                name=name,
                tags=[_tag(tag) for tag in tags],
            ),
        )

    def _pickle(*tags: str):
        return SimpleNamespace(tags=[_tag(tag) for tag in tags])

    assert (
        exclude_default_bdd_features(
            None,
            _document(name="fast suite", tags=["@xdist"]),
            _pickle(),
        )
        is False
    )
    assert (
        exclude_default_bdd_features(
            None,
            _document(name="fast suite", tags=[]),
            _pickle("@docker"),
        )
        is False
    )
    assert (
        exclude_default_bdd_features(
            None,
            _document(name="fast suite", tags=[]),
            _pickle(),
        )
        is True
    )
    assert (
        exclude_default_bdd_features(
            None,
            _document(
                name="xdist html reporting",
                tags=[],
                uri="file:07 Report/07 xdist HTML reporting.feature.md",
            ),
            _pickle(),
        )
        is True
    )
    assert (
        exclude_default_bdd_features(
            None,
            _document(
                name="report gathering outputs",
                tags=[],
                uri="file:07 Report/02 Gathering.feature.md",
            ),
            SimpleNamespace(
                name="HTML report could be produced on the feature run",
                tags=[],
            ),
        )
        is False
    )
    assert (
        exclude_default_bdd_features(
            None,
            _document(
                name="cucumber formatter reports",
                tags=[],
                uri="file:07 Report/09 Cucumber formatter reports.feature.md",
            ),
            _pickle(),
        )
        is True
    )
