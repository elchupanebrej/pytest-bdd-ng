"""

Integration coverage for compatibility shims.
"""

from __future__ import annotations

import pytest

from pytest_bdd.compatibility.enum import StrEnum

pytestmark = [pytest.mark.unit]


class CompatibilityEnum(StrEnum):
    A = "a"


def test_strenum_behaves_like_string() -> None:
    """
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
    assert CompatibilityEnum.A == "a"
    assert CompatibilityEnum.A.value == "a"
    assert isinstance(CompatibilityEnum.A, str)
