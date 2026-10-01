from __future__ import annotations

from pytest_cuke.model import message_converter as mc
from pytest_cuke.model.message_stream_validation import validate_message_stream


def test_seam3_stream_order_violation_detection() -> None:
    bad_stream = [
        mc.make_test_step_finished(test_case_started_id="tcs-x", test_step_id="ts-x"),
        mc.make_test_run_finished(),
    ]
    errors = validate_message_stream(bad_stream)
    assert len(errors) >= 2
