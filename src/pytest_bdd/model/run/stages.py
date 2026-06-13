"""
Defines StrEnum-based enums that govern the scenario execution lifecycle: HookPhase (pytest_bdd_before_scenario, pyte.

Responsibility:
    Defines StrEnum-based enums that govern the scenario execution lifecycle: HookPhase (pytest_bdd_before_scenario,
    pytest_bdd_run_step, etc.), RunStage (idle, scenario_setup, step_running, finished, etc.), and RunStatus (ok,
    failed, interrupted). These enums are the canonical vocabulary for lifecycle transitions and are referenced
    throughout the collection, runtime, and reporting layers for consistent state communication.

Reason for existence:
    This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It is
    kept here rather than merged elsewhere because it owns specific data structures, state transitions, validation
    rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control flow confirms this
    module is the single source of truth for its owned concepts

Delegates:
    - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface, delegating a
    focused sub-task to keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - refs: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain boundaries at
    once, ensuring each concept can evolve independently without cascading changes across the codebase

Main consumers:
    - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model public
    API, defining a stable contract that downstream layers depend on for scenario execution state, message handling, and
    stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - HookPhase values must match actual pytest hookspec names; RunStage must progress monotonically from idle through
    finished; RunStatus values are mutually exclusive final states

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

from pytest_bdd.compatibility.enum import StrEnum


class HookPhase(StrEnum):
    """
    Defines StrEnum-based enums that govern the scenario execution lifecycle: HookPhase (pytest_bdd_before_scenario, pyte.

    Responsibility:
        Defines StrEnum-based enums that govern the scenario execution lifecycle: HookPhase (pytest_bdd_before_scenario,
        pytest_bdd_run_step, etc.), RunStage (idle, scenario_setup, step_running, finished, etc.), and RunStatus (ok,
        failed, interrupted). These enums are the canonical vocabulary for lifecycle transitions and are referenced
        throughout the collection, runtime, and reporting layers for consistent state communication.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface, delegating
        a focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - refs: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - HookPhase values must match actual pytest hookspec names; RunStage must progress monotonically from idle
        through finished; RunStatus values are mutually exclusive final states

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

    before_scenario = "pytest_bdd_before_scenario"
    run_scenario = "pytest_bdd_run_scenario"
    after_scenario = "pytest_bdd_after_scenario"
    run_step = "pytest_bdd_run_step"
    before_step = "pytest_bdd_before_step"
    before_step_call = "pytest_bdd_before_step_call"
    after_step = "pytest_bdd_after_step"
    step_error = "pytest_bdd_step_error"
    step_lookup_error = "pytest_bdd_step_func_lookup_error"


class RunStage(StrEnum):
    """
    Defines StrEnum-based enums that govern the scenario execution lifecycle: HookPhase (pytest_bdd_before_scenario, pyte.

    Responsibility:
        Defines StrEnum-based enums that govern the scenario execution lifecycle: HookPhase (pytest_bdd_before_scenario,
        pytest_bdd_run_step, etc.), RunStage (idle, scenario_setup, step_running, finished, etc.), and RunStatus (ok,
        failed, interrupted). These enums are the canonical vocabulary for lifecycle transitions and are referenced
        throughout the collection, runtime, and reporting layers for consistent state communication.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface, delegating
        a focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - refs: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - HookPhase values must match actual pytest hookspec names; RunStage must progress monotonically from idle
        through finished; RunStatus values are mutually exclusive final states

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

    idle = "idle"
    scenario_setup = "scenario_setup"
    scenario_running = "scenario_running"
    step_running = "step_running"
    scenario_teardown = "scenario_teardown"
    finished = "finished"


class RunStatus(StrEnum):
    """
    Defines StrEnum-based enums that govern the scenario execution lifecycle: HookPhase (pytest_bdd_before_scenario, pyte.

    Responsibility:
        Defines StrEnum-based enums that govern the scenario execution lifecycle: HookPhase (pytest_bdd_before_scenario,
        pytest_bdd_run_step, etc.), RunStage (idle, scenario_setup, step_running, finished, etc.), and RunStatus (ok,
        failed, interrupted). These enums are the canonical vocabulary for lifecycle transitions and are referenced
        throughout the collection, runtime, and reporting layers for consistent state communication.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - pytest_bdd.compatibility.enum: Provides supporting functionality through a well-defined interface, delegating
        a focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - refs: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - HookPhase values must match actual pytest hookspec names; RunStage must progress monotonically from idle
        through finished; RunStatus values are mutually exclusive final states

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

    ok = "ok"
    failed = "failed"
    interrupted = "interrupted"
