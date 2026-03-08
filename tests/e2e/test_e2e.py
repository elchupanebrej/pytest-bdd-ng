from pytest_bdd import scenarios
from pytest_bdd.model.message_outcome_mapping import ObservedOutcome, validate_outcome_mappings
from tests.messages.message_capability_fixtures import make_mapping_rule


def _exclude_allure_features(config, feature, pickle):  # noqa: ARG001
    feature_uri = getattr(feature, "uri", "")
    feature_name = str(getattr(getattr(feature, "feature", None), "name", "")).lower()
    return "report/allure/" not in str(feature_uri).lower() and not feature_name.startswith("allure ")


test = scenarios(".", filter_=_exclude_allure_features)


def _fixed_rules():
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


def test_messages_fixed_release_readiness_matrix_is_valid() -> None:
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
