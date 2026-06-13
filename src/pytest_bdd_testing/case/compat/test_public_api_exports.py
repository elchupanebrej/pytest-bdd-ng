"""

Provide test public api exports helpers.
"""

from __future__ import annotations

import importlib
from types import ModuleType


def test_public_scenario_export_stays_callable_after_submodule_import() -> None:
    """
    Verify public scenario export stays callable after submodule import.

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
    importlib.import_module("pytest_bdd.scenario")

    from pytest_bdd import scenario

    assert not isinstance(scenario, ModuleType)
    assert callable(scenario)
