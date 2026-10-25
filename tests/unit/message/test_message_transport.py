from __future__ import annotations

from pytest_cuke.model import message_converter as mc, message_types as messages
from pytest_cuke.model.message_extension import StepDefinitionPatternType
from pytest_cuke.model.message_transport import MessageFanOutEmitter, MessageTransport, ValidatedMessageTransport

def test_message_transport_buffering_and_sinks() -> None:
    transport = MessageTransport()
    received: list[messages.Envelope] = []
    transport.add_sink(received.append)
    transport.emit_all([mc.make_test_run_started(100.0), mc.make_test_run_finished(timestamp=101.0)])
    assert len(received) == 2
    assert len(transport.get_envelopes()) == 2

    transport.remove_sink(received.append)
    transport.emit(mc.make_test_run_started(102.0))
    assert len(received) == 2
    assert len(transport.drain()) == 3
    assert transport.get_envelopes() == []

    emitter = MessageFanOutEmitter()
    calls: list[messages.Envelope] = []
    unsub = emitter.subscribe(calls.append)
    emitter.emit(mc.make_test_run_started(100.0))
    assert len(calls) == 1
    unsub()
    emitter.emit(mc.make_test_run_started(101.0))
    assert len(calls) == 1


def test_validated_transport_fans_out_official_wire_dataclasses() -> None:
    transport = ValidatedMessageTransport()
    received: list[messages.Envelope] = []
    transport.add_sink(received.append)
    internal = messages.Envelope(
        step_definition=messages.StepDefinition(
            id="definition-1",
            pattern=messages.StepDefinitionPattern(
                source="example",
                type=StepDefinitionPatternType.pytest_cuke_heuristic_expression,
            ),
            source_reference=messages.SourceReference(uri="steps.py", location=messages.Location(line=1)),
        )
    )

    transport.emit(internal)

    assert received[0].step_definition is not None
    assert received[0].step_definition.pattern.type is messages.MessageStepDefinitionPatternType.cucumber_expression
    assert messages.message_to_dict(received[0])["stepDefinition"]["pattern"]["type"] == "CUCUMBER_EXPRESSION"
