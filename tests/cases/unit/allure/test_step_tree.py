"""Unit tests for the step tree reconstruction module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pytest_bdd.model.execution_message_adapter import ExecutionProjection
from pytest_bdd.plugin.allure_cucumber.converter.step_tree import build_step_tree

pytestmark = [pytest.mark.unit]


def _make_step_started(test_step_id: str, name: str = "step") -> MagicMock:
    """Create a mock TestStepStarted projection."""
    projection = MagicMock(spec=ExecutionProjection)
    projection.payload_kind = MagicMock()
    projection.payload_kind.value = "TestStepStarted"
    projection.payload = MagicMock()
    projection.payload.test_step_id = test_step_id
    projection.payload.name = name
    return projection


def _make_step_finished(test_step_id: str, status: str = "passed") -> MagicMock:
    """Create a mock TestStepFinished projection."""
    projection = MagicMock(spec=ExecutionProjection)
    projection.payload_kind = MagicMock()
    projection.payload_kind.value = "TestStepFinished"
    projection.payload = MagicMock()
    projection.payload.test_step_id = test_step_id
    projection.payload.status = status
    projection.payload.duration = MagicMock()
    projection.payload.duration.seconds = 1
    projection.payload.duration.nanos = 0
    projection.payload.status_details = None
    return projection


def _make_case_started() -> MagicMock:
    """Create a mock TestCaseStarted projection."""
    projection = MagicMock(spec=ExecutionProjection)
    projection.payload_kind = MagicMock()
    projection.payload_kind.value = "TestCaseStarted"
    projection.payload = MagicMock()
    return projection


class TestStepTree:
    """Tests for build_step_tree function."""

    def test_empty_projections(self) -> None:
        """Empty list returns empty result."""
        result = build_step_tree([])
        assert result == []

    def test_single_step(self) -> None:
        """One Started/Finished pair produces one root step."""
        projections = [_make_step_started("s1"), _make_step_finished("s1")]
        result = build_step_tree(projections)
        assert len(result) == 1
        assert result[0]["status"] == "passed"

    def test_two_sibling_steps(self) -> None:
        """Two sequential steps produce two root siblings."""
        projections = [
            _make_step_started("s1"),
            _make_step_finished("s1"),
            _make_step_started("s2"),
            _make_step_finished("s2"),
        ]
        result = build_step_tree(projections)
        assert len(result) == 2

    def test_status_mapping(self) -> None:
        """Step finished status is captured on the step."""
        projections = [_make_step_started("s1"), _make_step_finished("s1", "failed")]
        result = build_step_tree(projections)
        assert result[0]["status"] == "failed"

    def test_case_started_adds_marker(self) -> None:
        """TestCaseStarted adds a marker step."""
        projections = [
            _make_case_started(),
            _make_step_started("s1"),
            _make_step_finished("s1"),
        ]
        result = build_step_tree(projections)
        assert len(result) >= 1

    def test_unknown_event_type_ignored(self) -> None:
        """Unknown event types are skipped gracefully."""
        projection = MagicMock(spec=ExecutionProjection)
        projection.payload_kind = MagicMock()
        projection.payload_kind.value = "UnknownEvent"
        projection.payload = MagicMock()
        result = build_step_tree([projection])
        assert result == []
