"""
Provide message baseline diff helpers.

Responsibility:
    Provide message baseline diff helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_baseline_diff` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - BaselineComparisonSchedule: owns nested behavior below this boundary
    - BaselineDiffRecord: owns nested behavior below this boundary
    - BaselineDiffExecutionResult: owns nested behavior below this boundary
    - next_weekly_run_at: owns nested behavior below this boundary
    - is_weekly_run_due: owns nested behavior below this boundary
    - _capability_signature: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `message_baseline_diff`
    - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `message_baseline_diff`

State and side effects:
    mutates record, current, BaselineCadence, WEEKLY_CADENCE, schedule_id; depends on __future__.annotations,
    datetime.datetime, datetime.timedelta, datetime.timezone, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.model.message_baseline_diff` keeps its documented import path, ownership boundary, and observable
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
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Final, Literal

from attrs import frozen

if TYPE_CHECKING:
    from .message_capability import MessageCapability

BaselineCadence = Literal["weekly"]
WEEKLY_CADENCE: Final[BaselineCadence] = "weekly"


@frozen
class BaselineComparisonSchedule:
    """
    Define schedule and metadata for baseline capability diffs.

    Responsibility:
        Define schedule and metadata for baseline capability diffs. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_baseline_diff.BaselineComparisonSchedule`
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
        - src/pytest_bdd/model/__init__.py: imports or references `BaselineComparisonSchedule`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `BaselineComparisonSchedule`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `BaselineComparisonSchedule`

    State and side effects:
        mutates schedule_id, cadence, last_run_at, next_run_at.

    Invariants:
        - `pytest_bdd.model.message_baseline_diff.BaselineComparisonSchedule` keeps its documented import path,
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

    schedule_id: str
    cadence: BaselineCadence
    last_run_at: datetime
    next_run_at: datetime


@frozen
class BaselineDiffRecord:
    """
    Capture the structural differences in capabilities between two specific reporting baselines.

    Responsibility:
        Capture the structural differences in capabilities between two specific reporting baselines. It directly owns
        the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_baseline_diff.BaselineDiffRecord` because it
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
        - src/pytest_bdd/model/__init__.py: imports or references `BaselineDiffRecord`
        - src/pytest_bdd/model/message_governance_checklist.py: imports or references `BaselineDiffRecord`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `BaselineDiffRecord`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `BaselineDiffRecord`

    State and side effects:
        mutates diff_run_id, previous_baseline, current_baseline, added_capability_ids, changed_capability_ids.

    Invariants:
        - `pytest_bdd.model.message_baseline_diff.BaselineDiffRecord` keeps its documented import path, ownership
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

    diff_run_id: str
    previous_baseline: str
    current_baseline: str
    added_capability_ids: tuple[str, ...]
    changed_capability_ids: tuple[str, ...]
    removed_capability_ids: tuple[str, ...]
    generated_at: datetime


@frozen
class BaselineDiffExecutionResult:
    """
    Aggregate the outcome of a scheduled baseline diff evaluation, including any generated records.

    Responsibility:
        Aggregate the outcome of a scheduled baseline diff evaluation, including any generated records. It directly owns
        the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_baseline_diff.BaselineDiffExecutionResult`
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
        - src/pytest_bdd/model/__init__.py: imports or references `BaselineDiffExecutionResult`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `BaselineDiffExecutionResult`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `BaselineDiffExecutionResult`

    State and side effects:
        mutates due, schedule, record.

    Invariants:
        - `pytest_bdd.model.message_baseline_diff.BaselineDiffExecutionResult` keeps its documented import path,
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

    due: bool
    schedule: BaselineComparisonSchedule
    record: BaselineDiffRecord | None


def next_weekly_run_at(last_run_at: datetime) -> datetime:
    """
    Calculate the next scheduled execution timestamp based on a weekly interval.

    Returns:
        A datetime object representing exactly one week after the provided last run time.

    Responsibility:
        Calculate the next scheduled execution timestamp based on a weekly interval. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_baseline_diff.next_weekly_run_at` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - timedelta: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `next_weekly_run_at`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `next_weekly_run_at`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `next_weekly_run_at`

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
    return last_run_at + timedelta(days=7)


def is_weekly_run_due(
    schedule: BaselineComparisonSchedule,
    *,
    now: datetime | None = None,
) -> bool:
    """
    Evaluate whether a weekly baseline comparison schedule is currently due for execution.

    Returns:
        True if the schedule dictates a run is due, otherwise False.

    Responsibility:
        Evaluate whether a weekly baseline comparison schedule is currently due for execution. It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_baseline_diff.is_weekly_run_due` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - datetime.now: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `is_weekly_run_due`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `is_weekly_run_due`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `is_weekly_run_due`

    State and side effects:
        mutates current.

    Invariants:
        - `pytest_bdd.model.message_baseline_diff.is_weekly_run_due` keeps its documented import path, ownership
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
    if schedule.cadence != WEEKLY_CADENCE:
        return False
    current = now or datetime.now(timezone.utc)
    return current >= schedule.next_run_at


def _capability_signature(capability: MessageCapability) -> tuple[object, ...]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_baseline_diff._capability_signature` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_baseline_diff._capability_signature` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `_capability_signature`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `_capability_signature`

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
        #arch-eval:locational_stability=3
    """
    return (
        capability.name,
        capability.description,
        capability.category,
        tuple(sorted(capability.affects)),
        capability.source_reference,
        capability.relevance,
    )


def build_baseline_diff(
    *,
    previous_baseline: str,
    current_baseline: str,
    previous_capabilities: list[MessageCapability],
    current_capabilities: list[MessageCapability],
    generated_at: datetime | None = None,
) -> BaselineDiffRecord:
    """
    Compute the specific capability additions, modifications, and removals between two baseline sets.

    Returns:
        A BaselineDiffRecord encapsulating the computed capability differences.

    Responsibility:
        Compute the specific capability additions, modifications, and removals between two baseline sets. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_baseline_diff.build_baseline_diff` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - tuple: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - _capability_signature: collaborator call used by this boundary
        - datetime.now: collaborator call used by this boundary
        - BaselineDiffRecord: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `build_baseline_diff`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references `build_baseline_diff`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references `build_baseline_diff`

    State and side effects:
        mutates previous_map, current_map, previous_ids, current_ids, added.

    Invariants:
        - `pytest_bdd.model.message_baseline_diff.build_baseline_diff` keeps its documented import path, ownership
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
    previous_map = {capability.capability_id: capability for capability in previous_capabilities}
    current_map = {capability.capability_id: capability for capability in current_capabilities}

    previous_ids = set(previous_map)
    current_ids = set(current_map)

    added = tuple(sorted(current_ids - previous_ids))
    removed = tuple(sorted(previous_ids - current_ids))

    changed_ids: list[str] = [
        capability_id
        for capability_id in sorted(previous_ids & current_ids)
        if _capability_signature(previous_map[capability_id]) != _capability_signature(current_map[capability_id])
    ]

    return BaselineDiffRecord(
        diff_run_id=f"diff-{int((generated_at or datetime.now(timezone.utc)).timestamp())}",
        previous_baseline=previous_baseline,
        current_baseline=current_baseline,
        added_capability_ids=added,
        changed_capability_ids=tuple(changed_ids),
        removed_capability_ids=removed,
        generated_at=generated_at or datetime.now(timezone.utc),
    )


def execute_weekly_baseline_diff(  # noqa: PLR0913
    *,
    schedule: BaselineComparisonSchedule,
    previous_baseline: str,
    current_baseline: str,
    previous_capabilities: list[MessageCapability],
    current_capabilities: list[MessageCapability],
    now: datetime | None = None,
) -> BaselineDiffExecutionResult:
    """
    Conditionally generate a baseline diff if the provided schedule indicates an execution is due.

    Returns:
        A BaselineDiffExecutionResult indicating whether a run occurred and the resulting record.

    Responsibility:
        Conditionally generate a baseline diff if the provided schedule indicates an execution is due. It directly owns
        the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_baseline_diff.execute_weekly_baseline_diff`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - BaselineDiffExecutionResult: collaborator call used by this boundary
        - datetime.now: collaborator call used by this boundary
        - is_weekly_run_due: collaborator call used by this boundary
        - build_baseline_diff: collaborator call used by this boundary
        - BaselineComparisonSchedule: collaborator call used by this boundary
        - next_weekly_run_at: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `execute_weekly_baseline_diff`
        - src/pytest_bdd/script/message_capability_governance/cli/_core.py: imports or references
          `execute_weekly_baseline_diff`
        - src/pytest_bdd/script/message_capability_governance/decisions.py: imports or references
          `execute_weekly_baseline_diff`

    State and side effects:
        mutates current, record, updated_schedule.

    Invariants:
        - `pytest_bdd.model.message_baseline_diff.execute_weekly_baseline_diff` keeps its documented import path,
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
    current = now or datetime.now(timezone.utc)
    if not is_weekly_run_due(schedule, now=current):
        return BaselineDiffExecutionResult(due=False, schedule=schedule, record=None)

    record = build_baseline_diff(
        previous_baseline=previous_baseline,
        current_baseline=current_baseline,
        previous_capabilities=previous_capabilities,
        current_capabilities=current_capabilities,
        generated_at=current,
    )
    updated_schedule = BaselineComparisonSchedule(
        schedule_id=schedule.schedule_id,
        cadence=WEEKLY_CADENCE,
        last_run_at=current,
        next_run_at=next_weekly_run_at(current),
    )
    return BaselineDiffExecutionResult(due=True, schedule=updated_schedule, record=record)
