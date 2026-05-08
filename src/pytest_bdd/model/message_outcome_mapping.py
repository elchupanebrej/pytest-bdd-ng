"""Provide message outcome mapping helpers."""

from __future__ import annotations

from typing import Final, Literal

from attrs import frozen

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
    """Define a rule for mapping a specific outcome scope and status to one or more capabilities."""

    mapping_id: str
    outcome_scope: OutcomeScope
    outcome_status: OutcomeStatus
    capability_ids: tuple[str, ...]
    priority: int
    mapping_rationale: str


@frozen
class ObservedOutcome:
    """Capture a concrete test outcome observed during execution, including environmental context."""

    outcome_scope: OutcomeScope
    outcome_status: OutcomeStatus
    is_retry: bool = False
    is_parallel_worker: bool = False


@frozen
class MappingValidationResult:
    """Summarize the validity and coverage of a set of mapping rules against observed outcomes."""

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

        """
        return self.status == "pass"


def normalize_outcome_status(value: object) -> OutcomeStatus | None:
    """
    Convert a raw outcome status string into a recognized canonical OutcomeStatus.

    Returns:
        The normalized OutcomeStatus, or None if the status cannot be matched.

    """
    if value is None:
        return None
    normalized = str(value).strip().split(".")[-1].lower()
    if not normalized:
        return None
    return OUTCOME_STATUS_ALIASES.get(normalized)


def normalize_outcome_scope(value: object) -> OutcomeScope | None:
    """
    Convert a raw scope identifier into a recognized canonical OutcomeScope.

    Returns:
        The normalized OutcomeScope, or None if the scope cannot be matched.

    """
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if not normalized:
        return None
    return OUTCOME_SCOPE_ALIASES.get(normalized)


def outcome_key(scope: OutcomeScope, status: OutcomeStatus) -> str:
    """
    Generate a unique dictionary key combining an outcome scope and status.

    Returns:
        A formatted string representing the outcome key.

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

    """
    matches = sorted(
        find_matching_rules(rules, outcome_scope=outcome_scope, outcome_status=outcome_status),
        key=lambda rule: rule.priority,
    )
    if not matches:
        return None, False
    if len(matches) > 1 and matches[0].priority == matches[1].priority:
        return None, True
    return matches[0], False


def _validate_fixed_matrix(observed_outcomes: list[ObservedOutcome]) -> tuple[str, ...]:
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
