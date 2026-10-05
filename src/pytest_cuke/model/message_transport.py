from __future__ import annotations

from collections import deque
from collections.abc import Callable
from copy import deepcopy
from threading import Lock, get_ident
from typing import TYPE_CHECKING, Any

from pytest_cuke.model.message_extension import get_payload_kind
from pytest_cuke.model.message_stream_validation import MessageStreamValidator
from pytest_cuke.model.message_types import message_to_dict
from pytest_cuke.model.message_validation import (
    MessageValidationDiagnostic,
    MessageValidationError,
    integration_diagnostic,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pytest_cuke.model import message_types as messages

MessageReceiver = Callable[["cucumber_messages.Envelope"], None]


class MessageTransport:
    def __init__(self) -> None:
        self._lock = Lock()
        self._envelopes: list[cucumber_messages.Envelope] = []
        self._sinks: list[MessageReceiver] = []

    def add_sink(self, sink: MessageReceiver) -> None:
        with self._lock:
            if sink not in self._sinks:
                self._sinks.append(sink)

    def remove_sink(self, sink: MessageReceiver) -> None:
        with self._lock:
            if sink in self._sinks:
                self._sinks.remove(sink)

    def emit(self, envelope: cucumber_messages.Envelope) -> None:
        with self._lock:
            self._envelopes.append(envelope)
            sinks = list(self._sinks)
        for sink in sinks:
            sink(envelope)

    def emit_all(self, envelopes: Iterable[cucumber_messages.Envelope]) -> None:
        for env in envelopes:
            self.emit(env)

    def drain(self) -> list[cucumber_messages.Envelope]:
        with self._lock:
            drained, self._envelopes = self._envelopes, []
            return drained

    def get_envelopes(self) -> list[cucumber_messages.Envelope]:
        with self._lock:
            return list(self._envelopes)

    def clear(self) -> None:
        with self._lock:
            self._envelopes.clear()


class MessageFanOutEmitter(MessageTransport):
    def subscribe(self, sink: MessageReceiver) -> Callable[[], None]:
        self.add_sink(sink)
        return lambda: self.remove_sink(sink)


class MessageEnvelopeView:
    """Expose a canonical serialized envelope while delegating model fields."""

    def __init__(self, envelope: messages.Envelope, *, exception_stack_trace: str) -> None:
        self._envelope = envelope
        self._exception_stack_trace = exception_stack_trace

    def __getattr__(self, name: str) -> Any:
        return getattr(self._envelope, name)

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        payload = message_to_dict(self._envelope)
        event_key = "testStepFinished"
        result_key = "testStepResult"
        exception_key = "exception"
        stack_trace_key = "stackTrace"
        event = payload.get(event_key)
        if not isinstance(event, dict):
            return payload
        result = event.get(result_key)
        if not isinstance(result, dict):
            return payload
        exception = result.get(exception_key)
        if isinstance(exception, dict):
            exception[stack_trace_key] = self._exception_stack_trace
        return payload


class ValidatedMessageTransport:
    """Validate each envelope before broadcasting it to ordered report sinks.

    Validation and fan-out share one ordered boundary. Re-entrant emissions from
    a sink are validated immediately and queued until every sink has received
    the envelope that caused the re-entry.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._envelopes: list[messages.Envelope] = []
        self._sinks: list[MessageReceiver] = []
        self._validator = MessageStreamValidator()
        self._dispatch_lock = Lock()
        self._dispatching_thread: int | None = None
        self._pending: deque[tuple[int, messages.Envelope]] = deque()
        self._position = 0
        self._sink_names: dict[int, str] = {}
        self._sink_diagnostics: list[MessageValidationDiagnostic] = []

    def add_sink(self, sink: MessageReceiver, *, name: str | None = None) -> None:
        with self._lock:
            if sink not in self._sinks:
                self._sinks.append(sink)
            if name is not None:
                self._sink_names[id(sink)] = name

    def remove_sink(self, sink: MessageReceiver) -> None:
        with self._lock:
            if sink in self._sinks:
                self._sinks.remove(sink)
            self._sink_names.pop(id(sink), None)

    def emit(self, envelope: messages.Envelope) -> tuple[MessageValidationDiagnostic, ...]:
        """Reject invalid envelopes before any sink sees them; return sink errors."""
        current_thread = get_ident()
        with self._lock:
            if self._dispatching_thread == current_thread:
                self._accept_locked(envelope)
                return ()

        with self._dispatch_lock:
            with self._lock:
                self._accept_locked(envelope)
                self._dispatching_thread = current_thread

            emitted_diagnostics: list[MessageValidationDiagnostic] = []
            try:
                while True:
                    with self._lock:
                        if not self._pending:
                            break
                        position, pending_envelope = self._pending.popleft()
                        sinks = list(self._sinks)

                    for sink in sinks:
                        try:
                            sink(pending_envelope)
                        except Exception as error:
                            diagnostic = self._make_sink_diagnostic(
                                position=position,
                                sink_name=self._sink_names.get(id(sink), _receiver_name(sink)),
                                envelope=pending_envelope,
                                error=error,
                            )
                            with self._lock:
                                self._sink_diagnostics.append(diagnostic)
                            emitted_diagnostics.append(diagnostic)
            finally:
                with self._lock:
                    self._dispatching_thread = None

            return tuple(emitted_diagnostics)

    def _accept_locked(self, envelope: messages.Envelope) -> None:
        position = self._position
        self._position += 1
        canonical_envelope = self._validator.accept(envelope)
        self._envelopes.append(canonical_envelope)
        self._pending.append((position, canonical_envelope))

    def preview_finish(self, envelope: messages.Envelope) -> tuple[MessageValidationDiagnostic, ...]:
        """Return terminal validation errors without changing the live stream."""
        with self._dispatch_lock, self._lock:
            preview = deepcopy(self._validator)
        try:
            preview.accept(envelope)
        except MessageValidationError as error:
            return error.diagnostics
        return preview.finish()

    def finish(self) -> tuple[MessageValidationDiagnostic, ...]:
        """Finish lifecycle validation after normal pytest session completion."""
        with self._dispatch_lock, self._lock:
            return self._validator.finish()

    def record_sink_failure(self, sink_name: str, error: Exception) -> MessageValidationDiagnostic:
        """Record an asynchronous sink failure discovered during finalization."""
        with self._lock:
            diagnostic = integration_diagnostic(
                "SINK_FAILURE",
                position=self._position,
                payload_kind=None,
                message=f"Message sink {sink_name!r} failed: {type(error).__name__}: {error}",
            )
            self._sink_diagnostics.append(diagnostic)
            return diagnostic

    @property
    def diagnostics(self) -> tuple[MessageValidationDiagnostic, ...]:
        with self._lock:
            return (*self._validator.diagnostics, *self._sink_diagnostics)

    @property
    def next_position(self) -> int:
        with self._lock:
            return self._position

    @property
    def has_errors(self) -> bool:
        return bool(self.diagnostics)

    def _make_sink_diagnostic(
        self,
        *,
        position: int,
        sink_name: str,
        envelope: messages.Envelope,
        error: Exception,
    ) -> MessageValidationDiagnostic:
        return integration_diagnostic(
            "SINK_FAILURE",
            position=position,
            payload_kind=get_payload_kind(envelope),
            message=f"Message sink {sink_name!r} failed: {type(error).__name__}: {error}",
        )


def _receiver_name(sink: MessageReceiver) -> str:
    name = getattr(sink, "__qualname__", None)
    if isinstance(name, str) and name:
        return name
    return type(sink).__name__


__all__ = [
    "MessageEnvelopeView",
    "MessageFanOutEmitter",
    "MessageReceiver",
    "MessageTransport",
    "ValidatedMessageTransport",
]
