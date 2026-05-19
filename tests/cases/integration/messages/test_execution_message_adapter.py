"""Provide test execution message adapter helpers."""

from __future__ import annotations

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import JavaMethod, JavaStackTraceElement, Location, SourceReference, StepDefinition, Timestamp
from cucumber_messages import StepDefinitionPattern as CucumberStepDefinitionPattern
from cucumber_messages import TestRunStarted as CucumberTestRunStarted

from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_converter import envelope_to_dict
from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.model.message_registry import EnvelopeRegistry
from pytest_bdd.model.message_serialization import MessageSerializationProfile


def test_execution_message_adapter_serializes_envelope_canonically() -> None:
    """Verify execution message adapter serializes envelope canonically."""
    envelope = Message(
        test_run_started=CucumberTestRunStarted(id="run-started-1", timestamp=Timestamp(seconds=0, nanos=0)),
    )

    serialized = ExecutionMessageAdapter.serialize(envelope)

    assert envelope_to_dict(serialized) == envelope_to_dict(envelope)


def test_execution_message_adapter_deserializes_with_registry_projection() -> None:
    """Verify execution message adapter deserializes with registry projection."""
    envelope = Message(
        test_run_started=CucumberTestRunStarted(id="run-started-1", timestamp=Timestamp(seconds=0, nanos=0)),
    )
    registry = EnvelopeRegistry()
    registry.add_envelope(envelope)

    projection = ExecutionMessageAdapter.deserialize(envelope, registry=registry)

    assert projection.payload_kind == "test_run_started"
    assert projection.payload_id == "run-started-1"
    assert projection.resolve("run-started-1") is registry.envelopes[0].test_run_started


def test_execution_message_adapter_serializes_schema_compatible_step_definition_pattern() -> None:
    """Verify execution message adapter serializes schema compatible step definition pattern."""
    envelope = Message(
        step_definition=StepDefinition(
            id="step-definition-1",
            pattern=CucumberStepDefinitionPattern(
                source="I have {count:d} cucumbers",
                type=StepDefinitionPatternType.pytest_bdd_parse_expression,
            ),
            source_reference=SourceReference(
                uri="steps.py",
                location=Location(line=1, column=1),
                java_method=JavaMethod(class_name="steps", method_name="step", method_parameter_types=[]),
                java_stack_trace_element=JavaStackTraceElement(
                    class_name="steps",
                    file_name="steps.py",
                    method_name="step",
                ),
            ),
        ),
    )

    serialized = ExecutionMessageAdapter.serialize_to_dict(
        envelope,
        profile=MessageSerializationProfile.schema_compatible,
    )

    assert serialized["stepDefinition"]["pattern"]["type"] == "REGULAR_EXPRESSION"
    assert envelope_to_dict(envelope)["stepDefinition"]["pattern"]["type"] == "PYTEST_BDD_PARSE_EXPRESSION"
