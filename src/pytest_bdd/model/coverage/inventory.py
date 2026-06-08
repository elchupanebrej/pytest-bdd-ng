"""
Provide inventory.

Responsibility:
    Provide inventory. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.coverage.inventory` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - FieldMetadata: owns nested behavior below this boundary
    - CapabilityInventory: owns nested behavior below this boundary
    - to_camel_case_identifier: owns nested behavior below this boundary
    - canonical_payload_kind: owns nested behavior below this boundary
    - canonical_capability_key: owns nested behavior below this boundary
    - parse_capability_id: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `inventory`
    - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `inventory`
    - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `inventory`
    - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `inventory`
    - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `inventory`

State and side effects:
    mutates payload_kind, field_type, msg, new_root, resolved; depends on __future__.annotations, argparse, json,
    pathlib.Path, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.model.coverage.inventory` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises TypeError, FileNotFoundError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from attrs import define, field

from pytest_bdd.model.message_capability_inventory import resolve_messages_schema_dir

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONArray, JSONObject, JSONValue

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "message_jsonschema"


@define(slots=True)
class FieldMetadata:
    """
    Metadata for a field in the capability inventory.

    Responsibility:
        Metadata for a field in the capability inventory. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory.FieldMetadata` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - define: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `FieldMetadata`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `FieldMetadata`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `FieldMetadata`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `FieldMetadata`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `FieldMetadata`

    State and side effects:
        mutates path, type, is_required, description.

    Invariants:
        - `pytest_bdd.model.coverage.inventory.FieldMetadata` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    path: str
    type: str
    is_required: bool
    description: str = ""


@define(slots=True)
class CapabilityInventory:
    """
    Inventory of message payload kinds and fields.

    Responsibility:
        Inventory of message payload kinds and fields. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory.CapabilityInventory` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - field: collaborator call used by this boundary
        - define: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `CapabilityInventory`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `CapabilityInventory`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `CapabilityInventory`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `CapabilityInventory`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `CapabilityInventory`

    State and side effects:
        mutates payload_kinds, fields.

    Invariants:
        - `pytest_bdd.model.coverage.inventory.CapabilityInventory` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    payload_kinds: list[str] = field(factory=list)
    fields: dict[tuple[str, str], FieldMetadata] = field(factory=dict)


def to_camel_case_identifier(value: str) -> str:
    """
    Convert value to camelCase identifier.

    Returns:
        camelCase formatted string.

    Responsibility:
        Convert value to camelCase identifier. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory.to_camel_case_identifier` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - value.split: collaborator call used by this boundary
        - join: collaborator call used by this boundary
        - upper: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `to_camel_case_identifier`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
          `to_camel_case_identifier`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `to_camel_case_identifier`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `to_camel_case_identifier`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `to_camel_case_identifier`

    State and side effects:
        mutates parts.

    Invariants:
        - `pytest_bdd.model.coverage.inventory.to_camel_case_identifier` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4

    """
    parts = [part for part in value.split("_") if part]
    if not parts:
        return value
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def canonical_payload_kind(payload_kind: str) -> str:
    """
    Get canonical payload kind.

    Returns:
        Canonical form of the payload kind.

    Responsibility:
        Get canonical payload kind. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory.canonical_payload_kind` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - payload_kind.strip: collaborator call used by this boundary
        - to_camel_case_identifier: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `canonical_payload_kind`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
          `canonical_payload_kind`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `canonical_payload_kind`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `canonical_payload_kind`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `canonical_payload_kind`

    State and side effects:
        mutates payload_kind.

    Invariants:
        - `pytest_bdd.model.coverage.inventory.canonical_payload_kind` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4

    """
    payload_kind = payload_kind.strip()
    if "_" not in payload_kind:
        return payload_kind
    return to_camel_case_identifier(payload_kind)


def canonical_capability_key(payload_kind: str, field_path: str) -> tuple[str, str]:
    """
    Get canonical capability key.

    Returns:
        Tuple of (payload_kind, field_path).

    Responsibility:
        Get canonical capability key. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory.canonical_capability_key` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - canonical_payload_kind: collaborator call used by this boundary
        - field_path.strip: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `canonical_capability_key`
        - src/pytest_bdd/model/coverage/tracker.py: imports or references `canonical_capability_key`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
          `canonical_capability_key`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `canonical_capability_key`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `canonical_capability_key`

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
        #arch-eval:locational_stability=4

    """
    return canonical_payload_kind(payload_kind), field_path.strip(".")


def parse_capability_id(capability_id: str) -> tuple[str, str]:
    """
    Parse capability ID into payload kind and field path.

    Returns:
        Tuple of (payload_kind, field_path).

    Responsibility:
        Parse capability ID into payload kind and field path. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory.parse_capability_id` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - canonical_payload_kind: collaborator call used by this boundary
        - capability_id.split: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `parse_capability_id`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `parse_capability_id`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `parse_capability_id`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `parse_capability_id`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `parse_capability_id`

    State and side effects:
        mutates payload_kind, field_path.

    Invariants:
        - `pytest_bdd.model.coverage.inventory.parse_capability_id` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4

    """
    if "." not in capability_id:
        return canonical_payload_kind(capability_id), ""
    payload_kind, field_path = capability_id.split(".", 1)
    return canonical_payload_kind(payload_kind), field_path


def canonical_capability_id(capability_id: str) -> str:
    """
    Get canonical capability ID.

    Returns:
        Canonical form of the capability ID.

    Responsibility:
        Get canonical capability ID. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory.canonical_capability_id` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parse_capability_id: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `canonical_capability_id`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
          `canonical_capability_id`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `canonical_capability_id`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `canonical_capability_id`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `canonical_capability_id`

    State and side effects:
        mutates payload_kind, field_path.

    Invariants:
        - `pytest_bdd.model.coverage.inventory.canonical_capability_id` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4

    """
    payload_kind, field_path = parse_capability_id(capability_id)
    return f"{payload_kind}.{field_path}" if field_path else payload_kind


def iter_capability_ids(inventory: CapabilityInventory) -> tuple[str, ...]:
    """
    Iterate capability IDs from inventory.

    Returns:
        Tuple of sorted, canonical capability IDs.

    Responsibility:
        Iterate capability IDs from inventory. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory.iter_capability_ids` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - canonical_capability_id: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `iter_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `iter_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `iter_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `iter_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `iter_capability_ids`

    State and side effects:
        mutates capability_ids.

    Invariants:
        - `pytest_bdd.model.coverage.inventory.iter_capability_ids` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4

    """
    capability_ids = [f"{payload_kind}.{path}" if path else payload_kind for payload_kind, path in inventory.fields]
    return tuple(sorted({canonical_capability_id(capability_id) for capability_id in capability_ids}))


def _schema_file_path(schema_dir: Path, normalized_file: str) -> Path:
    """
    Get schema file path.

    Returns:
        Path to the schema file.

    Responsibility:
        Get schema file path. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory._schema_file_path` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - target_path.is_file: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - requested_path.name.endswith: collaborator call used by this boundary
        - requested_path.with_name: collaborator call used by this boundary
        - alternate_path.is_file: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_schema_file_path`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `_schema_file_path`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `_schema_file_path`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_schema_file_path`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `_schema_file_path`

    State and side effects:
        mutates target_path, requested_path, alternate_path.

    Invariants:
        - `pytest_bdd.model.coverage.inventory._schema_file_path` keeps its documented import path, ownership boundary,
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
        #arch-eval:locational_stability=4

    """
    target_path = schema_dir / normalized_file
    if target_path.is_file():
        return target_path

    requested_path = Path(normalized_file)
    if requested_path.suffix == ".json" and not requested_path.name.endswith(".schema.json"):
        alternate_path = schema_dir / requested_path.with_name(f"{requested_path.stem}.schema.json")
        if alternate_path.is_file():
            return alternate_path

    return target_path


def _resolve_schema(schema_dir: Path, ref: str, root_schema: JSONObject) -> tuple[JSONObject, JSONObject]:
    """
    Resolve schema reference.

    Returns:
        Tuple of (resolved_schema, new_root_schema).

    Raises:
        FileNotFoundError: If the referenced schema file is not found.
        TypeError: If the schema reference resolves through a non-object segment or does not resolve to an object.

    Responsibility:
        Resolve schema reference. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory._resolve_schema` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - TypeError: collaborator call used by this boundary
        - ref.split: collaborator call used by this boundary
        - file_part.removeprefix: collaborator call used by this boundary
        - _schema_file_path: collaborator call used by this boundary
        - target_path.is_file: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_resolve_schema`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `_resolve_schema`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `_resolve_schema`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_resolve_schema`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `_resolve_schema`

    State and side effects:
        mutates msg, file_part, path_part, new_root, resolved.

    Invariants:
        - `pytest_bdd.model.coverage.inventory._resolve_schema` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises TypeError, FileNotFoundError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    if "#" in ref:
        file_part, path_part = ref.split("#", 1)
    else:
        file_part, path_part = ref, ""

    if file_part:
        normalized_file = file_part.removeprefix("./")
        target_path = _schema_file_path(schema_dir, normalized_file)
        if not target_path.is_file():
            msg = f"Referenced schema file '{normalized_file}' was not found in '{schema_dir}'."
            raise FileNotFoundError(msg)
        new_root = cast("JSONObject", json.loads(target_path.read_text(encoding="utf-8")))
    else:
        new_root = root_schema

    resolved: JSONValue = new_root
    if path_part:
        for part in (p for p in path_part.split("/") if p):
            if not isinstance(resolved, dict):
                msg = f"Schema reference '{ref}' resolved through non-object segment '{part}'."
                raise TypeError(msg)
            resolved = resolved[part]

    if not isinstance(resolved, dict):
        msg = f"Schema reference '{ref}' did not resolve to an object."
        raise TypeError(msg)
    return resolved, new_root


def _extract_fields(  # noqa: C901, PLR0912, PLR0913, PLR0917
    schema_dir: Path,
    schema: JSONObject,
    root_schema: JSONObject,
    payload_kind: str,
    current_path: str,
    inventory: CapabilityInventory,
    *,
    is_required: bool = False,
    visited: set[str] | None = None,
) -> None:
    """
    Extract fields from schema into inventory.

    Responsibility:
        Extract fields from schema into inventory. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory._extract_fields` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - schema.get: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - _extract_fields: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - _resolve_schema: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_extract_fields`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `_extract_fields`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references `_extract_fields`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_extract_fields`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `_extract_fields`

    State and side effects:
        mutates field_type, refs_seen, ref, resolved, new_root.

    Invariants:
        - `pytest_bdd.model.coverage.inventory._extract_fields` keeps its documented import path, ownership boundary,
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
        #arch-eval:locational_stability=4
    """
    refs_seen = visited or set()
    if "$ref" in schema:
        ref = str(schema["$ref"])
        if ref in refs_seen:
            return
        resolved, new_root = _resolve_schema(schema_dir, ref, root_schema)
        _extract_fields(
            schema_dir,
            resolved,
            new_root,
            payload_kind,
            current_path,
            inventory,
            is_required=is_required,
            visited=refs_seen | {ref},
        )
        return

    if schema.get("type") == "object" or "properties" in schema:
        raw_properties = schema.get("properties", {})
        properties = raw_properties if isinstance(raw_properties, dict) else {}
        raw_required_fields = schema.get("required", [])
        required_fields = set(raw_required_fields if isinstance(raw_required_fields, list) else [])
        for property_name, property_schema in properties.items():
            if not isinstance(property_schema, dict):
                continue
            child_path = f"{current_path}.{property_name}" if current_path else property_name
            _extract_fields(
                schema_dir,
                property_schema,
                root_schema,
                payload_kind,
                child_path,
                inventory,
                is_required=property_name in required_fields,
                visited=refs_seen,
            )
        return

    if schema.get("type") == "array" and "items" in schema:
        items_schema = schema["items"]
        if not isinstance(items_schema, dict):
            return
        _extract_fields(
            schema_dir,
            items_schema,
            root_schema,
            payload_kind,
            current_path,
            inventory,
            is_required=is_required,
            visited=refs_seen,
        )
        return

    for union_keyword in ("anyOf", "allOf", "oneOf"):
        raw_union_schemas = schema.get(union_keyword)
        if isinstance(raw_union_schemas, list):
            for sub_schema in raw_union_schemas:
                if not isinstance(sub_schema, dict):
                    continue
                _extract_fields(
                    schema_dir,
                    sub_schema,
                    root_schema,
                    payload_kind,
                    current_path,
                    inventory,
                    is_required=is_required,
                    visited=refs_seen,
                )
            return

    if current_path:
        raw_field_type = schema.get("type")
        field_type: str | JSONArray | None = raw_field_type if isinstance(raw_field_type, (str, list)) else None
        if field_type is None and "enum" in schema:
            field_type = "enum"
        if field_type is None:
            field_type = "unknown"
        if isinstance(field_type, list):
            field_type = " | ".join(str(item) for item in field_type)
        inventory.fields[payload_kind, current_path] = FieldMetadata(
            path=current_path,
            type=str(field_type),
            is_required=is_required,
            description=str(schema.get("description", "")),
        )


def generate_inventory(schema_dir: Path | None = None) -> CapabilityInventory:
    """
    Generate capability inventory from schema.

    Returns:
        Populated CapabilityInventory instance.

    Responsibility:
        Generate capability inventory from schema. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory.generate_inventory` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - resolve_messages_schema_dir: collaborator call used by this boundary
        - _resolve_schema: collaborator call used by this boundary
        - CapabilityInventory: collaborator call used by this boundary
        - envelope_schema.get: collaborator call used by this boundary
        - envelope_properties.items: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `generate_inventory`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `generate_inventory`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `generate_inventory`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `generate_inventory`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `generate_inventory`

    State and side effects:
        mutates resolved_schema_dir, envelope_schema, _, inventory, raw_envelope_properties.

    Invariants:
        - `pytest_bdd.model.coverage.inventory.generate_inventory` keeps its documented import path, ownership boundary,
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
        #arch-eval:locational_stability=4

    """
    resolved_schema_dir = resolve_messages_schema_dir(schema_dir)
    envelope_schema, _ = _resolve_schema(resolved_schema_dir, "Envelope.json", {})

    inventory = CapabilityInventory()
    raw_envelope_properties = envelope_schema.get("properties", {})
    envelope_properties = raw_envelope_properties if isinstance(raw_envelope_properties, dict) else {}
    for payload_kind, payload_schema in envelope_properties.items():
        if not isinstance(payload_schema, dict):
            continue
        canonical_kind = canonical_payload_kind(payload_kind)
        if canonical_kind not in inventory.payload_kinds:
            inventory.payload_kinds.append(canonical_kind)
        _extract_fields(
            resolved_schema_dir,
            payload_schema,
            envelope_schema,
            canonical_kind,
            "",
            inventory,
        )
    inventory.payload_kinds.sort()
    return inventory


def inventory_to_capability_payload(inventory: CapabilityInventory, *, baseline_release: str) -> JSONArray:
    """
    Convert inventory to capability payload.

    Returns:
        JSON array of capability objects.

    Responsibility:
        Convert inventory to capability payload. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory.inventory_to_capability_payload`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - iter_capability_ids: collaborator call used by this boundary
        - parse_capability_id: collaborator call used by this boundary
        - payload.append: collaborator call used by this boundary
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `inventory_to_capability_payload`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
          `inventory_to_capability_payload`
        - src/pytest_bdd/script/message_capability_governance/capabilities.py: imports or references
          `inventory_to_capability_payload`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `inventory_to_capability_payload`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `inventory_to_capability_payload`

    State and side effects:
        mutates payload, payload_kind, path, field_meta.

    Invariants:
        - `pytest_bdd.model.coverage.inventory.inventory_to_capability_payload` keeps its documented import path,
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
        #arch-eval:locational_stability=4

    """
    payload: JSONArray = []
    for capability_id in iter_capability_ids(inventory):
        payload_kind, path = parse_capability_id(capability_id)
        field_meta = inventory.fields[payload_kind, path]
        payload.append(
            {
                "capability_id": capability_id,
                "baseline_release": baseline_release,
                "name": capability_id,
                "description": field_meta.description or field_meta.path,
                "category": "core",
                "affects": cast("JSONArray", ["emitted_envelope_payload"]),
                "source_reference": "messages/jsonschema/src/Envelope.json",
                "explicit_relevance": "relevant",
            },
        )
    return payload


def main() -> None:
    """
    Generate capability inventory from messages schema.

    Responsibility:
        Generate capability inventory from messages schema. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.coverage.inventory.main` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parser.add_argument: collaborator call used by this boundary
        - argparse.ArgumentParser: collaborator call used by this boundary
        - parser.parse_args: collaborator call used by this boundary
        - generate_inventory: collaborator call used by this boundary
        - inventory_to_capability_payload: collaborator call used by this boundary
        - json.dumps: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `main`
        - src/pytest_bdd/script/__init__.py: imports or references `main`
        - src/pytest_bdd/script/compatibility_matrix.py: imports or references `main`
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `main`
        - src/pytest_bdd/script/message_capability_governance/__main__.py: imports or references `main`

    State and side effects:
        mutates parser, args, inventory, payload, output.

    Invariants:
        - `pytest_bdd.model.coverage.inventory.main` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    parser = argparse.ArgumentParser(description="Generate capability inventory from messages schema.")
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=None,
        help="Path to schema directory containing Envelope.json. Defaults to canonical resolver policy.",
    )
    parser.add_argument(
        "--baseline-release",
        type=str,
        default="unknown",
        help="Baseline release label to embed in generated capability payload output.",
    )
    parser.add_argument("--output", type=Path, default=None, help="Optional output file for generated JSON payload.")
    args = parser.parse_args()

    inventory = generate_inventory(args.schema_dir)
    payload = inventory_to_capability_payload(inventory, baseline_release=args.baseline_release)
    output = json.dumps(payload, indent=2, sort_keys=True)

    if args.output is None:
        print(output)  # noqa: T201
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
