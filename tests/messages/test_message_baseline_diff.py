"""Provide test message baseline diff helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pytest_bdd.model.message_baseline_diff import (
    WEEKLY_CADENCE,
    BaselineComparisonSchedule,
    build_baseline_diff,
    execute_weekly_baseline_diff,
    is_weekly_run_due,
    next_weekly_run_at,
)

from .message_capability_fixtures import make_capability


def test_next_weekly_run_at_adds_seven_days() -> None:
    """Verify next weekly run at adds seven days."""
    last_run = datetime(2026, 2, 1, 10, 0, tzinfo=UTC)

    next_run = next_weekly_run_at(last_run)

    assert next_run == last_run + timedelta(days=7)


def test_is_weekly_run_due_true_when_now_reaches_next_run() -> None:
    """Verify is weekly run due true when now reaches next run."""
    schedule = BaselineComparisonSchedule(
        schedule_id="weekly-mainline",
        cadence=WEEKLY_CADENCE,
        last_run_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
        next_run_at=datetime(2026, 2, 8, 9, 0, tzinfo=UTC),
    )

    assert is_weekly_run_due(schedule, now=datetime(2026, 2, 8, 9, 0, tzinfo=UTC)) is True
    assert is_weekly_run_due(schedule, now=datetime(2026, 2, 8, 8, 59, tzinfo=UTC)) is False


def test_build_baseline_diff_detects_added_changed_removed_capabilities() -> None:
    """Verify build baseline diff detects added changed removed capabilities."""
    previous = [
        make_capability("cap-1", description="stable"),
        make_capability("cap-2", description="old-description"),
        make_capability("cap-3", description="removed"),
    ]
    current = [
        make_capability("cap-1", description="stable"),
        make_capability("cap-2", description="new-description"),
        make_capability("cap-4", description="added"),
    ]

    diff = build_baseline_diff(
        previous_baseline="v32.0.0",
        current_baseline="v32.0.1",
        previous_capabilities=previous,
        current_capabilities=current,
        generated_at=datetime(2026, 2, 25, 12, 0, tzinfo=UTC),
    )

    assert diff.added_capability_ids == ("cap-4",)
    assert diff.changed_capability_ids == ("cap-2",)
    assert diff.removed_capability_ids == ("cap-3",)


def test_execute_weekly_baseline_diff_runs_only_when_due() -> None:
    """Verify execute weekly baseline diff runs only when due."""
    schedule = BaselineComparisonSchedule(
        schedule_id="weekly-mainline",
        cadence=WEEKLY_CADENCE,
        last_run_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
        next_run_at=datetime(2026, 2, 8, 9, 0, tzinfo=UTC),
    )
    previous = [make_capability("cap-1", description="stable")]
    current = [make_capability("cap-1", description="changed")]

    not_due_result = execute_weekly_baseline_diff(
        schedule=schedule,
        previous_baseline="v32.0.0",
        current_baseline="v32.0.1",
        previous_capabilities=previous,
        current_capabilities=current,
        now=datetime(2026, 2, 8, 8, 0, tzinfo=UTC),
    )
    due_result = execute_weekly_baseline_diff(
        schedule=schedule,
        previous_baseline="v32.0.0",
        current_baseline="v32.0.1",
        previous_capabilities=previous,
        current_capabilities=current,
        now=datetime(2026, 2, 8, 10, 0, tzinfo=UTC),
    )

    assert not_due_result.due is False
    assert not_due_result.record is None
    assert due_result.due is True
    assert due_result.record is not None
    assert due_result.record.changed_capability_ids == ("cap-1",)
