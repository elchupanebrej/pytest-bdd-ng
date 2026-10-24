from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BddMetadata(BaseModel):
    """BDD identity attached to an investigation artifact."""

    model_config = ConfigDict(extra="forbid", strict=True)

    feature_path: str | None = None
    feature_name: str | None = None
    scenario_name: str | None = None
    step_keyword: str | None = None
    step_text: str | None = None
    tags: list[str] = Field(default_factory=list)
    example_row: dict[str, str] = Field(default_factory=dict)


class InvestigationArtifact(BaseModel):
    """Strict, serializable report submitted by an external debugger client."""

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
