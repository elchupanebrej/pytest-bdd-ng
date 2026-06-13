"""Unit tests for the event collector module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pytest_bdd.model.execution_message_adapter import ExecutionProjection
from pytest_bdd.plugin.allure_formatter.converter.collector import group_by_test_case

pytestmark = [pytest.mark.unit]


def _make_projection(case_id: str | None = "case-1", event_type: str = "test_case_started") -> MagicMock:
    """Create a mock ExecutionProjection with given testCaseStartedId."""
    projection = MagicMock(spec=ExecutionProjection)
    projection.payload = MagicMock()
    projection.payload_kind = MagicMock()
    projection.payload_kind.value = event_type
    if case_id is not None:
        projection.payload.test_case_started_id = case_id
    else:
        projection.payload.test_case_started_id = None
        projection.payload.testCaseStartedId = None
        projection.payload.test_run_started_id = None
        projection.payload.testRunStartedId = None
    return projection


class TestCollector:
    """Tests for group_by_test_case function."""

    def test_empty_iterator(self) -> None:
        """Empty projections produce empty dict and empty structural context."""
        grouped, structural = group_by_test_case([])
        assert grouped == {}
        assert structural == {}

    def test_single_case_grouping(self) -> None:
        """Projections with same case_id grouped together."""
        projections = [_make_projection("c1"), _make_projection("c1")]
        grouped, _structural = group_by_test_case(projections)
        assert len(grouped) == 1
        assert "c1" in grouped
        assert len(grouped["c1"]) == 2

    def test_multi_case_grouping(self) -> None:
        """Projections with different case_ids form separate groups."""
        projections = [
            _make_projection("c1"),
            _make_projection("c2"),
            _make_projection("c1"),
        ]
        grouped, _structural = group_by_test_case(projections)
        assert len(grouped) == 2
        assert len(grouped["c1"]) == 2
        assert len(grouped["c2"]) == 1

    def test_skips_no_id_events(self) -> None:
        """Projections without testCaseStartedId or testRunStartedId are skipped."""
        projections = [_make_projection(None, event_type="attachment"), _make_projection("c1")]
        grouped, _structural = group_by_test_case(projections)
        assert len(grouped) == 1
        assert "c1" in grouped

    def test_handles_camel_case_ids(self) -> None:
        """Projections using camelCase testCaseStartedId attribute."""
        projection = MagicMock(spec=ExecutionProjection)
        projection.payload = MagicMock(spec=[])  # no snake_case attr
        projection.payload.testCaseStartedId = "camel-case-1"
        grouped, _structural = group_by_test_case([projection])
        assert "camel-case-1" in grouped

    def test_preserves_order(self) -> None:
        """Projections within a group preserve insertion order."""
        projections = [_make_projection("c1"), _make_projection("c1")]
        grouped, _structural = group_by_test_case(projections)
        assert grouped["c1"][0] is projections[0]
        assert grouped["c1"][1] is projections[1]

    def test_indexes_structural_messages(self) -> None:
        """Structural messages (pickle, test_case, hook) are indexed in context."""
        pickle_proj = MagicMock(spec=ExecutionProjection)
        pickle_proj.payload_kind.value = "pickle"
        pickle_proj.payload.id = "pk-1"
        pickle_proj.payload.name = "My Scenario"
        pickle_proj.payload.steps = []

        tc_proj = MagicMock(spec=ExecutionProjection)
        tc_proj.payload_kind.value = "test_case"
        tc_proj.payload.id = "tc-1"
        tc_proj.payload.pickle_id = "pk-1"
        tc_proj.payload.test_steps = []

        hook_proj = MagicMock(spec=ExecutionProjection)
        hook_proj.payload_kind.value = "hook"
        hook_proj.payload.id = "hk-1"
        hook_proj.payload.name = "setUp"

        # Also need an execution event to trigger indexing
        exec_proj = _make_projection("c1")

        _grouped, structural = group_by_test_case([exec_proj, pickle_proj, tc_proj, hook_proj])
        assert ("pickle", "pk-1") in structural
        assert ("test_case", "tc-1") in structural
        assert ("hook", "hk-1") in structural
        assert structural["pickle", "pk-1"].name == "My Scenario"

    def test_structural_test_case_with_run_id_is_not_grouped_as_run_event(self) -> None:
        """Structural TestCase links are indexed only, not rendered as run attachments."""
        run_started = _make_projection(None, event_type="test_run_started")
        run_started.payload.id = "run-1"

        test_case = _make_projection(None, event_type="test_case")
        test_case.payload.id = "tc-1"
        test_case.payload.pickle_id = "pk-1"
        test_case.payload.test_run_started_id = "run-1"

        grouped, structural = group_by_test_case([run_started, test_case])

        assert [projection.payload_kind.value for projection in grouped["run:run-1"]] == ["test_run_started"]
        assert ("test_case", "tc-1") in structural
