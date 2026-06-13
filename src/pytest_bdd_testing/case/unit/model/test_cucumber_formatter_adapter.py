"""

Provide test cucumber formatter adapter helpers.
"""

from __future__ import annotations

import pytest

from pytest_bdd.model.cucumber_formatter_adapter import (
    CucumberFormatterEnvelopeAdapter,
    normalize_formatter_envelope_dicts,
)

pytestmark = [pytest.mark.unit]


def _test_case(test_case_id: str, *test_steps: dict[str, object]) -> dict[str, object]:
    return {
        "testCase": {
            "id": test_case_id,
            "pickleId": f"pickle-{test_case_id}",
            "testSteps": list(test_steps),
        },
    }


def _pickle_step(test_step_id: str, pickle_step_id: str) -> dict[str, object]:
    return {
        "id": test_step_id,
        "pickleStepId": pickle_step_id,
        "stepDefinitionIds": [f"step-definition-{test_step_id}"],
    }


def _hook_step(test_step_id: str) -> dict[str, object]:
    return {"id": test_step_id, "hookId": f"hook-{test_step_id}"}


def _test_case_started(started_id: str, test_case_id: str) -> dict[str, object]:
    return {"testCaseStarted": {"id": started_id, "testCaseId": test_case_id, "attempt": 0}}


def _test_step_finished(started_id: str, test_step_id: str, status: str = "PASSED") -> dict[str, object]:
    return {
        "testStepFinished": {
            "testCaseStartedId": started_id,
            "testStepId": test_step_id,
            "timestamp": {"seconds": 11, "nanos": 7},
            "testStepResult": {
                "duration": {"seconds": 0, "nanos": 1},
                "status": status,
            },
        },
    }


def _test_case_finished(started_id: str) -> dict[str, object]:
    return {
        "testCaseFinished": {
            "testCaseStartedId": started_id,
            "timestamp": {"seconds": 13, "nanos": 5},
            "willBeRetried": False,
        },
    }


def _test_run_finished() -> dict[str, object]:
    return {
        "testRunFinished": {
            "timestamp": {"seconds": 17, "nanos": 3},
            "success": False,
        },
    }


def test_backfills_missing_pickle_step_result_before_test_case_finished() -> None:
    """
    Verify backfills missing pickle step result before test case finished.

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
    normalized = normalize_formatter_envelope_dicts(
        [
            _test_case("tc-1", _hook_step("hook-1"), _pickle_step("pickle-step-1", "pickle-1")),
            _test_case_started("attempt-1", "tc-1"),
            _test_case_finished("attempt-1"),
        ],
    )

    assert normalized[-2] == {
        "testStepFinished": {
            "testCaseStartedId": "attempt-1",
            "testStepId": "pickle-step-1",
            "timestamp": {"seconds": 13, "nanos": 5},
            "testStepResult": {
                "duration": {"seconds": 0, "nanos": 0},
                "status": "UNKNOWN",
            },
        },
    }
    assert normalized[-1] == _test_case_finished("attempt-1")


def test_does_not_duplicate_existing_pickle_step_result() -> None:
    """
    Verify does not duplicate existing pickle step result.

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
    normalized = normalize_formatter_envelope_dicts(
        [
            _test_case("tc-1", _pickle_step("pickle-step-1", "pickle-1")),
            _test_case_started("attempt-1", "tc-1"),
            _test_step_finished("attempt-1", "pickle-step-1", "FAILED"),
            _test_case_finished("attempt-1"),
        ],
    )

    assert [envelope for envelope in normalized if "testStepFinished" in envelope] == [
        _test_step_finished("attempt-1", "pickle-step-1", "FAILED"),
    ]


def test_flush_backfills_open_attempts_before_test_run_finished() -> None:
    """
    Verify flush backfills open attempts before test run finished.

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
    adapter = CucumberFormatterEnvelopeAdapter()
    envelopes = [
        _test_case("tc-1", _pickle_step("pickle-step-1", "pickle-1")),
        _test_case_started("attempt-1", "tc-1"),
    ]
    normalized = []
    for envelope in envelopes:
        normalized.extend(adapter.adapt_envelope_dict(envelope))
    normalized.extend(adapter.adapt_envelope_dict(_test_run_finished()))

    assert normalized[-2] == {
        "testStepFinished": {
            "testCaseStartedId": "attempt-1",
            "testStepId": "pickle-step-1",
            "timestamp": {"seconds": 17, "nanos": 3},
            "testStepResult": {
                "duration": {"seconds": 0, "nanos": 0},
                "status": "UNKNOWN",
            },
        },
    }
    assert normalized[-1] == _test_run_finished()
