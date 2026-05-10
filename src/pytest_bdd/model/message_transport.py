"""Provide message transport helpers."""

from __future__ import annotations

import json
import logging
from threading import Lock
from time import monotonic, sleep
from typing import TYPE_CHECKING, ClassVar, Protocol

from attrs import define, field, frozen

from pytest_bdd.model.stash_access import StashBound

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Stash
    from pytest_bdd.types.json import JSONObject

logger = logging.getLogger(__name__)

REPORTING_BATCH_EVENT = "pytest_bdd_message_chunk"
REPORTING_TRANSPORT_BINDING_STASH_KEY = "_pytest_bdd_xdist_transport_binding"


class ReportingEventSender(Protocol):
    """Represent reporting event sender state."""

    def __call__(self, name: str, **kwargs: object) -> None:
        """Send a reporting event with its associated payload."""
        ...


@frozen
class ReportingEventSenderBinding(StashBound):
    """Represent reporting event sender binding state."""

    STASH_KEY: ClassVar[str] = REPORTING_TRANSPORT_BINDING_STASH_KEY
    sender: ReportingEventSender
    gateway_mode: str | None = None


class _ConfigWithStash(Protocol):
    stash: Stash


def resolve_reporting_event_sender(config: _ConfigWithStash) -> ReportingEventSender | None:
    """
    Retrieve the configured reporting event sender from the pytest stash.

    Returns:
        The registered ReportingEventSender, or None if not found or not callable.

    """
    binding = ReportingEventSenderBinding.find_in_stash(config.stash)
    if binding is None:
        return None
    sender = binding.sender
    return sender if callable(sender) else None


def resolve_reporting_gateway_mode(config: _ConfigWithStash) -> str | None:
    """
    Retrieve the gateway mode from the configured reporting event sender binding.

    Returns:
        The gateway mode as a string, or None if not configured.

    """
    binding = ReportingEventSenderBinding.find_in_stash(config.stash)
    if binding is None:
        return None
    gateway_mode = binding.gateway_mode
    return gateway_mode if isinstance(gateway_mode, str) and gateway_mode else None


def _payload_int(payload: JSONObject, key: str, default: int | None = None) -> int:
    raw_value = payload.get(key, default)
    if isinstance(raw_value, (str, int, float)):
        return int(raw_value)
    if default is not None:
        return default
    msg = f"Expected integer-compatible transport field: {key}"
    raise TypeError(msg)


@frozen
class WorkerChunkBatch:
    """Represent worker chunk batch state."""

    worker_id: str
    batch_sequence: int
    envelopes: tuple[JSONObject, ...]
    is_terminal_batch: bool = False
    byte_count: int = 0
    gateway_mode: str | None = None

    def as_dict(self) -> JSONObject:
        """
        Convert the batch state into a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the worker chunk batch.

        """
        return {
            "worker_id": self.worker_id,
            "batch_sequence": self.batch_sequence,
            "envelopes": list(self.envelopes),
            "is_terminal_batch": self.is_terminal_batch,
            "byte_count": self.byte_count,
            "gateway_mode": self.gateway_mode,
        }

    @classmethod
    def from_dict(cls, payload: JSONObject) -> WorkerChunkBatch:
        """
        Instantiate a WorkerChunkBatch from a JSON-serializable dictionary payload.

        Returns:
            A new instance of WorkerChunkBatch initialized from the payload.

        """
        raw_envelopes = payload.get("envelopes", [])
        envelope_candidates = raw_envelopes if isinstance(raw_envelopes, list) else []
        envelopes = tuple(candidate for candidate in envelope_candidates if isinstance(candidate, dict))
        gateway_mode = payload.get("gateway_mode")
        return cls(
            worker_id=str(payload["worker_id"]),
            batch_sequence=_payload_int(payload, "batch_sequence"),
            envelopes=envelopes,
            is_terminal_batch=bool(payload.get("is_terminal_batch")),
            byte_count=_payload_int(payload, "byte_count", 0),
            gateway_mode=str(gateway_mode) if gateway_mode is not None else None,
        )


@frozen
class WorkerCompletionManifest:
    """Represent worker completion manifest state."""

    worker_id: str
    complete: bool
    last_batch_sequence: int | None
    transferred_batch_count: int
    transferred_envelope_count: int
    interruption_reason: str | None = None
    gateway_mode: str | None = None

    def as_dict(self) -> JSONObject:
        """
        Convert the completion manifest into a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the worker completion manifest.

        """
        return {
            "worker_id": self.worker_id,
            "complete": self.complete,
            "last_batch_sequence": self.last_batch_sequence,
            "transferred_batch_count": self.transferred_batch_count,
            "transferred_envelope_count": self.transferred_envelope_count,
            "interruption_reason": self.interruption_reason,
            "gateway_mode": self.gateway_mode,
        }

    @classmethod
    def from_dict(cls, payload: JSONObject) -> WorkerCompletionManifest:
        """
        Instantiate a WorkerCompletionManifest from a JSON-serializable dictionary payload.

        Returns:
            A new instance of WorkerCompletionManifest initialized from the payload.

        """
        interruption_reason = payload.get("interruption_reason")
        gateway_mode = payload.get("gateway_mode")
        return cls(
            worker_id=str(payload["worker_id"]),
            complete=bool(payload.get("complete")),
            last_batch_sequence=(
                _payload_int(payload, "last_batch_sequence") if payload.get("last_batch_sequence") is not None else None
            ),
            transferred_batch_count=_payload_int(payload, "transferred_batch_count", 0),
            transferred_envelope_count=_payload_int(payload, "transferred_envelope_count", 0),
            interruption_reason=str(interruption_reason) if interruption_reason is not None else None,
            gateway_mode=str(gateway_mode) if gateway_mode is not None else None,
        )


@define
class ReportingTransportSnapshot:
    """Represent reporting transport snapshot state."""

    expected_worker_ids: tuple[str, ...]
    batches_by_worker: dict[str, tuple[WorkerChunkBatch, ...]]
    manifests_by_worker: dict[str, WorkerCompletionManifest]


@define
class ReportingTransportSession:
    """Represent reporting transport session state."""

    _lock: Lock = field(init=False, factory=Lock, repr=False)
    _expected_worker_ids: set[str] = field(init=False, factory=set, repr=False)
    _batches_by_worker: dict[str, list[WorkerChunkBatch]] = field(init=False, factory=dict, repr=False)
    _manifests_by_worker: dict[str, WorkerCompletionManifest] = field(init=False, factory=dict, repr=False)

    def register_expected_worker(self, worker_id: str) -> None:
        """Register a worker identifier to track expected incoming batches."""
        with self._lock:
            self._expected_worker_ids.add(worker_id)

    def record_batch(self, batch: WorkerChunkBatch) -> None:
        """Store an incoming chunk batch for a specific worker."""
        with self._lock:
            self._batches_by_worker.setdefault(batch.worker_id, []).append(batch)

    def receive_remote_event(self, event_name: str, payload: JSONObject) -> None:
        """Process an incoming remote event, extracting and recording the batch payload if applicable."""
        if event_name != REPORTING_BATCH_EVENT:
            logger.warning("Ignoring unknown reporting event '%s'.", event_name)
            return
        batch_payload = payload.get("batch")
        if not isinstance(batch_payload, dict):
            logger.warning("Ignoring malformed reporting batch payload for event '%s'.", event_name)
            return
        self.record_batch(WorkerChunkBatch.from_dict(batch_payload))

    def record_manifest(self, manifest: WorkerCompletionManifest) -> None:
        """Store a completion manifest for a specific worker."""
        with self._lock:
            self._manifests_by_worker[manifest.worker_id] = manifest

    def batches_for_worker(self, worker_id: str) -> tuple[WorkerChunkBatch, ...]:
        """
        Retrieve all recorded batches for a specified worker, sorted by batch sequence.

        Returns:
            A tuple of sorted WorkerChunkBatch instances for the requested worker.

        """
        with self._lock:
            batches = tuple(self._batches_by_worker.get(worker_id, ()))
        return tuple(sorted(batches, key=lambda batch: batch.batch_sequence))

    def manifest_for_worker(self, worker_id: str) -> WorkerCompletionManifest | None:
        """
        Retrieve the completion manifest for a specified worker.

        Returns:
            The recorded WorkerCompletionManifest, or None if the worker has not completed.

        """
        with self._lock:
            return self._manifests_by_worker.get(worker_id)

    def snapshot(self) -> ReportingTransportSnapshot:
        """
        Generate a thread-safe snapshot of the current reporting transport session state.

        Returns:
            A ReportingTransportSnapshot representing the current expected workers, batches, and manifests.

        """
        with self._lock:
            return ReportingTransportSnapshot(
                expected_worker_ids=tuple(sorted(self._expected_worker_ids)),
                batches_by_worker={
                    worker_id: tuple(sorted(batches, key=lambda batch: batch.batch_sequence))
                    for worker_id, batches in self._batches_by_worker.items()
                },
                manifests_by_worker=dict(self._manifests_by_worker),
            )

    def wait_for_batches(
        self,
        worker_id: str,
        *,
        minimum_count: int = 1,
        timeout: float = 2.0,
    ) -> tuple[WorkerChunkBatch, ...]:
        """
        Wait for a specified number of batches to arrive from a worker within a timeout.

        Returns:
            A tuple of WorkerChunkBatch instances for the worker.

        """
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            batches = self.batches_for_worker(worker_id)
            if len(batches) >= minimum_count:
                return batches
            sleep(0.01)
        return self.batches_for_worker(worker_id)


@define
class ReportingTransportClient:
    """
    Represent reporting transport client state.

    Raises:
        ValueError: If the operation cannot be completed.
        RuntimeError: If the operation cannot be completed.

    """

    worker_id: str
    sender: ReportingEventSender
    gateway_mode: str | None = None
    batch_sequence: int = 0
    transferred_batch_count: int = 0
    transferred_envelope_count: int = 0
    last_publish_error: str | None = None

    def publish_envelopes(self, envelope_dicts: list[JSONObject]) -> WorkerChunkBatch:
        """
        Publish a batch of cucumber message envelopes via the configured sender.

        Returns:
            The generated WorkerChunkBatch representing the sent payload.

        Raises:
            ValueError: If the envelope list is empty.
            RuntimeError: If an error occurs during transmission.

        """
        if not envelope_dicts:
            msg = "Cannot publish an empty transport batch."
            raise ValueError(msg)
        batch = WorkerChunkBatch(
            worker_id=self.worker_id,
            batch_sequence=self.batch_sequence,
            envelopes=tuple(envelope_dicts),
            byte_count=len(json.dumps(envelope_dicts, separators=(",", ":"), sort_keys=True).encode("utf-8")),
            gateway_mode=self.gateway_mode,
        )
        try:
            self.sender(REPORTING_BATCH_EVENT, batch=batch.as_dict(), gateway_mode=self.gateway_mode)
        except Exception as exc:
            self.last_publish_error = str(exc)
            msg = f"Failed to publish worker transport batch for '{self.worker_id}'."
            raise RuntimeError(msg) from exc
        self.batch_sequence += 1
        self.transferred_batch_count += 1
        self.transferred_envelope_count += len(envelope_dicts)
        return batch

    def build_manifest(self, *, complete: bool, interruption_reason: str | None = None) -> WorkerCompletionManifest:
        """
        Construct a final manifest detailing the worker's transmission statistics and completion status.

        Returns:
            A WorkerCompletionManifest summarizing the worker's transport session.

        """
        resolved_reason = interruption_reason or self.last_publish_error
        resolved_complete = complete and resolved_reason is None
        last_batch_sequence = self.batch_sequence - 1 if self.transferred_batch_count else None
        return WorkerCompletionManifest(
            worker_id=self.worker_id,
            complete=resolved_complete,
            last_batch_sequence=last_batch_sequence,
            transferred_batch_count=self.transferred_batch_count,
            transferred_envelope_count=self.transferred_envelope_count,
            interruption_reason=resolved_reason,
            gateway_mode=self.gateway_mode,
        )
