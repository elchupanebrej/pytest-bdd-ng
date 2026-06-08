"""
Provide message governance checklist helpers.

Responsibility:
    Provide message governance checklist helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_governance_checklist` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - GovernanceChecklistEntry: owns nested behavior below this boundary
    - GovernanceChecklist: owns nested behavior below this boundary
    - _decision_index: owns nested behavior below this boundary
    - build_governance_checklist: owns nested behavior below this boundary
    - render_checklist_markdown: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
      `message_governance_checklist`

State and side effects:
    mutates delta, disposition, status, comment, comment_required; depends on __future__.annotations,
    typing.TYPE_CHECKING, typing.Final, typing.Literal, attrs.frozen.

Invariants:
    - `pytest_bdd.model.message_governance_checklist` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Literal

from attrs import frozen

from .message_capability import MessageCapability, capability_is_relevant
from .message_status_governance import (
    NON_IMPLEMENTED_STATUSES,
    CapabilityDecision,
    CapabilityStatus,
    evaluate_release_blockers,
    is_release_blocker_status,
    normalize_capability_status,
)

if TYPE_CHECKING:
    from .message_baseline_diff import BaselineDiffRecord

DEFAULT_CHECKLIST_NAME: Final[str] = "message-status-governance"
ChecklistDelta = Literal["unchanged", "added", "changed", "removed"]
ChecklistDisposition = Literal["approved", "blocked", "deferred"]


@frozen
class GovernanceChecklistEntry:
    """
    Record governance result for a single capability.

    Responsibility:
        Record governance result for a single capability. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_governance_checklist.GovernanceChecklistEntry` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `GovernanceChecklistEntry`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `GovernanceChecklistEntry`

    State and side effects:
        mutates capability_id, status, comment_required, comment, release_blocker.

    Invariants:
        - `pytest_bdd.model.message_governance_checklist.GovernanceChecklistEntry` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    capability_id: str
    status: CapabilityStatus
    comment_required: bool
    comment: str | None
    release_blocker: bool
    delta: ChecklistDelta
    disposition: ChecklistDisposition


@frozen
class GovernanceChecklist:
    """
    Consolidate capability governance entries into a checklist.

    Responsibility:
        Consolidate capability governance entries into a checklist. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_governance_checklist.GovernanceChecklist`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `GovernanceChecklist`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `GovernanceChecklist`

    State and side effects:
        mutates checklist_name, entries, unresolved_blockers.

    Invariants:
        - `pytest_bdd.model.message_governance_checklist.GovernanceChecklist` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    checklist_name: str
    entries: tuple[GovernanceChecklistEntry, ...]
    unresolved_blockers: int


def _decision_index(decisions: list[CapabilityDecision]) -> dict[str, CapabilityDecision]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_governance_checklist._decision_index` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_governance_checklist._decision_index`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `_decision_index`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return {decision.capability_id: decision for decision in decisions}


def build_governance_checklist(  # noqa: PLR0914
    capabilities: list[MessageCapability],
    decisions: list[CapabilityDecision],
    *,
    checklist_name: str = DEFAULT_CHECKLIST_NAME,
    baseline_diff: BaselineDiffRecord | None = None,
) -> GovernanceChecklist:
    """
    Evaluate each relevant capability against its corresponding decisions and generate a release governance checklist.

    Returns:
        A GovernanceChecklist containing per-capability disposition entries and the total count of unresolved blockers.

    Responsibility:
        Evaluate each relevant capability against its corresponding decisions and generate a release governance
        checklist. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_governance_checklist.build_governance_checklist` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - set: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - _decision_index: collaborator call used by this boundary
        - capability_is_relevant: collaborator call used by this boundary
        - evaluate_release_blockers: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `build_governance_checklist`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `build_governance_checklist`

    State and side effects:
        mutates delta, disposition, status, comment, index.

    Invariants:
        - `pytest_bdd.model.message_governance_checklist.build_governance_checklist` keeps its documented import path,
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
        #arch-eval:locational_stability=3

    """
    index = _decision_index(decisions)
    added = set(baseline_diff.added_capability_ids) if baseline_diff is not None else set()
    changed = set(baseline_diff.changed_capability_ids) if baseline_diff is not None else set()
    removed = set(baseline_diff.removed_capability_ids) if baseline_diff is not None else set()

    relevant_ids = [capability.capability_id for capability in capabilities if capability_is_relevant(capability)]
    blocker_evaluation = evaluate_release_blockers(decisions, relevant_capability_ids=tuple(relevant_ids))
    blocker_ids = set(blocker_evaluation.unresolved_blocker_capability_ids)
    deferred_ids = set(blocker_evaluation.deferred_capability_ids)

    entries: list[GovernanceChecklistEntry] = []

    for capability_id in sorted(set(relevant_ids).union(removed)):
        decision = index.get(capability_id)
        if decision is None:
            status: CapabilityStatus = "Pending"
            comment: str | None = (
                "Decision is missing" if capability_id not in removed else "Capability removed from baseline"
            )
        else:
            status = normalize_capability_status(decision.status) or "Pending"
            comment = decision.rationale

        if capability_id in removed:
            delta: ChecklistDelta = "removed"
        elif capability_id in added:
            delta = "added"
        elif capability_id in changed:
            delta = "changed"
        else:
            delta = "unchanged"

        comment_required = status in NON_IMPLEMENTED_STATUSES
        release_blocker = capability_id in blocker_ids or (
            capability_id not in removed and is_release_blocker_status(status)
        )
        if capability_id in deferred_ids:
            disposition: ChecklistDisposition = "deferred"
        elif release_blocker:
            disposition = "blocked"
        else:
            disposition = "approved"

        entries.append(
            GovernanceChecklistEntry(
                capability_id=capability_id,
                status=status,
                comment_required=comment_required,
                comment=comment,
                release_blocker=release_blocker,
                delta=delta,
                disposition=disposition,
            ),
        )

    unresolved_blockers = blocker_evaluation.blocker_count
    return GovernanceChecklist(
        checklist_name=checklist_name,
        entries=tuple(entries),
        unresolved_blockers=unresolved_blockers,
    )


def render_checklist_markdown(checklist: GovernanceChecklist) -> str:
    """
    Render a governance checklist as a human-readable markdown table, suitable for inclusion in release documentation.

    Returns:
        A markdown-formatted string with a table of capabilities, dispositions, and a final blocker count.

    Responsibility:
        Render a governance checklist as a human-readable markdown table, suitable for inclusion in release
        documentation. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_governance_checklist.render_checklist_markdown` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - lines.extend: collaborator call used by this boundary
        - str.lower: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - join: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `render_checklist_markdown`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `render_checklist_markdown`

    State and side effects:
        mutates lines.

    Invariants:
        - `pytest_bdd.model.message_governance_checklist.render_checklist_markdown` keeps its documented import path,
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
        #arch-eval:locational_stability=3

    """
    lines = [
        f"# {checklist.checklist_name}",
        "",
        "| Capability ID | Status | Delta | Disposition | Comment Required | Release Blocker |",
        "|---------------|--------|-------|-------------|------------------|-----------------|",
    ]
    lines.extend(
        "| "
        f"{entry.capability_id} | {entry.status} | {entry.delta} | {entry.disposition} | "
        f"{str(entry.comment_required).lower()} | {str(entry.release_blocker).lower()} |"
        for entry in checklist.entries
    )
    lines.extend(("", f"Unresolved blockers: {checklist.unresolved_blockers}"))
    return "\n".join(lines)
