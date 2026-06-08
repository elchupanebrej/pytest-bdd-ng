"""
Capability detection and inventory for message capability governance.

Responsibility:
    Capability detection and inventory for message capability governance. It directly owns the observable contract,
    local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.script.message_capability_governance.capabilities` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _load_capabilities: owns nested behavior below this boundary
    - _load_capabilities_from_governance_report: owns nested behavior below this boundary
    - _load_capability_ids: owns nested behavior below this boundary
    - _validate_scope_capability_ids: owns nested behavior below this boundary
    - _validate_runtime_required_scope: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/message_capability_inventory.py: imports or references `capabilities`
    - src/pytest_bdd/model/message_governance_checklist.py: imports or references `capabilities`
    - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `capabilities`
    - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `capabilities`
    - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `capabilities`

State and side effects:
    mutates msg, payload, sample, ALLOWED_CATEGORIES, ALLOWED_IMPACTS; depends on __future__.annotations, pathlib.Path,
    typing.cast, pytest_bdd.model.coverage.inventory.canonical_capability_id,
    pytest_bdd.model.message_capability.CapabilityCategory.

Invariants:
    - `pytest_bdd.script.message_capability_governance.capabilities` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Failure semantics:
    Raises or re-raises TypeError, ValueError; callers must treat these as boundary failures.

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
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.script.message_capability_governance.capabilities._load_capabilities` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.capabilities._load_capabilities` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - item.get: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - _load_json: collaborator call used by this boundary
        - TypeError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `_load_capabilities`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `_load_capabilities`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_load_capabilities`

    State and side effects:
        mutates payload, msg, result, affects, category_raw; depends on
        pytest_bdd.script.message_capability_governance.schema._load_json.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.capabilities._load_capabilities` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises TypeError; callers must treat these as boundary failures.

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
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.script.message_capability_governance.capabilities._load_capabilities_from_governance_report` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.capabilities._load_capabilities_from_governance_report` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - TypeError: collaborator call used by this boundary
        - payload.get: collaborator call used by this boundary
        - item.get: collaborator call used by this boundary
        - _load_json: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
          `_load_capabilities_from_governance_report`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `_load_capabilities_from_governance_report`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `_load_capabilities_from_governance_report`

    State and side effects:
        mutates msg, payload, capabilities_payload, baseline_release, capabilities; depends on
        pytest_bdd.script.message_capability_governance.schema._load_json.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.capabilities._load_capabilities_from_governance_report` keeps
          its documented import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises TypeError; callers must treat these as boundary failures.

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
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.script.message_capability_governance.capabilities._load_capability_ids` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.capabilities._load_capability_ids` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - set: collaborator call used by this boundary
        - path.read_text.splitlines: collaborator call used by this boundary
        - path.read_text: collaborator call used by this boundary
        - raw_line.strip: collaborator call used by this boundary
        - line.startswith: collaborator call used by this boundary
        - capability_ids.add: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references `_load_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `_load_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `_load_capability_ids`

    State and side effects:
        mutates capability_ids, line.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.capabilities._load_capability_ids` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

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
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.script.message_capability_governance.capabilities._validate_scope_capability_ids` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.capabilities._validate_scope_capability_ids` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - reconcile_inventory_with_mandatory_scope: collaborator call used by this boundary
        - list: collaborator call used by this boundary
        - join: collaborator call used by this boundary
        - ValueError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
          `_validate_scope_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `_validate_scope_capability_ids`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `_validate_scope_capability_ids`

    State and side effects:
        mutates reconciliation, unknown_ids, sample, msg.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.capabilities._validate_scope_capability_ids` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.script.message_capability_governance.capabilities._validate_runtime_required_scope` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.script.message_capability_governance.capabilities._validate_runtime_required_scope` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - sorted: collaborator call used by this boundary
        - set.difference: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - join: collaborator call used by this boundary
        - ValueError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/__init__.py: imports or references
          `_validate_runtime_required_scope`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `_validate_runtime_required_scope`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `_validate_runtime_required_scope`

    State and side effects:
        mutates out_of_scope, sample, msg.

    Invariants:
        - `pytest_bdd.script.message_capability_governance.capabilities._validate_runtime_required_scope` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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
    if not mandatory_capability_ids:
        return
    out_of_scope = sorted(set(runtime_required_capability_ids).difference(mandatory_capability_ids))
    if out_of_scope:
        sample = ", ".join(out_of_scope[:10])
        msg = f"runtime-required capability file contains IDs outside mandatory scope (first 10): {sample}"
        raise ValueError(msg)
