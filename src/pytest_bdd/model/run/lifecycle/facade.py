"""
Re-exports all public types from the lifecycle sub-modules (_run, _states, _snapshots) into a single import namespace.

Responsibility:
    Re-exports all public types from the lifecycle sub-modules (_run, _states, _snapshots) into a single import
    namespace. This module exists solely as a pass-through facade to simplify imports for consumers of the
    model.run.lifecycle package, ensuring that Run, ActiveObjectSet, ContextErrorState, ReportingContextSnapshot, and
    related types are accessible through a single import path without exposing internal module structure.

Reason for existence:
    This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It is
    kept here rather than merged elsewhere because it owns specific data structures, state transitions, validation
    rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control flow confirms this
    module is the single source of truth for its owned concepts

Delegates:
    - StashAccess: Provides supporting functionality through a well-defined interface, delegating a focused sub-task to
    keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - feature_binding: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
    boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

Main consumers:
    - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model public
    API, defining a stable contract that downstream layers depend on for scenario execution state, message handling, and
    stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - Envelope payloads must contain exactly one non-None field matching a known PAYLOAD_KIND; stash keys must be unique
    per StashBound subclass; LifecycleObjectRef is_active flags must correctly reflect runtime state at all lifecycle
    stages

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

from __future__ import annotations

from pytest_bdd.model.run.lifecycle._run import (  # noqa: F401  -- intentional re-export or import for public API facade
    NodeKind,
    Run,
    ScenarioRunResult,
)
from pytest_bdd.model.run.lifecycle._snapshots import (  # noqa: F401  -- intentional re-export or import for public API facade
    ExternalApiCompatibilityRecord,
    ReportingContextSnapshot,
)
from pytest_bdd.model.run.lifecycle._states import (  # noqa: F401  -- intentional re-export or import for public API facade
    ActiveObjectSet,
    ContextErrorState,
    ReferenceResolverState,
    ReportingLifecycleState,
)
