from __future__ import annotations

from cucumber_messages import Attachment  # type:ignore[attr-defined]
from cucumber_messages import TestCaseStarted as _TestCaseStarted  # type:ignore[attr-defined]
from cucumber_messages import TestStepFinished as _TestStepFinished  # type:ignore[attr-defined]
from cucumber_messages import TestStepStarted as _TestStepStarted  # type:ignore[attr-defined]

from .test_messages import list_filter_by_type, parse_and_unfold_messages, runpytest_with_message_reporter


def test_attachment_messages_are_correlated_to_active_step(testdir, tmp_path):
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment="""\
        Feature: attachment correlation

            Scenario: attach data
                Given Attach "hello" as string
        """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given('Attach "{value}" as string')
        def attach_string(attach, value):
            attach(value)
        """,
    )

    ndjson_path = tmp_path / "attachments.ndjson"
    result = runpytest_with_message_reporter(testdir, "--messages-ndjson", str(ndjson_path))
    result.assert_outcomes(passed=1)

    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())

    attachments = list_filter_by_type(Attachment, payloads)
    test_case_started_messages = list_filter_by_type(_TestCaseStarted, payloads)
    test_step_started_messages = list_filter_by_type(_TestStepStarted, payloads)
    test_step_finished_messages = list_filter_by_type(_TestStepFinished, payloads)

    assert len(attachments) == 1
    assert len(test_case_started_messages) == 1
    assert len(test_step_started_messages) == 1
    assert len(test_step_finished_messages) == 1

    attachment = attachments[0]
    assert attachment.test_case_started_id == test_case_started_messages[0].id
    assert attachment.test_step_id == test_step_started_messages[0].test_step_id
    assert attachment.test_step_id == test_step_finished_messages[0].test_step_id
