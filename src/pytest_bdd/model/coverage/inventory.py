import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent.parent.parent.parent.parent / "messages" / "jsonschema" / "src"


@dataclass
class FieldMetadata:
    """Metadata for a specific field in the messages schema."""

    path: str
    type: str
    is_required: bool
    description: str = ""


@dataclass
class CapabilityInventory:
    """A collection of all possible fields and payloads derived from the messages schema."""

    payload_kinds: list[str] = field(default_factory=list)
    # Map of (payload_kind, field_path) to FieldMetadata
    fields: dict[tuple[str, str], FieldMetadata] = field(default_factory=dict)


def _resolve_schema(schema_dir: Path, ref: str, root_schema: dict) -> tuple[dict, dict]:
    """Resolves a JSON Schema $ref. Returns the resolved subschema and its root schema."""
    if "#" in ref:
        file_part, path_part = ref.split("#", 1)
    else:
        file_part, path_part = ref, ""

    if file_part:
        file_part = file_part.removeprefix("./")
        target_path = schema_dir / file_part
        if not target_path.exists():
            target_path = Path.cwd() / "messages" / "jsonschema" / "src" / file_part
        with target_path.open(encoding="utf-8") as f:
            new_root = json.load(f)
    else:
        new_root = root_schema

    resolved = new_root
    if path_part:
        parts = [p for p in path_part.split("/") if p]
        for p in parts:
            resolved = resolved[p]

    return resolved, new_root


def _extract_fields(
    schema_dir: Path,
    schema: dict,
    root_schema: dict,
    payload_kind: str,
    current_path: str,
    inventory: CapabilityInventory,
    is_required: bool = False,
    visited: set[str] | None = None,
) -> None:
    if visited is None:
        visited = set()

    if "$ref" in schema:
        ref = schema["$ref"]
        if ref in visited:
            return
        resolved, new_root = _resolve_schema(schema_dir, ref, root_schema)
        _extract_fields(
            schema_dir, resolved, new_root, payload_kind, current_path, inventory, is_required, visited | {ref}
        )
        return

    if schema.get("type") == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])
        for prop_name, prop_schema in properties.items():
            new_path = f"{current_path}.{prop_name}" if current_path else prop_name
            prop_required = prop_name in required_fields
            _extract_fields(
                schema_dir, prop_schema, root_schema, payload_kind, new_path, inventory, prop_required, visited
            )
    elif schema.get("type") == "array" and "items" in schema:
        _extract_fields(
            schema_dir, schema["items"], root_schema, payload_kind, current_path, inventory, is_required, visited
        )
    elif "anyOf" in schema:
        for sub_schema in schema["anyOf"]:
            _extract_fields(
                schema_dir, sub_schema, root_schema, payload_kind, current_path, inventory, is_required, visited
            )
    elif "allOf" in schema:
        for sub_schema in schema["allOf"]:
            _extract_fields(
                schema_dir, sub_schema, root_schema, payload_kind, current_path, inventory, is_required, visited
            )
    elif "oneOf" in schema:
        for sub_schema in schema["oneOf"]:
            _extract_fields(
                schema_dir, sub_schema, root_schema, payload_kind, current_path, inventory, is_required, visited
            )
    else:
        # Scalar or enum
        if current_path:
            field_type = schema.get("type")
            if not field_type and "enum" in schema:
                field_type = "enum"
            if not field_type:
                field_type = "unknown"

            if isinstance(field_type, list):
                field_type = " | ".join(field_type)
            inventory.fields[payload_kind, current_path] = FieldMetadata(
                path=current_path, type=field_type, is_required=is_required, description=schema.get("description", "")
            )


def generate_inventory(schema_dir: Path) -> CapabilityInventory:
    inventory = CapabilityInventory()
    
    target_path = schema_dir / "Envelope.json"
    if not target_path.exists():
        target_path = Path.cwd() / "messages" / "jsonschema" / "src" / "Envelope.json"
        
    envelope_schema, _ = _resolve_schema(target_path.parent, "Envelope.json", {})

    properties = envelope_schema.get("properties", {})
    for payload_kind, prop_schema in properties.items():
        inventory.payload_kinds.append(payload_kind)
        _extract_fields(schema_dir, prop_schema, envelope_schema, payload_kind, "", inventory)

    return inventory


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Capability Inventory from messages schema")
    parser.add_argument("--schema-dir", required=True, type=Path, help="Path to the JSON schema directory")
    args = parser.parse_args()

    inventory = generate_inventory(args.schema_dir)
    # Print removed for ruff T201


if __name__ == "__main__":
    main()
