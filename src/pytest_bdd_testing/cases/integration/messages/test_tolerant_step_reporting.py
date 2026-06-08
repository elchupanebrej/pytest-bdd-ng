"""Tolerant step reporting tests."""

from __future__ import annotations

import textwrap

from contract.messages.test_messages import (
    list_filter_by_type,
    parse_and_unfold_messages,
    runpytest_with_message_reporter,
)
from cucumber_messages import (
    TestStepFinished as _TestStepFinished,  # type: ignore[attr-defined] — re-export alias not in stub
)


def _result_status_name(status: object) -> str:
    return str(getattr(status, "value", status)).lower()


def test_tolerant_ignored_step_still_reports_failed_step_result(testdir, tmp_path):
    """Ignored tolerant failures keep the step-level failed result."""
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    testdir.makefile(
        ".feature",
        tolerant=textwrap.dedent(
            """\
            Feature: Tolerant reporting

                Scenario: Tolerant failure
                    Given a tolerant step fails
                    Then a later step runs
            """,
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import given, scenario, then, tolerant


            @scenario("tolerant.feature", "Tolerant failure")
            def test_tolerant_failure():
                pass


            @tolerant
            @given("a tolerant step fails")
            def tolerant_step():
                raise AssertionError("soft failure")


            @then("a later step runs")
            def later_step():
                pass
            """,
        ),
    )

    ndjson_path = tmp_path / "tolerant.ndjson"
    result = runpytest_with_message_reporter(
        testdir,
        "--tolerant-status",
        "ignored",
        "--messages-ndjson",
        str(ndjson_path),
    )
    result.assert_outcomes(passed=1)

    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())
    test_step_finished_messages = list_filter_by_type(_TestStepFinished, payloads)

    assert len(test_step_finished_messages) == 2
    assert any(
        _result_status_name(message.test_step_result.status) == "failed" for message in test_step_finished_messages
    )
