import json

import pytest

from pytest_cuke.model.report_presentation import ReportPresentation, resolve_report_policy


@pytest.mark.parametrize("category", ["skip_as_failed", "xfail_as_failed", "tolerated_as_failed"])
def test_each_report_category_can_override_both_presets(category):
    diagnostic = resolve_report_policy("diagnostic", **{category: False})
    normal = resolve_report_policy("normal", **{category: True})
    assert diagnostic[category] is False
    assert normal[category] is True
    assert all(value for name, value in diagnostic.items() if name != category)
    assert not any(value for name, value in normal.items() if name != category)


@pytest.mark.parametrize("skip_as_failed,xfail_as_failed", [(False, False), (True, False), (False, True), (True, True)])
def test_skip_and_xfail_policies_are_independent(skip_as_failed, xfail_as_failed):
    presentation = ReportPresentation(skip_as_failed=skip_as_failed, xfail_as_failed=xfail_as_failed)
    for attempt, outcome in (("ordinary", "skip"), ("expected", "xfail")):
        presentation.accept(
            {
                "testStepFinished": {
                    "testCaseStartedId": attempt,
                    "testStepId": "step",
                    "testStepResult": {"status": "SKIPPED"},
                }
            }
        )
        presentation.accept(
            {
                "attachment": {
                    "mediaType": "application/vnd.pytest-cuke.pytest-outcome+json",
                    "body": json.dumps(
                        {"testCaseStartedId": attempt, "outcome": outcome, "reason": "example", "executed": False}
                    ),
                }
            }
        )
        projected = presentation.accept({"testCaseFinished": {"testCaseStartedId": attempt}})
        status = projected[0]["testStepFinished"]["testStepResult"]["status"] if len(projected) > 1 else "SKIPPED"
        assert status == ("FAILED" if (skip_as_failed if outcome == "skip" else xfail_as_failed) else "SKIPPED")


def _failure(attempt):
    return {
        "testStepFinished": {
            "testCaseStartedId": attempt,
            "testStepResult": {"status": "FAILED", "message": "actual failure"},
        }
    }


def _finish(attempt):
    return {"testCaseFinished": {"testCaseStartedId": attempt}}


def test_expected_failure_is_projected_without_changing_facts():
    presentation = ReportPresentation()
    failed = _failure("one")
    assert presentation.accept(failed) == []
    assert (
        presentation.accept(
            {
                "attachment": {
                    "mediaType": "application/vnd.pytest-cuke.pytest-outcome+json",
                    "body": json.dumps({"testCaseStartedId": "one", "outcome": "xfail", "reason": "known issue"}),
                }
            }
        )
        == []
    )
    projected, finished = presentation.accept(_finish("one"))
    assert projected["testStepFinished"]["testStepResult"] == {
        "status": "SKIPPED",
        "message": "xfail: known issue\nactual failure",
    }
    assert failed["testStepFinished"]["testStepResult"]["status"] == "FAILED"
    assert finished == _finish("one")


def test_parallel_attempts_do_not_share_outcomes_and_incomplete_run_keeps_failure():
    presentation = ReportPresentation()
    assert presentation.accept(_failure("one")) == []
    assert presentation.accept(_failure("two")) == []
    presentation.accept(
        {
            "attachment": {
                "mediaType": "application/vnd.pytest-cuke.pytest-outcome+json",
                "body": json.dumps({"testCaseStartedId": "one", "outcome": "xfail", "reason": "expected"}),
            }
        }
    )
    assert presentation.accept(_finish("two")) == [_failure("two"), _finish("two")]
    assert presentation.accept({"testRunFinished": {"success": False}}) == [
        _failure("one"),
        {"testRunFinished": {"success": False}},
    ]


def test_canonical_projection_retains_actual_failure_in_metadata():
    presentation = ReportPresentation(retain_metadata=True)
    failed = _failure("one")
    failed["testStepFinished"]["testStepId"] = "step-one"
    assert presentation.accept(failed) == []
    assert (
        presentation.accept(
            {
                "attachment": {
                    "mediaType": "application/vnd.pytest-cuke.pytest-outcome+json",
                    "body": json.dumps({"testCaseStartedId": "one", "outcome": "xfail", "reason": "known issue"}),
                }
            }
        )
        == []
    )
    projected, metadata, finished = presentation.accept(_finish("one"))
    assert projected["testStepFinished"]["testStepResult"]["status"] == "SKIPPED"
    assert json.loads(metadata["attachment"]["body"])["actualStepResults"] == [
        {"testStepId": "step-one", "result": {"status": "FAILED", "message": "actual failure"}}
    ]
    assert finished == _finish("one")


def test_diagnostic_xfail_restores_actual_failure_and_leaves_later_skips():
    presentation = ReportPresentation(xfail_as_failed=True)
    first = {
        "testStepFinished": {
            "testCaseStartedId": "one",
            "testStepId": "first",
            "testStepResult": {"status": "SKIPPED", "message": "xfail"},
        }
    }
    later = {
        "testStepFinished": {"testCaseStartedId": "one", "testStepId": "later", "testStepResult": {"status": "SKIPPED"}}
    }
    assert presentation.accept(first) == []
    assert presentation.accept(later) == []
    metadata = {
        "testCaseStartedId": "one",
        "outcome": "xfail",
        "executed": True,
        "reason": "known issue",
        "actualStepResults": [{"testStepId": "first", "result": {"status": "FAILED", "message": "actual failure"}}],
    }
    assert (
        presentation.accept(
            {
                "attachment": {
                    "mediaType": "application/vnd.pytest-cuke.pytest-outcome+json",
                    "body": json.dumps(metadata),
                }
            }
        )
        == []
    )
    first_result, later_result, _ = presentation.accept(_finish("one"))
    assert first_result["testStepFinished"]["testStepResult"] == {"status": "FAILED", "message": "actual failure"}
    assert later_result == later
    assert first["testStepFinished"]["testStepResult"]["status"] == "SKIPPED"


def test_diagnostic_not_run_xfail_is_failed_without_claiming_execution():
    presentation = ReportPresentation(xfail_as_failed=True)
    skipped = {
        "testStepFinished": {"testCaseStartedId": "one", "testStepId": "step", "testStepResult": {"status": "SKIPPED"}}
    }
    presentation.accept(skipped)
    presentation.accept(
        {
            "attachment": {
                "mediaType": "application/vnd.pytest-cuke.pytest-outcome+json",
                "body": json.dumps(
                    {"testCaseStartedId": "one", "outcome": "xfail", "executed": False, "reason": "known issue"}
                ),
            }
        }
    )
    projected, _ = presentation.accept(_finish("one"))
    assert projected["testStepFinished"]["testStepResult"] == {
        "status": "FAILED",
        "message": "xfail (not executed): known issue",
    }
