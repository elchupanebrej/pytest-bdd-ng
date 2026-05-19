"""Contract tests for Phase 4 large-file split targets."""

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
    """Verify Phase 4 target files stay below the large-file threshold."""
    failures = []
    for target in TARGETS:
        line_count = _physical_line_count(target)
        if line_count > MAX_PHYSICAL_LINES:
            failures.append(
                f"{target.relative_to(REPO_ROOT)} has {line_count} physical lines; expected <= {MAX_PHYSICAL_LINES}",
            )

    assert failures == []
