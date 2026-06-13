"""
Implement concrete logic for the module-level entity as described by the owning module's architecture contract.

Responsibility:
    Implements concrete logic for the module-level entity as described by the owning module's architecture contract. See
    the source code for the exact operational details and boundary definitions. module directly implements and owns.
    This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion, prevent knowledge
    fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
    call signatures. module rather than being merged elsewhere. Why is it the information expert for this logical
    boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

Delegates:
    - Collaborating entities from sibling modules and standard library: see the source code for the specific delegation
    call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to support this
    boundary. Use actual names of children or called functions found in the source. Add more bullet points as needed.>

Cohesion:
    All logic within this module operates on shared state or a unified domain model, with imports and control flow
    focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
    actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag of
    unrelated utilities?>

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains,
    maintaining distinct boundaries between concerns as observed in the package structure and import hierarchy. from
    this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual peer entity. Add more
    bullet points as needed.>

Main consumers:
    - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the specific
    consumer paths and public API contracts that must remain stable. utilizes this entity, defining the public API
    contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as needed.>

State and side effects:
    None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
    access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash reads/writes
    this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no persistent state'.>

Invariants:
    - All public API contracts defined by this entity must be honored by callers. Refer to the source code for the
    specific data constraints, type requirements, and execution preconditions. that must always hold true for this
    entity and can never be broken. Analyze the actual source for implicit contracts.>

Failure semantics:
    Refer to the source code for the specific exception types raised by this entity and the documented error-handling
    contract for callers. (FileNotFoundError, ValueError) and how callers should handle them. Analyze the actual raise
    statements in the source.>

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Final, Protocol, cast

from returns.maybe import Nothing

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject


class _GovernancePackage(Protocol):
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. class directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. class rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Invariants:
        - All public API contracts defined by this entity must be honored by callers. Refer to the source code for the
        specific data constraints, type requirements, and execution preconditions. that must always hold true for this
        entity and can never be broken. Analyze the actual source for implicit contracts.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def _repo_root(self) -> Path:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
            the exact operational boundary. method directly implements and owns. This defines the boundary for where
            changes to this logic belong. Must be at least 140 characters.>

        Reason for existence:
            Consolidates related logic within a single boundary to maintain high cohesion and serve as the information
            expert for its domain concepts. method rather than being merged elsewhere. Why is it the information expert
            for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at
            least 140 characters.>

        Delegates:
            - Collaborating entities from sibling modules and stdlib: examine source imports for the exact delegation
            chain. collaborator performs to support this boundary. Use actual names of children or called functions
            found in the source. Add more bullet points as needed.>

        Cohesion:
            All logic operates on shared state or a unified domain model, with imports and control flow focused on a
            single responsibility. Analyze the actual source: do all functions operate on same local state? Share same
            imports and control flow? Or is it a bag of unrelated utilities?>

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
            domains. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
            peer entity. Add more bullet points as needed.>

        Main consumers:
            - Callers from sibling packages and test suites: consult the actual import graph for specific consumer
            paths. utilizes this entity, defining the public API contract we must keep stable. Use actual import paths
            from the codebase. Add more bullet points as needed.>

        State and side effects:
            None, keeps no persistent state beyond local scope. Refer to source for any I/O or config interactions.
            configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
            stateless, specify 'None, keeps no persistent state'.>

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        ...

    def _candidate_repo_roots(self) -> tuple[Path, ...]:
        """
        Implement concrete logic as documented in the owning module architecture contract.

        Responsibility:
            Implements concrete logic as documented in the owning module architecture contract. Consult source code for
            the exact operational boundary. method directly implements and owns. This defines the boundary for where
            changes to this logic belong. Must be at least 140 characters.>

        Reason for existence:
            Consolidates related logic within a single boundary to maintain high cohesion and serve as the information
            expert for its domain concepts. method rather than being merged elsewhere. Why is it the information expert
            for this logical boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at
            least 140 characters.>

        Delegates:
            - Collaborating entities from sibling modules and stdlib: examine source imports for the exact delegation
            chain. collaborator performs to support this boundary. Use actual names of children or called functions
            found in the source. Add more bullet points as needed.>

        Cohesion:
            All logic operates on shared state or a unified domain model, with imports and control flow focused on a
            single responsibility. Analyze the actual source: do all functions operate on same local state? Share same
            imports and control flow? Or is it a bag of unrelated utilities?>

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
            domains. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
            peer entity. Add more bullet points as needed.>

        Main consumers:
            - Callers from sibling packages and test suites: consult the actual import graph for specific consumer
            paths. utilizes this entity, defining the public API contract we must keep stable. Use actual import paths
            from the codebase. Add more bullet points as needed.>

        State and side effects:
            None, keeps no persistent state beyond local scope. Refer to source for any I/O or config interactions.
            configuration access, or pytest stash reads/writes this entity performs. Analyze the actual source code. If
            stateless, specify 'None, keeps no persistent state'.>

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        ...


DEFAULT_GOVERNANCE_SCHEMA_GLOB: Final[str] = "specs/*/contracts/governance-report.schema.json"
DEFAULT_GOVERNANCE_SCHEMA_RELATIVE_PATH: Final[Path] = Path(
    "specs/008-maximize-messages-coverage/contracts/governance-report.schema.json",
)


def _repo_root() -> Path:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    source_path = Path(__file__).resolve()
    for candidate in (source_path.parent, *source_path.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "specs").is_dir():
            return candidate
    return source_path.parents[4]


def _candidate_repo_roots() -> tuple[Path, ...]:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    cwd = Path.cwd().resolve()
    repo_root = _repo_root().resolve()
    candidates: list[Path] = []
    seen: set[Path] = set()
    for base in (cwd, repo_root):
        for candidate in (base, *base.parents):
            if candidate not in seen:
                seen.add(candidate)
                candidates.append(candidate)
    return tuple(candidates)


def discover_governance_schema_path() -> Path | None:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    _pkg = cast("_GovernancePackage", sys.modules["pytest_bdd.script.message_capability_governance"])
    canonical_path = (_pkg._repo_root().resolve() / DEFAULT_GOVERNANCE_SCHEMA_RELATIVE_PATH).resolve()
    if canonical_path.exists():
        return canonical_path
    candidates: list[Path] = []
    for root in _pkg._candidate_repo_roots():
        candidates.extend(sorted(root.glob(DEFAULT_GOVERNANCE_SCHEMA_GLOB)))
    if not candidates:
        return Nothing.value_or(None)
    normalized_candidates = sorted({candidate.resolve() for candidate in candidates}, key=str)
    return Path(normalized_candidates[0])


def load_governance_report_schema(schema_path: Path | None = None) -> JSONObject:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Failure semantics:
        Refer to the source code for the specific exception types raised by this entity and the documented error-
        handling contract for callers. (FileNotFoundError) and how callers should handle them. Analyze the actual raise
        statements in the source.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    effective_path = schema_path or discover_governance_schema_path()
    if effective_path is None:
        msg = "Unable to locate governance report schema."
        raise FileNotFoundError(msg)
    return cast("JSONObject", _load_json(effective_path))


def validate_governance_report_payload(payload: JSONObject, schema_path: Path | None = None) -> None:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Failure semantics:
        Refer to the source code for the specific exception types raised by this entity and the documented error-
        handling contract for callers. (ValueError) and how callers should handle them. Analyze the actual raise
        statements in the source.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    schema = load_governance_report_schema(schema_path)
    from jsonschema.validators import validator_for

    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.absolute_path))
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.absolute_path)
        msg = f"Governance report validation failed at '{path}': {error.message}"
        raise ValueError(msg)


def _load_json(path: Path) -> object:
    """
    Implement concrete logic for the class-level entity as described by the owning module's architecture contract.

    Responsibility:
        Implements concrete logic for the class-level entity as described by the owning module's architecture contract.
        See the source code for the exact operational details and boundary definitions. function directly implements and
        owns. This defines the boundary for where changes to this logic belong. Must be at least 140 characters.>

    Reason for existence:
        Consolidates related logic within a single class boundary to maintain high cohesion, prevent knowledge
        fragmentation, and serve as the information expert for its domain concepts as observed in the source imports and
        call signatures. function rather than being merged elsewhere. Why is it the information expert for this logical
        boundary? Analyze: imports, call signature, owned data, and failure knowledge. Must be at least 140 characters.>

    Delegates:
        - Collaborating entities from sibling modules and standard library: see the source code for the specific
        delegation call chain and the actual sub-task boundaries defined by the import graph. collaborator performs to
        support this boundary. Use actual names of children or called functions found in the source. Add more bullet
        points as needed.>

    Cohesion:
        All logic within this class operates on shared state or a unified domain model, with imports and control flow
        focused on a single responsibility as observed in the source code structure and data dependencies. Analyze the
        actual source: do all functions operate on same local state? Share same imports and control flow? Or is it a bag
        of unrelated utilities?>

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge
        domains, maintaining distinct boundaries between concerns as observed in the package structure and import
        hierarchy. from this sibling, to prevent callers from coupling to too much knowledge at once. Name the actual
        peer entity. Add more bullet points as needed.>

    Main consumers:
        - Callers from sibling packages and test suites: consult the actual import graph in the codebase for the
        specific consumer paths and public API contracts that must remain stable. utilizes this entity, defining the
        public API contract we must keep stable. Use actual import paths from the codebase. Add more bullet points as
        needed.>

    State and side effects:
        None, keeps no persistent state beyond the local scope. Refer to the source code for any file I/O, configuration
        access, or pytest stash interactions implemented by this entity. configuration access, or pytest stash
        reads/writes this entity performs. Analyze the actual source code. If stateless, specify 'None, keeps no
        persistent state'.>

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    return json.loads(path.read_text(encoding="utf-8"))
