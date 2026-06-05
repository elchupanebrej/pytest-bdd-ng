"""Provide test message governance checklist helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from pytest_bdd.model.message_baseline_diff import BaselineDiffRecord
from pytest_bdd.model.message_governance_checklist import build_governance_checklist, render_checklist_markdown

from .message_capability_fixtures import make_capability, make_decision


def test_build_governance_checklist_includes_all_relevant_capabilities() -> None:
    """Verify build governance checklist includes all relevant capabilities."""
    capabilities = [
        make_capability("cap-implemented", affects=("status_mapping",)),
        make_capability("cap-missing-decision", affects=("governance_checklist_output",)),
        make_capability("cap-out-of-scope", affects=()),
    ]
    decisions = [
        make_decision("cap-implemented", status="Implemented"),
    ]

    checklist = build_governance_checklist(capabilities, decisions)

    assert [entry.capability_id for entry in checklist.entries] == ["cap-implemented", "cap-missing-decision"]
    assert checklist.entries[0].status == "Implemented"
    assert checklist.entries[1].status == "Pending"
    assert checklist.unresolved_blockers == 1


def test_build_governance_checklist_marks_newly_changed_capabilities() -> None:
    """Verify build governance checklist marks newly changed capabilities."""
    capabilities = [
        make_capability("cap-new"),
        make_capability("cap-changed"),
        make_capability("cap-stable"),
    ]
    decisions = [
        make_decision("cap-new", status="Non-Implementable", rationale="upstream limitation"),
        make_decision("cap-changed", status="Not-Acceptable", rationale="policy conflict"),
        make_decision("cap-stable", status="Implemented"),
    ]
    diff = BaselineDiffRecord(
        diff_run_id="diff-1",
        previous_baseline="v32.0.0",
        current_baseline="v32.0.1",
        added_capability_ids=("cap-new",),
        changed_capability_ids=("cap-changed",),
        removed_capability_ids=(),
        generated_at=datetime(2026, 2, 25, 8, 0, tzinfo=timezone.utc),
    )

    checklist = build_governance_checklist(capabilities, decisions, baseline_diff=diff)
    entry_index = {entry.capability_id: entry for entry in checklist.entries}

    assert entry_index["cap-new"].delta == "added"
    assert entry_index["cap-changed"].delta == "changed"
    assert entry_index["cap-stable"].delta == "unchanged"
    assert entry_index["cap-changed"].release_blocker is True


def test_render_checklist_markdown_includes_blocker_summary() -> None:
    """Verify render checklist markdown includes blocker summary."""
    checklist = build_governance_checklist(
        [make_capability("cap-1"), make_capability("cap-2")],
        [
            make_decision("cap-1", status="Implemented"),
            make_decision("cap-2", status="Pending"),
        ],
    )

    rendered = render_checklist_markdown(checklist)

    assert "# message-status-governance" in rendered
    assert "| cap-1 | Implemented |" in rendered
    assert "| cap-2 | Pending |" in rendered
    assert "Unresolved blockers: 1" in rendered
