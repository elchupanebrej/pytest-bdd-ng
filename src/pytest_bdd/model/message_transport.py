from __future__ import annotations

import json
import logging
from threading import Lock
from time import monotonic, sleep
from typing import TYPE_CHECKING, Any, ClassVar

from attrs import define, field, frozen

from pytest_bdd.model.stash_access import StashBound

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

REPORTING_BATCH_EVENT = "pytest_bdd_message_chunk"
REPORTING_TRANSPORT_BINDING_STASH_KEY = "_pytest_bdd_xdist_transport_binding"


@frozen
class ReportingEventSenderBinding(StashBound):
    STASH_KEY: ClassVar[str] = REPORTING_TRANSPORT_BINDING_STASH_KEY
    sender: Callable[..., None]
    gateway_mode: str | None = None


def _config_stash(config: Any) -> Any:
    stash = getattr(config, "stash", None)
    if stash is None:
        stash = {}
        config.stash = stash
    return stash


def install_reporting_event_sender(
    config: Any,
    sender: Callable[..., None],
    *,
    gateway_mode: str | None = None,
) -> None:
    ReportingEventSenderBinding(
        sender=sender,
        gateway_mode=gateway_mode,
    ).set_in_stash(_config_stash(config))


def resolve_reporting_event_sender(config: Any) -> Callable[..., None] | None:
    binding = ReportingEventSenderBinding.find_in_stash(_config_stash(config))
    if binding is None:
        return None
    sender = binding.sender
    return sender if callable(sender) else None


def resolve_reporting_gateway_mode(config: Any) -> str | None:
    binding = ReportingEventSenderBinding.find_in_stash(_config_stash(config))
    if binding is None:
        return None
    gateway_mode = binding.gateway_mode
    return gateway_mode if isinstance(gateway_mode, str) and gateway_mode else None


@frozen
class WorkerChunkBatch:
    worker_id: str
    batch_sequence: int
    envelopes: tuple[dict[str, Any], ...]
    is_terminal_batch: bool = False
    byte_count: int = 0
    gateway_mode: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "batch_sequence": self.batch_sequence,
            "envelopes": list(self.envelopes),
            "is_terminal_batch": self.is_terminal_batch,
            "byte_count": self.byte_count,
            "gateway_mode": self.gateway_mode,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> WorkerChunkBatch:
        raw_envelopes = payload.get("envelopes", ())
        envelopes = tuple(candidate for candidate in raw_envelopes if isinstance(candidate, dict))
        gateway_mode = payload.get("gateway_mode")
        return cls(
            worker_id=str(payload["worker_id"]),
            batch_sequence=int(payload["batch_sequence"]),
            envelopes=envelopes,
            is_terminal_batch=bool(payload.get("is_terminal_batch")),
            byte_count=int(payload.get("byte_count", 0)),
            gateway_mode=str(gateway_mode) if gateway_mode is not None else None,
        )


@frozen
class WorkerCompletionManifest:
    worker_id: str
    complete: bool
    last_batch_sequence: int | None
    transferred_batch_count: int
    transferred_envelope_count: int
    interruption_reason: str | None = None
    gateway_mode: str | None = None

    def as_dict(self) -> dict[str, Any]:
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
    def from_dict(cls, payload: dict[str, Any]) -> WorkerCompletionManifest:
        interruption_reason = payload.get("interruption_reason")
        gateway_mode = payload.get("gateway_mode")
        return cls(
            worker_id=str(payload["worker_id"]),
            complete=bool(payload.get("complete")),
            last_batch_sequence=(
                int(payload["last_batch_sequence"]) if payload.get("last_batch_sequence") is not None else None
            ),
            transferred_batch_count=int(payload.get("transferred_batch_count", 0)),
            transferred_envelope_count=int(payload.get("transferred_envelope_count", 0)),
            interruption_reason=str(interruption_reason) if interruption_reason is not None else None,
            gateway_mode=str(gateway_mode) if gateway_mode is not None else None,
        )


@define
class ReportingTransportSnapshot:
    expected_worker_ids: tuple[str, ...]
    batches_by_worker: dict[str, tuple[WorkerChunkBatch, ...]]
    manifests_by_worker: dict[str, WorkerCompletionManifest]


@define
class ReportingTransportSession:
    _lock: Lock = field(init=False, factory=Lock, repr=False)
    _expected_worker_ids: set[str] = field(init=False, factory=set, repr=False)
    _batches_by_worker: dict[str, list[WorkerChunkBatch]] = field(init=False, factory=dict, repr=False)
    _manifests_by_worker: dict[str, WorkerCompletionManifest] = field(init=False, factory=dict, repr=False)

    def register_expected_worker(self, worker_id: str) -> None:
        with self._lock:
            self._expected_worker_ids.add(worker_id)

    def record_batch(self, batch: WorkerChunkBatch) -> None:
        with self._lock:
            self._batches_by_worker.setdefault(batch.worker_id, []).append(batch)

    def receive_remote_event(self, event_name: str, payload: dict[str, Any]) -> None:
        if event_name != REPORTING_BATCH_EVENT:
            logger.warning("Ignoring unknown reporting event '%s'.", event_name)
            return
        batch_payload = payload.get("batch")
        if not isinstance(batch_payload, dict):
            logger.warning("Ignoring malformed reporting batch payload for event '%s'.", event_name)
            return
        self.record_batch(WorkerChunkBatch.from_dict(batch_payload))

    def record_manifest(self, manifest: WorkerCompletionManifest) -> None:
        with self._lock:
            self._manifests_by_worker[manifest.worker_id] = manifest

    def batches_for_worker(self, worker_id: str) -> tuple[WorkerChunkBatch, ...]:
        with self._lock:
            batches = tuple(self._batches_by_worker.get(worker_id, ()))
        return tuple(sorted(batches, key=lambda batch: batch.batch_sequence))

    def manifest_for_worker(self, worker_id: str) -> WorkerCompletionManifest | None:
        with self._lock:
            return self._manifests_by_worker.get(worker_id)

    def snapshot(self) -> ReportingTransportSnapshot:
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
        self, worker_id: str, *, minimum_count: int = 1, timeout: float = 2.0
    ) -> tuple[WorkerChunkBatch, ...]:
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            batches = self.batches_for_worker(worker_id)
            if len(batches) >= minimum_count:
                return batches
            sleep(0.01)
        return self.batches_for_worker(worker_id)


@define
class ReportingTransportClient:
    worker_id: str
    sender: Callable[..., None]
    gateway_mode: str | None = None
    batch_sequence: int = 0
    transferred_batch_count: int = 0
    transferred_envelope_count: int = 0
    last_publish_error: str | None = None

    def publish_envelopes(self, envelope_dicts: list[dict[str, Any]]) -> WorkerChunkBatch:
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
