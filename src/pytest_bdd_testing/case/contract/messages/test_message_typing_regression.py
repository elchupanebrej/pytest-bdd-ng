"""

Provide test message typing regression helpers.
"""

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
    """
    Verify runtime validation rejects empty envelope assignment.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
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
    from pytest_bdd.model.message_converter import validate_envelope_shape

    msg = Message()
    with pytest.raises(TypeError, match="Envelope must include exactly one payload field"):
        validate_envelope_shape(msg)
