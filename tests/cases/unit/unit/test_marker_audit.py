"""Unit marker audit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]


def test_all_unit_test_files_have_unit_pytestmark() -> None:
    """All unit test modules declare the unit marker."""
    unit_root = Path(__file__).parents[1]
    missing = [
        path.relative_to(unit_root).as_posix()
        for path in sorted(unit_root.glob("**/test_*.py"))
        if "pytestmark = [pytest.mark.unit]" not in path.read_text(encoding="utf-8")
    ]

    assert missing == []
