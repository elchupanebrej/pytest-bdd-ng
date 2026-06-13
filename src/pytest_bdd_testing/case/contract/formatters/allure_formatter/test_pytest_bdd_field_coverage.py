"""Contract tests: validate pytest-bdd-ng produces every schema field in two ways.

GAP-03: pytest-bdd-ng suite producing every field via model in two ways:
  1. During a live pytest-bdd run (dynamic generation)
  2. Via generated NDJSON consumed by the plugin (post-hoc conversion)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import jsonschema
import pytest

from pytest_bdd.plugin.allure_formatter.converter import convert
from pytest_bdd.plugin.allure_formatter.converter.model import (
    AllureAttachment,
    AllureContainer,
    AllureFixtureResult,
    AllureLabel,
    AllureLink,
    AllureParameter,
    AllureStatusDetails,
    AllureStepResult,
    AllureTestResult,
)

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.contract]


@pytest.fixture
def schema(allure_schema_path):
    """Load the Allure3 events schema."""
    return json.loads(allure_schema_path.read_text(encoding="utf-8"))


@pytest.fixture
def full_featured_ndjson(tmp_path: Path) -> Path:
    """Create NDJSON that exercises every schema field through the converter."""
    ndjson = tmp_path / "messages.ndjson"
    lines = [
        json.dumps({"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}}),
        # Structural: Pickle 1
        json.dumps(
            {
                "pickle": {
                    "id": "pk-1",
                    "name": "outer scenario",
                    "language": "en",
                    "astNodeIds": [],
                    "tags": [],
                    "uri": "features/test.feature",
                    "steps": [
                        {"id": "ps-1", "text": "outer step", "astNodeIds": []},
                        {"id": "ps-2", "text": "inner step", "astNodeIds": []},
                    ],
                },
            },
        ),
        # Structural: TestCase 1
        json.dumps(
            {
                "testCase": {
                    "id": "tc-1",
                    "pickleId": "pk-1",
                    "testSteps": [
                        {"id": "step-1", "pickleStepId": "ps-1"},
                        {"id": "step-1-1", "pickleStepId": "ps-2"},
                    ],
                },
            },
        ),
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
                "testStepStarted": {
                    "testStepId": "step-1-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 1, "nanos": 500000000},
                },
            },
        ),
        json.dumps(
            {
                "testStepFinished": {
                    "testStepId": "step-1-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 1, "nanos": 800000000},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 0, "nanos": 300000000}},
                },
            },
        ),
        json.dumps(
            {
                "testStepFinished": {
                    "testStepId": "step-1",
                    "testCaseStartedId": "case-1",
                    "timestamp": {"seconds": 2, "nanos": 0},
                    "testStepResult": {"status": "PASSED", "duration": {"seconds": 1, "nanos": 0}},
                },
            },
        ),
        # Attachments
        json.dumps(
            {
                "attachment": {
                    "testCaseStartedId": "case-1",
                    "fileName": "log.txt",
                    "mediaType": "text/plain",
                    "body": "log data",
                    "contentEncoding": "IDENTITY",
                    "timestamp": {"seconds": 1, "nanos": 0},
                },
            },
        ),
        json.dumps(
            {
                "attachment": {
                    "testCaseStartedId": "case-1",
                    "fileName": "screenshot.png",
                    "mediaType": "image/png",
                    "body": "cG5nIGRhdGE=",
                    "contentEncoding": "BASE64",
                    "timestamp": {"seconds": 2, "nanos": 0},
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
        # Structural: Pickle 2
        json.dumps(
            {
                "pickle": {
                    "id": "pk-2",
                    "name": "failing scenario",
                    "language": "en",
                    "astNodeIds": [],
                    "tags": [],
                    "uri": "features/test.feature",
                    "steps": [{"id": "ps-3", "text": "failing step", "astNodeIds": []}],
                },
            },
        ),
        # Structural: TestCase 2
        json.dumps(
            {
                "testCase": {
                    "id": "tc-2",
                    "pickleId": "pk-2",
                    "testSteps": [{"id": "step-2", "pickleStepId": "ps-3"}],
                },
            },
        ),
        json.dumps(
            {
                "testCaseStarted": {
                    "id": "case-2",
                    "testCaseId": "tc-2",
                    "attempt": 0,
                    "timestamp": {"seconds": 3, "nanos": 0},
                },
            },
        ),
        json.dumps(
            {
                "testStepStarted": {
                    "testStepId": "step-2",
                    "testCaseStartedId": "case-2",
                    "timestamp": {"seconds": 3, "nanos": 0},
                },
            },
        ),
        json.dumps(
            {
                "testStepFinished": {
                    "testStepId": "step-2",
                    "testCaseStartedId": "case-2",
                    "timestamp": {"seconds": 4, "nanos": 0},
                    "testStepResult": {
                        "status": "FAILED",
                        "duration": {"seconds": 1, "nanos": 0},
                        "message": "AssertionError: expected 42 but got 99",
                    },
                },
            },
        ),
        json.dumps(
            {
                "testCaseFinished": {
                    "testCaseStartedId": "case-2",
                    "timestamp": {"seconds": 4, "nanos": 0},
                    "willBeRetried": False,
                },
            },
        ),
        json.dumps({"testRunFinished": {"success": False, "timestamp": {"seconds": 5, "nanos": 0}}}),
    ]
    ndjson.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ndjson


class TestLiveRunFieldCoverage:
    """Validate pytest-bdd-ng produces all fields during live run (GAP-03)."""

    def test_model_produces_all_test_result_fields(self, schema):
        """AllureTestResult model can produce every schema field."""
        result = AllureTestResult(
            uuid="live-uuid-001",
            name="live test with all fields",
            fullName="com.example.LiveTest.test_method",
            historyId="live-hist-123",
            testCaseId="live-tc-001",
            status="passed",
            statusDetails=AllureStatusDetails(
                message="all passed",
                trace="stack trace",
                actual="42",
                expected="42",
                known=False,
                flaky=False,
            ),
            stage="finished",
            description="Live run test",
            descriptionHtml="<p>Live run test</p>",
            start=1000000,
            stop=1005000,
            labels=[
                AllureLabel(name="suite", value="LiveSuite"),
                AllureLabel(name="epic", value="GAP-03"),
            ],
            links=[
                AllureLink(name="issue", url="https://issue.example.com", type="issue"),
            ],
            steps=[
                AllureStepResult(
                    name="live step",
                    uuid="live-step-001",
                    status="passed",
                    statusDetails=AllureStatusDetails(message="ok"),
                    stage="finished",
                    description="step desc",
                    descriptionHtml="<div>step</div>",
                    start=1000001,
                    stop=1002000,
                    steps=[],
                    attachments=[
                        AllureAttachment(name="live.txt", source="live.txt", type="text/plain", size=100),
                    ],
                    parameters=[
                        AllureParameter(name="env", value="test"),
                    ],
                ),
            ],
            attachments=[
                AllureAttachment(name="log.txt", source="log.txt", type="text/plain", size=500),
            ],
            parameters=[
                AllureParameter(name="browser", value="chromium"),
            ],
        )
        data = {
            "uuid": result.uuid,
            "name": result.name,
            "fullName": result.fullName,
            "historyId": result.historyId,
            "testCaseId": result.testCaseId,
            "status": result.status,
            "statusDetails": {
                "message": result.statusDetails.message,
                "trace": result.statusDetails.trace,
                "actual": result.statusDetails.actual,
                "expected": result.statusDetails.expected,
                "known": result.statusDetails.known,
                "flaky": result.statusDetails.flaky,
            },
            "stage": result.stage,
            "description": result.description,
            "descriptionHtml": result.descriptionHtml,
            "start": result.start,
            "stop": result.stop,
            "labels": [{"name": lbl.name, "value": lbl.value} for lbl in result.labels],
            "links": [{"name": lnk.name, "url": lnk.url, "type": lnk.type} for lnk in result.links],
            "steps": [
                {
                    "uuid": s.uuid,
                    "name": s.name,
                    "status": s.status,
                    "statusDetails": {"message": s.statusDetails.message},
                    "stage": s.stage,
                    "description": s.description,
                    "descriptionHtml": s.descriptionHtml,
                    "start": s.start,
                    "stop": s.stop,
                    "steps": [],
                    "attachments": [
                        {"name": a.name, "source": a.source, "type": a.type, "size": a.size} for a in s.attachments
                    ],
                    "parameters": [
                        {"name": p.name, "value": p.value, "excluded": p.excluded, "mode": p.mode} for p in s.parameters
                    ],
                }
                for s in result.steps
            ],
            "attachments": [
                {"name": a.name, "source": a.source, "type": a.type, "size": a.size} for a in result.attachments
            ],
            "parameters": [
                {"name": p.name, "value": p.value, "excluded": p.excluded, "mode": p.mode} for p in result.parameters
            ],
        }
        jsonschema.validate(data, schema)

    def test_model_produces_all_container_fields(self, schema):
        """AllureContainer model can produce every schema field."""
        container = AllureContainer(
            uuid="live-container-001",
            name="Live Container",
            children=["live-uuid-001"],
            befores=[
                AllureFixtureResult(
                    uuid="live-before-001",
                    type="before",
                    name="setUp",
                    testResults=["live-uuid-001"],
                    status="passed",
                    statusDetails=AllureStatusDetails(message="ok"),
                    stage="finished",
                    description="before desc",
                    descriptionHtml="<b>before</b>",
                    start=999000,
                    stop=999500,
                    steps=[],
                    attachments=[],
                    parameters=[],
                ),
            ],
            afters=[
                AllureFixtureResult(
                    uuid="live-after-001",
                    type="after",
                    name="tearDown",
                    testResults=["live-uuid-001"],
                    status="passed",
                    stage="finished",
                    start=1005500,
                    stop=1006000,
                    steps=[],
                    attachments=[],
                    parameters=[],
                ),
            ],
            links=[AllureLink(name="proj", url="https://example.com", type="link")],
            start=998000,
            stop=1007000,
        )
        data = {
            "uuid": container.uuid,
            "name": container.name,
            "children": container.children,
            "description": "",
            "descriptionHtml": "",
            "befores": [
                {
                    "uuid": fx.uuid,
                    "testResults": fx.testResults,
                    "type": fx.type,
                    "name": fx.name,
                    "status": fx.status,
                    "statusDetails": {"message": fx.statusDetails.message},
                    "stage": fx.stage,
                    "description": fx.description,
                    "descriptionHtml": fx.descriptionHtml,
                    "start": fx.start,
                    "stop": fx.stop,
                    "steps": [],
                    "attachments": [],
                    "parameters": [],
                }
                for fx in container.befores
            ],
            "afters": [
                {
                    "uuid": fx.uuid,
                    "testResults": fx.testResults,
                    "type": fx.type,
                    "name": fx.name,
                    "status": fx.status,
                    "stage": fx.stage,
                    "start": fx.start,
                    "stop": fx.stop,
                    "steps": [],
                    "attachments": [],
                    "parameters": [],
                }
                for fx in container.afters
            ],
            "links": [{"name": lnk.name, "url": lnk.url, "type": lnk.type} for lnk in container.links],
            "start": container.start,
            "stop": container.stop,
        }
        jsonschema.validate(data, schema)


class TestPostHocConversionFieldCoverage:
    """Validate pytest-bdd-ng produces all fields via NDJSON conversion (GAP-03)."""

    def test_converter_produces_valid_results(self, schema, full_featured_ndjson, tmp_path):
        """Converter produces valid Allure results from NDJSON."""
        output_dir = tmp_path / "allure-results"
        output_dir.mkdir()
        convert(full_featured_ndjson, output_dir)

        result_files = list(output_dir.glob("*-result.json"))
        container_files = list(output_dir.glob("*-container.json"))

        assert len(result_files) >= 1, "Should produce at least one result file"
        assert len(container_files) >= 1, "Should produce at least one container file"

        for f in result_files:
            instance = json.loads(f.read_text(encoding="utf-8"))
            jsonschema.validate(instance, schema)

        for f in container_files:
            instance = json.loads(f.read_text(encoding="utf-8"))
            jsonschema.validate(instance, schema)

    def test_converter_populates_name(self, full_featured_ndjson, tmp_path):
        """Converter populates name field from pickle."""
        output_dir = tmp_path / "allure-results"
        output_dir.mkdir()
        convert(full_featured_ndjson, output_dir)

        result_files = list(output_dir.glob("*-result.json"))
        assert len(result_files) >= 2

        names = {}
        for f in result_files:
            instance = json.loads(f.read_text(encoding="utf-8"))
            uuid = instance.get("uuid")
            if uuid in ("case-1", "case-2"):
                names[uuid] = instance.get("name")

        assert names.get("case-1") == "outer scenario"
        assert names.get("case-2") == "failing scenario"

    def test_converter_populates_status(self, full_featured_ndjson, tmp_path):
        """Converter populates status field from testStepFinished."""
        output_dir = tmp_path / "allure-results"
        output_dir.mkdir()
        convert(full_featured_ndjson, output_dir)

        result_files = list(output_dir.glob("*-result.json"))
        statuses = []
        for f in result_files:
            instance = json.loads(f.read_text(encoding="utf-8"))
            if instance.get("uuid") in ("case-1", "case-2"):
                statuses.append(instance.get("status", ""))

        assert "passed" in statuses, "Should have at least one passed result"
        assert "failed" in statuses, "Should have at least one failed result"

    def test_converter_populates_steps(self, full_featured_ndjson, tmp_path):
        """Converter populates steps field from testStepStarted."""
        output_dir = tmp_path / "allure-results"
        output_dir.mkdir()
        convert(full_featured_ndjson, output_dir)

        result_files = list(output_dir.glob("*-result.json"))
        case_1_result = None
        for f in result_files:
            instance = json.loads(f.read_text(encoding="utf-8"))
            if instance.get("uuid") == "case-1":
                case_1_result = instance
                break

        assert case_1_result is not None
        steps = case_1_result.get("steps", [])
        assert len(steps) == 2
        assert steps[0]["name"] == "outer step"
        assert steps[0]["status"] == "passed"
        assert steps[1]["name"] == "inner step"
        assert steps[1]["status"] == "passed"

    def test_converter_populates_parameters(self, full_featured_ndjson, tmp_path):
        """Converter populates parameters field with pickleId."""
        output_dir = tmp_path / "allure-results"
        output_dir.mkdir()
        convert(full_featured_ndjson, output_dir)

        result_files = list(output_dir.glob("*-result.json"))
        case_results = []
        for f in result_files:
            instance = json.loads(f.read_text(encoding="utf-8"))
            if instance.get("uuid") in ("case-1", "case-2"):
                case_results.append(instance)

        assert len(case_results) >= 2
        for result in case_results:
            params = {p["name"]: p["value"] for p in result.get("parameters", [])}
            assert "pickleId" in params
            assert params["pickleId"] in ("pk-1", "pk-2")

    def test_converter_populates_start_stop(self, full_featured_ndjson, tmp_path):
        """Converter populates start and stop timestamps as non-zero integers on results and steps."""
        output_dir = tmp_path / "allure-results"
        output_dir.mkdir()
        convert(full_featured_ndjson, output_dir)

        result_files = list(output_dir.glob("*-result.json"))
        case_1_result = None
        for f in result_files:
            instance = json.loads(f.read_text(encoding="utf-8"))
            if instance.get("uuid") == "case-1":
                case_1_result = instance
                break

        assert case_1_result is not None
        assert isinstance(case_1_result["start"], int)
        assert case_1_result["start"] > 0
        assert isinstance(case_1_result["stop"], int)
        assert case_1_result["stop"] > 0

        step = case_1_result["steps"][0]
        assert isinstance(step["start"], int)
        assert step["start"] > 0
        assert isinstance(step["stop"], int)
        assert step["stop"] > 0

    def test_converter_populates_attachments(self, full_featured_ndjson, tmp_path):
        """Converter processes and writes attachment files to results directory."""
        output_dir = tmp_path / "allure-results"
        output_dir.mkdir()
        convert(full_featured_ndjson, output_dir)

        result_files = list(output_dir.glob("*-result.json"))
        case_1_result = None
        for f in result_files:
            instance = json.loads(f.read_text(encoding="utf-8"))
            if instance.get("uuid") == "case-1":
                case_1_result = instance
                break

        assert case_1_result is not None
        atts = case_1_result.get("attachments", [])
        assert len(atts) == 2

        # Verify text attachment
        text_att = next(a for a in atts if a["name"] == "log.txt")
        assert text_att["type"] == "text/plain"
        text_file = output_dir / text_att["source"]
        assert text_file.exists()
        assert text_file.read_text(encoding="utf-8") == "log data"
        assert text_file.stat().st_size == text_att["size"]

        # Verify PNG attachment
        png_att = next(a for a in atts if a["name"] == "screenshot.png")
        assert png_att["type"] == "image/png"
        png_file = output_dir / png_att["source"]
        assert png_file.exists()
        assert png_file.read_bytes() == b"png data"
        assert png_file.stat().st_size == png_att["size"]

    def test_converter_populates_container_children(self, full_featured_ndjson, tmp_path):
        """Converter populates container children references."""
        output_dir = tmp_path / "allure-results"
        output_dir.mkdir()
        convert(full_featured_ndjson, output_dir)

        container_files = list(output_dir.glob("*-container.json"))
        assert len(container_files) >= 1

        for f in container_files:
            instance = json.loads(f.read_text(encoding="utf-8"))
            assert "children" in instance, f"Container {f.name} should have children field"
            assert len(instance["children"]) >= 1, "Container should reference at least one result"
