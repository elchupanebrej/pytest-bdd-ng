"""
Provide message status governance helpers.

Responsibility:
    Provide message status governance helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_status_governance` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - CapabilityDecision: owns nested behavior below this boundary
    - DecisionValidationResult: owns nested behavior below this boundary
    - StatusUniquenessResult: owns nested behavior below this boundary
    - BlockerEvaluationResult: owns nested behavior below this boundary
    - _is_non_empty_text: owns nested behavior below this boundary
    - normalize_capability_status: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `message_status_governance`
    - src/pytest_bdd/message_stream_validation/status.py: imports or references `message_status_governance`
    - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
      `message_status_governance`
    - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
      `message_status_governance`
    - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
      `message_status_governance`

State and side effects:
    mutates status, rationale, hard_limitation, accepted, violations; depends on __future__.annotations,
    typing.TYPE_CHECKING, typing.Final, typing.Literal, attrs.frozen.

Invariants:
    - `pytest_bdd.model.message_status_governance` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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

from typing import TYPE_CHECKING, Final, Literal

from attrs import frozen

if TYPE_CHECKING:
    from datetime import datetime

CapabilityStatus = Literal[
    "Implemented",
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
]
LegacyCapabilityStatus = Literal[
    "done",
    "partly-applicable",
    "partially-applicable",
    "non-implementable",
    "not-acceptable",
    "not-applicable",
    "pending",
]
CapabilityStatusLike = CapabilityStatus | LegacyCapabilityStatus | str

CAPABILITY_STATUSES: Final[tuple[CapabilityStatus, ...]] = (
    "Implemented",
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
)

NON_IMPLEMENTED_STATUSES: Final[set[CapabilityStatus]] = {
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
    "Pending",
}

MANDATORY_SCOPE_FORBIDDEN_STATUSES: Final[set[CapabilityStatus]] = {
    "Partly-Applicable",
    "Non-Implementable",
    "Not-Acceptable",
    "Not-Applicable",
}

MANDATORY_EVIDENCE_FIELDS: Final[tuple[str, ...]] = (
    "rationale",
    "decision_owner",
    "evidence_refs",
    "reviewed_at",
)

NON_IMPLEMENTABLE_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "recheck_trigger",
    "hard_limitation",
)

FORBIDDEN_NON_IMPLEMENTABLE_PATTERNS: Final[tuple[str, ...]] = (
    "not implemented yet",
    "future work",
    "not observed in this test only",
)

RELEASE_BLOCKER_STATUSES: Final[set[CapabilityStatus]] = {
    "Pending",
    "Not-Acceptable",
}

LEGACY_STATUS_ALIASES: Final[dict[str, CapabilityStatus]] = {
    "done": "Implemented",
    "partly-applicable": "Partly-Applicable",
    "partially-applicable": "Partly-Applicable",
    "non-implementable": "Non-Implementable",
    "not-acceptable": "Not-Acceptable",
    "not-applicable": "Not-Applicable",
    "pending": "Pending",
}


@frozen
class CapabilityDecision:
    """
    Represent a recorded implementation decision for a specific cucumber-messages capability.

    Responsibility:
        Represent a recorded implementation decision for a specific cucumber-messages capability. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_status_governance.CapabilityDecision`
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
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `CapabilityDecision`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `CapabilityDecision`
        - src/pytest_bdd/model/__init__.py: imports or references `CapabilityDecision`
        - src/pytest_bdd/model/message_governance_checklist.py: imports or references `CapabilityDecision`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `CapabilityDecision`

    State and side effects:
        mutates capability_id, status, release_target, rationale, hard_limitation.

    Invariants:
        - `pytest_bdd.model.message_status_governance.CapabilityDecision` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    capability_id: str
    status: CapabilityStatus
    release_target: str
    rationale: str | None = None
    hard_limitation: str | None = None
    decision_owner: str | None = None
    evidence_refs: tuple[str, ...] = ()
    reviewed_at: datetime | None = None
    recheck_trigger: str | None = None


@frozen
class DecisionValidationResult:
    """
    Hold the outcome of validating a capability decision against governance policies.

    Responsibility:
        Hold the outcome of validating a capability decision against governance policies. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_status_governance.DecisionValidationResult`
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
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `DecisionValidationResult`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `DecisionValidationResult`
        - src/pytest_bdd/model/__init__.py: imports or references `DecisionValidationResult`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `DecisionValidationResult`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `DecisionValidationResult`

    State and side effects:
        mutates accepted, missing_required_evidence_fields, violations.

    Invariants:
        - `pytest_bdd.model.message_status_governance.DecisionValidationResult` keeps its documented import path,
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
        #arch-eval:locational_stability=4
    """

    accepted: bool
    missing_required_evidence_fields: tuple[str, ...]
    violations: tuple[str, ...]


@frozen
class StatusUniquenessResult:
    """
    Indicate whether all provided capability decisions are uniquely assigned per target release.

    Responsibility:
        Indicate whether all provided capability decisions are uniquely assigned per target release. It directly owns
        the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_status_governance.StatusUniquenessResult`
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
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `StatusUniquenessResult`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `StatusUniquenessResult`
        - src/pytest_bdd/model/__init__.py: imports or references `StatusUniquenessResult`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `StatusUniquenessResult`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `StatusUniquenessResult`

    State and side effects:
        mutates is_unique, duplicates.

    Invariants:
        - `pytest_bdd.model.message_status_governance.StatusUniquenessResult` keeps its documented import path,
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
        #arch-eval:locational_stability=4
    """

    is_unique: bool
    duplicates: tuple[str, ...]


@frozen
class BlockerEvaluationResult:
    """
    Summarize any release-blocking capability states based on current implementation decisions.

    Responsibility:
        Summarize any release-blocking capability states based on current implementation decisions. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_status_governance.BlockerEvaluationResult`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - blocker_count: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `BlockerEvaluationResult`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `BlockerEvaluationResult`
        - src/pytest_bdd/model/__init__.py: imports or references `BlockerEvaluationResult`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `BlockerEvaluationResult`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `BlockerEvaluationResult`

    State and side effects:
        mutates unresolved_blocker_capability_ids, deferred_capability_ids, missing_decision_capability_ids.

    Invariants:
        - `pytest_bdd.model.message_status_governance.BlockerEvaluationResult` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    unresolved_blocker_capability_ids: tuple[str, ...]
    deferred_capability_ids: tuple[str, ...]
    missing_decision_capability_ids: tuple[str, ...]

    @property
    def blocker_count(self) -> int:
        """
        Calculate the total number of unresolved blocker capabilities.

        Returns:
            The integer count of unresolved blockers.

        Responsibility:
            Calculate the total number of unresolved blocker capabilities. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_status_governance.BlockerEvaluationResult.blocker_count` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `blocker_count`
            - src/pytest_bdd/message_stream_validation/status.py: imports or references `blocker_count`
            - src/pytest_bdd/model/message_governance_checklist.py: imports or references `blocker_count`
            - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `blocker_count`
            - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `blocker_count`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        return len(self.unresolved_blocker_capability_ids)


def _is_non_empty_text(value: object) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_status_governance._is_non_empty_text` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_status_governance._is_non_empty_text`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - bool: collaborator call used by this boundary
        - value.strip: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_is_non_empty_text`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `_is_non_empty_text`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `_is_non_empty_text`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references `_is_non_empty_text`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `_is_non_empty_text`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    return isinstance(value, str) and bool(value.strip())


def normalize_capability_status(status: CapabilityStatusLike) -> CapabilityStatus | None:
    """
    Standardize a raw status string into a recognized CapabilityStatus, handling legacy aliases.

    Returns:
        The normalized CapabilityStatus, or None if the status string is unrecognized.

    Responsibility:
        Standardize a raw status string into a recognized CapabilityStatus, handling legacy aliases. It directly owns
        the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_status_governance.normalize_capability_status` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - CAPABILITY_STATUSES.index: collaborator call used by this boundary
        - LEGACY_STATUS_ALIASES.get: collaborator call used by this boundary
        - str.strip.lower: collaborator call used by this boundary
        - str.strip: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `normalize_capability_status`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `normalize_capability_status`
        - src/pytest_bdd/model/__init__.py: imports or references `normalize_capability_status`
        - src/pytest_bdd/model/message_governance_checklist.py: imports or references `normalize_capability_status`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `normalize_capability_status`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    if status in CAPABILITY_STATUSES:
        return CAPABILITY_STATUSES[CAPABILITY_STATUSES.index(status)]
    return LEGACY_STATUS_ALIASES.get(str(status).strip().lower())


def missing_required_evidence_fields(decision: CapabilityDecision) -> tuple[str, ...]:
    """
    Identify which mandatory evidence fields are missing for a given decision, based on its status.

    Returns:
        A tuple of string field names that require population.

    Responsibility:
        Identify which mandatory evidence fields are missing for a given decision, based on its status. It directly owns
        the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_status_governance.missing_required_evidence_fields` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - missing.append: collaborator call used by this boundary
        - _is_non_empty_text: collaborator call used by this boundary
        - normalize_capability_status: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `missing_required_evidence_fields`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `missing_required_evidence_fields`
        - src/pytest_bdd/model/__init__.py: imports or references `missing_required_evidence_fields`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `missing_required_evidence_fields`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `missing_required_evidence_fields`

    State and side effects:
        mutates status, missing.

    Invariants:
        - `pytest_bdd.model.message_status_governance.missing_required_evidence_fields` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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
    status = normalize_capability_status(decision.status)
    if status is None or status not in NON_IMPLEMENTED_STATUSES:
        return ()

    missing: list[str] = []
    if not _is_non_empty_text(decision.rationale):
        missing.append("rationale")
    if not _is_non_empty_text(decision.decision_owner):
        missing.append("decision_owner")
    if not decision.evidence_refs:
        missing.append("evidence_refs")
    if decision.reviewed_at is None:
        missing.append("reviewed_at")
    if status == "Non-Implementable":
        if not _is_non_empty_text(decision.recheck_trigger):
            missing.append("recheck_trigger")
        if not _is_non_empty_text(decision.hard_limitation):
            missing.append("hard_limitation")
    return tuple(missing)


def validate_non_implementable_policy(decision: CapabilityDecision) -> tuple[str, ...]:
    """
    Check if a 'Non-Implementable' decision violates policy by using forbidden rationale patterns.

    Returns:
        A tuple of violation message strings, empty if compliant.

    Responsibility:
        Check if a 'Non-Implementable' decision violates policy by using forbidden rationale patterns. It directly owns
        the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_status_governance.validate_non_implementable_policy` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - normalize_capability_status: collaborator call used by this boundary
        - lower: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references
          `validate_non_implementable_policy`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `validate_non_implementable_policy`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `validate_non_implementable_policy`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `validate_non_implementable_policy`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `validate_non_implementable_policy`

    State and side effects:
        mutates status, rationale, hard_limitation, combined_text.

    Invariants:
        - `pytest_bdd.model.message_status_governance.validate_non_implementable_policy` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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
    status = normalize_capability_status(decision.status)
    if status != "Non-Implementable":
        return ()

    rationale = decision.rationale or ""
    hard_limitation = decision.hard_limitation or ""
    combined_text = f"{rationale}\n{hard_limitation}".lower()

    return tuple(
        f"non-implementable rationale uses forbidden phrase: '{pattern}'"
        for pattern in FORBIDDEN_NON_IMPLEMENTABLE_PATTERNS
        if pattern in combined_text
    )


def validate_partly_applicable_policy(decision: CapabilityDecision) -> tuple[str, ...]:
    """
    Check if a 'Partly-Applicable' decision provides an acceptable rationale regarding runtime differences.

    Returns:
        A tuple of violation message strings, empty if compliant.

    Responsibility:
        Check if a 'Partly-Applicable' decision provides an acceptable rationale regarding runtime differences. It
        directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_status_governance.validate_partly_applicable_policy` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - normalize_capability_status: collaborator call used by this boundary
        - lower: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references
          `validate_partly_applicable_policy`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `validate_partly_applicable_policy`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `validate_partly_applicable_policy`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `validate_partly_applicable_policy`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `validate_partly_applicable_policy`

    State and side effects:
        mutates status, rationale.

    Invariants:
        - `pytest_bdd.model.message_status_governance.validate_partly_applicable_policy` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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
    status = normalize_capability_status(decision.status)
    if status != "Partly-Applicable":
        return ()

    rationale = (decision.rationale or "").lower()
    if "language" in rationale and ("model" in rationale or "runtime" in rationale):
        return ()
    return (
        (
            "partly-applicable rationale must explain language/runtime model mismatch "
            "(for example: no native language-equivalent model in current runtime)"
        ),
    )


def validate_capability_decision(decision: CapabilityDecision) -> DecisionValidationResult:
    """
    Perform comprehensive policy and evidence validation on a capability decision.

    Returns:
        A DecisionValidationResult capturing whether the decision is fully compliant or has violations.

    Responsibility:
        Perform comprehensive policy and evidence validation on a capability decision. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_status_governance.validate_capability_decision` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - violations.extend: collaborator call used by this boundary
        - normalize_capability_status: collaborator call used by this boundary
        - violations.append: collaborator call used by this boundary
        - validate_non_implementable_policy: collaborator call used by this boundary
        - validate_partly_applicable_policy: collaborator call used by this boundary
        - missing_required_evidence_fields: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `validate_capability_decision`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `validate_capability_decision`
        - src/pytest_bdd/model/__init__.py: imports or references `validate_capability_decision`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `validate_capability_decision`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `validate_capability_decision`

    State and side effects:
        mutates violations, status, missing, accepted.

    Invariants:
        - `pytest_bdd.model.message_status_governance.validate_capability_decision` keeps its documented import path,
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
        #arch-eval:locational_stability=4

    """
    violations: list[str] = []
    status = normalize_capability_status(decision.status)
    if status is None:
        violations.append(f"Unknown status: {decision.status}")
    violations.extend(validate_non_implementable_policy(decision))
    violations.extend(validate_partly_applicable_policy(decision))
    missing = missing_required_evidence_fields(decision)
    accepted = not violations and not missing
    return DecisionValidationResult(
        accepted=accepted,
        missing_required_evidence_fields=missing,
        violations=tuple(violations),
    )


def validate_mandatory_scope_decision(
    decision: CapabilityDecision,
    *,
    mandatory_capability_ids: set[str],
) -> tuple[str, ...]:
    """
    Ensure that a capability in the mandatory scope is not assigned a deferred or rejected status.

    Returns:
        A tuple of violation message strings, empty if compliant.

    Responsibility:
        Ensure that a capability in the mandatory scope is not assigned a deferred or rejected status. It directly owns
        the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_status_governance.validate_mandatory_scope_decision` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - normalize_capability_status: collaborator call used by this boundary
        - join: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references
          `validate_mandatory_scope_decision`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `validate_mandatory_scope_decision`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `validate_mandatory_scope_decision`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `validate_mandatory_scope_decision`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `validate_mandatory_scope_decision`

    State and side effects:
        mutates status, message.

    Invariants:
        - `pytest_bdd.model.message_status_governance.validate_mandatory_scope_decision` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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
    if decision.capability_id not in mandatory_capability_ids:
        return ()
    status = normalize_capability_status(decision.status)
    if status in MANDATORY_SCOPE_FORBIDDEN_STATUSES:
        message = (
            "mandatory scope capabilities cannot use deferred statuses "
            f"({', '.join(sorted(MANDATORY_SCOPE_FORBIDDEN_STATUSES))}): {decision.capability_id} -> {status}"
        )
        return (message,)
    return ()


def ensure_single_status_per_capability(decisions: list[CapabilityDecision]) -> StatusUniquenessResult:
    """
    Verify that no capability is assigned conflicting statuses for the same release target.

    Returns:
        A StatusUniquenessResult indicating if duplicates exist.

    Responsibility:
        Verify that no capability is assigned conflicting statuses for the same release target. It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_status_governance.ensure_single_status_per_capability` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - set: collaborator call used by this boundary
        - duplicates.append: collaborator call used by this boundary
        - seen.add: collaborator call used by this boundary
        - StatusUniquenessResult: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references
          `ensure_single_status_per_capability`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references
          `ensure_single_status_per_capability`
        - src/pytest_bdd/model/__init__.py: imports or references `ensure_single_status_per_capability`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `ensure_single_status_per_capability`
        - src/pytest_bdd/script/message_capability_governance/cli/_report.py: imports or references
          `ensure_single_status_per_capability`

    State and side effects:
        mutates seen, duplicates, uniqueness_key.

    Invariants:
        - `pytest_bdd.model.message_status_governance.ensure_single_status_per_capability` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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
    seen: set[tuple[str, str]] = set()
    duplicates: list[str] = []
    for decision in decisions:
        uniqueness_key = (decision.capability_id, decision.release_target)
        if uniqueness_key in seen:
            duplicates.append(f"{decision.capability_id}@{decision.release_target}")
        else:
            seen.add(uniqueness_key)
    return StatusUniquenessResult(is_unique=not duplicates, duplicates=tuple(sorted(set(duplicates))))


def is_release_blocker_status(status: CapabilityStatus) -> bool:
    """
    Determine if a specific capability status represents a release blocker.

    Returns:
        True if the status blocks a release, False otherwise.

    Responsibility:
        Determine if a specific capability status represents a release blocker. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_status_governance.is_release_blocker_status`
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
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `is_release_blocker_status`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `is_release_blocker_status`
        - src/pytest_bdd/model/__init__.py: imports or references `is_release_blocker_status`
        - src/pytest_bdd/model/message_governance_checklist.py: imports or references `is_release_blocker_status`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `is_release_blocker_status`

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
        #arch-eval:locational_stability=4

    """
    return status in RELEASE_BLOCKER_STATUSES


def evaluate_release_blockers(
    decisions: list[CapabilityDecision],
    *,
    relevant_capability_ids: tuple[str, ...] = (),
) -> BlockerEvaluationResult:
    """
    Analyze all decisions and identify any that block a release, including missing relevant decisions.

    Returns:
        A BlockerEvaluationResult summarizing all blockers and deferred capabilities.

    Responsibility:
        Analyze all decisions and identify any that block a release, including missing relevant decisions. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_status_governance.evaluate_release_blockers`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - set: collaborator call used by this boundary
        - blocker_ids.add: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - normalize_capability_status: collaborator call used by this boundary
        - is_release_blocker_status: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `evaluate_release_blockers`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `evaluate_release_blockers`
        - src/pytest_bdd/model/__init__.py: imports or references `evaluate_release_blockers`
        - src/pytest_bdd/model/message_governance_checklist.py: imports or references `evaluate_release_blockers`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `evaluate_release_blockers`

    State and side effects:
        mutates index, blocker_ids, deferred_ids, missing_ids, status.

    Invariants:
        - `pytest_bdd.model.message_status_governance.evaluate_release_blockers` keeps its documented import path,
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
        #arch-eval:locational_stability=4

    """
    index = {decision.capability_id: decision for decision in decisions}
    blocker_ids: set[str] = set()
    deferred_ids: set[str] = set()
    missing_ids: set[str] = set()

    for decision in decisions:
        status = normalize_capability_status(decision.status)
        if status is None:
            blocker_ids.add(decision.capability_id)
            continue
        if is_release_blocker_status(status):
            blocker_ids.add(decision.capability_id)
        elif status in {"Partly-Applicable", "Non-Implementable", "Not-Applicable"}:
            deferred_ids.add(decision.capability_id)

    for capability_id in relevant_capability_ids:
        if capability_id not in index:
            missing_ids.add(capability_id)
            blocker_ids.add(capability_id)

    return BlockerEvaluationResult(
        unresolved_blocker_capability_ids=tuple(sorted(blocker_ids)),
        deferred_capability_ids=tuple(sorted(deferred_ids)),
        missing_decision_capability_ids=tuple(sorted(missing_ids)),
    )
