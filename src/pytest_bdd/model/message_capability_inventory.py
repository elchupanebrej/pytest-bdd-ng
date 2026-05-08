"""Provide message capability inventory helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable  # noqa: TC003
from pathlib import Path
from typing import cast

from attrs import frozen

from pytest_bdd.types.json import JSONObject

from .message_capability import MessageCapability, capability_is_relevant

SCHEMA_RELATIVE_DIR = Path("messages") / "jsonschema" / "src"
PACKAGE_SCHEMA_RELATIVE_DIR = Path("message_jsonschema")


@frozen
class CapabilitySyncResult:
    """Represent capability sync result state."""

    total_relevant: int
    total_out_of_scope: int
    duplicate_capability_ids: tuple[str, ...]
    capabilities: tuple[MessageCapability, ...]


@frozen
class MandatoryScopeReconciliation:
    """Represent mandatory scope reconciliation state."""

    inventory_capability_ids: tuple[str, ...]
    mandatory_capability_ids: tuple[str, ...]
    missing_mandatory_capability_ids: tuple[str, ...]

    @property
    def mandatory_total(self) -> int:
        """Handle mandatory total."""
        return len(self.mandatory_capability_ids)

    @property
    def inventory_total(self) -> int:
        """Handle inventory total."""
        return len(self.inventory_capability_ids)

    @property
    def has_missing_mandatory_capabilities(self) -> bool:
        """Return missing mandatory capabilities."""
        return bool(self.missing_mandatory_capability_ids)


@frozen
class CoverageScopeReconciliation:
    """Represent coverage scope reconciliation state."""

    inventory_capability_ids: tuple[str, ...]
    runtime_required_capability_ids: tuple[str, ...]
    observed_capability_ids: tuple[str, ...]
    classified_capability_ids: tuple[str, ...]
    missing_runtime_required_capability_ids: tuple[str, ...]
    uncovered_non_runtime_unclassified_capability_ids: tuple[str, ...]

    @property
    def runtime_required_total(self) -> int:
        """Handle runtime required total."""
        return len(self.runtime_required_capability_ids)

    @property
    def runtime_required_covered(self) -> int:
        """Handle runtime required covered."""
        return self.runtime_required_total - len(self.missing_runtime_required_capability_ids)

    @property
    def runtime_required_missing(self) -> int:
        """Handle runtime required missing."""
        return len(self.missing_runtime_required_capability_ids)

    @property
    def non_runtime_required_total(self) -> int:
        """Handle non runtime required total."""
        return len(tuple(set(self.inventory_capability_ids).difference(self.runtime_required_capability_ids)))

    @property
    def non_runtime_covered(self) -> int:
        """Handle non runtime covered."""
        non_runtime_set = set(self.inventory_capability_ids).difference(self.runtime_required_capability_ids)
        observed_set = set(self.observed_capability_ids)
        return len(non_runtime_set.intersection(observed_set))

    @property
    def non_runtime_classified(self) -> int:
        """Handle non runtime classified."""
        non_runtime_set = set(self.inventory_capability_ids).difference(self.runtime_required_capability_ids)
        classified_set = set(self.classified_capability_ids)
        return len(non_runtime_set.intersection(classified_set))

    @property
    def has_unclassified_non_runtime_gaps(self) -> bool:
        """Return unclassified non runtime gaps."""
        return bool(self.uncovered_non_runtime_unclassified_capability_ids)


def _to_camel_case_identifier(value: str) -> str:
    parts = [part for part in value.split("_") if part]
    if not parts:
        return value
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _canonical_payload_kind(payload_kind: str) -> str:
    payload_kind = payload_kind.strip()
    if "_" not in payload_kind:
        return payload_kind
    return _to_camel_case_identifier(payload_kind)


def _canonical_capability_id(capability_id: str) -> str:
    if "." not in capability_id:
        return _canonical_payload_kind(capability_id)
    payload_kind, field_path = capability_id.split(".", 1)
    return f"{_canonical_payload_kind(payload_kind)}.{field_path}"


def normalize_capability_ids(capability_ids: Iterable[str]) -> tuple[str, ...]:
    """Normalize capability ids."""
    return tuple(sorted({_canonical_capability_id(capability_id) for capability_id in capability_ids}))


def reconcile_inventory_with_mandatory_scope(
    inventory_capability_ids: Iterable[str],
    mandatory_capability_ids: Iterable[str],
) -> MandatoryScopeReconciliation:
    """Handle reconcile inventory with mandatory scope."""
    normalized_inventory = normalize_capability_ids(inventory_capability_ids)
    normalized_mandatory = normalize_capability_ids(mandatory_capability_ids)
    inventory_set = set(normalized_inventory)
    mandatory_set = set(normalized_mandatory)
    missing = tuple(sorted(mandatory_set.difference(inventory_set)))
    return MandatoryScopeReconciliation(
        inventory_capability_ids=normalized_inventory,
        mandatory_capability_ids=normalized_mandatory,
        missing_mandatory_capability_ids=missing,
    )


def reconcile_runtime_scope_coverage(
    *,
    inventory_capability_ids: Iterable[str],
    runtime_required_capability_ids: Iterable[str],
    observed_capability_ids: Iterable[str],
    classified_capability_ids: Iterable[str],
) -> CoverageScopeReconciliation:
    """Handle reconcile runtime scope coverage."""
    inventory_ids = normalize_capability_ids(inventory_capability_ids)
    runtime_required_ids = normalize_capability_ids(runtime_required_capability_ids)
    observed_ids = normalize_capability_ids(observed_capability_ids)
    classified_ids = normalize_capability_ids(classified_capability_ids)

    inventory_set = set(inventory_ids)
    runtime_required_set = set(runtime_required_ids)
    observed_set = set(observed_ids)
    classified_set = set(classified_ids)

    missing_runtime_required = tuple(sorted(runtime_required_set.difference(observed_set)))
    non_runtime_ids = inventory_set.difference(runtime_required_set)
    uncovered_non_runtime = non_runtime_ids.difference(observed_set)
    uncovered_non_runtime_unclassified = tuple(sorted(uncovered_non_runtime.difference(classified_set)))

    return CoverageScopeReconciliation(
        inventory_capability_ids=inventory_ids,
        runtime_required_capability_ids=runtime_required_ids,
        observed_capability_ids=observed_ids,
        classified_capability_ids=classified_ids,
        missing_runtime_required_capability_ids=missing_runtime_required,
        uncovered_non_runtime_unclassified_capability_ids=uncovered_non_runtime_unclassified,
    )


def _envelope_path(schema_dir: Path) -> Path:
    canonical = schema_dir / "Envelope.json"
    if canonical.is_file():
        return canonical
    alt = schema_dir / "Envelope.schema.json"
    if alt.is_file():
        return alt
    return canonical


def _schema_dir_from_git_root() -> Path | None:
    roots: list[Path] = []
    for seed in (Path.cwd(), Path(__file__).resolve()):
        for parent in (seed, *seed.parents):
            if (parent / ".git").exists():
                roots.append(parent)
                break
    for root in roots:
        candidate = (root / SCHEMA_RELATIVE_DIR).resolve()
        if _envelope_path(candidate).is_file():
            return candidate
    return None


def resolve_messages_schema_dir(preferred: Path | None = None) -> Path:
    """
    Resolve messages schema dir.

    Raises:
        FileNotFoundError: If the operation cannot be completed.

    """
    candidates: list[Path] = []
    if preferred is not None:
        candidates.append(preferred)

    package_schema_dir = Path(__file__).resolve().parent / PACKAGE_SCHEMA_RELATIVE_DIR
    candidates.extend(
        (
            Path.cwd() / SCHEMA_RELATIVE_DIR,
            package_schema_dir,
            Path(__file__).resolve().parents[3] / SCHEMA_RELATIVE_DIR,
        ),
    )

    git_candidate = _schema_dir_from_git_root()
    if git_candidate is not None:
        candidates.append(git_candidate)

    for candidate in candidates:
        resolved = candidate.resolve()
        if _envelope_path(resolved).is_file():
            return resolved

    paths = ", ".join(str(path.resolve()) for path in candidates)
    msg = f"Unable to resolve messages schema directory with Envelope.json or Envelope.schema.json. Checked: {paths}"
    raise FileNotFoundError(msg)


def load_envelope_schema(schema_dir: Path | None = None) -> tuple[Path, JSONObject]:
    """Load envelope schema."""
    resolved_schema_dir = resolve_messages_schema_dir(schema_dir)
    envelope_path = _envelope_path(resolved_schema_dir)
    return resolved_schema_dir, cast(JSONObject, json.loads(envelope_path.read_text(encoding="utf-8")))


def sync_capability_inventory(
    baseline_release: str,
    source_entries: list[MessageCapability],
) -> CapabilitySyncResult:
    """Synchronize capability inventory."""
    seen: set[str] = set()
    duplicates: set[str] = set()
    synchronized: list[MessageCapability] = []

    for entry in source_entries:
        if entry.capability_id in seen:
            duplicates.add(entry.capability_id)
            continue
        seen.add(entry.capability_id)
        synchronized.append(
            MessageCapability(
                capability_id=entry.capability_id,
                baseline_release=baseline_release,
                name=entry.name,
                description=entry.description,
                category=entry.category,
                affects=entry.affects,
                source_reference=entry.source_reference,
                explicit_relevance=entry.explicit_relevance,
            ),
        )

    total_relevant = sum(1 for capability in synchronized if capability_is_relevant(capability))
    total_out_of_scope = len(synchronized) - total_relevant

    return CapabilitySyncResult(
        total_relevant=total_relevant,
        total_out_of_scope=total_out_of_scope,
        duplicate_capability_ids=tuple(sorted(duplicates)),
        capabilities=tuple(synchronized),
    )
