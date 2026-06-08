"""Provide test e2e helpers."""

from collections.abc import Iterable
from types import SimpleNamespace
from typing import TypeAlias

import pytest

from pytest_bdd import scenarios
from pytest_bdd.model.message_outcome_mapping import ObservedOutcome, validate_outcome_mappings
from pytest_bdd_testing.cases.contract.messages.message_capability_fixtures import make_mapping_rule

Namespace: TypeAlias = SimpleNamespace

pytestmark = [pytest.mark.e2e_retain_technical]

_EXCLUDED_TAGS = {"allure", "docker", "slow", "xdist"}
_EXCLUDED_FEATURE_URI_FRAGMENTS = ("07 report/08 xdist remote network reporting.feature.md",)
_EXCLUDED_FEATURE_SCENARIOS = {
    (
        "07 report/02 gathering.feature.md",
        "html report could be produced on the feature run",
    ),
}


def _iter_tag_names(feature: Namespace, pickle: Namespace) -> Iterable[str]:
    yield from (str(tag.name).lstrip("@").lower() for tag in getattr(getattr(feature, "feature", None), "tags", ()))
    yield from (str(tag.name).lstrip("@").lower() for tag in getattr(pickle, "tags", ()))


def _exclude_default_bdd_features(config: object, feature: Namespace, pickle: Namespace) -> bool:  # noqa: ARG001
    feature_uri = str(getattr(feature, "uri", "")).lower()
    feature_name = str(getattr(getattr(feature, "feature", None), "name", "")).lower()
    scenario_name = str(getattr(pickle, "name", "")).lower()
    tag_names = set(_iter_tag_names(feature, pickle))
    return (
        "allure" not in feature_uri
        and not feature_name.startswith("allure ")
        and not any(fragment in feature_uri for fragment in _EXCLUDED_FEATURE_URI_FRAGMENTS)
        and not any(
            fragment in feature_uri and scenario == scenario_name for fragment, scenario in _EXCLUDED_FEATURE_SCENARIOS
        )
        and tag_names.isdisjoint(_EXCLUDED_TAGS)
    )


test = scenarios(".", filter_=_exclude_default_bdd_features)

pytest_plugins = [
    "pytest_bdd_testing.cases.e2e.steps_go_parser",
    "pytest_bdd_testing.cases.e2e.steps_tag_expressions",
    "pytest_bdd_testing.cases.e2e.steps_heading_validation",
    "pytest_bdd_testing.cases.e2e.steps_mimetype",
    "pytest_bdd_testing.cases.e2e.steps_struct_bdd",
    "pytest_bdd_testing.cases.e2e.steps_formatters",
    "pytest_bdd_testing.cases.e2e.steps_code_generator",
    "pytest_bdd_testing.cases.e2e.steps_scenario_reporter",
    "pytest_bdd_testing.cases.e2e.steps_compatibility",
    "pytest_bdd_testing.cases.e2e.steps_batch_collection",
]


def _fixed_rules() -> list[object]:
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


def _raise_assertion(message: str) -> None:
    """
    Raise an assertion failure.

    Raises:
        AssertionError: Always raised with the provided message.

    """
    raise AssertionError(message)


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

    if result.status != "pass":
        msg = f"expected pass status, got {result.status}"
        _raise_assertion(msg)


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

    if result.status != "fail":
        msg = f"expected fail status, got {result.status}"
        _raise_assertion(msg)
    if "missing_parallel_worker_scenario" not in result.missing_required_matrix_cases:
        msg = "expected missing_parallel_worker_scenario in missing cases"
        _raise_assertion(msg)


def test_default_bdd_filter_excludes_tagged_slow_scenarios() -> None:
    """Verify default bdd filter excludes tagged slow scenarios."""

    def _tag(name: str) -> Namespace:
        return SimpleNamespace(name=name)

    def _document(*, name: str, tags: list[str], uri: str = "file:test.feature") -> Namespace:
        return SimpleNamespace(
            uri=uri,
            feature=SimpleNamespace(
                name=name,
                tags=[_tag(tag) for tag in tags],
            ),
        )

    def _pickle(*tags: str) -> Namespace:
        return SimpleNamespace(tags=[_tag(tag) for tag in tags])

    filter_cases = (
        (_document(name="fast suite", tags=["@xdist"]), _pickle(), False),
        (_document(name="fast suite", tags=[]), _pickle("@docker"), False),
        (_document(name="fast suite", tags=[]), _pickle(), True),
        (
            _document(
                name="xdist html reporting",
                tags=[],
                uri="file:07 Report/07 xdist HTML reporting.feature.md",
            ),
            _pickle(),
            True,
        ),
        (
            _document(
                name="report gathering outputs",
                tags=[],
                uri="file:07 Report/02 Gathering.feature.md",
            ),
            SimpleNamespace(
                name="HTML report could be produced on the feature run",
                tags=[],
            ),
            False,
        ),
        (
            _document(
                name="cucumber formatter reports",
                tags=[],
                uri="file:07 Report/09 Cucumber formatter reports.feature.md",
            ),
            _pickle(),
            True,
        ),
    )
    for feature, pickle, expected in filter_cases:
        actual = _exclude_default_bdd_features(None, feature, pickle)
        if actual is not expected:
            msg = f"expected filter result {expected}, got {actual}"
            _raise_assertion(msg)
