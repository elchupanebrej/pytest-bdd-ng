"""Unit tests for the Allure-Cucumber converter modules."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from cucumber_messages import TestCaseStarted as MsgTestCaseStarted

from pytest_bdd.model.execution_message_adapter import ExecutionProjection
from pytest_bdd.plugin.allure_formatter.converter.collector import group_by_test_case
from pytest_bdd.plugin.allure_formatter.converter.emitter import emit_container, emit_results
from pytest_bdd.plugin.allure_formatter.converter.mapper import (
    _map_status,
    map_test_case_to_result,
    map_unmappable_to_attachment,
)
from pytest_bdd.plugin.allure_formatter.converter.model import AllureAttachment, AllureTestResult
from pytest_bdd.plugin.allure_formatter.converter.step_tree import build_step_tree

pytestmark = [pytest.mark.unit]

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def mock_projection() -> MagicMock:
    """Create a mock ExecutionProjection."""
    projection = MagicMock(spec=ExecutionProjection)
    projection.payload_kind = MagicMock()
    projection.payload_kind.value = "test_case_started"
    projection.payload = MagicMock(spec=MsgTestCaseStarted)
    projection.payload.timestamp = 1234567890
    projection.payload.test_case_started_id = "test-123"
    projection.payload.testCaseStartedId = "test-123"
    return projection


@pytest.fixture
def sample_ndjson_file(tmp_path: Path) -> Path:
    """Create a sample NDJSON file for testing."""
    ndjson_content = json.dumps(
        {
            "meta": {"schema": "cucumber-messages/1.0"},
            "type": "TestCaseStarted",
            "testCaseStarted": {
                "id": "test-123",
                "testCaseId": "tc-123",
                "pickleId": "pickle-123",
                "timestamp": 1234567890,
            },
        },
    )
    file_path = tmp_path / "test-messages.ndjson"
    file_path.write_text(ndjson_content, encoding="utf-8")
    return file_path


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output = tmp_path / "allure-results"
    output.mkdir(parents=True, exist_ok=True)
    return output


def test_group_by_test_case_empty() -> None:
    """Test grouping with empty projections."""
    grouped, structural = group_by_test_case([])
    assert grouped == {}
    assert structural == {}


def test_group_by_test_case_single(mock_projection: MagicMock) -> None:
    """Test grouping with a single projection."""
    grouped, _structural = group_by_test_case([mock_projection])
    assert len(grouped) == 1
    assert "test-123" in grouped


def test_map_status_passed() -> None:
    """Test mapping passed status."""
    assert _map_status("passed") == "passed"


def test_map_status_failed() -> None:
    """Test mapping failed status."""
    assert _map_status("failed") == "failed"


def test_map_status_unknown() -> None:
    """Test mapping unknown status."""
    assert _map_status("unknown") == "skipped"


def test_map_test_case_to_result() -> None:
    """Test mapping a test case to AllureTestResult with structural context."""
    proj = MagicMock(spec=ExecutionProjection)
    proj.payload_kind = MagicMock()
    proj.payload_kind.value = "test_case_started"
    proj.payload = MagicMock(spec=MsgTestCaseStarted)
    proj.payload.test_case_id = "tc-1"
    proj.payload.timestamp = 1234567890
    mock_tc = MagicMock()
    mock_tc.pickle_id = "pk-1"
    mock_pickle = MagicMock()
    mock_pickle.name = "Test Feature"
    mock_pickle.steps = []
    structural = {
        ("test_case", "tc-1"): mock_tc,
        ("pickle", "pk-1"): mock_pickle,
    }
    result = map_test_case_to_result("test-123", [proj], structural)
    assert isinstance(result, AllureTestResult)
    assert result.uuid == "test-123"
    assert result.name == "Test Feature"


def test_map_unmappable_to_attachment(mock_projection: MagicMock) -> None:
    """Test mapping unmappable event to attachment."""
    attachment = map_unmappable_to_attachment(mock_projection)
    assert isinstance(attachment, AllureAttachment)
    assert attachment.name.startswith("unmapped-")


def test_build_step_tree_empty() -> None:
    """Test building step tree from empty projections."""
    result = build_step_tree([])
    assert result == []


def test_emit_results_empty(output_dir: Path) -> None:
    """Test emitting empty results."""
    emit_results([], output_dir)
    assert output_dir.exists()


def test_emit_results_single(output_dir: Path) -> None:
    """Test emitting a single result."""
    result = AllureTestResult(uuid="test-123", name="Test")
    emit_results([result], output_dir)
    files = list(output_dir.glob("*-result.json"))
    assert len(files) == 1
    content = json.loads(files[0].read_text(encoding="utf-8"))
    assert content["uuid"] == "test-123"


def test_emit_container_single(output_dir: Path) -> None:
    """Test emitting a container referencing one result."""
    result = AllureTestResult(uuid="test-456", name="Test")
    container_path = emit_container([result], output_dir)
    assert container_path.exists()
    content = json.loads(container_path.read_text(encoding="utf-8"))
    assert "uuid" in content
    assert content["children"] == ["test-456"]
