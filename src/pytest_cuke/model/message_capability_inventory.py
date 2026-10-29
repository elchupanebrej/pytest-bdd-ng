"""Build deterministic capability inventories from a Cucumber Messages schema baseline."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Final, cast

from jsonschema.validators import validator_for  # type: ignore[import-untyped]

from pytest_cuke.model.message_capability import RELEVANT_IMPACTS, MessageCapability

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

_IDENTIFIER_BOUNDARY_1: Final = re.compile(r"([A-Z]+)([A-Z][a-z])")
_IDENTIFIER_BOUNDARY_2: Final = re.compile(r"([a-z0-9])([A-Z])")
_SEPARATORS: Final = re.compile(r"[^A-Za-z0-9]+")


def _snake_case(value: str) -> str:
    value = _IDENTIFIER_BOUNDARY_1.sub(r"\1_\2", value)
    value = _IDENTIFIER_BOUNDARY_2.sub(r"\1_\2", value)
    return _SEPARATORS.sub("_", value).strip("_").lower()


def normalize_field_name(value: str) -> str:
    """Normalize one wire field name to the inventory's snake_case vocabulary."""
    return _snake_case(value)


def normalize_capability_id(capability_id: str) -> str:
    """Canonicalize payload kinds and field paths to dotted snake_case IDs."""
    if not isinstance(capability_id, str) or not capability_id.strip():
        raise ValueError("capability id must be a non-empty string")
    parts = capability_id.strip().split(".")
    if any(not part.strip() for part in parts):
        raise ValueError(f"invalid capability id {capability_id!r}: empty path segment")
    normalized_parts = tuple(_snake_case(part.strip()) for part in parts)
    if any(not part for part in normalized_parts):
        raise ValueError(f"invalid capability id {capability_id!r}: a path segment normalizes to empty")
    return ".".join(normalized_parts)


def normalize_capability_ids(capability_ids: Iterable[str]) -> tuple[str, ...]:
    """Return unique canonical IDs in stable order."""
    return tuple(sorted({normalize_capability_id(capability_id) for capability_id in capability_ids}))


def _read_schemas(schema_dir: Path) -> dict[str, dict[str, Any]]:
    if not schema_dir.exists() or not schema_dir.is_dir() or schema_dir.is_symlink():
        raise ValueError(f"schema directory does not exist or is not a directory: {schema_dir}")
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted(schema_dir.rglob("*.json"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise ValueError(f"schema directory contains a symbolic link: {path}")
        name = path.name.removesuffix(".schema.json").removesuffix(".json") + ".json"
        if name in schemas:
            raise ValueError(f"schema directory has duplicate normalized schema name {name!r}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"cannot read schema {path}: {error}") from error
        if not isinstance(payload, dict):
            raise ValueError(f"schema file must contain a JSON object: {path}")
        try:
            validator_for(payload).check_schema(payload)
        except Exception as error:
            raise ValueError(f"invalid JSON Schema in {path}: {error}") from error
        schemas[name] = cast("dict[str, Any]", payload)
    if "Envelope.json" not in schemas:
        raise ValueError(f"schema directory is missing Envelope.schema.json or Envelope.json: {schema_dir}")
    return schemas


def _resolve_reference(
    reference: str,
    current_file: str,
    schemas: Mapping[str, dict[str, Any]],
) -> tuple[str, object, tuple[str, ...]]:
    file_part, separator, pointer = reference.partition("#")
    if file_part.startswith(("http:", "https:", "/")):
        raise ValueError(f"remote or absolute schema reference is not allowed: {reference!r}")
    target_file = str(PurePosixPath(current_file).parent / file_part) if file_part else current_file
    target_file = str(PurePosixPath(target_file))
    while target_file.startswith("./"):
        target_file = target_file[2:]
    if target_file not in schemas:
        raise ValueError(f"schema reference {reference!r} from {current_file!r} cannot be resolved")
    value: object = schemas[target_file]
    pointer_parts: tuple[str, ...] = ()
    if separator and pointer:
        if not pointer.startswith("/"):
            raise ValueError(f"unsupported JSON Schema reference fragment: {reference!r}")
        pointer_parts = tuple(segment.replace("~1", "/").replace("~0", "~") for segment in pointer[1:].split("/"))
        for segment in pointer_parts:
            if not isinstance(value, dict) or segment not in value:
                raise ValueError(f"schema reference {reference!r} cannot be resolved")
            value = value[segment]
    return target_file, value, pointer_parts


def _category(payload_kind: str) -> str:
    if payload_kind == "attachment":
        return "attachment"
    if payload_kind in {"parameter_type", "undefined_parameter_type"}:
        return "parameter"
    if payload_kind == "meta":
        return "metadata"
    if payload_kind == "hook" or payload_kind.startswith("test_run_hook_"):
        return "hook"
    if payload_kind.startswith(("test_run_", "test_case_", "test_step_")):
        return "lifecycle"
    return "core"


def build_capability_inventory(schema_dir: Path, *, baseline_release: str) -> tuple[MessageCapability, ...]:
    """Walk payload schemas and return one capability per stable dotted field path."""
    if not baseline_release.strip():
        raise ValueError("baseline release must be a non-empty name")
    schemas = _read_schemas(schema_dir)
    envelope_properties = schemas["Envelope.json"].get("properties")
    if not isinstance(envelope_properties, dict):
        raise ValueError("Envelope schema must define a properties object")

    capabilities: dict[str, MessageCapability] = {}

    def walk(
        schema: object,
        schema_file: str,
        payload_kind: str,
        path_parts: tuple[str, ...],
        schema_pointer_parts: tuple[str, ...],
        reference_stack: frozenset[tuple[str, str]],
    ) -> None:
        if not isinstance(schema, dict):
            return
        reference = schema.get("$ref")
        if isinstance(reference, str):
            target_file, target_schema, target_pointer_parts = _resolve_reference(reference, schema_file, schemas)
            ref_key = (target_file, reference.partition("#")[2])
            if ref_key not in reference_stack:
                walk(
                    target_schema,
                    target_file,
                    payload_kind,
                    path_parts,
                    target_pointer_parts,
                    reference_stack | {ref_key},
                )

        properties = schema.get("properties")
        if isinstance(properties, dict):
            for raw_name in sorted(properties):
                if not isinstance(raw_name, str) or not raw_name:
                    raise ValueError(f"schema property names must be non-empty strings in {schema_file}")
                field_name = _snake_case(raw_name)
                child_path = (*path_parts, field_name)
                capability_id = normalize_capability_id(".".join((payload_kind, *child_path)))
                child_schema = properties[raw_name]
                description = child_schema.get("description") if isinstance(child_schema, dict) else None
                if not isinstance(description, str) or not description.strip():
                    description = f"Cucumber Messages {baseline_release} field {capability_id}."
                pointer_parts = (*schema_pointer_parts, "properties", raw_name)
                pointer = "/".join(part.replace("~", "~0").replace("/", "~1") for part in pointer_parts)
                source_reference = f"{schema_file}#/{pointer}"
                candidate = MessageCapability(
                    capability_id=capability_id,
                    baseline_release=baseline_release,
                    name=" ".join(part.replace("_", " ") for part in child_path).title(),
                    description=description.strip(),
                    category=cast("Any", _category(payload_kind)),
                    affects=frozenset({"emitted_envelope_payload"}),
                    source_reference=source_reference,
                )
                existing = capabilities.get(capability_id)
                if existing is None or candidate.source_reference < existing.source_reference:
                    capabilities[capability_id] = candidate
                walk(
                    child_schema,
                    schema_file,
                    payload_kind,
                    child_path,
                    (*schema_pointer_parts, "properties", raw_name),
                    reference_stack,
                )

        items = schema.get("items")
        if items is not None:
            walk(items, schema_file, payload_kind, path_parts, (*schema_pointer_parts, "items"), reference_stack)
        for keyword in ("allOf", "anyOf", "oneOf"):
            alternatives = schema.get(keyword)
            if isinstance(alternatives, list):
                for index, alternative in enumerate(alternatives):
                    walk(
                        alternative,
                        schema_file,
                        payload_kind,
                        path_parts,
                        (*schema_pointer_parts, keyword, str(index)),
                        reference_stack,
                    )

    for raw_payload_kind, payload_schema in sorted(envelope_properties.items()):
        if not isinstance(raw_payload_kind, str):
            raise ValueError("Envelope schema payload names must be strings")
        payload_kind = _snake_case(raw_payload_kind)
        walk(payload_schema, "Envelope.json", payload_kind, (), (), frozenset())

    return tuple(capabilities[key] for key in sorted(capabilities))


def sync_capability_inventory(
    baseline_release: str,
    source_entries: Iterable[MessageCapability],
) -> tuple[MessageCapability, ...]:
    """Normalize, deduplicate, version, and sort capability records."""
    if not baseline_release.strip():
        raise ValueError("baseline release must be a non-empty name")
    grouped: dict[str, list[MessageCapability]] = {}
    for entry in source_entries:
        capability_id = normalize_capability_id(entry.capability_id)
        grouped.setdefault(capability_id, []).append(entry)

    synchronized: dict[str, MessageCapability] = {}
    for capability_id, entries in grouped.items():
        explicit_relevance = {entry.explicit_relevance for entry in entries if entry.explicit_relevance is not None}
        categories = {entry.category for entry in entries}
        if len(explicit_relevance) > 1:
            raise ValueError(f"duplicate capability {capability_id!r} has conflicting relevance classifications")
        if len(categories) > 1:
            raise ValueError(f"duplicate capability {capability_id!r} has conflicting categories")
        selected = min(
            entries,
            key=lambda entry: (
                entry.source_reference,
                entry.name,
                entry.description,
                tuple(sorted(entry.affects)),
            ),
        )
        synchronized[capability_id] = MessageCapability(
            capability_id=capability_id,
            baseline_release=baseline_release,
            name=selected.name,
            description=selected.description,
            category=selected.category,
            affects=frozenset().union(*(entry.affects for entry in entries)),
            source_reference=selected.source_reference,
            explicit_relevance=next(iter(explicit_relevance), None),
        )
    return tuple(synchronized[key] for key in sorted(synchronized))


def capabilities_from_json(payload: object) -> tuple[MessageCapability, ...]:
    """Parse the stable JSON artifact emitted by capability inventory sync."""
    if not isinstance(payload, dict) or not isinstance(payload.get("capabilities"), list):
        raise ValueError("capability inventory must be an object with a 'capabilities' array")
    baseline_release = payload.get("baseline_release")
    if not isinstance(baseline_release, str) or not baseline_release.strip():
        raise ValueError("capability inventory is missing baseline_release")
    inventory_version = payload.get("inventory_version", 1)
    if not isinstance(inventory_version, int) or isinstance(inventory_version, bool) or inventory_version != 1:
        raise ValueError(f"unsupported capability inventory version: {inventory_version!r}")
    entries: list[MessageCapability] = []
    valid_categories = {"core", "lifecycle", "hook", "attachment", "parameter", "metadata"}
    for index, item in enumerate(payload["capabilities"]):
        if not isinstance(item, dict):
            raise ValueError(f"capability {index + 1} must be a JSON object")
        capability_id = item.get("capability_id")
        category = item.get("category", "core")
        affects = item.get("affects", ["emitted_envelope_payload"])
        entry_baseline = item.get("baseline_release", baseline_release)
        if not isinstance(capability_id, str):
            raise ValueError(f"capability {index + 1} is missing string capability_id")
        if entry_baseline != baseline_release:
            raise ValueError(f"capability {capability_id!r} has a different baseline_release")
        if not isinstance(category, str) or category not in valid_categories:
            raise ValueError(f"capability {capability_id!r} has unknown category {category!r}")
        if not isinstance(affects, list) or any(not isinstance(value, str) for value in affects):
            raise ValueError(f"capability {capability_id!r} affects must be an array of strings")
        unknown_impacts = sorted(set(affects) - RELEVANT_IMPACTS)
        if unknown_impacts:
            raise ValueError(f"capability {capability_id!r} has unknown affects values: {', '.join(unknown_impacts)}")
        name = item.get("name", capability_id)
        description = item.get("description", "")
        source_reference = item.get("source_reference", "")
        explicit_relevance = item.get("explicit_relevance", item.get("relevance"))
        if explicit_relevance == "relevant":
            explicit_relevance = "relevant"
        elif explicit_relevance == "out_of_scope":
            explicit_relevance = "out_of_scope"
        elif explicit_relevance is not None:
            raise ValueError(f"capability {capability_id!r} has invalid relevance {explicit_relevance!r}")
        if not all(isinstance(value, str) for value in (name, description, source_reference)):
            raise ValueError(f"capability {capability_id!r} has non-string metadata")
        entries.append(
            MessageCapability(
                capability_id=normalize_capability_id(capability_id),
                baseline_release=baseline_release,
                name=name,
                description=description,
                category=cast("Any", category),
                affects=frozenset(affects),
                source_reference=source_reference,
                explicit_relevance=cast("Any", explicit_relevance),
            )
        )
    return sync_capability_inventory(baseline_release, entries)


def capability_inventory_to_dict(
    capabilities: Iterable[MessageCapability],
    *,
    baseline_release: str,
) -> dict[str, object]:
    """Serialize an inventory with stable ordering and explicit baseline metadata."""
    records: list[dict[str, object]] = []
    for capability in sync_capability_inventory(baseline_release, capabilities):
        record: dict[str, object] = {
            "affects": sorted(capability.affects),
            "baseline_release": baseline_release,
            "capability_id": capability.capability_id,
            "category": capability.category,
            "description": capability.description,
            "name": capability.name,
            "relevance": capability.relevance,
            "source_reference": capability.source_reference,
        }
        if capability.explicit_relevance is not None:
            record["explicit_relevance"] = capability.explicit_relevance
        records.append(record)
    return {
        "baseline_release": baseline_release,
        "capabilities": records,
        "inventory_version": 1,
        "summary": {
            "total": len(records),
            "relevant": sum(item["relevance"] == "relevant" for item in records),
            "out_of_scope": sum(item["relevance"] == "out_of_scope" for item in records),
        },
    }


__all__ = [
    "build_capability_inventory",
    "capabilities_from_json",
    "capability_inventory_to_dict",
    "normalize_capability_id",
    "normalize_capability_ids",
    "normalize_field_name",
    "sync_capability_inventory",
]
