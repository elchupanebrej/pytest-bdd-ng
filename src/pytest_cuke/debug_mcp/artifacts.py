from __future__ import annotations

import json
import re
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pytest_cuke.debug_mcp.schemas import InvestigationArtifact

if TYPE_CHECKING:
    from pathlib import Path

    from pydantic import ValidationError


@dataclass(frozen=True, slots=True)
class ArtifactWriteResult:
    """The paired artifact files created for one held failure."""

    artifact_id: str
    json_path: Path
    markdown_path: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "artifact_id": self.artifact_id,
            "json_path": str(self.json_path),
            "markdown_path": str(self.markdown_path),
        }


@dataclass(frozen=True, slots=True)
class ArtifactSink:
    """Validate investigation reports and write a paired JSON/Markdown record."""

    root: Path

    def write(self, *, sequence: int, nodeid: str, payload: object) -> ArtifactWriteResult:
        artifact = InvestigationArtifact.model_validate(payload)
        if artifact.nodeid != nodeid:
            raise ValueError("artifact nodeid must match the active held failure")
        if isinstance(sequence, bool) or sequence < 1:
            raise ValueError("artifact sequence must be a positive integer")

        stem = f"failure-{sequence:04d}-{safe_nodeid(nodeid)}"
        json_path = self.root / f"{stem}.json"
        markdown_path = self.root / f"{stem}.md"
        json_content = json.dumps(artifact.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        markdown_content = render_markdown(artifact)

        created: list[Path] = []
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            with json_path.open("x", encoding="utf-8", newline="\n") as stream:
                created.append(json_path)
                stream.write(json_content)
            with markdown_path.open("x", encoding="utf-8", newline="\n") as stream:
                created.append(markdown_path)
                stream.write(markdown_content)
        except BaseException:
            for path in reversed(created):
                with suppress(OSError):
                    path.unlink(missing_ok=True)
            raise

        return ArtifactWriteResult(artifact.artifact_id, json_path, markdown_path)


def safe_nodeid(nodeid: str) -> str:
    """Map arbitrary pytest node IDs to a bounded, single path component."""
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", nodeid).strip("-._")
    slug = slug[:120].rstrip("-._")
    return slug or "unknown"


def render_markdown(artifact: InvestigationArtifact) -> str:
    """Render the validated report as readable Markdown without changing its content."""
    metadata = artifact.bdd_metadata
    lines = [
        f"# Investigation {artifact.artifact_id}",
        "",
        f"- **Node ID:** `{artifact.nodeid}`",
        f"- **Pytest phase:** `{artifact.pytest_phase}`",
        f"- **Status:** `{artifact.status}`",
    ]
    if artifact.links:
        lines.extend(["- **Links:** " + ", ".join(artifact.links)])
    lines.extend(["", "## Summary", "", artifact.summary, "", "## Evidence", ""])
    lines.extend(f"- {item}" for item in artifact.evidence)
    lines.extend(["", "## Inspected commands", ""])
    lines.extend(f"- `{command}`" for command in artifact.inspected_commands)
    lines.extend(
        ["", "## Suspected cause", "", artifact.suspected_cause, "", "## Next action", "", artifact.next_action]
    )
    if metadata.feature_name is not None or metadata.scenario_name is not None:
        lines.extend(["", "## BDD context", ""])
        if metadata.feature_name is not None:
            lines.append(f"- **Feature:** {metadata.feature_name}")
        if metadata.scenario_name is not None:
            lines.append(f"- **Scenario:** {metadata.scenario_name}")
        if metadata.step_keyword is not None or metadata.step_text is not None:
            lines.append(f"- **Step:** {metadata.step_keyword or ''} {metadata.step_text or ''}".strip())
        if metadata.example_row:
            lines.append(f"- **Example row:** `{json.dumps(metadata.example_row, ensure_ascii=False, sort_keys=True)}`")
    return "\n".join(lines) + "\n"


def validation_error_payload(error: ValidationError) -> dict[str, object]:
    """Return JSON-safe details for a rejected external artifact submission."""
    return {
        "ok": False,
        "error": "validation_error",
        "details": error.errors(include_context=False, include_input=False, include_url=False),
    }


__all__ = ["ArtifactSink", "ArtifactWriteResult", "safe_nodeid", "validation_error_payload"]
