"""
Pydantic schemas for debug MCP artifacts.

Responsibility:
    Pydantic schemas for debug MCP artifacts. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.debug_mcp.schemas` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - BddMetadata: owns nested behavior below this boundary
    - ActiveFailure: owns nested behavior below this boundary
    - InvestigationArtifact: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates model_config, nodeid, pytest_phase, feature_path, feature_name; depends on __future__.annotations,
    typing.Literal, pydantic.BaseModel, pydantic.ConfigDict, pydantic.Field.

Invariants:
    - `pytest_bdd.plugin.debug_mcp.schemas` keeps its documented import path, ownership boundary, and observable
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

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BddMetadata(BaseModel):
    """
    Best-effort BDD context snapshot.

    Responsibility:
        Best-effort BDD context snapshot. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.schemas.BddMetadata` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/bdd_adapter.py: imports or references `BddMetadata`

    State and side effects:
        mutates model_config, feature_path, feature_name, scenario_name, step_keyword.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.schemas.BddMetadata` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    feature_path: str | None = None
    feature_name: str | None = None
    scenario_name: str | None = None
    step_keyword: str | None = None
    step_text: str | None = None
    tags: list[str] = Field(default_factory=list)
    example_row: dict[str, str] = Field(default_factory=dict)


class ActiveFailure(BaseModel):
    """
    Active failure schema for sidecar consumers.

    Responsibility:
        Active failure schema for sidecar consumers. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.schemas.ActiveFailure` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates model_config, sequence_id, nodeid, pytest_phase, exception_type.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.schemas.ActiveFailure` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    sequence_id: int
    nodeid: str
    pytest_phase: Literal["setup", "call", "teardown"]
    exception_type: str
    message: str
    artifact_status: Literal["missing", "written"] = "missing"
    bdd: BddMetadata | None = None


class InvestigationArtifact(BaseModel):
    """
    Validated agent investigation artifact.

    Responsibility:
        Validated agent investigation artifact. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.debug_mcp.schemas.InvestigationArtifact` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/artifacts.py: imports or references `InvestigationArtifact`

    State and side effects:
        mutates model_config, artifact_id, links, nodeid, pytest_phase.

    Invariants:
        - `pytest_bdd.plugin.debug_mcp.schemas.InvestigationArtifact` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    artifact_id: str
    links: list[str] = Field(default_factory=list)
    nodeid: str
    pytest_phase: Literal["setup", "call", "teardown"]
    status: Literal["investigated", "needs_followup", "resolved"]
    summary: str
    inspected_commands: list[str]
    evidence: list[str]
    suspected_cause: str
    next_action: str
    bdd_metadata: BddMetadata = Field(default_factory=BddMetadata)
