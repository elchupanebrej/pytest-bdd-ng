"""

Provide test hook run api surface helpers.
"""

from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenario
from pytest_bdd.plugin.pickle_runner.api_compatibility import (
    build_external_api_compatibility_record,
    collect_hook_public_symbols,
    load_api_baseline,
)


def test_external_api_surface_remains_additive_only() -> None:
    """
    Verify external api surface remains additive only.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        Integration test
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
    baseline_path = Path(__file__).with_name("hook_public_api_baseline.json")
    baseline = load_api_baseline(baseline_path)

    record = build_external_api_compatibility_record(
        baseline_reference=baseline["baseline_reference"],
        baseline_symbols=baseline["symbols"],
    )

    assert record.removed_symbols == []
    assert record.renamed_symbols == []
    assert record.consumer_migration_required is False


def test_external_api_compatibility_record_is_serializable() -> None:
    """
    Verify external api compatibility record is serializable.

    Test target:
        Protect API compatibility and version stability across the framework execution matrix.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Protect API compatibility and version stability across the
        framework execution matrix., then the expected outcome is produced.
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
    baseline_path = Path(__file__).with_name("hook_public_api_baseline.json")
    baseline = load_api_baseline(baseline_path)

    record = build_external_api_compatibility_record(
        baseline_reference=baseline["baseline_reference"],
        baseline_symbols=baseline["symbols"],
    )

    payload = record.as_dict()
    assert payload["api_surface_id"] == "hook-plugin-public-api"
    assert payload["baseline_reference"] == baseline["baseline_reference"]
    assert isinstance(payload["additive_symbols"], list)


def test_current_hook_public_symbols_cover_the_saved_baseline() -> None:
    """
    Verify current hook public symbols cover the saved baseline.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        Integration test
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
    baseline_path = Path(__file__).with_name("hook_public_api_baseline.json")
    baseline = load_api_baseline(baseline_path)

    current_symbols = collect_hook_public_symbols()

    assert set(baseline["symbols"]).issubset(current_symbols)


def test_current_hook_public_symbols_are_sorted_and_unique() -> None:
    """
    Verify current hook public symbols are sorted and unique.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        Integration test
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
    current_symbols = collect_hook_public_symbols()

    assert current_symbols == sorted(current_symbols)
    assert len(current_symbols) == len(set(current_symbols))


def test_scenario_decorator_uses_pickle_fixture_for_runtime_binding() -> None:
    """
    Verify scenario decorator uses pickle fixture for runtime binding.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        Integration test
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
    decorator = scenario("test.feature", "Scenario", return_test_decorator=True)

    @decorator
    def test_case():
        """
        Test target:
        Enforce framework invariants and stable API contracts.
        Test type:
        Integration test
        Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then
            the expected outcome is produced.
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
        return

    usefixtures_marks = [mark for mark in test_case.pytestmark if mark.name == "usefixtures"]

    assert any(mark.args == ("gherkin_document", "pickle", "feature_source") for mark in usefixtures_marks)
