"""
Provide message consolidation helpers.

Responsibility:
    Provide message consolidation helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_consolidation` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - ConsolidationDiagnostic: owns nested behavior below this boundary
    - MessageFragment: owns nested behavior below this boundary
    - _EnvelopeRecord: owns nested behavior below this boundary
    - ConsolidatedMessageStream: owns nested behavior below this boundary
    - _participant_sort_key: owns nested behavior below this boundary
    - _semantic_clone: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `message_consolidation`

State and side effects:
    mutates payload, worker_id, envelopes, diagnostics, canonical; depends on __future__.annotations, json,
    typing.TYPE_CHECKING, typing.Literal, typing.cast.

Invariants:
    - `pytest_bdd.model.message_consolidation` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal, cast

from attrs import define, frozen
from returns.maybe import Nothing

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

    from pytest_bdd.types.json import JSONObject, JSONValue


@frozen
class ConsolidationDiagnostic:
    """
    Represent a warning or error generated during the process of merging distributed message streams.

    Responsibility:
        Represent a warning or error generated during the process of merging distributed message streams. It directly
        owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation.ConsolidationDiagnostic`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `ConsolidationDiagnostic`

    State and side effects:
        mutates code, severity, worker_id, message, affected_ids.

    Invariants:
        - `pytest_bdd.model.message_consolidation.ConsolidationDiagnostic` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    code: str
    severity: Literal["info", "warning", "error"]
    worker_id: str | None
    message: str
    affected_ids: tuple[str, ...] = ()


@frozen
class MessageFragment:
    """
    Contain a sequence of messages from a single execution participant.

    Responsibility:
        Contain a sequence of messages from a single execution participant. It directly owns the observable contract,
        local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation.MessageFragment` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - from_path: owns nested behavior below this boundary
        - from_envelopes: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `MessageFragment`

    State and side effects:
        mutates envelopes, worker_id, role, path, complete.

    Invariants:
        - `pytest_bdd.model.message_consolidation.MessageFragment` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    worker_id: str
    role: ParticipantRole
    path: Path | None = None
    complete: bool = True
    envelopes: tuple[JSONObject, ...] = ()
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
        """
        Instantiate a MessageFragment by reading line-delimited JSON envelopes from a file.

        Returns:
            A new MessageFragment populated with parsed envelopes.

        Responsibility:
            Instantiate a MessageFragment by reading line-delimited JSON envelopes from a file. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.message_consolidation.MessageFragment.from_path`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls: collaborator call used by this boundary
            - path.exists: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - json.loads: collaborator call used by this boundary
            - path.read_text.splitlines: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `from_path`

        State and side effects:
            mutates envelopes.

        Invariants:
            - `pytest_bdd.model.message_consolidation.MessageFragment.from_path` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        if path is None or not path.exists():
            return cls(worker_id=worker_id, role=role, path=path, complete=False, envelopes=())

        envelopes = tuple(
            cast("JSONObject", json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        return cls(worker_id=worker_id, role=role, path=path, complete=complete, envelopes=envelopes)

    @classmethod
    def from_envelopes(  # noqa: PLR0913
        cls,
        *,
        worker_id: str,
        role: ParticipantRole,
        envelopes: tuple[JSONObject, ...],
        complete: bool,
        manifest_received: bool,
        transferred_batch_count: int = 0,
        last_batch_sequence: int | None = None,
        interruption_reason: str | None = None,
    ) -> MessageFragment:
        """
        Instantiate a MessageFragment directly from an in-memory tuple of JSON envelope dictionaries.

        Returns:
            A new MessageFragment containing the provided envelopes.

        Responsibility:
            Instantiate a MessageFragment directly from an in-memory tuple of JSON envelope dictionaries. It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_consolidation.MessageFragment.from_envelopes` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `from_envelopes`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
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


@define(slots=True)
class _EnvelopeRecord:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._EnvelopeRecord` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._EnvelopeRecord` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - define: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `_EnvelopeRecord`

    State and side effects:
        mutates envelope_dict, payload_kind, worker_id, role, fragment_index.

    Invariants:
        - `pytest_bdd.model.message_consolidation._EnvelopeRecord` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    envelope_dict: JSONObject
    payload_kind: str
    worker_id: str
    role: ParticipantRole
    fragment_index: int
    sequence_in_fragment: int
    retain: bool = True
    discovery_index: int = 0


@frozen
class ConsolidatedMessageStream:
    """
    Store the unified message sequence from all participants.

    Responsibility:
        Store the unified message sequence from all participants. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation.ConsolidatedMessageStream`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `ConsolidatedMessageStream`

    State and side effects:
        mutates envelopes, envelope_dicts, diagnostics.

    Invariants:
        - `pytest_bdd.model.message_consolidation.ConsolidatedMessageStream` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    envelopes: tuple[object, ...]
    envelope_dicts: tuple[JSONObject, ...]
    diagnostics: tuple[ConsolidationDiagnostic, ...]


def _participant_sort_key(fragment: MessageFragment) -> tuple[int, str]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._participant_sort_key` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._participant_sort_key` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_participant_sort_key`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return (0 if fragment.role == "controller" else 1, fragment.worker_id)


def _semantic_clone(value: JSONValue, *, strip_reference_ids: bool) -> JSONValue:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._semantic_clone` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._semantic_clone` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - _semantic_clone: collaborator call used by this boundary
        - value.items: collaborator call used by this boundary
        - _is_reference_key: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `_semantic_clone`

    State and side effects:
        mutates result.

    Invariants:
        - `pytest_bdd.model.message_consolidation._semantic_clone` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    if isinstance(value, dict):
        result: JSONObject = {}
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


def _payload_root(envelope_dict: JSONObject, payload_kind: str) -> JSONObject:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._payload_root` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._payload_root` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - payload_kind.split: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - join: collaborator call used by this boundary
        - part.title: collaborator call used by this boundary
        - envelope_dict.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `_payload_root`

    State and side effects:
        mutates camel_case_payload_kind, payload.

    Invariants:
        - `pytest_bdd.model.message_consolidation._payload_root` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    if payload_kind in envelope_dict and isinstance(envelope_dict[payload_kind], dict):
        return cast("JSONObject", envelope_dict[payload_kind])
    camel_case_payload_kind = payload_kind.split("_", maxsplit=1)[0] + "".join(
        part.title() for part in payload_kind.split("_")[1:]
    )
    payload = envelope_dict.get(camel_case_payload_kind)
    return payload if isinstance(payload, dict) else {}


def _structural_identity(record: _EnvelopeRecord, *, strip_reference_ids: bool) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._structural_identity` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._structural_identity` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _payload_root: collaborator call used by this boundary
        - json.dumps: collaborator call used by this boundary
        - _semantic_clone: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_structural_identity`

    State and side effects:
        mutates payload.

    Invariants:
        - `pytest_bdd.model.message_consolidation._structural_identity` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
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


def _collect_ids_by_path(value: JSONValue, path: tuple[object, ...] = ()) -> dict[tuple[object, ...], str]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._collect_ids_by_path` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._collect_ids_by_path` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - collected.update: collaborator call used by this boundary
        - _collect_ids_by_path: collaborator call used by this boundary
        - value.get: collaborator call used by this boundary
        - value.items: collaborator call used by this boundary
        - enumerate: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_collect_ids_by_path`

    State and side effects:
        mutates collected, raw_id.

    Invariants:
        - `pytest_bdd.model.message_consolidation._collect_ids_by_path` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    collected: dict[tuple[object, ...], str] = {}
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
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._build_duplicate_id_map` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._build_duplicate_id_map`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _collect_ids_by_path: collaborator call used by this boundary
        - _payload_root: collaborator call used by this boundary
        - duplicate_ids.items: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_build_duplicate_id_map`

    State and side effects:
        mutates canonical_ids, duplicate_ids.

    Invariants:
        - `pytest_bdd.model.message_consolidation._build_duplicate_id_map` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    canonical_ids = _collect_ids_by_path(_payload_root(canonical.envelope_dict, canonical.payload_kind))
    duplicate_ids = _collect_ids_by_path(_payload_root(duplicate.envelope_dict, duplicate.payload_kind))
    return {
        duplicate_id: canonical_ids[path]
        for path, duplicate_id in duplicate_ids.items()
        if path in canonical_ids and duplicate_id != canonical_ids[path]
    }


def _is_reference_key(key: str) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._is_reference_key` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._is_reference_key` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - key.endswith: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/execution_message_adapter.py: imports or references `_is_reference_key`
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `_is_reference_key`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    if key == "workerId":
        return False
    return key.endswith(("Id", "Ids", "_id", "_ids"))


def _hook_name_from_identifier(identifier: object) -> str | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._hook_name_from_identifier` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._hook_name_from_identifier`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - identifier.endswith: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_hook_name_from_identifier`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    if not isinstance(identifier, str):
        return Nothing.value_or(None)
    for candidate in (*_PRE_RUN_HOOK_NAMES, *_POST_RUN_HOOK_NAMES):
        if identifier == candidate or identifier.endswith(f":{candidate}"):
            return candidate
    return Nothing.value_or(None)


def _resolve_hook_id_by_started_id(records: list[_EnvelopeRecord]) -> dict[str, str]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._resolve_hook_id_by_started_id` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_consolidation._resolve_hook_id_by_started_id` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - payload.get: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - _payload_root: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_resolve_hook_id_by_started_id`

    State and side effects:
        mutates result, payload, hook_started_id, hook_id.

    Invariants:
        - `pytest_bdd.model.message_consolidation._resolve_hook_id_by_started_id` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
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
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._record_sort_key` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._record_sort_key` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references `_record_sort_key`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return (record.fragment_index, record.sequence_in_fragment, record.discovery_index)


def _categorize_execution_record(record: _EnvelopeRecord, hook_ids_by_started_id: dict[str, str]) -> int:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._categorize_execution_record` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._categorize_execution_record`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _payload_root: collaborator call used by this boundary
        - _hook_name_from_identifier: collaborator call used by this boundary
        - payload.get: collaborator call used by this boundary
        - hook_ids_by_started_id.get: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_categorize_execution_record`

    State and side effects:
        mutates payload, hook_name, hook_identifier.

    Invariants:
        - `pytest_bdd.model.message_consolidation._categorize_execution_record` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
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
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_consolidation._diagnostics_for_fragment` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation._diagnostics_for_fragment`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - diagnostics.append: collaborator call used by this boundary
        - ConsolidationDiagnostic: collaborator call used by this boundary
        - fragment.path.exists: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `_diagnostics_for_fragment`

    State and side effects:
        mutates diagnostics.

    Invariants:
        - `pytest_bdd.model.message_consolidation._diagnostics_for_fragment` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    diagnostics: list[ConsolidationDiagnostic] = []
    if fragment.role == "worker" and not fragment.manifest_received:
        diagnostics.append(
            ConsolidationDiagnostic(
                code="missing_worker_manifest",
                severity="warning",
                worker_id=fragment.worker_id,
                message=f"Worker manifest for '{fragment.worker_id}' was not received.",
            ),
        )
    if not fragment.envelopes:
        if fragment.path is None:
            diagnostics.append(
                ConsolidationDiagnostic(
                    code="missing_worker_fragment",
                    severity="warning",
                    worker_id=fragment.worker_id,
                    message=f"Worker transport data for '{fragment.worker_id}' was not registered.",
                ),
            )
        elif not fragment.path.exists():
            diagnostics.append(
                ConsolidationDiagnostic(
                    code="missing_worker_fragment",
                    severity="warning",
                    worker_id=fragment.worker_id,
                    message=f"Worker fragment '{fragment.path}' is missing for '{fragment.worker_id}'.",
                ),
            )
    elif fragment.path is not None and not fragment.path.exists():
        diagnostics.append(
            ConsolidationDiagnostic(
                code="missing_worker_fragment",
                severity="warning",
                worker_id=fragment.worker_id,
                message=f"Worker fragment '{fragment.path}' is missing for '{fragment.worker_id}'.",
            ),
        )
    if fragment.interruption_reason is not None:
        diagnostics.append(
            ConsolidationDiagnostic(
                code="interrupted_worker_transfer",
                severity="warning",
                worker_id=fragment.worker_id,
                message=f"Worker transfer for '{fragment.worker_id}' was interrupted: {fragment.interruption_reason}",
            ),
        )
    if not fragment.complete:
        diagnostics.append(
            ConsolidationDiagnostic(
                code="partial_stream",
                severity="warning",
                worker_id=fragment.worker_id,
                message=f"Worker fragment for '{fragment.worker_id}' is incomplete.",
            ),
        )
    return diagnostics


def consolidate_message_fragments(  # noqa: C901, PLR0912, PLR0914, PLR0915
    fragments: list[MessageFragment],
) -> ConsolidatedMessageStream:
    """
    Merge multiple message fragments into a single, valid cucumber-messages stream.

    This function handles ID deduplication, sorts events chronologically, and resolves
    conflicts between multiple workers emitting structurally identical elements.

    Returns:
        A ConsolidatedMessageStream containing the ordered envelopes and any consolidation diagnostics.

    Responsibility:
        Merge multiple message fragments into a single, valid cucumber-messages stream. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_consolidation.consolidate_message_fragments`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - singular_records_by_kind.get: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - id_remap.update: collaborator call used by this boundary
        - _build_duplicate_id_map: collaborator call used by this boundary
        - ordered_records.append: collaborator call used by this boundary
        - ordered_records.extend: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
          `consolidate_message_fragments`

    State and side effects:
        mutates canonical, record.retain, identity, record.envelope_dict, diagnostics.

    Invariants:
        - `pytest_bdd.model.message_consolidation.consolidate_message_fragments` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
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
                ),
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
        key=lambda record: (_categorize_execution_record(record, hook_ids_by_started_id), *_record_sort_key(record)),
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
