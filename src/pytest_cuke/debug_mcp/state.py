from __future__ import annotations

import copy
import time
from threading import TIMEOUT_MAX, Condition
from typing import TYPE_CHECKING, Any, Literal, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

_WriteResult = TypeVar("_WriteResult")

ReleaseReason = Literal["explicit", "timeout", "lease_expired", "debugger_continuation", "shutdown"]
_RELEASE_REASONS = {"explicit", "timeout", "lease_expired", "debugger_continuation", "shutdown"}


class FailureHoldError(RuntimeError):
    """A client attempted to inspect, heartbeat or release an unavailable failure."""


class FailureQueue:
    """Own one active failure hold and its monotonic timeout and heartbeat lease."""

    def __init__(
        self,
        *,
        session_id: str,
        timeout_seconds: float,
        lease_seconds: float,
        on_change: Callable[[dict[str, Any]], None] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.session_id = session_id
        self.timeout_seconds = timeout_seconds
        self.lease_seconds = lease_seconds
        self._on_change = on_change
        self._clock = clock
        self._condition = Condition()
        self._active_failure: dict[str, Any] | None = None
        self._last_release: dict[str, Any] | None = None
        self._active_started_at: float | None = None
        self._last_heartbeat_at: float | None = None
        self._connected = False
        self._closed = False
        self._sequence = 0
        self._artifact_written_sequences: set[int] = set()
        self._status = "waiting"

    def hold_failure(
        self,
        *,
        nodeid: str,
        phase: str,
        error_type: str,
        error_message: str,
        bdd_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Publish a failed report, block its pytest hook, then return its release record."""
        with self._condition:
            if self._closed:
                raise FailureHoldError("Debug MCP session is closed")
            if self._active_failure is not None:
                raise FailureHoldError("another Debug MCP failure is already active")
            self._sequence += 1
            sequence = self._sequence
            self._active_failure = {
                "sequence": sequence,
                "nodeid": nodeid,
                "phase": phase,
                "error_type": error_type,
                "error_message": error_message,
                "bdd_context": copy.deepcopy(bdd_context),
            }
            self._status = "holding_failure"
            self._last_release = None
            self._last_heartbeat_at = None
            self._connected = False
            started_at = self._clock()
            self._active_started_at = started_at
            hold_deadline = started_at + self.timeout_seconds
            self._publish_locked()

            while self._active_failure is not None and self._active_failure["sequence"] == sequence:
                if self._closed:
                    self._release_locked("shutdown")
                    break
                if self._expire_active_locked():
                    break
                now = self._clock()
                wait_seconds = hold_deadline - now
                if self._connected and self._last_heartbeat_at is not None:
                    remaining_lease = self.lease_seconds - (now - self._last_heartbeat_at)
                    wait_seconds = min(wait_seconds, remaining_lease)
                self._condition.wait(timeout=min(TIMEOUT_MAX, max(0.001, wait_seconds)))

            if self._last_release is None or self._last_release["sequence"] != sequence:
                raise FailureHoldError("the active Debug MCP failure was released without a record")
            return copy.deepcopy(self._last_release)

    def inspect_failure(self) -> dict[str, Any]:
        with self._condition:
            self._expire_active_locked()
            return {
                "session_id": self.session_id,
                "status": self._status,
                "active_failure": copy.deepcopy(self._active_failure),
            }

    def heartbeat(self, *, session_id: str, sequence: int) -> dict[str, Any]:
        with self._condition:
            self._expire_active_locked()
            self._require_active_locked(session_id=session_id, sequence=sequence)
            self._connected = True
            self._last_heartbeat_at = self._clock()
            self._condition.notify_all()
            return {
                "session_id": self.session_id,
                "sequence": sequence,
                "lease_seconds": self.lease_seconds,
            }

    def release_failure(
        self,
        *,
        session_id: str,
        sequence: int,
        reason: ReleaseReason = "explicit",
    ) -> dict[str, Any]:
        if reason not in _RELEASE_REASONS - {"timeout", "lease_expired", "shutdown"}:
            raise FailureHoldError(f"unsupported Debug MCP release reason: {reason!r}")
        with self._condition:
            self._expire_active_locked()
            self._require_active_locked(session_id=session_id, sequence=sequence)
            record = self._release_locked(reason)
            return {"released": True, "status": self._status, **copy.deepcopy(record)}

    def mark_artifact_written(self, *, session_id: str, sequence: int) -> None:
        """Retain artifact status if another pytest-cuke component wrote one for this hold."""
        with self._condition:
            self._expire_active_locked()
            self._require_active_locked(session_id=session_id, sequence=sequence)
            self._artifact_written_sequences.add(sequence)

    def write_artifact(
        self,
        *,
        session_id: str,
        sequence: int,
        writer: Callable[[dict[str, Any]], _WriteResult],
    ) -> _WriteResult:
        """Write under the active hold lock and mark success only after the writer returns."""
        with self._condition:
            self._expire_active_locked()
            failure = self._require_active_locked(session_id=session_id, sequence=sequence)
            if sequence in self._artifact_written_sequences:
                raise FailureHoldError("an investigation artifact was already written for this failure")
            result = writer(copy.deepcopy(failure))
            self._artifact_written_sequences.add(sequence)
            self._condition.notify_all()
            return result

    @property
    def last_release(self) -> dict[str, Any] | None:
        with self._condition:
            return copy.deepcopy(self._last_release)

    def set_change_callback(self, callback: Callable[[dict[str, Any]], None] | None) -> None:
        """Attach the discovery writer once endpoint startup has completed."""
        with self._condition:
            self._on_change = callback

    def close(self) -> None:
        with self._condition:
            if self._closed:
                return
            self._closed = True
            if self._active_failure is not None:
                self._release_locked("shutdown")
            self._status = "closed"
            self._publish_locked()
            self._condition.notify_all()

    def _require_active_locked(self, *, session_id: str, sequence: int) -> dict[str, Any]:
        active = self._active_failure
        if (
            active is None
            or session_id != self.session_id
            or isinstance(sequence, bool)
            or sequence != active["sequence"]
            or self._closed
        ):
            raise FailureHoldError("there is no active failure matching this Debug MCP session and sequence")
        return active

    def _expire_active_locked(self) -> bool:
        active = self._active_failure
        started_at = self._active_started_at
        if active is None or started_at is None or self._closed:
            return False
        now = self._clock()
        if now >= started_at + self.timeout_seconds:
            self._release_locked("timeout")
            return True
        if (
            self._connected
            and self._last_heartbeat_at is not None
            and now >= self._last_heartbeat_at + self.lease_seconds
        ):
            self._release_locked("lease_expired")
            return True
        return False

    def _release_locked(self, reason: ReleaseReason) -> dict[str, Any]:
        active = self._active_failure
        if active is None:
            raise FailureHoldError("there is no active Debug MCP failure to release")
        sequence = active["sequence"]
        record = {
            "session_id": self.session_id,
            "sequence": sequence,
            "reason": reason,
            "artifact_status": "written" if sequence in self._artifact_written_sequences else "missing",
        }
        self._last_release = record
        self._active_failure = None
        self._active_started_at = None
        self._connected = False
        self._last_heartbeat_at = None
        self._status = "closed" if self._closed else "waiting"
        self._publish_locked()
        self._condition.notify_all()
        return record

    def _publish_locked(self) -> None:
        if self._on_change is not None:
            self._on_change(
                {
                    "session_id": self.session_id,
                    "status": self._status,
                    "active_failure": copy.deepcopy(self._active_failure),
                    "last_release": copy.deepcopy(self._last_release),
                }
            )
