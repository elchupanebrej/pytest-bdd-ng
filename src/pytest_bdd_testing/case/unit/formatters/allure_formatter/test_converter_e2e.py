"""End-to-end tests for the converter pipeline."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.plugin.allure_formatter.converter import convert

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.unit]


def _write_ndjson(path: Path, lines: list[dict]) -> None:
    """Write a list of cucumber message dicts as NDJSON."""
    path.write_text(
        "\n".join(json.dumps(line) for line in lines) + "\n",
        encoding="utf-8",
    )


class TestConverterE2E:
    """End-to-end converter tests."""

    def test_produces_output_files(self, tmp_path: Path) -> None:
        """Convert produces result and container JSON files."""
        ndjson = tmp_path / "messages.ndjson"
        _write_ndjson(
            ndjson,
            [
                {"testRunStarted": {"id": "r1", "timestamp": {"seconds": 0, "nanos": 0}}},
                {
                    "testCaseStarted": {
                        "id": "c1",
                        "testCaseId": "tc1",
                        "attempt": 0,
                        "timestamp": {"seconds": 1, "nanos": 0},
                    },
                },
                {
                    "testStepStarted": {
                        "testStepId": "s1",
                        "testCaseStartedId": "c1",
                        "timestamp": {"seconds": 1, "nanos": 0},
                    },
                },
                {
                    "testStepFinished": {
                        "testStepId": "s1",
                        "testCaseStartedId": "c1",
                        "timestamp": {"seconds": 2, "nanos": 0},
                        "testStepResult": {
                            "status": "PASSED",
                            "duration": {"seconds": 1, "nanos": 0},
                            "exception": None,
                            "message": None,
                        },
                    },
                },
                {
                    "testCaseFinished": {
                        "testCaseStartedId": "c1",
                        "timestamp": {"seconds": 2, "nanos": 0},
                        "willBeRetried": False,
                    },
                },
                {"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}},
            ],
        )

        output = tmp_path / "allure-results"
        convert(ndjson, output)

        result_files = list(output.glob("*-result.json"))
        container_files = list(output.glob("*-container.json"))
        assert len(result_files) >= 1, f"Expected result files, got {len(result_files)}"
        assert len(container_files) >= 1, f"Expected container files, got {len(container_files)}"

    def test_empty_ndjson_no_error(self, tmp_path: Path) -> None:
        """Empty NDJSON file completes without error."""
        ndjson = tmp_path / "empty.ndjson"
        ndjson.write_text("", encoding="utf-8")
        output = tmp_path / "allure-results"
        convert(ndjson, output)
        # Empty input produces no output files — no crash, no dir created
        result_files = list(output.glob("*-result.json")) if output.exists() else []
        assert result_files == []

    def test_output_json_is_valid(self, tmp_path: Path) -> None:
        """Output JSON files are valid JSON with expected structure."""
        ndjson = tmp_path / "messages.ndjson"
        _write_ndjson(
            ndjson,
            [
                {"testRunStarted": {"id": "r1", "timestamp": {"seconds": 0, "nanos": 0}}},
                {
                    "testCaseStarted": {
                        "id": "c1",
                        "testCaseId": "tc1",
                        "attempt": 0,
                        "timestamp": {"seconds": 1, "nanos": 0},
                    },
                },
                {
                    "testStepStarted": {
                        "testStepId": "s1",
                        "testCaseStartedId": "c1",
                        "timestamp": {"seconds": 1, "nanos": 0},
                    },
                },
                {
                    "testStepFinished": {
                        "testStepId": "s1",
                        "testCaseStartedId": "c1",
                        "timestamp": {"seconds": 2, "nanos": 0},
                        "testStepResult": {
                            "status": "PASSED",
                            "duration": {"seconds": 1, "nanos": 0},
                            "exception": None,
                            "message": None,
                        },
                    },
                },
                {
                    "testCaseFinished": {
                        "testCaseStartedId": "c1",
                        "timestamp": {"seconds": 2, "nanos": 0},
                        "willBeRetried": False,
                    },
                },
                {"testRunFinished": {"success": True, "timestamp": {"seconds": 3, "nanos": 0}}},
            ],
        )

        output = tmp_path / "allure-results"
        convert(ndjson, output)

        for f in output.glob("*.json"):
            content = json.loads(f.read_text(encoding="utf-8"))
            assert "uuid" in content, f"{f.name} missing uuid"
