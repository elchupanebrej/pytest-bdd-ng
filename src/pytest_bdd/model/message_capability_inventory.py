from __future__ import annotations

from dataclasses import dataclass

from .message_capability import MessageCapability, capability_is_relevant


@dataclass(frozen=True, slots=True)
class CapabilitySyncResult:
    total_relevant: int
    total_out_of_scope: int
    duplicate_capability_ids: tuple[str, ...]
    capabilities: tuple[MessageCapability, ...]


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
