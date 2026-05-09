"""Provide message baseline diff helpers."""

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
    """Define schedule and metadata for baseline capability diffs."""

    schedule_id: str
    cadence: BaselineCadence
    last_run_at: datetime
    next_run_at: datetime


@frozen
class BaselineDiffRecord:
    """Capture the structural differences in capabilities between two specific reporting baselines."""

    diff_run_id: str
    previous_baseline: str
    current_baseline: str
    added_capability_ids: tuple[str, ...]
    changed_capability_ids: tuple[str, ...]
    removed_capability_ids: tuple[str, ...]
    generated_at: datetime


@frozen
class BaselineDiffExecutionResult:
    """Aggregate the outcome of a scheduled baseline diff evaluation, including any generated records."""

    due: bool
    schedule: BaselineComparisonSchedule
    record: BaselineDiffRecord | None


def next_weekly_run_at(last_run_at: datetime) -> datetime:
    """
    Calculate the next scheduled execution timestamp based on a weekly interval.

    Returns:
        A datetime object representing exactly one week after the provided last run time.

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

    """
    if schedule.cadence != WEEKLY_CADENCE:
        return False
    current = now or datetime.now(timezone.utc)
    return current >= schedule.next_run_at


def _capability_signature(capability: MessageCapability) -> tuple[object, ...]:
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
