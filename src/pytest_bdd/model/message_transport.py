from __future__ import annotations

from collections.abc import Callable
from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    import messages

MessageReceiver = Callable[["messages.Envelope"], None]


class MessageTransport:
    def __init__(self) -> None:
        self._lock = Lock()
        self._envelopes: list[messages.Envelope] = []
        self._sinks: list[MessageReceiver] = []

    def add_sink(self, sink: MessageReceiver) -> None:
        with self._lock:
            if sink not in self._sinks:
                self._sinks.append(sink)

    def remove_sink(self, sink: MessageReceiver) -> None:
        with self._lock:
            if sink in self._sinks:
                self._sinks.remove(sink)

    def emit(self, envelope: messages.Envelope) -> None:
        with self._lock:
            self._envelopes.append(envelope)
            sinks = list(self._sinks)
        for sink in sinks:
            sink(envelope)

    def emit_all(self, envelopes: Iterable[messages.Envelope]) -> None:
        for env in envelopes:
            self.emit(env)

    def drain(self) -> list[messages.Envelope]:
        with self._lock:
            drained, self._envelopes = self._envelopes, []
            return drained

    def get_envelopes(self) -> list[messages.Envelope]:
        with self._lock:
            return list(self._envelopes)

    def clear(self) -> None:
        with self._lock:
            self._envelopes.clear()


class MessageFanOutEmitter(MessageTransport):
    def subscribe(self, sink: MessageReceiver) -> Callable[[], None]:
        self.add_sink(sink)
        return lambda: self.remove_sink(sink)


__all__ = ["MessageFanOutEmitter", "MessageReceiver", "MessageTransport"]
