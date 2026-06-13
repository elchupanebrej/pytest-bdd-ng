"""

Compliance test: T2 — mypy --strict src/ exits 0.

This test checks the requirement that ``mypy --strict src/`` exits 0
with all strict flags enabled. T2 is now SATISFIED — Plan 20-18 resolved
all 183 remaining mypy errors across 56 files.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_mypy_strict_exits_zero():
    """
    Mypy --strict src/ should exit 0 when T2 is complete.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
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
    src_dir = str(REPO_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", src_dir],
        capture_output=True,
        text=True,
        timeout=180,
    )
    # mypy writes errors to stdout, not stderr
    last_line = result.stdout.strip().split("\n")[-1] if result.stdout else "(no output)"
    assert result.returncode == 0, (
        f"mypy --strict src/ exit code should be 0, got {result.returncode}.\nLast line: {last_line}"
    )
