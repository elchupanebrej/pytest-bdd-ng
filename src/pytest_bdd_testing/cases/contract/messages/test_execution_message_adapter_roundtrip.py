"""Provide test execution message adapter roundtrip helpers."""

from __future__ import annotations

from cucumber_messages import (
    Envelope as Message,  # type:ignore[attr-defined, import-untyped] — upstream library missing type stubs
)
from cucumber_messages import TestCase as CucumberTestCase
from cucumber_messages import TestStep as CucumberTestStep

from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_converter import envelope_to_dict
from pytest_bdd.model.message_registry import EnvelopeRegistry


def test_execution_message_adapter_roundtrip_preserves_test_case_links() -> None:
    """Verify execution message adapter roundtrip preserves test case links."""
    envelope = Message(
        test_case=CucumberTestCase(
            id="test-case-1",
            pickle_id="pickle-1",
            test_steps=[
                CucumberTestStep(id="test-step-1", pickle_step_id="pickle-step-1"),
                CucumberTestStep(id="test-step-2", pickle_step_id="pickle-step-2"),
            ],
        ),
    )
    registry = EnvelopeRegistry()
    registry.add_envelope(envelope)

    serialized = ExecutionMessageAdapter.serialize(envelope)
    projection = ExecutionMessageAdapter.deserialize_dict(envelope_to_dict(serialized), registry=registry)

    assert projection.payload_kind == "test_case"
    assert projection.payload.id == "test-case-1"
    assert projection.resolve("test-case-1") is registry.envelopes[0].test_case
    assert projection.resolve("test-step-1") is registry.envelopes[0].test_case.test_steps[0]
