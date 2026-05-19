"""Provide test message attachments helpers."""

from __future__ import annotations

from contract.messages.test_messages import (
    list_filter_by_type,
    parse_and_unfold_messages,
    runpytest_with_message_reporter,
)
from cucumber_messages import (
    Attachment,  # type:ignore[attr-defined]
    ExternalAttachment,  # type:ignore[attr-defined]
)
from cucumber_messages import TestCaseStarted as _TestCaseStarted  # type:ignore[attr-defined]
from cucumber_messages import TestStepFinished as _TestStepFinished  # type:ignore[attr-defined]
from cucumber_messages import TestStepStarted as _TestStepStarted  # type:ignore[attr-defined]


def test_attachment_messages_are_correlated_to_active_step(testdir, tmp_path):
    """Verify attachment messages are correlated to active step."""
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
    external_attachments = list_filter_by_type(ExternalAttachment, payloads)
    test_case_started_messages = list_filter_by_type(_TestCaseStarted, payloads)
    test_step_started_messages = list_filter_by_type(_TestStepStarted, payloads)
    test_step_finished_messages = list_filter_by_type(_TestStepFinished, payloads)

    assert len(attachments) == 1
    assert len(external_attachments) == 0
    assert len(test_case_started_messages) == 1
    assert len(test_step_started_messages) == 1
    assert len(test_step_finished_messages) == 1

    attachment = attachments[0]
    assert attachment.test_case_started_id == test_case_started_messages[0].id
    assert attachment.test_step_id == test_step_started_messages[0].test_step_id
    assert attachment.test_step_id == test_step_finished_messages[0].test_step_id
    assert attachment.source is None
    assert attachment.url is None


def test_attachment_messages_populate_mandatory_metadata_fields(testdir, tmp_path):
    """Verify attachment messages populate mandatory metadata fields."""
    testdir.makefile(
        ".feature",
        # language=gherkin
        attachment="""\
        Feature: attachment metadata

            Scenario: attach data with metadata
                Given Attach "hello" with metadata
        """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given('Attach "{value}" with metadata')
        def attach_with_metadata(attach, value):
            attach(
                value.encode("utf-8"),
                media_type="application/octet-stream",
                file_name="evidence.bin",
                source_data="Feature: source",
                source_media_type="text/x.cucumber.gherkin+plain",
                source_uri="features/source.feature",
                url="https://example.invalid/evidence.bin",
                as_external=True,
                test_run_hook_started_id="hook-started-id",
                test_run_started_id="run-started-id",
            )
        """,
    )

    ndjson_path = tmp_path / "attachments-metadata.ndjson"
    result = runpytest_with_message_reporter(
        testdir,
        "--messages-ndjson",
        str(ndjson_path),
    )
    result.assert_outcomes(passed=1)

    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())

    attachments = list_filter_by_type(Attachment, payloads)
    external_attachments = list_filter_by_type(ExternalAttachment, payloads)

    assert attachments, "Expected at least one attachment payload"
    assert external_attachments, "Expected at least one external attachment payload"

    attachment = attachments[-1]
    assert attachment.file_name == "evidence.bin"
    assert attachment.url == "https://example.invalid/evidence.bin"
    assert attachment.source is not None
    assert attachment.source.data == "Feature: source"
    assert str(getattr(attachment.source.media_type, "value", attachment.source.media_type)) == (
        "text/x.cucumber.gherkin+plain"
    )
    assert attachment.source.uri == "features/source.feature"
    assert attachment.test_run_hook_started_id == "hook-started-id"
    assert attachment.test_run_started_id == "run-started-id"
    assert attachment.timestamp is not None

    external = external_attachments[-1]
    assert external.url == "https://example.invalid/evidence.bin"
    assert external.media_type == "application/octet-stream"
    assert external.test_run_hook_started_id == "hook-started-id"
    assert external.timestamp is not None
