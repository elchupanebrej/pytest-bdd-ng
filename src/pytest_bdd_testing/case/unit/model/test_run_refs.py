"""

Unit tests for run lifecycle reference helpers.
"""

from __future__ import annotations

import pytest

from pytest_bdd.model.run.refs import (
    LifecycleObjectRef,
    NoPreviousStep,
    _finished_feature_ref,
    _finished_previous_step_ref,
    _finished_scenario_ref,
    _finished_step_ref,
    _inactive_feature_ref,
    _inactive_scenario_ref,
    _inactive_step_ref,
    _no_previous_step_ref,
)

pytestmark = [pytest.mark.unit]


def test_lifecycle_object_ref_serializes_all_fields() -> None:
    """
    LifecycleObjectRef.as_dict returns all public fields.

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
    ref = LifecycleObjectRef(
        kind="scenario",
        object_id="scenario-1",
        name="Scenario",
        source="test",
        is_active=True,
        empty_state_reason=None,
        fail_fast_code=None,
    )

    assert ref.as_dict() == {
        "kind": "scenario",
        "object_id": "scenario-1",
        "name": "Scenario",
        "source": "test",
        "is_active": True,
        "empty_state_reason": None,
        "fail_fast_code": None,
    }


@pytest.mark.parametrize(
    ("factory", "kind", "reason", "fail_fast_code"),
    [
        (_inactive_feature_ref, "feature", "idle", None),
        (_inactive_scenario_ref, "scenario", "idle", None),
        (_inactive_step_ref, "step", "idle", "object_inactive"),
        (_no_previous_step_ref, "step", "no_previous_step", None),
        (_finished_feature_ref, "feature", "finished", None),
        (_finished_scenario_ref, "scenario", "finished", None),
        (_finished_step_ref, "step", "finished", "object_inactive"),
        (_finished_previous_step_ref, "step", "finished", None),
    ],
)
def test_reference_factories_return_expected_inactive_refs(
    factory,
    kind: str,
    reason: str,
    fail_fast_code: str | None,
) -> None:
    """
    Reference helper factories create expected inactive refs.

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
    ref = factory()

    assert ref.kind == kind
    assert ref.object_id == f"{kind}:{reason}"
    assert ref.is_active is False
    assert ref.empty_state_reason == reason
    assert ref.fail_fast_code == fail_fast_code


def test_inactive_ref_allows_custom_source_name_and_fail_fast_code() -> None:
    """
    LifecycleObjectRef.inactive preserves optional custom fields.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
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
    ref = LifecycleObjectRef.inactive("feature", reason="blocked", name="Feature", source="fixture", fail_fast_code="x")

    assert ref.name == "Feature"
    assert ref.source == "fixture"
    assert ref.fail_fast_code == "x"


def test_no_previous_step_defaults_are_serializable() -> None:
    """
    NoPreviousStep exposes stable default fields.

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
    step = NoPreviousStep()

    assert step.id == "step:no_previous_step"
    assert not step.text
    assert not step.keyword
