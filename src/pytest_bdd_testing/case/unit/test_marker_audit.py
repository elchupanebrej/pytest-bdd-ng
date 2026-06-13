"""

Unit marker audit tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]


def test_all_unit_test_files_have_unit_pytestmark() -> None:
    """
    All unit test modules declare the unit marker.

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
    unit_root = Path(__file__).parent
    missing = [
        path.relative_to(unit_root).as_posix()
        for path in sorted(unit_root.glob("**/test_*.py"))
        if "pytestmark = [pytest.mark.unit]" not in path.read_text(encoding="utf-8")
    ]

    assert missing == []
