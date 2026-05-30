"""Capability detection and inventory for message capability governance."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from pytest_bdd.model.coverage.inventory import canonical_capability_id
from pytest_bdd.model.message_capability import (
    CapabilityCategory,
    CapabilityImpact,
    CapabilityRelevance,
    MessageCapability,
)
from pytest_bdd.model.message_capability_inventory import (
    reconcile_inventory_with_mandatory_scope,
)

ALLOWED_CATEGORIES: set[str] = {"core", "lifecycle", "hook", "attachment", "parameter", "metadata"}
ALLOWED_IMPACTS: set[str] = {
    "emitted_envelope_payload",
    "lifecycle_linkage",
    "status_mapping",
    "governance_checklist_output",
}
ALLOWED_RELEVANCE: set[str] = {"relevant", "out_of_scope"}


def _load_capabilities(path: Path) -> list[MessageCapability]:
    from pytest_bdd.script.message_capability_governance.schema import _load_json

    payload = _load_json(path)
    if not isinstance(payload, list):
        msg = f"Expected capability list in {path}"
        raise TypeError(msg)

    result: list[MessageCapability] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        affects = item.get("affects") or []
        category_raw = str(item.get("category", "core"))
        category: CapabilityCategory = cast(
            "CapabilityCategory",
            category_raw if category_raw in ALLOWED_CATEGORIES else "core",
        )
        explicit_relevance_raw = item.get("explicit_relevance")
        explicit_relevance: CapabilityRelevance | None = (
            cast("CapabilityRelevance", explicit_relevance_raw)
            if isinstance(explicit_relevance_raw, str) and explicit_relevance_raw in ALLOWED_RELEVANCE
            else None
        )
        validated_affects = frozenset(
            cast("CapabilityImpact", effect_text)
            for effect in affects
            for effect_text in (str(effect),)
            if effect_text in ALLOWED_IMPACTS
        )
        result.append(
            MessageCapability(
                capability_id=str(item["capability_id"]),
                baseline_release=str(item.get("baseline_release", "")),
                name=str(item.get("name", "")),
                description=str(item.get("description", "")),
                category=category,
                affects=validated_affects,
                source_reference=str(item.get("source_reference", "")),
                explicit_relevance=explicit_relevance,
            ),
        )
    return result


def _load_capabilities_from_governance_report(path: Path) -> list[MessageCapability]:
    from pytest_bdd.script.message_capability_governance.schema import _load_json

    payload = _load_json(path)
    if not isinstance(payload, dict):
        msg = f"Expected governance report object in {path}"
        raise TypeError(msg)
    capabilities_payload = payload.get("capabilities")
    if not isinstance(capabilities_payload, list):
        msg = f"Expected governance report capability list in {path}"
        raise TypeError(msg)

    baseline_release = str(payload.get("baseline_release", "unknown"))
    capabilities: list[MessageCapability] = []
    for item in capabilities_payload:
        if not isinstance(item, dict):
            continue
        capability_id = str(item.get("capability_id", ""))
        if not capability_id:
            continue
        capabilities.append(
            MessageCapability(
                capability_id=capability_id,
                baseline_release=baseline_release,
                name=capability_id,
                description=str(item.get("rationale") or capability_id),
                category="core",
                affects=frozenset({"emitted_envelope_payload"}),
                source_reference="generated-governance-report",
                explicit_relevance="relevant",
            ),
        )
    return capabilities


def _load_capability_ids(path: Path) -> set[str]:
    capability_ids: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        capability_ids.add(canonical_capability_id(line))
    return capability_ids


def _validate_scope_capability_ids(
    capability_ids: set[str],
    inventory_capability_ids: set[str],
    *,
    scope_name: str,
) -> None:
    reconciliation = reconcile_inventory_with_mandatory_scope(
        inventory_capability_ids=inventory_capability_ids,
        mandatory_capability_ids=capability_ids,
    )
    unknown_ids = list(reconciliation.missing_mandatory_capability_ids)
    if unknown_ids:
        sample = ", ".join(unknown_ids[:10])
        msg = f"{scope_name} file contains unknown capability IDs (first 10): {sample}"
        raise ValueError(msg)


def _validate_runtime_required_scope(
    *,
    runtime_required_capability_ids: set[str],
    mandatory_capability_ids: set[str],
) -> None:
    if not mandatory_capability_ids:
        return
    out_of_scope = sorted(set(runtime_required_capability_ids).difference(mandatory_capability_ids))
    if out_of_scope:
        sample = ", ".join(out_of_scope[:10])
        msg = f"runtime-required capability file contains IDs outside mandatory scope (first 10): {sample}"
        raise ValueError(msg)
