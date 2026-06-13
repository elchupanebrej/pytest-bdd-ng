"""

Provide test message governance checklist helpers.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pytest_bdd.model.message_baseline_diff import BaselineDiffRecord
from pytest_bdd.model.message_governance_checklist import build_governance_checklist, render_checklist_markdown
from pytest_bdd_testing.tool.message.capability_fixtures import make_capability, make_decision


def test_build_governance_checklist_includes_all_relevant_capabilities() -> None:
    """
    Verify build governance checklist includes all relevant capabilities.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
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
    """
    Verify build governance checklist marks newly changed capabilities.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
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
    """
    Verify render checklist markdown includes blocker summary.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
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
