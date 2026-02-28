from __future__ import annotations

from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]
from cucumber_messages import Meta, Product, Timestamp  # type:ignore[attr-defined]
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
