"""
Investigation artifact sink for debug MCP.

Responsibility:
    Investigation artifact sink for debug MCP. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.artifacts` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - ArtifactWriteResult: owns nested behavior below this boundary
    - ArtifactSink: owns nested behavior below this boundary
    - artifact_root_for_state: owns nested behavior below this boundary
    - safe_nodeid: owns nested behavior below this boundary
    - render_markdown: owns nested behavior below this boundary
    - validation_error_payload: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates json_path, markdown_path, artifact_id, root, artifact; depends on __future__.annotations, json, re,
    pathlib.Path, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.artifacts` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

import attrs

from .schemas import InvestigationArtifact

if TYPE_CHECKING:
    from pydantic import ValidationError

    from pytest_bdd.compatibility.pytest import PytestPluginManager

    from .state import DebugMcpState


@attrs.define(frozen=True, slots=True)
class ArtifactWriteResult:
    """
    Result of a successful artifact write.

    Responsibility:
        Result of a successful artifact write. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.artifacts.ArtifactWriteResult` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - as_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates artifact_id, json_path, markdown_path.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.artifacts.ArtifactWriteResult` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """

    artifact_id: str
    json_path: Path
    markdown_path: Path

    def as_dict(self) -> dict[str, str]:
        """
        Return JSON-compatible result.

        Returns:
            Paths and identifier as strings.

        Responsibility:
            Return JSON-compatible result. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.debug_mcp.artifacts.ArtifactWriteResult.as_dict` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/message_transport.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`
            - src/pytest_bdd/model/scenario_run.py: imports or references `as_dict`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        return {
            "artifact_id": self.artifact_id,
            "json_path": str(self.json_path),
            "markdown_path": str(self.markdown_path),
        }


@attrs.define(frozen=True, slots=True)
class ArtifactSink:
    """
    Writes paired JSON and Markdown investigation artifacts.

    Responsibility:
        Writes paired JSON and Markdown investigation artifacts. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.artifacts.ArtifactSink` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - write: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `ArtifactSink`

    State and side effects:
        mutates root, artifact, stem, json_path, markdown_path.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.artifacts.ArtifactSink` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    root: Path

    def write(self, *, sequence_id: int, nodeid: str, payload: object) -> ArtifactWriteResult:
        """
        Validate and write artifact payload.

        Returns:
            Artifact write result.

        Responsibility:
            Validate and write artifact payload. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.debug_mcp.artifacts.ArtifactSink.write` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - InvestigationArtifact.model_validate: collaborator call used by this boundary
            - safe_nodeid: collaborator call used by this boundary
            - self.root.mkdir: collaborator call used by this boundary
            - json_path.write_text: collaborator call used by this boundary
            - json.dumps: collaborator call used by this boundary
            - artifact.model_dump: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `write`
            - src/pytest_bdd/plugin/code_generator/rendering.py: imports or references `write`
            - src/pytest_bdd/plugin/debug_mcp/discovery.py: imports or references `write`
            - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `write`
            - src/pytest_bdd/plugin/debug_mcp/xdist.py: imports or references `write`

        State and side effects:
            mutates artifact, stem, json_path, markdown_path.

        Invariants:
            - `pytest_bdd.plugin.debug_mcp.artifacts.ArtifactSink.write` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        artifact = InvestigationArtifact.model_validate(payload)
        stem = f"failure-{sequence_id:04d}-{safe_nodeid(nodeid)}"
        json_path = self.root / f"{stem}.json"
        markdown_path = self.root / f"{stem}.md"
        self.root.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        markdown_path.write_text(render_markdown(artifact), encoding="utf-8")
        return ArtifactWriteResult(
            artifact_id=artifact.artifact_id,
            json_path=json_path,
            markdown_path=markdown_path,
        )


def artifact_root_for_state(state: DebugMcpState) -> Path:
    """
    Return artifact root for a debug MCP state.

    Returns:
        Configured artifact root, with session id appended for the default root.

    Responsibility:
        Return artifact root for a debug MCP state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.artifacts.artifact_root_for_state`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `artifact_root_for_state`

    State and side effects:
        mutates default_root.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.artifacts.artifact_root_for_state` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    default_root = Path(".pytest_cache") / "mcp-pdb" / "artifacts"
    if state.options.artifacts_path == default_root:
        return default_root / state.session_id
    return state.options.artifacts_path


def safe_nodeid(nodeid: str) -> str:
    """
    Slug a pytest nodeid for filenames.

    Returns:
        Stable filename-safe nodeid slug.

    Responsibility:
        Slug a pytest nodeid for filenames. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.artifacts.safe_nodeid` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - re.sub.strip: collaborator call used by this boundary
        - re.sub: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates slug.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.artifacts.safe_nodeid` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", nodeid).strip("-")
    return slug or "unknown"


def render_markdown(artifact: InvestigationArtifact) -> str:
    """
    Render Markdown from a validated artifact.

    Returns:
        Markdown artifact content.

    Responsibility:
        Render Markdown from a validated artifact. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.artifacts.render_markdown` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - join: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates lines.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.artifacts.render_markdown` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    lines = [
        f"# Investigation {artifact.artifact_id}",
        "",
        f"- **Nodeid:** `{artifact.nodeid}`",
        f"- **Pytest phase:** `{artifact.pytest_phase}`",
        f"- **Status:** {artifact.status}",
        "",
        "## Summary",
        "",
        artifact.summary,
        "",
        "## Evidence",
        "",
        *(f"- {item}" for item in artifact.evidence),
        "",
        "## Inspected Commands",
        "",
        *(f"- `{item}`" for item in artifact.inspected_commands),
        "",
        "## Suspected Cause",
        "",
        artifact.suspected_cause,
        "",
        "## Next Action",
        "",
        artifact.next_action,
        "",
    ]
    return "\n".join(lines)


def validation_error_payload(error: ValidationError) -> dict[str, object]:
    """
    Return sidecar-friendly validation error payload.

    Returns:
        Error dictionary with no filesystem writes.

    Responsibility:
        Return sidecar-friendly validation error payload. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.artifacts.validation_error_payload`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - error.errors: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `validation_error_payload`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    return {"ok": False, "error": "validation_error", "details": error.errors()}


def emit_artifact_created(
    pluginmanager: PytestPluginManager,
    *,
    artifact: object,
    result: ArtifactWriteResult,
) -> None:
    """
    Emit debug MCP artifact-created hook.

    Responsibility:
        Emit debug MCP artifact-created hook. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.artifacts.emit_artifact_created` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - InvestigationArtifact.model_validate: collaborator call used by this boundary
        - pluginmanager.hook.pytest_bdd_debug_mcp_artifact_created: collaborator call used by this boundary
        - validated.bdd_metadata.model_dump: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/sidecar.py: imports or references `emit_artifact_created`

    State and side effects:
        mutates validated.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.artifacts.emit_artifact_created` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    validated = InvestigationArtifact.model_validate(artifact)
    pluginmanager.hook.pytest_bdd_debug_mcp_artifact_created(
        nodeid=validated.nodeid,
        pytest_phase=validated.pytest_phase,
        bdd_metadata=validated.bdd_metadata.model_dump(mode="json"),
        json_path=result.json_path,
        markdown_path=result.markdown_path,
        status=validated.status,
        summary=validated.summary,
    )
