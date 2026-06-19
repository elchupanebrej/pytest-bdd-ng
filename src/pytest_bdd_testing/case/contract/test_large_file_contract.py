"""

Contract tests for Phase 4 large-file split targets.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MAX_PHYSICAL_LINES = 399
TARGETS = (
    REPO_ROOT / "src" / "pytest_bdd" / "plugin" / "gherkin_message_reporter" / "live_formatter_runtime.py",
    REPO_ROOT / "src" / "pytest_bdd" / "model" / "message_validation.py",
)


def _physical_line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def test_phase_4_large_file_targets_are_split_below_400_lines() -> None:
    """
    Verify Phase 4 target files stay below the large-file threshold.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    failures = []
    for target in TARGETS:
        line_count = _physical_line_count(target)
        if line_count > MAX_PHYSICAL_LINES:
            failures.append(
                f"{target.relative_to(REPO_ROOT)} has {line_count} physical lines; expected <= {MAX_PHYSICAL_LINES}",
            )

    assert failures == []
