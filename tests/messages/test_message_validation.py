from __future__ import annotations

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]
from cucumber_messages import (  # type:ignore[attr-defined]
    ExternalAttachment,  # type:ignore[attr-defined]
    Meta,
    Product,
    Timestamp,
)
from cucumber_messages import TestRunFinished as CucumberTestRunFinished  # type:ignore[attr-defined]

from pytest_bdd.model.message_validation import validate_message_stream


def test_validate_message_stream_rejects_unsupported_protocol_version() -> None:
    envelopes = [
        Message(
            meta=Meta(
                protocol_version="0.0.0",
                implementation=Product(name="pytest-bdd-ng", version="test"),
                runtime=Product(name="python", version="3.x"),
                os=Product(name="os", version="1"),
                cpu=Product(name="cpu", version="1"),
            )
        )
    ]

    result = validate_message_stream(envelopes, latest_protocol_version="999.0.0")
    codes = {violation.code for violation in result.violations}
    assert result.status == "fail"
    assert "UNSUPPORTED_PROTOCOL_VERSION" in codes


def test_validate_message_stream_reports_fixed_matrix_diagnostics_when_enabled() -> None:
    envelopes = [
        Message(
            test_run_finished=CucumberTestRunFinished(
                timestamp=Timestamp(seconds=1, nanos=0),
                success=True,
            )
        )
    ]

    result = validate_message_stream(envelopes, enforce_mapping_diagnostics=True)
    codes = {violation.code for violation in result.violations}

    assert result.status == "fail"
    assert "MISSING_FIXED_MATRIX_CASE" in codes


def test_validate_message_stream_tracks_external_attachment_fields() -> None:
    envelopes = [
        Message(
            external_attachment=ExternalAttachment(
                media_type="application/octet-stream",
                url="https://example.invalid/external.bin",
                test_case_started_id="case-started-id",
                test_step_id="step-id",
                test_run_hook_started_id="run-hook-id",
                timestamp=Timestamp(seconds=1, nanos=1),
            )
        )
    ]

    result = validate_message_stream(envelopes, track_coverage=True)

    assert result.observed_coverage is not None
    observed = result.observed_coverage.observed_fields
    assert ("externalAttachment", "") in observed
    assert ("externalAttachment", "mediaType") in observed
    assert ("externalAttachment", "url") in observed
    assert ("externalAttachment", "testCaseStartedId") in observed
    assert ("externalAttachment", "testStepId") in observed
    assert ("externalAttachment", "testRunHookStartedId") in observed
    assert ("externalAttachment", "timestamp.seconds") in observed
    assert ("externalAttachment", "timestamp.nanos") in observed
