"""Provide test live formatter output relay helpers."""

from __future__ import annotations

import io
import os
import time
from threading import Lock, Thread

from pytest_bdd.plugin.gherkin_message_reporter.stream_relay import relay_live_formatter_output


class _RecordingTarget(io.StringIO):
    def __init__(self) -> None:
        super().__init__()
        self._lock = Lock()

    def write(self, value: str) -> int:
        with self._lock:
            return super().write(value)

    def flush(self) -> None:  # noqa: PLR6301 -- test class, pytest requires instance methods
        return None

    def value(self) -> str:
        with self._lock:
            return self.getvalue()


def _wait_for_value(target: _RecordingTarget, expected: str, *, timeout_seconds: float = 1.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if target.value() == expected:
            return
        time.sleep(0.01)
    assert target.value() == expected


def test_relay_live_formatter_output_streams_partial_writes_without_newlines() -> None:
    """Verify relay live formatter output streams partial writes without newlines."""
    read_fd, write_fd = os.pipe()
    target = _RecordingTarget()
    read_stream = os.fdopen(read_fd, "r", encoding="utf-8", newline="")
    relay_thread = Thread(
        target=relay_live_formatter_output,
        args=(read_stream, target),
        daemon=True,
    )
    relay_thread.start()

    with os.fdopen(write_fd, "wb", buffering=0) as write_stream:
        write_stream.write(b".")
        _wait_for_value(target, ".")
        write_stream.write(b"F\r")
        _wait_for_value(target, ".F\r")

    relay_thread.join(timeout=1)

    assert relay_thread.is_alive() is False
