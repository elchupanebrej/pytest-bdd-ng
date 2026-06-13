"""
Implement plugin module operations for pytest-bdd.

Responsibility:
    Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
    consumed by the broader BDD infrastructure.

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion and serve as the information
    expert for its domain concepts.

Delegates:
    - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

Cohesion:
    All logic within this entity operates on a single responsibility domain with focused imports and control flow.

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

Main consumers:
    - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

State and side effects:
    None, keeps no persistent state beyond local scope.

Invariants:
    - All public API contracts defined by this entity must be honored by callers.

Architecture score:
    #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
    #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
    #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
    #arch-eval:cohesion=4  # Internal logic focus (1-5)
    #arch-eval:separation=4  # Distinctness from peers (1-5)
    #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
    #arch-eval:state_invariants=4  # Control of state mutations (1-5)
    #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
    #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BddMetadata(BaseModel):
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
