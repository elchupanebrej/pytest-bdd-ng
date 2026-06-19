"""Contract tests: validate CCK NDJSON to Allure conversion.

Tests the allure-cucumber converter with all 45 CCK sample NDJSON files
and edge cases (empty NDJSON, single-line, failed scenarios).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pytest_bdd.plugin.allure_formatter.converter import convert
from pytest_bdd.testing.cck import CCK_SAMPLE_NAMES

pytestmark = [pytest.mark.contract]


class TestCCKAllureConversion:
    """Validate allure-cucumber converter handles all CCK samples."""

    @pytest.mark.parametrize("sample_name", CCK_SAMPLE_NAMES)
    def test_sample_produces_allure_results(
        self,
        sample_name: str,
        cck_samples: dict[str, Path],
        tmp_path: Path,
    ):
        """Each CCK sample should produce Allure result files."""
        if sample_name not in cck_samples:
            pytest.skip(f"CCK sample '{sample_name}' not available")

        ndjson_path = cck_samples[sample_name]
        output_dir = tmp_path / f"allure-{sample_name}"
        output_dir.mkdir()

        convert(ndjson_path, output_dir)

        result_files = list(output_dir.glob("*-result.json"))
        container_files = list(output_dir.glob("*-container.json"))

        # At least one result or container file should be produced
        # (empty NDJSON may produce neither)
        if ndjson_path.stat().st_size > 0:
            assert len(result_files) > 0 or len(container_files) > 0, (
                f"No Allure result/container files produced for sample '{sample_name}'"
            )

    @pytest.mark.parametrize("sample_name", CCK_SAMPLE_NAMES)
    def test_result_files_have_required_fields(
        self,
        sample_name: str,
        cck_samples: dict[str, Path],
        tmp_path: Path,
    ):
        """Each Allure result file should have required fields."""
        if sample_name not in cck_samples:
            pytest.skip(f"CCK sample '{sample_name}' not available")

        ndjson_path = cck_samples[sample_name]
        output_dir = tmp_path / f"allure-{sample_name}"
        output_dir.mkdir()

        convert(ndjson_path, output_dir)

        for result_file in output_dir.glob("*-result.json"):
            with Path(result_file).open(encoding="utf-8") as f:
                data = json.load(f)
            assert "name" in data, f"Result file {result_file.name} missing 'name' field"
            assert "status" in data, f"Result file {result_file.name} missing 'status' field"

    def test_empty_ndjson_produces_no_results(self, tmp_path: Path):
        """Empty NDJSON should not crash and should produce no results."""
        ndjson_path = tmp_path / "empty.ndjson"
        ndjson_path.write_text("", encoding="utf-8")

        output_dir = tmp_path / "allure-results"
        output_dir.mkdir()

        convert(ndjson_path, output_dir)

        result_files = list(output_dir.glob("*-result.json"))
        assert len(result_files) == 0, "Empty NDJSON should produce no result files"

    def test_single_line_ndjson_produces_minimal_output(self, tmp_path: Path):
        """NDJSON with only testRunStarted should produce minimal output."""
        ndjson_path = tmp_path / "single-line.ndjson"
        line = json.dumps({"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}})
        ndjson_path.write_text(line + "\n", encoding="utf-8")

        output_dir = tmp_path / "allure-results"
        output_dir.mkdir()

        convert(ndjson_path, output_dir)

        # May produce no results or minimal results - just verify no crash
        result_files = list(output_dir.glob("*-result.json"))
        container_files = list(output_dir.glob("*-container.json"))
        # A single testRunStarted produces one result with "Test Run" name
        if result_files:
            with Path(result_files[0]).open(encoding="utf-8") as f:
                data = json.load(f)
            assert data["name"] == "Test Run"
            assert data["status"] in ("passed", "unknown")

    def test_failed_scenarios_render_failure_status(self, tmp_path: Path):
        """NDJSON with failed steps should produce FAILED status in Allure results."""
        ndjson_path = tmp_path / "failed.ndjson"
        lines = [
            json.dumps({"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}}),
            json.dumps(
                {
                    "testCaseStarted": {
                        "id": "case-1",
                        "testCaseId": "tc-1",
                        "attempt": 0,
                        "timestamp": {"seconds": 1, "nanos": 0},
                    },
                },
            ),
            json.dumps(
                {
                    "testStepStarted": {
                        "testStepId": "step-1",
                        "testCaseStartedId": "case-1",
                        "timestamp": {"seconds": 1, "nanos": 0},
                    },
                },
            ),
            json.dumps(
                {
                    "testStepFinished": {
                        "testStepId": "step-1",
                        "testCaseStartedId": "case-1",
                        "timestamp": {"seconds": 2, "nanos": 0},
                        "testStepResult": {
                            "status": "FAILED",
                            "duration": {"seconds": 1, "nanos": 0},
                            "message": "Step failed",
                        },
                    },
                },
            ),
            json.dumps(
                {
                    "testCaseFinished": {
                        "testCaseStartedId": "case-1",
                        "timestamp": {"seconds": 2, "nanos": 0},
                        "willBeRetried": False,
                    },
                },
            ),
            json.dumps({"testRunFinished": {"success": False, "timestamp": {"seconds": 3, "nanos": 0}}}),
        ]
        ndjson_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        output_dir = tmp_path / "allure-results"
        output_dir.mkdir()

        convert(ndjson_path, output_dir)

        result_files = list(output_dir.glob("*-result.json"))
        assert len(result_files) > 0, "Failed scenario should produce result files"

        for result_file in result_files:
            with Path(result_file).open(encoding="utf-8") as f:
                data = json.load(f)
            assert data.get("status") == "failed", (
                f"Expected failed status (Allure3 lowercase), got {data.get('status')}"
            )
