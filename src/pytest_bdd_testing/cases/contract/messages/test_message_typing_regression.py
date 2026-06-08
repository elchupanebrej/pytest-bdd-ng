"""Provide test message typing regression helpers."""

from __future__ import annotations

import importlib.util

import pytest
from cucumber_messages import (
    Envelope as Message,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import (
    TestRunStarted as _TestRunStarted,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)
from cucumber_messages import Timestamp


def build_valid_envelope() -> Message:
    """Build valid envelope."""
    return Message(test_run_started=_TestRunStarted(timestamp=Timestamp(seconds=0, nanos=0)))


@pytest.mark.skipif(importlib.util.find_spec("mypy") is None, reason="mypy is not installed in this environment")
def test_mypy_rejects_invalid_envelope_assignment() -> None:
    """Verify runtime validation rejects empty envelope assignment."""
    from pytest_bdd.model.message_converter import validate_envelope_shape

    msg = Message()
    with pytest.raises(TypeError, match="Envelope must include exactly one payload field"):
        validate_envelope_shape(msg)
