from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .message_capability import MessageCapability, capability_is_relevant

SCHEMA_RELATIVE_DIR = Path("messages") / "jsonschema" / "src"


@dataclass(frozen=True, slots=True)
class CapabilitySyncResult:
    total_relevant: int
    total_out_of_scope: int
    duplicate_capability_ids: tuple[str, ...]
    capabilities: tuple[MessageCapability, ...]


def _envelope_path(schema_dir: Path) -> Path:
    return schema_dir / "Envelope.json"


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
    candidates: list[Path] = []
    if preferred is not None:
        candidates.append(preferred)

    candidates.extend(
        (
            Path.cwd() / SCHEMA_RELATIVE_DIR,
            Path(__file__).resolve().parents[3] / SCHEMA_RELATIVE_DIR,
        )
    )

    git_candidate = _schema_dir_from_git_root()
    if git_candidate is not None:
        candidates.append(git_candidate)

    for candidate in candidates:
        resolved = candidate.resolve()
        if _envelope_path(resolved).is_file():
            return resolved

    paths = ", ".join(str(path.resolve()) for path in candidates)
    msg = f"Unable to resolve messages schema directory with Envelope.json. Checked: {paths}"
    raise FileNotFoundError(msg)


def load_envelope_schema(schema_dir: Path | None = None) -> tuple[Path, dict[str, Any]]:
    resolved_schema_dir = resolve_messages_schema_dir(schema_dir)
    envelope_path = _envelope_path(resolved_schema_dir)
    return resolved_schema_dir, json.loads(envelope_path.read_text(encoding="utf-8"))


def sync_capability_inventory(
    baseline_release: str,
    source_entries: list[MessageCapability],
) -> CapabilitySyncResult:
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
            )
        )

    total_relevant = sum(1 for capability in synchronized if capability_is_relevant(capability))
    total_out_of_scope = len(synchronized) - total_relevant

    return CapabilitySyncResult(
        total_relevant=total_relevant,
        total_out_of_scope=total_out_of_scope,
        duplicate_capability_ids=tuple(sorted(duplicates)),
        capabilities=tuple(synchronized),
    )
