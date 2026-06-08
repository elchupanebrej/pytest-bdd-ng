"""
Provide message outcome mapping helpers.

Responsibility:
    Provide message outcome mapping helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_outcome_mapping` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - OutcomeMappingRule: owns nested behavior below this boundary
    - ObservedOutcome: owns nested behavior below this boundary
    - MappingValidationResult: owns nested behavior below this boundary
    - normalize_outcome_status: owns nested behavior below this boundary
    - normalize_outcome_scope: owns nested behavior below this boundary
    - outcome_key: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `message_outcome_mapping`
    - src/pytest_bdd/message_stream_validation/status.py: imports or references `message_outcome_mapping`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
      `message_outcome_mapping`
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `message_outcome_mapping`

State and side effects:
    mutates status, missing_cases, outcome_scope, outcome_status, normalized; depends on __future__.annotations,
    typing.Final, typing.Literal, attrs.frozen, returns.maybe.Nothing.

Invariants:
    - `pytest_bdd.model.message_outcome_mapping` keeps its documented import path, ownership boundary, and observable
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

from typing import Final, Literal

from attrs import frozen
from returns.maybe import Nothing

MatrixProfile = Literal["fixed_release_readiness_v1"]
OutcomeScope = Literal["run", "scenario", "step", "hook", "attachment"]
OutcomeStatus = Literal["passed", "failed", "skipped", "undefined", "interrupted"]

MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1: Final[MatrixProfile] = "fixed_release_readiness_v1"
REQUIRED_MATRIX_STATUSES: Final[set[OutcomeStatus]] = {
    "passed",
    "failed",
    "skipped",
    "undefined",
    "interrupted",
}
OUTCOME_STATUS_ALIASES: Final[dict[str, OutcomeStatus]] = {
    "pass": "passed",
    "passed": "passed",
    "fail": "failed",
    "failed": "failed",
    "error": "failed",
    "skip": "skipped",
    "skipped": "skipped",
    "undefined": "undefined",
    "interrupted": "interrupted",
}
OUTCOME_SCOPE_ALIASES: Final[dict[str, OutcomeScope]] = {
    "run": "run",
    "scenario": "scenario",
    "step": "step",
    "hook": "hook",
    "attachment": "attachment",
}


@frozen
class OutcomeMappingRule:
    """
    Define a rule for mapping a specific outcome scope and status to one or more capabilities.

    Responsibility:
        Define a rule for mapping a specific outcome scope and status to one or more capabilities. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_outcome_mapping.OutcomeMappingRule` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `OutcomeMappingRule`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `OutcomeMappingRule`
        - src/pytest_bdd/model/__init__.py: imports or references `OutcomeMappingRule`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `OutcomeMappingRule`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `OutcomeMappingRule`

    State and side effects:
        mutates mapping_id, outcome_scope, outcome_status, capability_ids, priority.

    Invariants:
        - `pytest_bdd.model.message_outcome_mapping.OutcomeMappingRule` keeps its documented import path, ownership
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

    mapping_id: str
    outcome_scope: OutcomeScope
    outcome_status: OutcomeStatus
    capability_ids: tuple[str, ...]
    priority: int
    mapping_rationale: str


@frozen
class ObservedOutcome:
    """
    Capture a concrete test outcome observed during execution, including environmental context.

    Responsibility:
        Capture a concrete test outcome observed during execution, including environmental context. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_outcome_mapping.ObservedOutcome` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `ObservedOutcome`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `ObservedOutcome`
        - src/pytest_bdd/model/__init__.py: imports or references `ObservedOutcome`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `ObservedOutcome`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `ObservedOutcome`

    State and side effects:
        mutates outcome_scope, outcome_status, is_retry, is_parallel_worker.

    Invariants:
        - `pytest_bdd.model.message_outcome_mapping.ObservedOutcome` keeps its documented import path, ownership
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

    outcome_scope: OutcomeScope
    outcome_status: OutcomeStatus
    is_retry: bool = False
    is_parallel_worker: bool = False


@frozen
class MappingValidationResult:
    """
    Summarize the validity and coverage of a set of mapping rules against observed outcomes.

    Responsibility:
        Summarize the validity and coverage of a set of mapping rules against observed outcomes. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_outcome_mapping.MappingValidationResult`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - is_valid: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `MappingValidationResult`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `MappingValidationResult`
        - src/pytest_bdd/model/__init__.py: imports or references `MappingValidationResult`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `MappingValidationResult`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `MappingValidationResult`

    State and side effects:
        mutates status, matrix_profile, ambiguous_outcomes, unmapped_outcomes, missing_required_matrix_cases.

    Invariants:
        - `pytest_bdd.model.message_outcome_mapping.MappingValidationResult` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    status: Literal["pass", "fail"]
    matrix_profile: MatrixProfile
    ambiguous_outcomes: tuple[str, ...]
    unmapped_outcomes: tuple[str, ...]
    missing_required_matrix_cases: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        """
        Check if the mapping validation passed without ambiguities, unmapped outcomes, or missing cases.

        Returns:
            True if the mapping rules completely cover the observed outcomes and matrix profile, False otherwise.

        Responsibility:
            Check if the mapping validation passed without ambiguities, unmapped outcomes, or missing cases. It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_outcome_mapping.MappingValidationResult.is_valid` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `is_valid`
            - src/pytest_bdd/message_stream_validation/status.py: imports or references `is_valid`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `is_valid`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `is_valid`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `is_valid`

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
        return self.status == "pass"


def normalize_outcome_status(value: object) -> OutcomeStatus | None:
    """
    Convert a raw outcome status string into a recognized canonical OutcomeStatus.

    Returns:
        The normalized OutcomeStatus, or None if the status cannot be matched.

    Responsibility:
        Convert a raw outcome status string into a recognized canonical OutcomeStatus. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_outcome_mapping.normalize_outcome_status`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - lower: collaborator call used by this boundary
        - str.strip.split: collaborator call used by this boundary
        - str.strip: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - OUTCOME_STATUS_ALIASES.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `normalize_outcome_status`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `normalize_outcome_status`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `normalize_outcome_status`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `normalize_outcome_status`

    State and side effects:
        mutates normalized.

    Invariants:
        - `pytest_bdd.model.message_outcome_mapping.normalize_outcome_status` keeps its documented import path,
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
    if value is None:
        return Nothing.value_or(None)
    normalized = str(value).strip().split(".")[-1].lower()
    if not normalized:
        return Nothing.value_or(None)
    return OUTCOME_STATUS_ALIASES.get(normalized)


def normalize_outcome_scope(value: object) -> OutcomeScope | None:
    """
    Convert a raw scope identifier into a recognized canonical OutcomeScope.

    Returns:
        The normalized OutcomeScope, or None if the scope cannot be matched.

    Responsibility:
        Convert a raw scope identifier into a recognized canonical OutcomeScope. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_outcome_mapping.normalize_outcome_scope`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - str.strip.lower: collaborator call used by this boundary
        - str.strip: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - OUTCOME_SCOPE_ALIASES.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `normalize_outcome_scope`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `normalize_outcome_scope`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `normalize_outcome_scope`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `normalize_outcome_scope`

    State and side effects:
        mutates normalized.

    Invariants:
        - `pytest_bdd.model.message_outcome_mapping.normalize_outcome_scope` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    if value is None:
        return Nothing.value_or(None)
    normalized = str(value).strip().lower()
    if not normalized:
        return Nothing.value_or(None)
    return OUTCOME_SCOPE_ALIASES.get(normalized)


def outcome_key(scope: OutcomeScope, status: OutcomeStatus) -> str:
    """
    Generate a unique dictionary key combining an outcome scope and status.

    Returns:
        A formatted string representing the outcome key.

    Responsibility:
        Generate a unique dictionary key combining an outcome scope and status. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_outcome_mapping.outcome_key` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `outcome_key`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `outcome_key`
        - src/pytest_bdd/model/__init__.py: imports or references `outcome_key`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `outcome_key`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `outcome_key`

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
    return f"{scope}:{status}"


def find_matching_rules(
    rules: list[OutcomeMappingRule],
    *,
    outcome_scope: OutcomeScope,
    outcome_status: OutcomeStatus,
) -> list[OutcomeMappingRule]:
    """
    Filter a list of rules to find those that exactly match the provided scope and status.

    Returns:
        A list of OutcomeMappingRule instances matching the criteria.

    Responsibility:
        Filter a list of rules to find those that exactly match the provided scope and status. It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_outcome_mapping.find_matching_rules` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `find_matching_rules`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `find_matching_rules`
        - src/pytest_bdd/model/__init__.py: imports or references `find_matching_rules`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `find_matching_rules`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `find_matching_rules`

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
    return [rule for rule in rules if rule.outcome_scope == outcome_scope and rule.outcome_status == outcome_status]


def resolve_outcome_mapping(
    rules: list[OutcomeMappingRule],
    *,
    outcome_scope: OutcomeScope,
    outcome_status: OutcomeStatus,
) -> tuple[OutcomeMappingRule | None, bool]:
    """
    Select the highest-priority mapping rule for a specific scope and status.

    Returns:
        A tuple containing the best-matching OutcomeMappingRule (or None if no match)
        and a boolean flag indicating if multiple rules share the highest priority (ambiguous).

    Responsibility:
        Select the highest-priority mapping rule for a specific scope and status. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_outcome_mapping.resolve_outcome_mapping`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - find_matching_rules: collaborator call used by this boundary
        - len: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `resolve_outcome_mapping`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `resolve_outcome_mapping`
        - src/pytest_bdd/model/__init__.py: imports or references `resolve_outcome_mapping`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `resolve_outcome_mapping`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `resolve_outcome_mapping`

    State and side effects:
        mutates matches.

    Invariants:
        - `pytest_bdd.model.message_outcome_mapping.resolve_outcome_mapping` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    matches = sorted(
        find_matching_rules(rules, outcome_scope=outcome_scope, outcome_status=outcome_status),
        key=lambda rule: rule.priority,
    )
    if not matches:
        return Nothing.value_or(None), False
    if len(matches) > 1 and matches[0].priority == matches[1].priority:
        return Nothing.value_or(None), True
    return matches[0], False


def _validate_fixed_matrix(observed_outcomes: list[ObservedOutcome]) -> tuple[str, ...]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_outcome_mapping._validate_fixed_matrix` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_outcome_mapping._validate_fixed_matrix`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - any: collaborator call used by this boundary
        - missing.append: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - tuple: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_validate_fixed_matrix`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `_validate_fixed_matrix`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_validate_fixed_matrix`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_validate_fixed_matrix`

    State and side effects:
        mutates statuses, missing.

    Invariants:
        - `pytest_bdd.model.message_outcome_mapping._validate_fixed_matrix` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    statuses = {outcome.outcome_status for outcome in observed_outcomes}
    missing: list[str] = [
        f"missing_status:{required_status}"
        for required_status in sorted(REQUIRED_MATRIX_STATUSES)
        if required_status not in statuses
    ]

    if not any(outcome.is_retry for outcome in observed_outcomes):
        missing.append("missing_retry_scenario")
    if not any(outcome.is_parallel_worker for outcome in observed_outcomes):
        missing.append("missing_parallel_worker_scenario")

    return tuple(missing)


def validate_outcome_mappings(
    rules: list[OutcomeMappingRule],
    observed_outcomes: list[ObservedOutcome],
    *,
    matrix_profile: MatrixProfile = MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1,
) -> MappingValidationResult:
    """
    Evaluate a set of mapping rules against actual observed outcomes to ensure complete coverage.

    Returns:
        A MappingValidationResult detailing any ambiguous mappings, unmapped outcomes, or missing matrix cases.

    Responsibility:
        Evaluate a set of mapping rules against actual observed outcomes to ensure complete coverage. It directly owns
        the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_outcome_mapping.validate_outcome_mappings`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - resolve_outcome_mapping: collaborator call used by this boundary
        - outcome_key: collaborator call used by this boundary
        - ambiguous.append: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `validate_outcome_mappings`
        - src/pytest_bdd/message_stream_validation/status.py: imports or references `validate_outcome_mappings`
        - src/pytest_bdd/model/__init__.py: imports or references `validate_outcome_mappings`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `validate_outcome_mappings`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `validate_outcome_mappings`

    State and side effects:
        mutates missing_cases, status, ambiguous, unmapped, rule.

    Invariants:
        - `pytest_bdd.model.message_outcome_mapping.validate_outcome_mappings` keeps its documented import path,
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
    ambiguous: list[str] = []
    unmapped: list[str] = []

    for outcome in observed_outcomes:
        rule, is_ambiguous = resolve_outcome_mapping(
            rules,
            outcome_scope=outcome.outcome_scope,
            outcome_status=outcome.outcome_status,
        )
        key = outcome_key(outcome.outcome_scope, outcome.outcome_status)
        if is_ambiguous:
            ambiguous.append(key)
        elif rule is None:
            unmapped.append(key)

    missing_cases: tuple[str, ...]
    if matrix_profile == MATRIX_PROFILE_FIXED_RELEASE_READINESS_V1:
        missing_cases = _validate_fixed_matrix(observed_outcomes)
    else:
        missing_cases = ()

    status: Literal["pass", "fail"] = "pass"
    if ambiguous or unmapped or missing_cases:
        status = "fail"

    return MappingValidationResult(
        status=status,
        matrix_profile=matrix_profile,
        ambiguous_outcomes=tuple(sorted(set(ambiguous))),
        unmapped_outcomes=tuple(sorted(set(unmapped))),
        missing_required_matrix_cases=missing_cases,
    )
