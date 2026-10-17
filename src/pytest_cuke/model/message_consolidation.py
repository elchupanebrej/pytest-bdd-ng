"""Pure helpers for merging distributed Cucumber Messages streams."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

from pytest_cuke.model.message_extension import (
    CONTROLLER_SINGULAR_PAYLOAD_KINDS,
    IDE_DIAGNOSTIC_MEDIA_TYPE,
    IDE_LAUNCH_MEDIA_TYPE,
    IDE_STEP_BINDING_MEDIA_TYPE,
    STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS,
)
from pytest_cuke.model.message_types import Envelope, message_from_dict

_IDE_JSON_ATTACHMENT_MEDIA_TYPES = frozenset(
    {IDE_DIAGNOSTIC_MEDIA_TYPE, IDE_LAUNCH_MEDIA_TYPE, IDE_STEP_BINDING_MEDIA_TYPE}
)
_XDIST_EXECNET_STAGING_PATH = re.compile(
    r"(?:pytest-cuke-execnet-remote-\d+-[^/\\]+|_remote-\d+-[^/\\]+)/pyexecnetcache/",
    re.IGNORECASE,
)


def _is_identifier_key(key: str) -> bool:
    return key == "id" or key.endswith(("Id", "Ids", "_id", "_ids"))


def _namespace_identifier(value: Any, worker_id: str) -> Any:
    if isinstance(value, str):
        return f"{worker_id}:{value}"
    if isinstance(value, list):
        return [_namespace_identifier(item, worker_id) for item in value]
    return value


def _namespace_nested(value: Any, worker_id: str, *, use_payload_worker_ids: bool = False) -> Any:
    if isinstance(value, Mapping):
        if use_payload_worker_ids and isinstance(value.get("workerId"), str) and value["workerId"]:
            worker_id = value["workerId"]
        namespaced: dict[str, Any] = {}
        media_type = value.get("mediaType")
        for key, item in value.items():
            if key == "workerId":
                namespaced[key] = item
            elif key == "body" and media_type in _IDE_JSON_ATTACHMENT_MEDIA_TYPES and isinstance(item, str):
                try:
                    attachment_payload = json.loads(item)
                except json.JSONDecodeError:
                    namespaced[key] = item
                else:
                    namespaced[key] = json.dumps(
                        _namespace_nested(attachment_payload, worker_id, use_payload_worker_ids=True),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
            elif _is_identifier_key(key):
                namespaced[key] = _namespace_identifier(item, worker_id)
            else:
                namespaced[key] = _namespace_nested(
                    item,
                    worker_id,
                    use_payload_worker_ids=use_payload_worker_ids,
                )
        return namespaced
    if isinstance(value, list):
        return [
            _namespace_nested(item, worker_id, use_payload_worker_ids=use_payload_worker_ids)
            for item in value
        ]
    return value


def namespace_envelope_ids(envelope: Mapping[str, Any], *, worker_id: str) -> dict[str, Any]:
    """Namespace every message identifier and reference while retaining worker identity."""
    return cast("dict[str, Any]", _namespace_nested(envelope, worker_id))


ParticipantRole = Literal["controller", "worker"]


@dataclass(frozen=True, slots=True)
class MessageFragment:
    """An ordered Messages fragment emitted by one controller or worker."""

    worker_id: str
    role: ParticipantRole
    envelopes: tuple[dict[str, Any], ...]


@dataclass(frozen=True, slots=True)
class MessageConsolidationDiagnostic:
    """A stable diagnostic produced while merging worker fragments."""

    code: str
    message: str
    worker_id: str | None = None
    offending_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConsolidatedMessageStream:
    """The deterministic envelope stream and diagnostics produced by consolidation."""

    envelopes: tuple[Envelope, ...]
    envelope_dicts: tuple[dict[str, Any], ...]
    diagnostics: tuple[MessageConsolidationDiagnostic, ...] = ()


@dataclass(slots=True)
class _EnvelopeRecord:
    envelope: dict[str, Any]
    payload_kind: str
    worker_id: str
    fragment_index: int
    sequence_in_fragment: int
    retain: bool = True


def _snake_case(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def _payload_kind(envelope: Mapping[str, Any]) -> str:
    payloads = [(key, value) for key, value in envelope.items() if isinstance(value, dict)]
    if len(payloads) != 1:
        raise ValueError("a Messages envelope must contain exactly one payload")
    return _snake_case(payloads[0][0])


def _payload(envelope: Mapping[str, Any], payload_kind: str) -> dict[str, Any]:
    key = payload_kind.split("_", maxsplit=1)[0] + "".join(part.title() for part in payload_kind.split("_")[1:])
    value = envelope.get(key)
    return value if isinstance(value, dict) else {}


def _is_reference_key(key: str) -> bool:
    return key != "workerId" and key.endswith(("Id", "Ids", "_id", "_ids"))


def _semantic_clone(value: Any, *, strip_reference_ids: bool) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, nested in value.items():
            if key in {"workerId", "id"}:
                continue
            if strip_reference_ids and _is_reference_key(key):
                continue
            result[key] = _semantic_clone(nested, strip_reference_ids=strip_reference_ids)
        return result
    if isinstance(value, list):
        return [_semantic_clone(item, strip_reference_ids=strip_reference_ids) for item in value]
    return value


def _structural_identity(record: _EnvelopeRecord, *, strip_reference_ids: bool) -> str:
    return json.dumps(
        {
            "kind": record.payload_kind,
            "payload": _semantic_clone(
                _payload(record.envelope, record.payload_kind),
                strip_reference_ids=strip_reference_ids,
            ),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _source_identity_without_uri(record: _EnvelopeRecord) -> str:
    source = {key: value for key, value in _payload(record.envelope, "source").items() if key != "uri"}
    return json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _execnet_rsync_relative_uri(uri: str) -> str | None:
    normalized = uri.replace("\\", "/")
    match = _XDIST_EXECNET_STAGING_PATH.search(normalized)
    return normalized[match.end() :] if match is not None else None


def _canonicalize_execnet_staged_uris(records: Sequence[_EnvelopeRecord]) -> None:
    """Map xdist's staged feature paths back to a unique controller source URI."""
    sources = [record for record in records if record.payload_kind == "source"]
    local_uris_by_content: dict[str, set[str]] = {}
    for record in sources:
        payload = _payload(record.envelope, "source")
        uri = payload.get("uri")
        if not isinstance(uri, str) or _execnet_rsync_relative_uri(uri) is not None:
            continue
        local_uris_by_content.setdefault(_source_identity_without_uri(record), set()).add(uri)

    remap_candidates: dict[str, set[str]] = {}
    for record in sources:
        payload = _payload(record.envelope, "source")
        uri = payload.get("uri")
        if not isinstance(uri, str):
            continue
        relative_uri = _execnet_rsync_relative_uri(uri)
        if relative_uri is None:
            continue
        matching_uris = {
            candidate
            for candidate in local_uris_by_content.get(_source_identity_without_uri(record), set())
            if candidate.replace("\\", "/").endswith(f"/{relative_uri}")
        }
        if len(matching_uris) == 1:
            remap_candidates.setdefault(uri, set()).update(matching_uris)

    uri_remap = {
        staged_uri: next(iter(candidates))
        for staged_uri, candidates in remap_candidates.items()
        if len(candidates) == 1
    }
    if not uri_remap:
        return

    for record in records:
        payload = _payload(record.envelope, record.payload_kind)
        uri = payload.get("uri")
        if isinstance(uri, str) and uri in uri_remap:
            payload["uri"] = uri_remap[uri]


def _pickle_order_identity(record: _EnvelopeRecord) -> str:
    """Normalize one worker's namespace while retaining pickle AST references."""
    def normalize_worker_references(value: Any, *, is_reference: bool = False) -> Any:
        if isinstance(value, Mapping):
            return {
                key: normalize_worker_references(nested, is_reference=_is_reference_key(key))
                for key, nested in value.items()
            }
        if isinstance(value, list):
            return [normalize_worker_references(item, is_reference=is_reference) for item in value]
        if is_reference and isinstance(value, str):
            return value.removeprefix(f"{record.worker_id}:")
        return value

    payload = _semantic_clone(_payload(record.envelope, record.payload_kind), strip_reference_ids=False)
    return json.dumps(
        normalize_worker_references(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _collect_object_ids(value: Any, path: tuple[str | int, ...] = ()) -> dict[tuple[str | int, ...], str]:
    collected: dict[tuple[str | int, ...], str] = {}
    if isinstance(value, Mapping):
        identifier = value.get("id")
        if isinstance(identifier, str):
            collected[(*path, "id")] = identifier
        for key, nested in value.items():
            if key != "id":
                collected.update(_collect_object_ids(nested, (*path, key)))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            collected.update(_collect_object_ids(nested, (*path, index)))
    return collected


def _duplicate_object_id_map(canonical: _EnvelopeRecord, duplicate: _EnvelopeRecord) -> dict[str, str]:
    canonical_ids = _collect_object_ids(_payload(canonical.envelope, canonical.payload_kind))
    duplicate_ids = _collect_object_ids(_payload(duplicate.envelope, duplicate.payload_kind))
    return {
        duplicate_id: canonical_ids[path]
        for path, duplicate_id in duplicate_ids.items()
        if path in canonical_ids and duplicate_id != canonical_ids[path]
    }


def _rewrite_references(value: Any, id_remap: Mapping[str, str]) -> Any:
    if isinstance(value, Mapping):
        rewritten: dict[str, Any] = {}
        media_type = value.get("mediaType")
        for key, nested in value.items():
            if key == "workerId":
                rewritten[key] = nested
            elif key == "body" and media_type in _IDE_JSON_ATTACHMENT_MEDIA_TYPES and isinstance(nested, str):
                try:
                    attachment_payload = json.loads(nested)
                except json.JSONDecodeError:
                    rewritten[key] = nested
                else:
                    rewritten[key] = json.dumps(
                        _rewrite_references(attachment_payload, id_remap),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
            elif key == "id" or _is_reference_key(key):
                rewritten[key] = _rewrite_reference_value(nested, id_remap)
            else:
                rewritten[key] = _rewrite_references(nested, id_remap)
        return rewritten
    if isinstance(value, list):
        return [_rewrite_references(item, id_remap) for item in value]
    return value


def _rewrite_reference_value(value: Any, id_remap: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        return id_remap.get(value, value)
    if isinstance(value, list):
        return [_rewrite_reference_value(item, id_remap) for item in value]
    return value


def _record_sort_key(record: _EnvelopeRecord) -> tuple[int, int]:
    return record.fragment_index, record.sequence_in_fragment


def _scenario_rank_sort_key(rank: int | None) -> tuple[int, int]:
    """Keep known cases in collection order and opaque records in stable fallback order."""
    return (0, rank) if rank is not None else (1, 0)


def _json_attachment_references(record: _EnvelopeRecord) -> tuple[str | None, str | None]:
    """Return case and pickle IDs from a pytest-cuke JSON attachment body."""
    attachment = _payload(record.envelope, record.payload_kind)
    body = attachment.get("body")
    if attachment.get("mediaType") in _IDE_JSON_ATTACHMENT_MEDIA_TYPES and isinstance(body, str):
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, Mapping):
            case_id = payload.get("testCaseId")
            pickle_id = payload.get("pickleId")
            return (
                case_id if isinstance(case_id, str) else None,
                pickle_id if isinstance(pickle_id, str) else None,
            )
    return None, None


def _json_attachment_scenario_rank(
    record: _EnvelopeRecord,
    case_ranks: Mapping[str, int],
    pickle_ranks: Mapping[str, int],
) -> int | None:
    """Resolve a pytest-cuke JSON attachment to its scenario when it carries IDs."""
    case_id, pickle_id = _json_attachment_references(record)
    rank = case_ranks.get(case_id) if case_id is not None else None
    return rank if rank is not None or pickle_id is None else pickle_ranks.get(pickle_id)


def _record_scenario_rank(
    record: _EnvelopeRecord,
    *,
    case_ranks: Mapping[str, int],
    pickle_ranks: Mapping[str, int],
    attempt_ranks: Mapping[str, int],
    hook_started_ranks: Mapping[str, int],
) -> int | None:
    """Resolve execution records through their test case, attempt, or hook references."""
    payload = _payload(record.envelope, record.payload_kind)
    rank = None
    case_id = payload.get("testCaseId")
    if isinstance(case_id, str):
        rank = case_ranks.get(case_id)
    pickle_id = payload.get("pickleId")
    if rank is None and isinstance(pickle_id, str):
        rank = pickle_ranks.get(pickle_id)

    if rank is None and record.payload_kind == "test_case_started":
        started_id = payload.get("id")
        if isinstance(started_id, str):
            rank = attempt_ranks.get(started_id)

    attempt_id = payload.get("testCaseStartedId")
    if rank is None and isinstance(attempt_id, str):
        rank = attempt_ranks.get(attempt_id)

    hook_started_id = payload.get("testRunHookStartedId")
    if rank is None and isinstance(hook_started_id, str):
        rank = hook_started_ranks.get(hook_started_id)

    if rank is None and record.payload_kind == "attachment":
        rank = _json_attachment_scenario_rank(record, case_ranks, pickle_ranks)
    return rank


def _case_attachment_attempts(
    execution: Sequence[_EnvelopeRecord],
    case_ranks: Mapping[str, int],
    pickle_ranks: Mapping[str, int],
) -> dict[tuple[int, int], int]:
    """Associate case JSON attachments with the closest same-fragment attempt."""
    finished_at: dict[tuple[int, str], int] = {}
    for record in execution:
        if record.payload_kind != "test_case_finished":
            continue
        payload = _payload(record.envelope, record.payload_kind)
        started_id = payload.get("testCaseStartedId")
        if not isinstance(started_id, str):
            continue
        key = (record.fragment_index, started_id)
        finished_at[key] = min(finished_at.get(key, record.sequence_in_fragment), record.sequence_in_fragment)

    attempts_by_fragment: dict[int, list[tuple[str, int | None, int | None, int, int | None]]] = {}
    for record in execution:
        if record.payload_kind != "test_case_started":
            continue
        payload = _payload(record.envelope, record.payload_kind)
        case_id = payload.get("testCaseId")
        if not isinstance(case_id, str):
            continue
        raw_attempt = payload.get("attempt")
        attempt = raw_attempt if type(raw_attempt) is int else None
        attempts_by_fragment.setdefault(record.fragment_index, []).append(
            (
                case_id,
                case_ranks.get(case_id),
                attempt,
                record.sequence_in_fragment,
                finished_at.get((record.fragment_index, str(payload.get("id")))),
            )
        )

    associated_attempts: dict[tuple[int, int], int] = {}
    for record in execution:
        if record.payload_kind != "attachment":
            continue
        attachment = _payload(record.envelope, record.payload_kind)
        if isinstance(attachment.get("testCaseStartedId"), str) or isinstance(
            attachment.get("testRunHookStartedId"), str
        ):
            continue
        case_id, pickle_id = _json_attachment_references(record)
        pickle_rank = pickle_ranks.get(pickle_id) if pickle_id is not None else None
        if case_id is None and pickle_rank is None:
            continue

        candidates = attempts_by_fragment.get(record.fragment_index, [])
        if case_id is not None:
            candidates = [attempt for attempt in candidates if attempt[0] == case_id]
        elif pickle_rank is not None:
            candidates = [attempt for attempt in candidates if attempt[1] == pickle_rank]
        sequence = record.sequence_in_fragment
        active = [
            attempt
            for attempt in candidates
            if attempt[3] <= sequence and (attempt[4] is None or sequence < attempt[4])
        ]
        following = [attempt for attempt in candidates if attempt[3] > sequence]
        previous = [
            attempt
            for attempt in candidates
            if attempt[3] <= sequence and attempt[4] is not None and attempt[4] < sequence
        ]
        selected = (
            max(active, key=lambda attempt: attempt[3])
            if active
            else min(following, key=lambda attempt: attempt[3])
            if following
            else max(previous, key=lambda attempt: attempt[3])
            if previous
            else None
        )
        if selected is not None and selected[2] is not None:
            associated_attempts[(record.fragment_index, record.sequence_in_fragment)] = selected[2]
    return associated_attempts


def _record_attempt_number(
    record: _EnvelopeRecord,
    attempt_numbers: Mapping[str, int],
    hook_started_attempts: Mapping[str, int],
    attachment_attempts: Mapping[tuple[int, int], int],
) -> int | None:
    """Resolve the retry ordinal through Cucumber's started-case/hook references."""
    payload = _payload(record.envelope, record.payload_kind)
    if record.payload_kind == "test_case_started":
        raw_attempt = payload.get("attempt")
        return raw_attempt if type(raw_attempt) is int else None
    started_id = payload.get("testCaseStartedId")
    if isinstance(started_id, str) and started_id in attempt_numbers:
        return attempt_numbers[started_id]
    hook_started_id = payload.get("testRunHookStartedId")
    if isinstance(hook_started_id, str) and hook_started_id in hook_started_attempts:
        return hook_started_attempts[hook_started_id]
    return attachment_attempts.get((record.fragment_index, record.sequence_in_fragment))


def _apply_id_remap(records: Sequence[_EnvelopeRecord], id_remap: dict[str, str]) -> None:
    if not id_remap:
        return
    for record in records:
        record.envelope = _rewrite_references(record.envelope, id_remap)
    id_remap.clear()


class LiveMessageAdapter:
    """Normalize controller and worker envelopes for one live formatter stream.

    Worker batches already have worker-scoped IDs when they reach the controller.
    This adapter removes worker run-level envelopes, aliases worker run IDs to the
    controller run, keeps controller run hooks canonical, and deduplicates
    repeated structural records incrementally.
    """

    def __init__(self) -> None:
        self._controller_run_id: str | None = None
        self._id_remap: dict[str, str] = {}
        self._structural_by_identity: dict[str, _EnvelopeRecord] = {}
        self._hook_types: dict[str, str] = {}
        self._run_hook_types: dict[str, str] = {}

    def controller_envelope(self, envelope: Mapping[str, Any]) -> dict[str, Any] | None:
        """Accept one controller envelope and return its formatter-facing copy."""
        normalized = dict(envelope)
        payload_kind = _payload_kind(normalized)
        if payload_kind == "test_run_started":
            run_id = _payload(normalized, payload_kind).get("id")
            if run_id is not None and not isinstance(run_id, str):
                raise ValueError("Controller TestRunStarted has no string ID.")
            self._controller_run_id = run_id
        elif payload_kind == "hook":
            self._remember_hook_type(normalized)
        normalized = _rewrite_references(normalized, self._id_remap)
        return self._remember_structural(normalized, payload_kind, worker_id="master")

    def worker_envelope(self, envelope: Mapping[str, Any], *, worker_id: str) -> dict[str, Any] | None:
        """Normalize one already-namespaced worker envelope for a single live run."""
        normalized = dict(envelope)
        payload_kind = _payload_kind(normalized)
        if payload_kind in CONTROLLER_SINGULAR_PAYLOAD_KINDS:
            if payload_kind == "test_run_started":
                worker_run_id = _payload(normalized, payload_kind).get("id")
                if not isinstance(worker_run_id, str):
                    raise ValueError(f"Worker '{worker_id}' TestRunStarted has no string ID.")
                if self._controller_run_id is None:
                    raise ValueError("Worker Messages arrived before the controller TestRunStarted envelope.")
                self._id_remap[worker_run_id] = self._controller_run_id
            return None

        if payload_kind == "hook":
            hook_payload = _payload(normalized, payload_kind)
            hook_id = hook_payload.get("id")
            hook_type = hook_payload.get("type")
            if isinstance(hook_id, str) and isinstance(hook_type, str):
                self._hook_types[hook_id] = hook_type
            if hook_type in {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}:
                return None
            normalized = _rewrite_references(normalized, self._id_remap)
            result = self._remember_structural(normalized, payload_kind, worker_id=worker_id)
            if isinstance(hook_id, str) and isinstance(hook_type, str):
                self._hook_types[self._id_remap.get(hook_id, hook_id)] = hook_type
            return result

        if payload_kind == "test_run_hook_started":
            started_payload = _payload(normalized, payload_kind)
            hook_id = started_payload.get("hookId")
            started_id = started_payload.get("id")
            hook_type = self._hook_types.get(self._id_remap.get(str(hook_id), str(hook_id)))
            if isinstance(started_id, str) and hook_type is not None:
                self._run_hook_types[started_id] = hook_type
            if hook_type in {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}:
                return None

        if payload_kind in {"test_run_hook_finished", "attachment"}:
            started_id = _payload(normalized, payload_kind).get("testRunHookStartedId")
            if self._run_hook_types.get(str(started_id)) in {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}:
                return None

        normalized = _rewrite_references(normalized, self._id_remap)
        return self._remember_structural(normalized, payload_kind, worker_id=worker_id)

    def _remember_hook_type(self, envelope: dict[str, Any]) -> None:
        payload = _payload(envelope, "hook")
        hook_id = payload.get("id")
        hook_type = payload.get("type")
        if isinstance(hook_id, str) and isinstance(hook_type, str):
            self._hook_types[hook_id] = hook_type

    def _remember_structural(
        self,
        envelope: dict[str, Any],
        payload_kind: str,
        *,
        worker_id: str,
    ) -> dict[str, Any] | None:
        if payload_kind not in STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS:
            return envelope

        record = _EnvelopeRecord(
            envelope=envelope,
            payload_kind=payload_kind,
            worker_id=worker_id,
            fragment_index=0,
            sequence_in_fragment=0,
        )
        identity = _structural_identity(record, strip_reference_ids=False)
        canonical = self._structural_by_identity.get(identity)
        if canonical is None:
            self._structural_by_identity[identity] = record
            return envelope

        self._id_remap.update(_duplicate_object_id_map(canonical, record))
        return None


def _run_hook_phase(
    record: _EnvelopeRecord,
    hook_types: Mapping[str, str],
    started_to_type: Mapping[str, str],
) -> int:
    """Place run hooks around scenario execution while retaining each participant's order."""
    if record.payload_kind == "test_run_hook_started":
        hook_id = _payload(record.envelope, record.payload_kind).get("hookId")
        hook_type = hook_types.get(str(hook_id), "")
    elif record.payload_kind in {"test_run_hook_finished", "attachment"}:
        started_id = _payload(record.envelope, record.payload_kind).get("testRunHookStartedId")
        hook_type = started_to_type.get(str(started_id), "")
    else:
        return 1
    if hook_type in {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}:
        return 0 if hook_type == "BEFORE_TEST_RUN" else 2
    return 1


def consolidate_message_fragments(fragments: Sequence[MessageFragment]) -> ConsolidatedMessageStream:
    """Namespace, structurally deduplicate and deterministically order message fragments."""
    sorted_fragments = sorted(fragments, key=lambda fragment: (fragment.role != "controller", fragment.worker_id))
    records: list[_EnvelopeRecord] = []
    diagnostics: list[MessageConsolidationDiagnostic] = []
    incomplete_workers: set[str] = set()
    for fragment_index, fragment in enumerate(sorted_fragments):
        for sequence_in_fragment, wire_envelope in enumerate(fragment.envelopes):
            namespaced = namespace_envelope_ids(wire_envelope, worker_id=fragment.worker_id)
            try:
                payload_kind = _payload_kind(namespaced)
            except ValueError as error:
                diagnostics.append(
                    MessageConsolidationDiagnostic(
                        code="interrupted_worker_transfer",
                        message=(
                            f"Worker '{fragment.worker_id}' sent an invalid Messages envelope "
                            f"at fragment position {sequence_in_fragment}: {error}"
                        ),
                        worker_id=fragment.worker_id,
                    )
                )
                incomplete_workers.add(fragment.worker_id)
                continue
            records.append(
                _EnvelopeRecord(
                    envelope=namespaced,
                    payload_kind=payload_kind,
                    worker_id=fragment.worker_id,
                    fragment_index=fragment_index,
                    sequence_in_fragment=sequence_in_fragment,
                )
            )

    id_remap: dict[str, str] = {}
    singular_by_kind: dict[str, _EnvelopeRecord] = {}
    for record in records:
        if record.payload_kind not in CONTROLLER_SINGULAR_PAYLOAD_KINDS:
            continue
        canonical = singular_by_kind.get(record.payload_kind)
        if canonical is None:
            singular_by_kind[record.payload_kind] = record
        else:
            record.retain = False
            id_remap.update(_duplicate_object_id_map(canonical, record))

    structural_kinds = set(STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS) - {"test_case"}
    _apply_id_remap(records, id_remap)
    _canonicalize_execnet_staged_uris(records)
    structural_by_identity: dict[str, _EnvelopeRecord] = {}
    structural_order = ("source", "gherkin_document", "parameter_type", "pickle", "step_definition", "hook")
    for payload_kind in structural_order:
        if payload_kind not in structural_kinds:
            continue
        for record in records:
            if record.payload_kind != payload_kind:
                continue
            identity = _structural_identity(record, strip_reference_ids=False)
            canonical = structural_by_identity.get(identity)
            if canonical is None:
                structural_by_identity[identity] = record
            else:
                record.retain = False
                id_remap.update(_duplicate_object_id_map(canonical, record))
        _apply_id_remap(records, id_remap)

    test_cases_by_identity: dict[str, _EnvelopeRecord] = {}
    for record in records:
        if record.payload_kind != "test_case":
            continue
        identity = _structural_identity(record, strip_reference_ids=False)
        canonical = test_cases_by_identity.get(identity)
        if canonical is None:
            test_cases_by_identity[identity] = record
        else:
            record.retain = False
            id_remap.update(_duplicate_object_id_map(canonical, record))

    _apply_id_remap(records, id_remap)

    retained = [record for record in records if record.retain]
    structural = sorted(
        (record for record in retained if record.payload_kind in structural_kinds),
        key=_record_sort_key,
    )
    test_cases = [record for record in retained if record.payload_kind == "test_case"]
    execution = [
        record
        for record in retained
        if record.payload_kind not in CONTROLLER_SINGULAR_PAYLOAD_KINDS
        and record.payload_kind not in STRUCTURAL_DEDUPLICATED_PAYLOAD_KINDS
    ]

    pickle_records_by_fragment: dict[int, list[_EnvelopeRecord]] = {}
    for record in structural:
        if record.payload_kind == "pickle":
            pickle_records_by_fragment.setdefault(record.fragment_index, []).append(record)

    pickle_ranks: dict[str, int] = {}
    fallback_pickle_ranks: dict[tuple[str, int], int] = {}
    if pickle_records_by_fragment:
        canonical_fragment = min(
            pickle_records_by_fragment,
            key=lambda fragment_index: (-len(pickle_records_by_fragment[fragment_index]), fragment_index),
        )
        canonical_pickles = pickle_records_by_fragment[canonical_fragment]
        canonical_identities = [_pickle_order_identity(record) for record in canonical_pickles]
        for rank, record in enumerate(canonical_pickles):
            pickle_id = _payload(record.envelope, record.payload_kind).get("id")
            if isinstance(pickle_id, str):
                pickle_ranks.setdefault(pickle_id, rank)

        for fragment_index in sorted(pickle_records_by_fragment):
            if fragment_index == canonical_fragment:
                continue
            next_rank = 0
            identity_occurrences: dict[str, int] = {}
            for record in pickle_records_by_fragment[fragment_index]:
                identity = _pickle_order_identity(record)
                occurrence = identity_occurrences.get(identity, 0)
                identity_occurrences[identity] = occurrence + 1
                matched_rank = next(
                    (
                        candidate_rank
                        for candidate_rank in range(next_rank, len(canonical_identities))
                        if canonical_identities[candidate_rank] == identity
                    ),
                    None,
                )
                if matched_rank is not None:
                    next_rank = matched_rank + 1
                    rank = matched_rank
                else:
                    fallback_identity = (identity, occurrence)
                    rank = fallback_pickle_ranks.setdefault(
                        fallback_identity,
                        len(canonical_pickles) + len(fallback_pickle_ranks),
                    )
                pickle_id = _payload(record.envelope, record.payload_kind).get("id")
                if isinstance(pickle_id, str):
                    pickle_ranks.setdefault(pickle_id, rank)

    case_ranks: dict[str, int] = {}
    for record in test_cases:
        payload = _payload(record.envelope, record.payload_kind)
        case_id = payload.get("id")
        pickle_id = payload.get("pickleId")
        if isinstance(case_id, str) and isinstance(pickle_id, str) and pickle_id in pickle_ranks:
            case_ranks.setdefault(case_id, pickle_ranks[pickle_id])

    test_cases.sort(
        key=lambda record: (
            *_scenario_rank_sort_key(
                case_ranks.get(str(_payload(record.envelope, record.payload_kind).get("id")))
            ),
            *_record_sort_key(record),
        )
    )

    hook_types = {
        str(payload.get("id")): str(payload.get("type"))
        for record in structural
        if record.payload_kind == "hook"
        if isinstance((payload := _payload(record.envelope, record.payload_kind)).get("id"), str)
    }
    started_to_type = {
        str(payload.get("id")): hook_types.get(str(payload.get("hookId")), "")
        for record in execution
        if record.payload_kind == "test_run_hook_started"
        if isinstance((payload := _payload(record.envelope, record.payload_kind)).get("id"), str)
    }

    attempt_ranks: dict[str, int] = {}
    attempt_numbers: dict[str, int] = {}
    for record in execution:
        if record.payload_kind != "test_case_started":
            continue
        payload = _payload(record.envelope, record.payload_kind)
        started_id = payload.get("id")
        case_id = payload.get("testCaseId")
        raw_attempt = payload.get("attempt")
        if isinstance(started_id, str) and type(raw_attempt) is int:
            attempt_numbers.setdefault(started_id, raw_attempt)
        if isinstance(started_id, str) and isinstance(case_id, str) and case_id in case_ranks:
            attempt_ranks.setdefault(started_id, case_ranks[case_id])

    hook_started_ranks: dict[str, int] = {}
    hook_started_attempts: dict[str, int] = {}
    for record in execution:
        if record.payload_kind != "test_run_hook_started":
            continue
        payload = _payload(record.envelope, record.payload_kind)
        hook_started_id = payload.get("id")
        attempt_id = payload.get("testCaseStartedId")
        if (
            isinstance(hook_started_id, str)
            and isinstance(attempt_id, str)
            and attempt_id in attempt_numbers
        ):
            hook_started_attempts.setdefault(hook_started_id, attempt_numbers[attempt_id])
        if (
            isinstance(hook_started_id, str)
            and isinstance(attempt_id, str)
            and attempt_id in attempt_ranks
        ):
            hook_started_ranks.setdefault(hook_started_id, attempt_ranks[attempt_id])

    attachment_attempts = _case_attachment_attempts(execution, case_ranks, pickle_ranks)

    def execution_sort_key(record: _EnvelopeRecord) -> tuple[int, int, int, int, int, int, int]:
        phase = _run_hook_phase(record, hook_types, started_to_type)
        if phase != 1:
            return (phase, 0, 0, 0, 0, *_record_sort_key(record))
        scenario_rank = _record_scenario_rank(
                record,
                case_ranks=case_ranks,
                pickle_ranks=pickle_ranks,
                attempt_ranks=attempt_ranks,
                hook_started_ranks=hook_started_ranks,
            )
        attempt_number = _record_attempt_number(
            record,
            attempt_numbers=attempt_numbers,
            hook_started_attempts=hook_started_attempts,
            attachment_attempts=attachment_attempts,
        )
        attempt_key = (0, attempt_number) if attempt_number is not None else (1, 0)
        return (phase, *_scenario_rank_sort_key(scenario_rank), *attempt_key, *_record_sort_key(record))

    execution.sort(key=execution_sort_key)

    ordered: list[_EnvelopeRecord] = []
    if (meta := singular_by_kind.get("meta")) is not None:
        ordered.append(meta)
    ordered.extend(structural)
    if (run_started := singular_by_kind.get("test_run_started")) is not None:
        ordered.append(run_started)
    ordered.extend(test_cases)
    ordered.extend(execution)
    if (run_finished := singular_by_kind.get("test_run_finished")) is not None:
        ordered.append(run_finished)

    diagnostics.extend(
        MessageConsolidationDiagnostic(
            code="partial_stream",
            message=f"Cucumber Messages stream is partial because worker '{worker_id}' sent invalid data.",
            worker_id=worker_id,
        )
        for worker_id in sorted(incomplete_workers)
    )
    envelope_dicts = tuple(record.envelope for record in ordered)
    envelopes = tuple(message_from_dict(wire, Envelope) for wire in envelope_dicts)
    return ConsolidatedMessageStream(
        envelopes=envelopes,
        envelope_dicts=envelope_dicts,
        diagnostics=tuple(diagnostics),
    )
