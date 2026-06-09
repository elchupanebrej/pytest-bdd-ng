"""Unit tests for the JSON emitter module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.plugin.allure_cucumber.converter.emitter import emit_container, emit_results
from pytest_bdd.plugin.allure_cucumber.converter.model import AllureTestResult

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.unit]


class TestEmitResults:
    """Tests for emit_results function."""

    def test_empty_results(self, tmp_path: Path) -> None:
        """Empty results list creates dir but no files."""
        output = tmp_path / "out"
        written = emit_results([], output)
        assert output.exists()
        assert written == []

    def test_single_result(self, tmp_path: Path) -> None:
        """Single result produces one JSON file."""
        output = tmp_path / "out"
        result = AllureTestResult(uuid="test-uuid", name="Test")
        written = emit_results([result], output)
        assert len(written) == 1
        assert written[0].exists()
        content = json.loads(written[0].read_text(encoding="utf-8"))
        assert content["uuid"] == "test-uuid"
        assert content["name"] == "Test"

    def test_json_is_valid(self, tmp_path: Path) -> None:
        """Emitted JSON is valid and has correct structure."""
        output = tmp_path / "out"
        result = AllureTestResult(uuid="u1", name="T", status="passed")
        emit_results([result], output)
        files = list(output.glob("*-result.json"))
        content = json.loads(files[0].read_text(encoding="utf-8"))
        assert "uuid" in content
        assert "name" in content
        assert "status" in content
        assert "steps" in content
        assert "attachments" in content


class TestEmitContainer:
    """Tests for emit_container function."""

    def test_creates_container_file(self, tmp_path: Path) -> None:
        """Container is written as JSON file."""
        output = tmp_path / "out"
        result = AllureTestResult(uuid="r1", name="T")
        path = emit_container([result], output)
        assert path.exists()
        assert path.name.endswith("-container.json")

    def test_container_references_results(self, tmp_path: Path) -> None:
        """Container children list references result UUIDs."""
        output = tmp_path / "out"
        r1 = AllureTestResult(uuid="uuid-1", name="T1")
        r2 = AllureTestResult(uuid="uuid-2", name="T2")
        path = emit_container([r1, r2], output)
        content = json.loads(path.read_text(encoding="utf-8"))
        assert content["children"] == ["uuid-1", "uuid-2"]

    def test_json_is_valid(self, tmp_path: Path) -> None:
        """Container JSON has required fields."""
        output = tmp_path / "out"
        path = emit_container([], output)
        content = json.loads(path.read_text(encoding="utf-8"))
        assert "uuid" in content
        assert "name" in content
        assert "children" in content
