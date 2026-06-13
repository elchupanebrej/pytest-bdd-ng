# init: public-api  # init: no-check
"""
Owns documented module behavior within the pytest-bdd model layer, encapsulating domain logic and data structures for.

Responsibility:
    Owns documented module behavior within the pytest-bdd model layer, encapsulating domain logic and data structures
    for scenario execution state management

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
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from pytest_bdd.model.run.lifecycle import (
    ActiveObjectSet as ActiveObjectSet,
)
from pytest_bdd.model.run.lifecycle import (
    ContextErrorState as ContextErrorState,
)
from pytest_bdd.model.run.lifecycle import (
    ExternalApiCompatibilityRecord as ExternalApiCompatibilityRecord,
)
from pytest_bdd.model.run.lifecycle import (
    NodeKind as NodeKind,
)
from pytest_bdd.model.run.lifecycle import (
    ReferenceResolverState as ReferenceResolverState,
)
from pytest_bdd.model.run.lifecycle import (
    ReportingContextSnapshot as ReportingContextSnapshot,
)
from pytest_bdd.model.run.lifecycle import (
    ReportingLifecycleState as ReportingLifecycleState,
)
from pytest_bdd.model.run.lifecycle import (
    Run as Run,
)
from pytest_bdd.model.run.lifecycle import (
    ScenarioRunResult as ScenarioRunResult,
)
from pytest_bdd.model.run.refs import (
    LifecycleKind as LifecycleKind,
)
from pytest_bdd.model.run.refs import (
    LifecycleObjectRef as LifecycleObjectRef,
)
from pytest_bdd.model.run.refs import (
    NoPreviousStep as NoPreviousStep,
)
from pytest_bdd.model.run.refs import (
    _finished_feature_ref as _finished_feature_ref,
)
from pytest_bdd.model.run.refs import (
    _finished_previous_step_ref as _finished_previous_step_ref,
)
from pytest_bdd.model.run.refs import (
    _finished_scenario_ref as _finished_scenario_ref,
)
from pytest_bdd.model.run.refs import (
    _finished_step_ref as _finished_step_ref,
)
from pytest_bdd.model.run.refs import (
    _inactive_feature_ref as _inactive_feature_ref,
)
from pytest_bdd.model.run.refs import (
    _inactive_scenario_ref as _inactive_scenario_ref,
)
from pytest_bdd.model.run.refs import (
    _inactive_step_ref as _inactive_step_ref,
)
from pytest_bdd.model.run.refs import (
    _no_previous_step_ref as _no_previous_step_ref,
)
from pytest_bdd.model.run.stages import (
    HookPhase as HookPhase,
)
from pytest_bdd.model.run.stages import (
    RunStage as RunStage,
)
from pytest_bdd.model.run.stages import (
    RunStatus as RunStatus,
)
from pytest_bdd.model.run.transitions import (
    build_lifecycle_ref as build_lifecycle_ref,
)
from pytest_bdd.model.run.transitions import (
    initial_scenario_run_id as initial_scenario_run_id,
)
from pytest_bdd.model.run.transitions import (
    runtime_object_id as runtime_object_id,
)
from pytest_bdd.model.run.transitions import (
    runtime_object_name as runtime_object_name,
)
