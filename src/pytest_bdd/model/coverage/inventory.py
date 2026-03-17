from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from attrs import define, field

from pytest_bdd.model.message_capability_inventory import resolve_messages_schema_dir

SCHEMA_DIR = resolve_messages_schema_dir()


@define(slots=True)
class FieldMetadata:
    path: str
    type: str
    is_required: bool
    description: str = ""


@define(slots=True)
class CapabilityInventory:
    payload_kinds: list[str] = field(factory=list)
    fields: dict[tuple[str, str], FieldMetadata] = field(factory=dict)


def to_camel_case_identifier(value: str) -> str:
    parts = [part for part in value.split("_") if part]
    if not parts:
        return value
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def canonical_payload_kind(payload_kind: str) -> str:
    payload_kind = payload_kind.strip()
    if "_" not in payload_kind:
        return payload_kind
    return to_camel_case_identifier(payload_kind)


def canonical_capability_key(payload_kind: str, field_path: str) -> tuple[str, str]:
    return canonical_payload_kind(payload_kind), field_path.strip(".")


def parse_capability_id(capability_id: str) -> tuple[str, str]:
    if "." not in capability_id:
        return canonical_payload_kind(capability_id), ""
    payload_kind, field_path = capability_id.split(".", 1)
    return canonical_payload_kind(payload_kind), field_path


def canonical_capability_id(capability_id: str) -> str:
    payload_kind, field_path = parse_capability_id(capability_id)
    return f"{payload_kind}.{field_path}" if field_path else payload_kind


def iter_capability_ids(inventory: CapabilityInventory) -> tuple[str, ...]:
    capability_ids = [f"{payload_kind}.{path}" if path else payload_kind for payload_kind, path in inventory.fields]
    return tuple(sorted({canonical_capability_id(capability_id) for capability_id in capability_ids}))


def _resolve_schema(schema_dir: Path, ref: str, root_schema: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if "#" in ref:
        file_part, path_part = ref.split("#", 1)
    else:
        file_part, path_part = ref, ""

    if file_part:
        normalized_file = file_part.removeprefix("./")
        target_path = schema_dir / normalized_file
        if not target_path.is_file():
            msg = f"Referenced schema file '{normalized_file}' was not found in '{schema_dir}'."
            raise FileNotFoundError(msg)
        new_root = json.loads(target_path.read_text(encoding="utf-8"))
    else:
        new_root = root_schema

    resolved: Any = new_root
    if path_part:
        for part in (p for p in path_part.split("/") if p):
            resolved = resolved[part]

    return resolved, new_root


def _extract_fields(  # noqa: C901
    schema_dir: Path,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    payload_kind: str,
    current_path: str,
    inventory: CapabilityInventory,
    *,
    is_required: bool = False,
    visited: set[str] | None = None,
) -> None:
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
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", ()))
        for property_name, property_schema in properties.items():
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
        _extract_fields(
            schema_dir,
            schema["items"],
            root_schema,
            payload_kind,
            current_path,
            inventory,
            is_required=is_required,
            visited=refs_seen,
        )
        return

    for union_keyword in ("anyOf", "allOf", "oneOf"):
        if union_keyword in schema:
            for sub_schema in schema[union_keyword]:
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
        field_type: str | list[str] | None = schema.get("type")
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
    resolved_schema_dir = resolve_messages_schema_dir(schema_dir)
    envelope_schema, _ = _resolve_schema(resolved_schema_dir, "Envelope.json", {})

    inventory = CapabilityInventory()
    for payload_kind, payload_schema in envelope_schema.get("properties", {}).items():
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


def inventory_to_capability_payload(inventory: CapabilityInventory, *, baseline_release: str) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
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
                "affects": ["emitted_envelope_payload"],
                "source_reference": "messages/jsonschema/src/Envelope.json",
                "explicit_relevance": "relevant",
            }
        )
    return payload


def main() -> None:
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
