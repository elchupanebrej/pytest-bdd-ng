"""Unit tests for the cucumber-to-allure mapper module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from cucumber_messages import (
    Attachment as MsgAttachment,
)
from cucumber_messages import (
    Hook as MsgHook,
)
from cucumber_messages import (
    Pickle as MsgPickle,
)
from cucumber_messages import (
    TestCase as MsgTestCase,
)
from cucumber_messages import (
    TestCaseFinished as MsgTestCaseFinished,
)
from cucumber_messages import (
    TestCaseStarted as MsgTestCaseStarted,
)
from cucumber_messages import (
    TestRunFinished as MsgTestRunFinished,
)
from cucumber_messages import (
    TestRunHookFinished as MsgTestRunHookFinished,
)
from cucumber_messages import (
    TestRunHookStarted as MsgTestRunHookStarted,
)
from cucumber_messages import (
    TestRunStarted as MsgTestRunStarted,
)
from cucumber_messages import (
    TestStepFinished as MsgTestStepFinished,
)
from cucumber_messages import (
    TestStepStarted as MsgTestStepStarted,
)

from pytest_bdd.model.execution_message_adapter import ExecutionProjection
from pytest_bdd.plugin.allure_formatter.converter.mapper import (
    _map_status,
    map_test_case_to_result,
    map_unmappable_to_attachment,
)
from pytest_bdd.plugin.allure_formatter.converter.model import (
    AllureAttachment,
    AllureTestResult,
)

pytestmark = [pytest.mark.unit]


def _make_projection(event_type: str, **payload_attrs: object) -> MagicMock:
    """Create a mock ExecutionProjection with given event type."""
    projection = MagicMock(spec=ExecutionProjection)
    projection.payload_kind = MagicMock()
    projection.payload_kind.value = event_type

    class_map = {
        "test_case_started": MsgTestCaseStarted,
        "test_case_finished": MsgTestCaseFinished,
        "test_step_started": MsgTestStepStarted,
        "test_step_finished": MsgTestStepFinished,
        "test_run_started": MsgTestRunStarted,
        "test_run_finished": MsgTestRunFinished,
        "test_run_hook_started": MsgTestRunHookStarted,
        "test_run_hook_finished": MsgTestRunHookFinished,
        "attachment": MsgAttachment,
        "pickle": MsgPickle,
        "test_case": MsgTestCase,
        "hook": MsgHook,
    }
    payload_class = class_map.get(event_type.lower())
    if payload_class is not None:
        projection.payload = MagicMock(spec=payload_class)
    else:
        projection.payload = MagicMock()

    for key, value in payload_attrs.items():
        setattr(projection.payload, key, value)
    return projection


def test_status_passed() -> None:
    assert _map_status("passed") == "passed"


def test_status_failed() -> None:
    assert _map_status("failed") == "failed"


def test_status_skipped() -> None:
    assert _map_status("skipped") == "skipped"


def test_status_unknown() -> None:
    assert _map_status("unknown") == "skipped"


def test_status_case_insensitive() -> None:
    assert _map_status("PASSED") == "passed"


def test_maps_name_from_test_case_started() -> None:
    """TestCaseStarted resolves name from Pickle via lookup chain."""
    proj_started = _make_projection(
        "test_case_started",
        test_case_id="tc-1",
        timestamp=1000,
    )
    # Build structural context with test_case -> pickle lookup
    mock_tc = MagicMock()
    mock_tc.pickle_id = "pk-1"
    mock_pickle = MagicMock()
    mock_pickle.name = "My Test"
    mock_pickle.steps = []
    structural = {
        ("test_case", "tc-1"): mock_tc,
        ("pickle", "pk-1"): mock_pickle,
    }
    result = map_test_case_to_result("c1", [proj_started], structural)
    assert isinstance(result, AllureTestResult)
    assert result.name == "My Test"
    assert result.uuid == "c1"


def test_maps_status_from_test_step_finished() -> None:
    """Last TestStepFinished sets result status via test_step_id matching."""
    proj_started = _make_projection("test_case_started", test_case_id="tc-1", timestamp=0)
    proj_step_started = _make_projection(
        "test_step_started",
        test_step_id="step-1",
        timestamp=100,
    )
    step_result_mock = MagicMock()
    step_result_mock.status.value = "failed"
    proj_step_finished = _make_projection(
        "test_step_finished",
        test_step_id="step-1",
        timestamp=200,
    )
    proj_step_finished.payload.test_step_result = step_result_mock
    proj_finished = _make_projection("test_case_finished", timestamp=1000)
    result = map_test_case_to_result(
        "c1",
        [proj_started, proj_step_started, proj_step_finished, proj_finished],
    )
    assert result.status == "failed"


def test_unmappable_becomes_attachment() -> None:
    """Unmappable event types produce attachments, not silent drops."""
    proj_unknown = _make_projection("some_unknown_event")
    result = map_test_case_to_result("c1", [proj_unknown])
    assert len(result.attachments) == 1
    assert result.attachments[0].name.startswith("unmapped-")


def test_run_result_start_uses_test_run_started_timestamp() -> None:
    """Run-level result start time comes from TestRunStarted, not Unix epoch."""
    proj_run_started = _make_projection("test_run_started", id="run-1", timestamp=1000)
    proj_run_finished = _make_projection("test_run_finished", success=True, timestamp=2000)

    result = map_test_case_to_result("run:run-1", [proj_run_started, proj_run_finished])

    assert result.start == 1000
    assert result.stop == 2000


def test_returns_allure_attachment() -> None:
    proj = MagicMock(spec=ExecutionProjection)
    proj.payload_kind = MagicMock()
    proj.payload_kind.value = "custom_event"
    attachment = map_unmappable_to_attachment(proj)
    assert isinstance(attachment, AllureAttachment)
    assert "unmapped-" in attachment.name
    assert attachment.type == "application/json"
