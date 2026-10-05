from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from pytest_cuke.debug_mcp.artifacts import ArtifactSink
from pytest_cuke.debug_mcp.schemas import InvestigationArtifact

pytestmark = pytest.mark.unit


def _valid_artifact(**changes: object) -> dict[str, object]:
    return {
        "artifact_id": "debug-17",
        "nodeid": "features/проверка.feature::Scenario Outline: handles <name> [line:12/案例]",
        "pytest_phase": "call",
        "status": "investigated",
        "summary": "The result changed after the fixture was configured.",
        "inspected_commands": ["pytest -q features/test_debug.feature"],
        "evidence": ["The fixture returned the stale value."],
        "suspected_cause": "The fixture reads configuration before the override.",
        "next_action": "Move the override before fixture construction.",
        "bdd_metadata": {
            "feature_path": "features/test_debug.feature",
            "feature_name": "Debug feature",
            "scenario_name": "handles <name>",
            "step_keyword": "When",
            "step_text": "I inspect the value for <name>",
            "tags": ["@debug"],
            "example_row": {"name": "пример/row"},
        },
        **changes,
    }


def test_investigation_artifact_uses_strict_schema_and_default_metadata() -> None:
    payload = _valid_artifact()

    artifact = InvestigationArtifact.model_validate(payload)

    assert artifact.bdd_metadata.example_row == {"name": "пример/row"}
    assert artifact.links == []
    assert InvestigationArtifact.model_validate(
        {key: value for key, value in payload.items() if key != "bdd_metadata"}
    ).bdd_metadata.example_row == {}


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "unknown"},
        {"pytest_phase": "collection"},
        {"status": True},
        {"unexpected": "field"},
    ],
)
def test_investigation_artifact_rejects_invalid_enum_types_and_extra_fields(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        InvestigationArtifact.model_validate(_valid_artifact(**changes))


def test_artifact_sink_writes_paired_utf8_files_without_escaping_root(tmp_path: Path) -> None:
    artifact_payload = _valid_artifact()
    root = tmp_path / "artifacts"

    result = ArtifactSink(root).write(
        sequence=7,
        nodeid=str(artifact_payload["nodeid"]),
        payload=artifact_payload,
    )

    json_path = Path(result.json_path)
    markdown_path = Path(result.markdown_path)
    assert json_path.parent == root
    assert markdown_path.parent == root
    assert json_path.suffix == ".json"
    assert markdown_path.suffix == ".md"
    stored = json.loads(json_path.read_text(encoding="utf-8"))
    assert stored["bdd_metadata"]["example_row"] == {"name": "пример/row"}
    assert stored["nodeid"] == artifact_payload["nodeid"]
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Investigation debug-17" in markdown
    assert "The fixture returned the stale value." in markdown
    assert "Move the override before fixture construction." in markdown


def test_artifact_sink_validates_before_creating_output_directory(tmp_path: Path) -> None:
    root = tmp_path / "must-not-exist"
    payload = _valid_artifact(status="invented")

    with pytest.raises(ValidationError):
        ArtifactSink(root).write(sequence=1, nodeid=str(payload["nodeid"]), payload=payload)

    assert not root.exists()


def test_artifact_sink_reports_filesystem_failure_without_partial_outputs(tmp_path: Path) -> None:
    root = tmp_path / "not-a-directory"
    root.write_text("occupied", encoding="utf-8")

    with pytest.raises(OSError):
        ArtifactSink(root / "child").write(
            sequence=1,
            nodeid="tests/test_debug.py::test_failure",
            payload=_valid_artifact(nodeid="tests/test_debug.py::test_failure"),
        )

    assert sorted(path.name for path in tmp_path.iterdir()) == ["not-a-directory"]


def test_artifact_sink_removes_json_when_markdown_pair_cannot_be_created(tmp_path: Path) -> None:
    nodeid = "tests/test_failure.py::test_occupied"
    root = tmp_path / "artifacts"
    root.mkdir()
    markdown_path = root / "failure-0001-tests-test_failure.py-test_occupied.md"
    markdown_path.write_text("owned by an earlier artifact", encoding="utf-8")

    with pytest.raises(FileExistsError):
        ArtifactSink(root).write(
            sequence=1,
            nodeid=nodeid,
            payload=_valid_artifact(nodeid=nodeid),
        )

    assert not markdown_path.with_suffix(".json").exists()
    assert markdown_path.read_text(encoding="utf-8") == "owned by an earlier artifact"
