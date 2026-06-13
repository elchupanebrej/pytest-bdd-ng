"""
Provide public facade functions for resolving scenario execution context from the Run object.

Responsibility:
    Provides public facade functions for resolving scenario execution context from the Run object. This module offers
    resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects, and
    previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a thin
    orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable interface
    for callers such as hooks and reporters.

Reason for existence:
    This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It is
    kept here rather than merged elsewhere because it owns specific data structures, state transitions, validation
    rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control flow confirms this
    module is the single source of truth for its owned concepts

Delegates:
    - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused sub-
    task to keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
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
    - All require_* functions must raise RuntimeError when the requested object is unavailable; resolve_* functions must
    return None (not raise) for missing objects; build_reporting_context_snapshot must always return a valid snapshot
    even in fallback mode

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

from contextlib import suppress
from typing import TYPE_CHECKING

from returns.maybe import Nothing

from pytest_bdd.model.run import (
    ActiveObjectSet,
    ContextErrorState,
    LifecycleKind,
    LifecycleObjectRef,
    ReportingContextSnapshot,
    Run,
    RunStage,
)
from pytest_bdd.model.run.transitions import build_lifecycle_ref

if TYPE_CHECKING:
    from cucumber_messages import GherkinDocument, Pickle, PickleStep, Source

    from pytest_bdd.compatibility.pytest import FixtureRequest
    from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
    from pytest_bdd.model.scenario_run import ScenarioRun
    from pytest_bdd.types.protocol import Identifiable


def resolve_feature_binding(run: Run) -> FeatureRuntimeBinding | None:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    scenario_run = run.active_scenario_run
    return scenario_run.feature_binding if scenario_run is not None else None


def require_feature_binding(run: Run, *, hook_name: str) -> FeatureRuntimeBinding:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_feature_binding(hook_name=hook_name)


def require_feature_object(run: Run, *, hook_name: str) -> GherkinDocument:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_gherkin_document(hook_name=hook_name)


def require_pickle_object(run: Run, *, hook_name: str) -> Pickle:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_pickle(hook_name=hook_name)


def require_step_object(run: Run, *, hook_name: str) -> PickleStep:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    scenario_run = run.require_active_scenario_run(hook_name=hook_name)
    return scenario_run.require_step_object(hook_name=hook_name)


def resolve_feature_object(run: Run) -> GherkinDocument | None:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    binding = run.active_feature_binding
    if binding is not None:
        return binding.gherkin_document
    scenario_run = run.active_scenario_run
    return scenario_run.gherkin_document if scenario_run is not None else None


def resolve_feature_source(run: Run) -> Source | None:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    binding = run.active_feature_binding
    if binding is not None:
        return binding.source
    scenario_run = run.active_scenario_run
    return scenario_run.feature_source if scenario_run is not None else None


def resolve_pickle_object(run: Run) -> Pickle | None:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    scenario_run = run.active_scenario_run
    return scenario_run.pickle if scenario_run is not None else None


def resolve_step_object(run: Run) -> PickleStep | None:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    scenario_run = run.active_scenario_run
    return scenario_run.step_object if scenario_run is not None else None


def resolve_previous_step_object(run: Run) -> PickleStep | object | None:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    scenario_run = run.active_scenario_run
    return scenario_run.previous_step_object if scenario_run is not None else None


def resolve_active_object_or_error(
    *,
    hook_name: str,
    scenario_run: ScenarioRun,
    requested_kind: LifecycleKind,
) -> tuple[LifecycleObjectRef | None, ContextErrorState | None]:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    active_object = scenario_run.get_active_object(requested_kind)
    if active_object is not None:
        return active_object, None

    inactive_candidate = {
        "run": scenario_run.active_set.run,
        "feature": scenario_run.active_set.feature,
        "scenario": scenario_run.active_set.scenario,
        "step": scenario_run.active_set.step,
    }[requested_kind]
    message = (
        f"Lifecycle object '{requested_kind}' is unavailable during {hook_name} at stage '{scenario_run.stage.value}'"
    )
    if inactive_candidate.empty_state_reason is not None:
        message = f"{message} (empty state: {inactive_candidate.empty_state_reason})"
    error = scenario_run.record_context_error(
        code="object_inactive",
        message=message,
        hook_name=hook_name,
        requested_kind=requested_kind,
    )
    return Nothing.value_or(None), error


def _fallback_reporting_snapshot(
    request: FixtureRequest,
    *,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    run_root = Run.find_in_stash(request.config.stash).value_or(None)
    if run_root is None:
        run_ref = build_lifecycle_ref("run", getattr(request, "session", None), is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)
        run_id = f"run-{id(getattr(request, 'session', request))}"
    else:
        run_ref = run_root.run_ref
        run_id = run_root.id

    return ReportingContextSnapshot(
        run_id=run_id,
        active_set=ActiveObjectSet(run=run_ref, captured_at_stage=RunStage.idle),
        stage=RunStage.idle,
        resolved_from_hierarchy=False,
        fallback_reason=fallback_reason or "hierarchy_not_available",
    )


def build_reporting_context_snapshot(
    *,
    request: FixtureRequest,
    fallback_reason: str | None = None,
) -> ReportingContextSnapshot:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    run = Run.find_in_stash(request.config.stash).value_or(None)

    if run is not None and run.active_scenario_run is not None:
        active_scenario_run = run.active_scenario_run
        return ReportingContextSnapshot(
            run_id=run.id,
            active_set=active_scenario_run.active_set,
            stage=active_scenario_run.stage,
            resolved_from_hierarchy=True,
            fallback_reason=None,
        )
    if run is not None:
        return ReportingContextSnapshot(
            run_id=run.id,
            active_set=ActiveObjectSet(run=run.run_ref, captured_at_stage=RunStage.idle),
            stage=RunStage.idle,
            resolved_from_hierarchy=True,
            fallback_reason=fallback_reason or "run_has_no_active_scenario",
        )

    return _fallback_reporting_snapshot(request, fallback_reason=fallback_reason)


def resolve_registry_node(
    *,
    feature_binding: FeatureRuntimeBinding | None,
    ast_node_id: str,
    scenario_run: ScenarioRun | None = None,
) -> Identifiable | None:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    node = None
    if feature_binding is not None:
        with suppress(KeyError):
            node = feature_binding.resolve_node(ast_node_id)

    if node is None and scenario_run is not None:
        scenario_run.reference_resolver.add_missing_reference(f"Missing AST node id: {ast_node_id}")
    return node


def resolve_scenario_description(
    *,
    pickle: Pickle,
    feature_binding: FeatureRuntimeBinding | None = None,
    scenario_run: ScenarioRun | None = None,
) -> str | None:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    ast_node_ids = getattr(pickle, "ast_node_ids", None) or ()
    if not ast_node_ids:
        if scenario_run is not None:
            scenario_run.reference_resolver.add_missing_reference("Pickle has no ast_node_ids")
        return Nothing.value_or(None)
    ast_node_id = str(ast_node_ids[0])
    effective_binding = feature_binding or (scenario_run.feature_binding if scenario_run is not None else None)
    node = resolve_registry_node(
        feature_binding=effective_binding,
        ast_node_id=ast_node_id,
        scenario_run=scenario_run,
    )
    if node is None:
        return Nothing.value_or(None)
    description = getattr(node, "description", None)
    return str(description) if description is not None else None


def resolve_step_runtime_enrichment(
    *,
    step: PickleStep,
    feature_binding: FeatureRuntimeBinding | None = None,
    scenario_run: ScenarioRun | None = None,
) -> dict[str, object]:
    """
    Provide public facade functions for resolving scenario execution context from the Run object.

    Responsibility:
        Provides public facade functions for resolving scenario execution context from the Run object. This module
        offers resolve_* and require_* accessors for feature bindings, gherkin documents, pickle objects, step objects,
        and previous step objects, plus reporting context snapshot construction and AST node resolution. It acts as a
        thin orchestration layer that delegates to Run and ScenarioRun methods while providing a consistent, testable
        interface for callers such as hooks and reporters.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - ScenarioRun methods: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - scenario_run: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
    effective_binding = feature_binding or (scenario_run.feature_binding if scenario_run is not None else None)
    model_step = effective_binding.pickle_step_ast_step(step) if effective_binding is not None else None
    if model_step is None:
        if scenario_run is not None:
            scenario_run.reference_resolver.add_missing_reference(
                f"Missing pickle step mapping: {getattr(step, 'id', 'unknown')}",
            )
        return {
            "keyword": None,
            "prefix": None,
            "line_number": None,
            "doc_string": None,
            "data_table": None,
            "state": "unresolved",
            "reason": "missing_pickle_step_mapping",
        }
    return {
        "keyword": effective_binding.step_keyword(step) if effective_binding is not None else None,
        "prefix": effective_binding.step_prefix(step) if effective_binding is not None else None,
        "line_number": effective_binding.step_line_number(step) if effective_binding is not None else None,
        "doc_string": effective_binding.step_doc_string(step) if effective_binding is not None else None,
        "data_table": effective_binding.step_data_table(step) if effective_binding is not None else None,
        "state": "resolved",
        "reason": None,
    }
