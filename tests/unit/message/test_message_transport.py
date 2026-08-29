from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.model import message_converter as mc
from pytest_bdd.model.message_transport import MessageFanOutEmitter, MessageTransport

if TYPE_CHECKING:
    import messages


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
