from __future__ import annotations

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]
from cucumber_messages import TestRunStarted as CucumberTestRunStarted
from cucumber_messages import Timestamp

from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_converter import envelope_to_dict
from pytest_bdd.model.message_registry import EnvelopeRegistry


def test_execution_message_adapter_serializes_envelope_canonically() -> None:
    envelope = Message(
        test_run_started=CucumberTestRunStarted(id="run-started-1", timestamp=Timestamp(seconds=0, nanos=0))
    )

    serialized = ExecutionMessageAdapter.serialize(envelope)

    assert envelope_to_dict(serialized) == envelope_to_dict(envelope)


def test_execution_message_adapter_deserializes_with_registry_projection() -> None:
    envelope = Message(
        test_run_started=CucumberTestRunStarted(id="run-started-1", timestamp=Timestamp(seconds=0, nanos=0))
    )
    registry = EnvelopeRegistry()
    registry.add_envelope(envelope)

    projection = ExecutionMessageAdapter.deserialize(envelope, registry=registry)

    assert projection.payload_kind == "test_run_started"
    assert projection.payload_id == "run-started-1"
    assert projection.resolve("run-started-1") is registry.envelopes[0].test_run_started
