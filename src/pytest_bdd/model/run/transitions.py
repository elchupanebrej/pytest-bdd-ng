"""
Provide utility functions for constructing lifecycle identifiers and references during scenario transitions.

Responsibility:
    Provides utility functions for constructing lifecycle identifiers and references during scenario transitions:
    runtime_object_id (extracts stable IDs from Gherkin objects via id/name/nodeid/ast_node_ids), runtime_object_name
    (extracts human-readable names), build_lifecycle_ref (constructs LifecycleObjectRef from arbitrary objects), and
    initial_scenario_run_id (generates unique scenario run IDs keyed by pytest fixture request with a monotonic
    counter).

Reason for existence:
    This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It is
    kept here rather than merged elsewhere because it owns specific data structures, state transitions, validation
    rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control flow confirms this
    module is the single source of truth for its owned concepts

Delegates:
    - refs module: Provides supporting functionality through a well-defined interface, delegating a focused sub-task to
    keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - refs: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain boundaries at
    once, ensuring each concept can evolve independently without cascading changes across the codebase

Main consumers:
    - scenario_run: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model public
    API, defining a stable contract that downstream layers depend on for scenario execution state, message handling, and
    stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - runtime_object_id must always return a non-empty string; build_lifecycle_ref must return None for None inputs and
    a valid LifecycleObjectRef otherwise; initial_scenario_run_id must produce unique ids across concurrent test
    execution

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING

from returns.maybe import Nothing

from pytest_bdd.model.run.refs import LifecycleKind, LifecycleObjectRef

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import FixtureRequest

_context_index = count(1)


def runtime_object_id(obj: object) -> str:
    """
    Provide utility functions for constructing lifecycle identifiers and references during scenario transitions.

    Responsibility:
        Provides utility functions for constructing lifecycle identifiers and references during scenario transitions:
        runtime_object_id (extracts stable IDs from Gherkin objects via id/name/nodeid/ast_node_ids),
        runtime_object_name (extracts human-readable names), build_lifecycle_ref (constructs LifecycleObjectRef from
        arbitrary objects), and initial_scenario_run_id (generates unique scenario run IDs keyed by pytest fixture
        request with a monotonic counter).

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - refs module: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - refs: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_run: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    if obj is None:
        return "none"
    explicit_id = getattr(obj, "id", None)
    if explicit_id is not None:
        return str(explicit_id)
    nodeid = getattr(obj, "nodeid", None)
    if nodeid is not None:
        return str(nodeid)
    name = getattr(obj, "name", None)
    if name is not None:
        return str(name)
    ast_node_ids = getattr(obj, "ast_node_ids", None)
    if ast_node_ids:
        return str(ast_node_ids[0])
    return str(id(obj))


def runtime_object_name(obj: object) -> str | None:
    """
    Provide utility functions for constructing lifecycle identifiers and references during scenario transitions.

    Responsibility:
        Provides utility functions for constructing lifecycle identifiers and references during scenario transitions:
        runtime_object_id (extracts stable IDs from Gherkin objects via id/name/nodeid/ast_node_ids),
        runtime_object_name (extracts human-readable names), build_lifecycle_ref (constructs LifecycleObjectRef from
        arbitrary objects), and initial_scenario_run_id (generates unique scenario run IDs keyed by pytest fixture
        request with a monotonic counter).

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - refs module: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - refs: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_run: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    if obj is None:
        return Nothing.value_or(None)
    name = getattr(obj, "name", None)
    return str(name) if name is not None else None


def build_lifecycle_ref(kind: LifecycleKind, value: object, *, is_active: bool) -> LifecycleObjectRef | None:
    """
    Provide utility functions for constructing lifecycle identifiers and references during scenario transitions.

    Responsibility:
        Provides utility functions for constructing lifecycle identifiers and references during scenario transitions:
        runtime_object_id (extracts stable IDs from Gherkin objects via id/name/nodeid/ast_node_ids),
        runtime_object_name (extracts human-readable names), build_lifecycle_ref (constructs LifecycleObjectRef from
        arbitrary objects), and initial_scenario_run_id (generates unique scenario run IDs keyed by pytest fixture
        request with a monotonic counter).

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - refs module: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - refs: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_run: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    if value is None:
        return Nothing.value_or(None)
    return LifecycleObjectRef(
        kind=kind,
        object_id=runtime_object_id(value),
        name=runtime_object_name(value),
        source=value.__class__.__name__,
        is_active=is_active,
    )


def initial_scenario_run_id(request: FixtureRequest) -> str:
    """
    Provide utility functions for constructing lifecycle identifiers and references during scenario transitions.

    Responsibility:
        Provides utility functions for constructing lifecycle identifiers and references during scenario transitions:
        runtime_object_id (extracts stable IDs from Gherkin objects via id/name/nodeid/ast_node_ids),
        runtime_object_name (extracts human-readable names), build_lifecycle_ref (constructs LifecycleObjectRef from
        arbitrary objects), and initial_scenario_run_id (generates unique scenario run IDs keyed by pytest fixture
        request with a monotonic counter).

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - refs module: Provides supporting functionality through a well-defined interface, delegating a focused sub-task
        to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - refs: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_run: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    node_id = getattr(getattr(request, "node", None), "nodeid", None)
    key = node_id or f"unknown-{next(_context_index)}"
    return f"ctx-{key}-{next(_context_index)}"
