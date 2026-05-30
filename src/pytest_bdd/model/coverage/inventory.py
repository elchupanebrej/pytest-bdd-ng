"""Provide inventory."""

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
    """Metadata for a field in the capability inventory."""

    path: str
    type: str
    is_required: bool
    description: str = ""


@define(slots=True)
class CapabilityInventory:
    """Inventory of message payload kinds and fields."""

    payload_kinds: list[str] = field(factory=list)
    fields: dict[tuple[str, str], FieldMetadata] = field(factory=dict)


def to_camel_case_identifier(value: str) -> str:
    """
    Convert value to camelCase identifier.

    Returns:
        camelCase formatted string.

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

    """
    return canonical_payload_kind(payload_kind), field_path.strip(".")


def parse_capability_id(capability_id: str) -> tuple[str, str]:
    """
    Parse capability ID into payload kind and field path.

    Returns:
        Tuple of (payload_kind, field_path).

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

    """
    payload_kind, field_path = parse_capability_id(capability_id)
    return f"{payload_kind}.{field_path}" if field_path else payload_kind


def iter_capability_ids(inventory: CapabilityInventory) -> tuple[str, ...]:
    """
    Iterate capability IDs from inventory.

    Returns:
        Tuple of sorted, canonical capability IDs.

    """
    capability_ids = [f"{payload_kind}.{path}" if path else payload_kind for payload_kind, path in inventory.fields]
    return tuple(sorted({canonical_capability_id(capability_id) for capability_id in capability_ids}))


def _schema_file_path(schema_dir: Path, normalized_file: str) -> Path:
    """
    Get schema file path.

    Returns:
        Path to the schema file.

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
    """Extract fields from schema into inventory."""
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
    """Generate capability inventory from messages schema."""
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
