"""Compliance test: T2 — mypy --strict src/ exits 0.

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

REPO_ROOT = Path(__file__).resolve().parents[5]


def test_mypy_strict_exits_zero():
    """mypy --strict src/ should exit 0 when T2 is complete."""
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
