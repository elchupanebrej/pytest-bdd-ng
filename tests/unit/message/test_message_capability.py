from __future__ import annotations

import messages
from pytest_bdd.model.message_capability import (
    MessageCapability,
    capability_is_relevant,
    classify_capability_relevance,
)
from pytest_bdd.model.message_extension import (
    CONTROLLER_SINGULAR_PAYLOAD_KINDS,
    EXECUTION_PRESERVED_PAYLOAD_KINDS,
    STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS,
    LifecycleCorrelation,
    StepDefinitionPatternType,
    get_payload_kind,
    get_payload_merge_class,
    has_single_payload,
)


def test_message_capability_classification() -> None:
    cap_relevant = MessageCapability(
        capability_id="cap-1",
        baseline_release="2.3.1",
        name="Test Run Start",
        description="Emits test run started envelope",
        category="core",
        affects=frozenset({"emitted_envelope_payload"}),
    )
    assert cap_relevant.relevance == "relevant"
    assert capability_is_relevant(cap_relevant) is True

    cap_out_of_scope = MessageCapability(
        capability_id="cap-2",
        baseline_release="2.3.1",
        name="UI Theme",
        description="Theme customization",
        category="metadata",
    )
    assert cap_out_of_scope.relevance == "out_of_scope"
    assert capability_is_relevant(cap_out_of_scope) is False

    cap_explicit = MessageCapability(
        capability_id="cap-3",
        baseline_release="2.3.1",
        name="Override",
        description="Explicitly set relevance",
        category="metadata",
        affects=frozenset({"emitted_envelope_payload"}),
        explicit_relevance="out_of_scope",
    )
    assert classify_capability_relevance(cap_explicit) == "out_of_scope"


def test_message_extension_payload_helpers() -> None:
    env_empty = messages.Envelope()
    assert get_payload_kind(env_empty) is None
    assert has_single_payload(env_empty) is False
    assert get_payload_merge_class(None) is None

    ts = messages.Timestamp(seconds=1, nanos=0)
    env_started = messages.Envelope(test_run_started=messages.TestRunStarted(timestamp=ts))
    kind = get_payload_kind(env_started)
    assert kind == "test_run_started"
    assert has_single_payload(env_started) is True
    assert get_payload_merge_class(kind) == "controller_singular"

    assert get_payload_merge_class("source") == "structural_deduplicated"
    assert get_payload_merge_class("test_step_started") == "execution_preserved"
    assert "meta" in CONTROLLER_SINGULAR_PAYLOAD_KINDS
    assert "gherkin_document" in STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS
    assert "test_step_finished" in EXECUTION_PRESERVED_PAYLOAD_KINDS


def test_message_extension_pattern_and_lifecycle() -> None:
    assert StepDefinitionPatternType.pytest_bdd_heuristic_expression.value == "PYTEST_BDD_HEURISTIC_EXPRESSION"
    assert StepDefinitionPatternType.regular_expression.value == "REGULAR_EXPRESSION"

    correlation = LifecycleCorrelation(
        run_id="run-1",
        scenario_attempt_id="att-1",
        worker_id="master",
        attempt_index=0,
        step_id="step-1",
    )
    assert correlation.run_id == "run-1"
    assert correlation.step_id == "step-1"
