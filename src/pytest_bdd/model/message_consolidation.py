from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

from .execution_message_adapter import ExecutionMessageAdapter
from .message_converter import envelope_from_dict
from .message_extension import (
    CONTROLLER_SINGULAR_PAYLOAD_KINDS,
    STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS,
)

ParticipantRole = Literal["controller", "worker"]

_STRUCTURAL_PHASE_ONE_KINDS = tuple(
    payload_kind for payload_kind in STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS if payload_kind != "test_case"
)
_POST_RUN_HOOK_NAMES = ("pytest-bdd-ng.after-test-run",)
_PRE_RUN_HOOK_NAMES = ("pytest-bdd-ng.before-test-run",)

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class ConsolidationDiagnostic:
    code: str
    severity: Literal["info", "warning", "error"]
    worker_id: str | None
    message: str
    affected_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MessageFragment:
    worker_id: str
    role: ParticipantRole
    path: Path | None = None
    complete: bool = True
    envelopes: tuple[dict[str, Any], ...] = ()
    manifest_received: bool = True
    transferred_batch_count: int = 0
    last_batch_sequence: int | None = None
    interruption_reason: str | None = None

    @classmethod
    def from_path(
        cls,
        *,
        worker_id: str,
        role: ParticipantRole,
        path: Path | None,
        complete: bool = True,
    ) -> MessageFragment:
        if path is None or not path.exists():
            return cls(worker_id=worker_id, role=role, path=path, complete=False, envelopes=())

        envelopes = tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        return cls(worker_id=worker_id, role=role, path=path, complete=complete, envelopes=envelopes)

    @classmethod
    def from_envelopes(
        cls,
        *,
        worker_id: str,
        role: ParticipantRole,
        envelopes: tuple[dict[str, Any], ...],
        complete: bool,
        manifest_received: bool,
        transferred_batch_count: int = 0,
        last_batch_sequence: int | None = None,
        interruption_reason: str | None = None,
    ) -> MessageFragment:
        return cls(
            worker_id=worker_id,
            role=role,
            path=None,
            complete=complete,
            envelopes=envelopes,
            manifest_received=manifest_received,
            transferred_batch_count=transferred_batch_count,
            last_batch_sequence=last_batch_sequence,
            interruption_reason=interruption_reason,
        )


@dataclass(slots=True)
class _EnvelopeRecord:
    envelope_dict: dict[str, Any]
    payload_kind: str
    worker_id: str
    role: ParticipantRole
    fragment_index: int
    sequence_in_fragment: int
    retain: bool = True
    discovery_index: int = 0


@dataclass(frozen=True, slots=True)
class ConsolidatedMessageStream:
    envelopes: tuple[Any, ...]
    envelope_dicts: tuple[dict[str, Any], ...]
    diagnostics: tuple[ConsolidationDiagnostic, ...]


def _participant_sort_key(fragment: MessageFragment) -> tuple[int, str]:
    return (0 if fragment.role == "controller" else 1, fragment.worker_id)


def _semantic_clone(value: Any, *, strip_reference_ids: bool) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key == "workerId":
                continue
            if key == "id":
                continue
            if strip_reference_ids and _is_reference_key(key):
                continue
            result[key] = _semantic_clone(item, strip_reference_ids=strip_reference_ids)
        return result
    if isinstance(value, list):
        return [_semantic_clone(item, strip_reference_ids=strip_reference_ids) for item in value]
    return value


def _payload_root(envelope_dict: dict[str, Any], payload_kind: str) -> dict[str, Any]:
    if payload_kind in envelope_dict and isinstance(envelope_dict[payload_kind], dict):
        return cast(dict[str, Any], envelope_dict[payload_kind])
    camel_case_payload_kind = payload_kind.split("_")[0] + "".join(part.title() for part in payload_kind.split("_")[1:])
    payload = envelope_dict.get(camel_case_payload_kind)
    return payload if isinstance(payload, dict) else {}


def _structural_identity(record: _EnvelopeRecord, *, strip_reference_ids: bool) -> str:
    payload = _payload_root(record.envelope_dict, record.payload_kind)
    return json.dumps(
        {
            "payload_kind": record.payload_kind,
            "payload": _semantic_clone(payload, strip_reference_ids=strip_reference_ids),
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _collect_ids_by_path(value: Any, path: tuple[Any, ...] = ()) -> dict[tuple[Any, ...], str]:
    collected: dict[tuple[Any, ...], str] = {}
    if isinstance(value, dict):
        raw_id = value.get("id")
        if isinstance(raw_id, str):
            collected[(*path, "id")] = raw_id
        for key, item in value.items():
            if key == "id":
                continue
            collected.update(_collect_ids_by_path(item, (*path, key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            collected.update(_collect_ids_by_path(item, (*path, index)))
    return collected


def _build_duplicate_id_map(canonical: _EnvelopeRecord, duplicate: _EnvelopeRecord) -> dict[str, str]:
    canonical_ids = _collect_ids_by_path(_payload_root(canonical.envelope_dict, canonical.payload_kind))
    duplicate_ids = _collect_ids_by_path(_payload_root(duplicate.envelope_dict, duplicate.payload_kind))
    return {
        duplicate_id: canonical_ids[path]
        for path, duplicate_id in duplicate_ids.items()
        if path in canonical_ids and duplicate_id != canonical_ids[path]
    }


def _is_reference_key(key: str) -> bool:
    if key == "workerId":
        return False
    return key.endswith(("Id", "Ids", "_id", "_ids"))


def _hook_name_from_identifier(identifier: Any) -> str | None:
    if not isinstance(identifier, str):
        return None
    for candidate in (*_PRE_RUN_HOOK_NAMES, *_POST_RUN_HOOK_NAMES):
        if identifier == candidate or identifier.endswith(f":{candidate}"):
            return candidate
    return None


def _resolve_hook_id_by_started_id(records: list[_EnvelopeRecord]) -> dict[str, str]:
    result: dict[str, str] = {}
    for record in records:
        if record.payload_kind != "test_run_hook_started":
            continue
        payload = _payload_root(record.envelope_dict, record.payload_kind)
        hook_started_id = payload.get("id")
        hook_id = payload.get("hookId")
        if isinstance(hook_started_id, str) and isinstance(hook_id, str):
            result[hook_started_id] = hook_id
    return result


def _record_sort_key(record: _EnvelopeRecord) -> tuple[int, int, int]:
    return (record.fragment_index, record.sequence_in_fragment, record.discovery_index)


def _categorize_execution_record(record: _EnvelopeRecord, hook_ids_by_started_id: dict[str, str]) -> int:
    if record.payload_kind == "test_run_hook_started":
        payload = _payload_root(record.envelope_dict, record.payload_kind)
        hook_name = _hook_name_from_identifier(payload.get("hookId"))
        if hook_name in _PRE_RUN_HOOK_NAMES:
            return 0
        if hook_name in _POST_RUN_HOOK_NAMES:
            return 2
    if record.payload_kind == "test_run_hook_finished":
        payload = _payload_root(record.envelope_dict, record.payload_kind)
        hook_identifier = hook_ids_by_started_id.get(str(payload.get("testRunHookStartedId")))
        hook_name = _hook_name_from_identifier(hook_identifier)
        if hook_name in _PRE_RUN_HOOK_NAMES:
            return 0
        if hook_name in _POST_RUN_HOOK_NAMES:
            return 2
    return 1


def _diagnostics_for_fragment(fragment: MessageFragment) -> list[ConsolidationDiagnostic]:
    diagnostics: list[ConsolidationDiagnostic] = []
    if fragment.role == "worker" and not fragment.manifest_received:
        diagnostics.append(
            ConsolidationDiagnostic(
                code="missing_worker_manifest",
                severity="warning",
                worker_id=fragment.worker_id,
                message=f"Worker manifest for '{fragment.worker_id}' was not received.",
            )
        )
    if not fragment.envelopes:
        if fragment.path is None:
            diagnostics.append(
                ConsolidationDiagnostic(
                    code="missing_worker_fragment",
                    severity="warning",
                    worker_id=fragment.worker_id,
                    message=f"Worker transport data for '{fragment.worker_id}' was not registered.",
                )
            )
        elif not fragment.path.exists():
            diagnostics.append(
                ConsolidationDiagnostic(
                    code="missing_worker_fragment",
                    severity="warning",
                    worker_id=fragment.worker_id,
                    message=f"Worker fragment '{fragment.path}' is missing for '{fragment.worker_id}'.",
                )
            )
    elif fragment.path is not None and not fragment.path.exists():
        diagnostics.append(
            ConsolidationDiagnostic(
                code="missing_worker_fragment",
                severity="warning",
                worker_id=fragment.worker_id,
                message=f"Worker fragment '{fragment.path}' is missing for '{fragment.worker_id}'.",
            )
        )
    if fragment.interruption_reason is not None:
        diagnostics.append(
            ConsolidationDiagnostic(
                code="interrupted_worker_transfer",
                severity="warning",
                worker_id=fragment.worker_id,
                message=f"Worker transfer for '{fragment.worker_id}' was interrupted: {fragment.interruption_reason}",
            )
        )
    if not fragment.complete:
        diagnostics.append(
            ConsolidationDiagnostic(
                code="partial_stream",
                severity="warning",
                worker_id=fragment.worker_id,
                message=f"Worker fragment for '{fragment.worker_id}' is incomplete.",
            )
        )
    return diagnostics


def consolidate_message_fragments(  # noqa: C901
    fragments: list[MessageFragment],
) -> ConsolidatedMessageStream:
    diagnostics = [diagnostic for fragment in fragments for diagnostic in _diagnostics_for_fragment(fragment)]
    sorted_fragments = sorted(fragments, key=_participant_sort_key)
    records: list[_EnvelopeRecord] = []

    for fragment_index, fragment in enumerate(sorted_fragments):
        for sequence_in_fragment, envelope_dict in enumerate(fragment.envelopes):
            namespaced = ExecutionMessageAdapter.namespace_dict_ids(envelope_dict, namespace=fragment.worker_id)
            projection = ExecutionMessageAdapter.deserialize_dict(namespaced)
            records.append(
                _EnvelopeRecord(
                    envelope_dict=namespaced,
                    payload_kind=projection.payload_kind,
                    worker_id=fragment.worker_id,
                    role=fragment.role,
                    fragment_index=fragment_index,
                    sequence_in_fragment=sequence_in_fragment,
                    discovery_index=len(records),
                )
            )

    id_remap: dict[str, str] = {}

    singular_records_by_kind: dict[str, _EnvelopeRecord] = {}
    for record in records:
        if record.payload_kind not in CONTROLLER_SINGULAR_PAYLOAD_KINDS:
            continue
        canonical = singular_records_by_kind.get(record.payload_kind)
        if canonical is None:
            singular_records_by_kind[record.payload_kind] = record
            continue
        record.retain = False
        id_remap.update(_build_duplicate_id_map(canonical, record))

    structural_phase_one_by_identity: dict[str, _EnvelopeRecord] = {}
    for record in records:
        if record.payload_kind not in _STRUCTURAL_PHASE_ONE_KINDS:
            continue
        identity = _structural_identity(record, strip_reference_ids=True)
        canonical = structural_phase_one_by_identity.get(identity)
        if canonical is None:
            structural_phase_one_by_identity[identity] = record
            continue
        record.retain = False
        id_remap.update(_build_duplicate_id_map(canonical, record))

    if id_remap:
        for record in records:
            record.envelope_dict = ExecutionMessageAdapter.rewrite_dict_ids(record.envelope_dict, id_remap)

    structural_phase_two_by_identity: dict[str, _EnvelopeRecord] = {}
    for record in records:
        if record.payload_kind != "test_case":
            continue
        identity = _structural_identity(record, strip_reference_ids=False)
        canonical = structural_phase_two_by_identity.get(identity)
        if canonical is None:
            structural_phase_two_by_identity[identity] = record
            continue
        record.retain = False
        id_remap.update(_build_duplicate_id_map(canonical, record))

    if id_remap:
        for record in records:
            record.envelope_dict = ExecutionMessageAdapter.rewrite_dict_ids(record.envelope_dict, id_remap)

    retained_records = [record for record in records if record.retain]
    retained_structural = sorted(
        (
            record
            for record in retained_records
            if record.payload_kind in STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS and record.payload_kind != "test_case"
        ),
        key=_record_sort_key,
    )
    retained_test_cases = sorted(
        (record for record in retained_records if record.payload_kind == "test_case"),
        key=_record_sort_key,
    )
    retained_execution = [
        record
        for record in retained_records
        if record.payload_kind not in CONTROLLER_SINGULAR_PAYLOAD_KINDS
        and record.payload_kind not in STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS
    ]
    hook_ids_by_started_id = _resolve_hook_id_by_started_id(retained_execution)
    retained_execution.sort(
        key=lambda record: (_categorize_execution_record(record, hook_ids_by_started_id), *_record_sort_key(record))
    )

    ordered_records: list[_EnvelopeRecord] = []
    if (meta := singular_records_by_kind.get("meta")) is not None:
        ordered_records.append(meta)
    ordered_records.extend(retained_structural)
    if (run_started := singular_records_by_kind.get("test_run_started")) is not None:
        ordered_records.append(run_started)
    ordered_records.extend(retained_test_cases)
    ordered_records.extend(retained_execution)
    if (run_finished := singular_records_by_kind.get("test_run_finished")) is not None:
        ordered_records.append(run_finished)

    ordered_envelope_dicts = tuple(record.envelope_dict for record in ordered_records)
    ordered_envelopes = tuple(envelope_from_dict(envelope_dict) for envelope_dict in ordered_envelope_dicts)
    return ConsolidatedMessageStream(
        envelopes=ordered_envelopes,
        envelope_dicts=ordered_envelope_dicts,
        diagnostics=tuple(diagnostics),
    )
