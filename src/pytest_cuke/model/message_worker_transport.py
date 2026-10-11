"""JSON-safe worker batches and completion accounting for xdist reporting."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class MessageBatch:
    """One ordered batch carried inside a serialized pytest report."""

    worker_id: str
    sequence: int
    envelopes: tuple[dict[str, Any], ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "sequence": self.sequence,
            "envelopes": deepcopy(list(self.envelopes)),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> MessageBatch:
        worker_id = payload.get("worker_id")
        sequence = payload.get("sequence")
        envelopes = payload.get("envelopes")
        if not isinstance(worker_id, str) or not worker_id:
            raise ValueError("worker message batch must include a non-empty worker_id")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
            raise ValueError("worker message batch sequence must be a non-negative integer")
        if not isinstance(envelopes, list) or any(not isinstance(envelope, dict) for envelope in envelopes):
            raise ValueError("worker message batch envelopes must be a list of JSON objects")
        return cls(worker_id, sequence, tuple(deepcopy(envelopes)))


@dataclass(frozen=True, slots=True)
class WorkerCompletionManifest:
    """Completion accounting sent through xdist's workeroutput channel."""

    worker_id: str
    batch_count: int
    envelope_count: int
    complete: bool
    last_sequence: int | None
    interruption_reason: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "batch_count": self.batch_count,
            "envelope_count": self.envelope_count,
            "complete": self.complete,
            "last_sequence": self.last_sequence,
            "interruption_reason": self.interruption_reason,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> WorkerCompletionManifest:
        worker_id = payload.get("worker_id")
        batch_count = payload.get("batch_count")
        envelope_count = payload.get("envelope_count")
        complete = payload.get("complete")
        last_sequence = payload.get("last_sequence")
        interruption_reason = payload.get("interruption_reason")
        if not isinstance(worker_id, str) or not worker_id:
            raise ValueError("worker completion manifest must include a non-empty worker_id")
        if not isinstance(batch_count, int) or isinstance(batch_count, bool) or batch_count < 0:
            raise ValueError("worker completion manifest batch_count must be a non-negative integer")
        if not isinstance(envelope_count, int) or isinstance(envelope_count, bool) or envelope_count < 0:
            raise ValueError("worker completion manifest envelope_count must be a non-negative integer")
        if not isinstance(complete, bool):
            raise ValueError("worker completion manifest complete must be a boolean")
        if last_sequence is not None and (
            not isinstance(last_sequence, int) or isinstance(last_sequence, bool) or last_sequence < 0
        ):
            raise ValueError("worker completion manifest last_sequence must be null or a non-negative integer")
        if interruption_reason is not None and not isinstance(interruption_reason, str):
            raise ValueError("worker completion manifest interruption_reason must be a string or null")
        return cls(worker_id, batch_count, envelope_count, complete, last_sequence, interruption_reason)


class MessageBatcher:
    """Assign worker-local sequence numbers and create completion manifests."""

    def __init__(self, worker_id: str) -> None:
        if not worker_id:
            raise ValueError("worker_id must not be empty")
        self.worker_id = worker_id
        self.batch_count = 0
        self.envelope_count = 0

    def make_batch(self, envelopes: Sequence[dict[str, Any]]) -> MessageBatch:
        batch = MessageBatch(self.worker_id, self.batch_count, tuple(deepcopy(envelopes)))
        self.batch_count += 1
        self.envelope_count += len(envelopes)
        return batch

    def make_manifest(
        self,
        *,
        complete: bool,
        interruption_reason: str | None = None,
    ) -> WorkerCompletionManifest:
        return WorkerCompletionManifest(
            worker_id=self.worker_id,
            batch_count=self.batch_count,
            envelope_count=self.envelope_count,
            complete=complete,
            last_sequence=self.batch_count - 1 if self.batch_count else None,
            interruption_reason=interruption_reason,
        )


@dataclass(frozen=True, slots=True)
class WorkerMessageFragment:
    """Received worker data and its completion state."""

    worker_id: str
    envelopes: tuple[dict[str, Any], ...]
    complete: bool
    manifest_received: bool
    last_sequence: int | None


@dataclass(frozen=True, slots=True)
class WorkerTransportDiagnostic:
    """A partial-transfer diagnostic emitted by the controller receiver."""

    code: str
    message: str
    worker_id: str | None = None


@dataclass(frozen=True, slots=True)
class WorkerMessageResult:
    """All observed fragments and transfer diagnostics after controller finalization."""

    fragments: tuple[WorkerMessageFragment, ...]
    diagnostics: tuple[WorkerTransportDiagnostic, ...]


@dataclass(slots=True)
class _WorkerState:
    batches: dict[int, MessageBatch] = field(default_factory=dict)
    manifest: WorkerCompletionManifest | None = None
    error: str | None = None
    malformed: list[WorkerTransportDiagnostic] = field(default_factory=list)


class WorkerMessageReceiver:
    """Collect report batches and verify worker manifests without shared paths."""

    def __init__(self, *, expected_workers: Sequence[str] = ()) -> None:
        self.expected_workers = set(expected_workers)
        self._workers: dict[str, _WorkerState] = {}
        self._finalized = False

    def register_expected_worker(self, worker_id: str) -> None:
        self._ensure_open()
        if worker_id:
            self.expected_workers.add(worker_id)

    def receive_batch(self, payload: Mapping[str, Any]) -> bool:
        self._ensure_open()
        try:
            batch = MessageBatch.from_payload(payload)
        except ValueError as error:
            self._record_malformed(payload.get("worker_id"), str(error))
            return False
        state = self._workers.setdefault(batch.worker_id, _WorkerState())
        previous = state.batches.get(batch.sequence)
        if previous is not None:
            state.malformed.append(
                WorkerTransportDiagnostic(
                    code="duplicate_worker_batch",
                    message=f"Worker '{batch.worker_id}' sent batch sequence {batch.sequence} more than once.",
                    worker_id=batch.worker_id,
                )
            )
            return False
        state.batches[batch.sequence] = batch
        return True

    def record_manifest(
        self,
        payload: Mapping[str, Any],
        *,
        expected_worker_id: str | None = None,
    ) -> None:
        self._ensure_open()
        try:
            manifest = WorkerCompletionManifest.from_payload(payload)
        except ValueError as error:
            self._record_malformed(expected_worker_id or payload.get("worker_id"), str(error))
            return
        worker_id = expected_worker_id or manifest.worker_id
        state = self._workers.setdefault(worker_id, _WorkerState())
        if manifest.worker_id != worker_id:
            state.malformed.append(
                WorkerTransportDiagnostic(
                    code="worker_manifest_mismatch",
                    message=(
                        f"Worker '{worker_id}' sent a manifest for '{manifest.worker_id}'."
                    ),
                    worker_id=worker_id,
                )
            )
            return
        if state.manifest is not None:
            state.malformed.append(
                WorkerTransportDiagnostic(
                    code="duplicate_worker_manifest",
                    message=f"Worker '{worker_id}' sent more than one completion manifest.",
                    worker_id=worker_id,
                )
            )
            return
        state.manifest = manifest

    def mark_worker_down(self, worker_id: str, error: object | None) -> None:
        self._ensure_open()
        if error is None:
            return
        state = self._workers.setdefault(worker_id, _WorkerState())
        state.error = str(error)[:500]

    def finalize(self) -> WorkerMessageResult:
        self._ensure_open()
        self._finalized = True
        diagnostics: list[WorkerTransportDiagnostic] = []
        fragments: list[WorkerMessageFragment] = []
        worker_ids = sorted(self.expected_workers | self._workers.keys())
        for worker_id in worker_ids:
            state = self._workers.get(worker_id, _WorkerState())
            worker_diagnostics = list(state.malformed)
            ordered_sequences = sorted(state.batches)
            envelopes = tuple(
                envelope
                for sequence in ordered_sequences
                for envelope in state.batches[sequence].envelopes
            )
            manifest = state.manifest
            if manifest is None:
                worker_diagnostics.append(
                    WorkerTransportDiagnostic(
                        code="missing_worker_manifest",
                        message=f"Worker '{worker_id}' did not publish a completion manifest.",
                        worker_id=worker_id,
                    )
                )
            empty_complete_manifest = (
                manifest is not None
                and manifest.complete
                and manifest.batch_count == 0
                and manifest.envelope_count == 0
                and manifest.last_sequence is None
            )
            if not state.batches and not empty_complete_manifest:
                worker_diagnostics.append(
                    WorkerTransportDiagnostic(
                        code="missing_worker_fragment",
                        message=f"No message batches were received from worker '{worker_id}'.",
                        worker_id=worker_id,
                    )
                )
            if state.error is not None:
                worker_diagnostics.append(
                    WorkerTransportDiagnostic(
                        code="interrupted_worker_transfer",
                        message=f"Worker '{worker_id}' stopped before transfer completed: {state.error}",
                        worker_id=worker_id,
                    )
                )
            if manifest is not None:
                expected_sequences = list(range(manifest.batch_count))
                observed_count = len(ordered_sequences)
                observed_envelope_count = sum(len(batch.envelopes) for batch in state.batches.values())
                if ordered_sequences != expected_sequences:
                    worker_diagnostics.append(
                        WorkerTransportDiagnostic(
                            code="interrupted_worker_transfer",
                            message=(
                                f"Worker '{worker_id}' batch sequence is incomplete: "
                                f"expected {expected_sequences}, received {ordered_sequences}."
                            ),
                            worker_id=worker_id,
                        )
                    )
                if observed_count != manifest.batch_count or observed_envelope_count != manifest.envelope_count:
                    worker_diagnostics.append(
                        WorkerTransportDiagnostic(
                            code="interrupted_worker_transfer",
                            message=(
                                f"Worker '{worker_id}' manifest counts do not match received batches "
                                f"({observed_count}/{observed_envelope_count} received, "
                                f"{manifest.batch_count}/{manifest.envelope_count} declared)."
                            ),
                            worker_id=worker_id,
                        )
                    )
                expected_last = manifest.batch_count - 1 if manifest.batch_count else None
                if manifest.last_sequence != expected_last:
                    worker_diagnostics.append(
                        WorkerTransportDiagnostic(
                            code="worker_manifest_mismatch",
                            message=f"Worker '{worker_id}' manifest has inconsistent last_sequence.",
                            worker_id=worker_id,
                        )
                    )
                if not manifest.complete:
                    reason = manifest.interruption_reason or "worker reported an incomplete stream"
                    worker_diagnostics.append(
                        WorkerTransportDiagnostic(
                            code="interrupted_worker_transfer",
                            message=f"Worker '{worker_id}' reported partial transfer: {reason}",
                            worker_id=worker_id,
                        )
                    )
            if worker_diagnostics:
                worker_diagnostics.append(
                    WorkerTransportDiagnostic(
                        code="partial_stream",
                        message=f"Cucumber Messages stream is partial because worker '{worker_id}' is incomplete.",
                        worker_id=worker_id,
                    )
                )
            diagnostics.extend(worker_diagnostics)
            fragments.append(
                WorkerMessageFragment(
                    worker_id=worker_id,
                    envelopes=envelopes,
                    complete=not worker_diagnostics,
                    manifest_received=manifest is not None,
                    last_sequence=ordered_sequences[-1] if ordered_sequences else None,
                )
            )
        return WorkerMessageResult(tuple(fragments), tuple(diagnostics))

    def _record_malformed(self, worker_id: object, message: str) -> None:
        safe_worker_id = worker_id if isinstance(worker_id, str) else "unknown"
        self._workers.setdefault(safe_worker_id, _WorkerState()).malformed.append(
            WorkerTransportDiagnostic(
                code="interrupted_worker_transfer",
                message=f"Malformed worker message data for '{safe_worker_id}': {message}",
                worker_id=safe_worker_id,
            )
        )

    def _ensure_open(self) -> None:
        if self._finalized:
            raise RuntimeError("worker message receiver has already been finalized")
