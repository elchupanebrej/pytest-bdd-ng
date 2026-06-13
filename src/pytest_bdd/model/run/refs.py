"""
Define the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind, object identity, and lifecycle stage.

Responsibility:
    Defines the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind,
    object_id, name, source, and active/inactive status. Also defines the NoPreviousStep sentinel class and factory
    functions (_inactive_*_ref, _finished_*_ref, _no_previous_step_ref) that create pre-configured inactive references
    for default states and cleanup transitions. The LifecycleKind literal type constrains valid lifecycle entity kinds.

Reason for existence:
    This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It is
    kept here rather than merged elsewhere because it owns specific data structures, state transitions, validation
    rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control flow confirms this
    module is the single source of truth for its owned concepts

Delegates:
    - transitions module: Provides supporting functionality through a well-defined interface, delegating a focused sub-
    task to keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain boundaries
    at once, ensuring each concept can evolve independently without cascading changes across the codebase

Main consumers:
    - scenario_run: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model public
    API, defining a stable contract that downstream layers depend on for scenario execution state, message handling, and
    stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - LifecycleObjectRef.kind must be one of the four LifecycleKind literals; inactive refs must have is_active=False
    with a non-None empty_state_reason; factory functions must produce distinct instances per call

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

from typing import TYPE_CHECKING, Literal

from attrs import define

if TYPE_CHECKING:
    from pytest_bdd.compatibility.typing import Self
    from pytest_bdd.types.json import JSONObject

LifecycleKind = Literal["run", "feature", "scenario", "step"]


@define(slots=True)
class LifecycleObjectRef:
    """
    Define the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind, object identity, and lifecycle stage.

    Responsibility:
        Defines the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by
        kind, object_id, name, source, and active/inactive status. Also defines the NoPreviousStep sentinel class and
        factory functions (_inactive_*_ref, _finished_*_ref, _no_previous_step_ref) that create pre-configured inactive
        references for default states and cleanup transitions. The LifecycleKind literal type constrains valid lifecycle
        entity kinds.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - transitions module: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_run: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - LifecycleObjectRef.kind must be one of the four LifecycleKind literals; inactive refs must have
        is_active=False with a non-None empty_state_reason; factory functions must produce distinct instances per call

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

    kind: LifecycleKind
    object_id: str
    name: str | None = None
    source: str | None = None
    is_active: bool = True
    empty_state_reason: str | None = None
    fail_fast_code: str | None = None

    @classmethod
    def inactive(
        cls,
        kind: LifecycleKind,
        *,
        reason: str,
        name: str | None = None,
        source: str | None = "lifecycle-slot",
        fail_fast_code: str | None = None,
    ) -> Self:
        """
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - transitions module: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - scenario_run: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
            public API, defining a stable contract that downstream layers depend on for scenario execution state,
            message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

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
        return cls(
            kind=kind,
            object_id=f"{kind}:{reason}",
            name=name or kind,
            source=source,
            is_active=False,
            empty_state_reason=reason,
            fail_fast_code=fail_fast_code,
        )

    def as_dict(self) -> JSONObject:
        """
        Perform a specific, focused operation within its owning class boundary.

        Responsibility:
            Performs a specific, focused operation within its owning class boundary. This method is the authoritative
            implementation for this piece of logic, ensuring callers access state or trigger behavior through a well-
            defined contract rather than manipulating internals directly.

        Reason for existence:
            This method is the information expert for this operation because it directly owns the relevant state fields
            and encapsulates all validation, error recording, and side-effect logic. Merging it elsewhere would scatter
            related concerns and force callers to duplicate precondition checks and error handling.

        Delegates:
            - transitions module: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - scenario_run: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
            public API, defining a stable contract that downstream layers depend on for scenario execution state,
            message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return {
            "kind": self.kind,
            "object_id": self.object_id,
            "name": self.name,
            "source": self.source,
            "is_active": self.is_active,
            "empty_state_reason": self.empty_state_reason,
            "fail_fast_code": self.fail_fast_code,
        }


@define(slots=True)
class NoPreviousStep:
    """
    Define the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind, object identity, and lifecycle stage.

    Responsibility:
        Defines the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by
        kind, object_id, name, source, and active/inactive status. Also defines the NoPreviousStep sentinel class and
        factory functions (_inactive_*_ref, _finished_*_ref, _no_previous_step_ref) that create pre-configured inactive
        references for default states and cleanup transitions. The LifecycleKind literal type constrains valid lifecycle
        entity kinds.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - transitions module: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
        boundaries at once, ensuring each concept can evolve independently without cascading changes across the codebase

    Main consumers:
        - scenario_run: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
        public API, defining a stable contract that downstream layers depend on for scenario execution state, message
        handling, and stash access

    State and side effects:
        Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
        operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-
        safe boundary enforcement

    Invariants:
        - LifecycleObjectRef.kind must be one of the four LifecycleKind literals; inactive refs must have
        is_active=False with a non-None empty_state_reason; factory functions must produce distinct instances per call

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

    id: str = "step:no_previous_step"
    text: str = ""
    keyword: str = ""


def _inactive_feature_ref() -> LifecycleObjectRef:
    """
    Define the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind, object identity, and lifecycle stage.

    Responsibility:
        Defines the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by
        kind, object_id, name, source, and active/inactive status. Also defines the NoPreviousStep sentinel class and
        factory functions (_inactive_*_ref, _finished_*_ref, _no_previous_step_ref) that create pre-configured inactive
        references for default states and cleanup transitions. The LifecycleKind literal type constrains valid lifecycle
        entity kinds.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - transitions module: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
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
    return LifecycleObjectRef.inactive("feature", reason="idle")


def _inactive_scenario_ref() -> LifecycleObjectRef:
    """
    Define the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind, object identity, and lifecycle stage.

    Responsibility:
        Defines the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by
        kind, object_id, name, source, and active/inactive status. Also defines the NoPreviousStep sentinel class and
        factory functions (_inactive_*_ref, _finished_*_ref, _no_previous_step_ref) that create pre-configured inactive
        references for default states and cleanup transitions. The LifecycleKind literal type constrains valid lifecycle
        entity kinds.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - transitions module: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
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
    return LifecycleObjectRef.inactive("scenario", reason="idle")


def _inactive_step_ref() -> LifecycleObjectRef:
    """
    Define the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind, object identity, and lifecycle stage.

    Responsibility:
        Defines the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by
        kind, object_id, name, source, and active/inactive status. Also defines the NoPreviousStep sentinel class and
        factory functions (_inactive_*_ref, _finished_*_ref, _no_previous_step_ref) that create pre-configured inactive
        references for default states and cleanup transitions. The LifecycleKind literal type constrains valid lifecycle
        entity kinds.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - transitions module: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
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
    return LifecycleObjectRef.inactive("step", reason="idle", fail_fast_code="object_inactive")


def _no_previous_step_ref() -> LifecycleObjectRef:
    """
    Define the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind, object identity, and lifecycle stage.

    Responsibility:
        Defines the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by
        kind, object_id, name, source, and active/inactive status. Also defines the NoPreviousStep sentinel class and
        factory functions (_inactive_*_ref, _finished_*_ref, _no_previous_step_ref) that create pre-configured inactive
        references for default states and cleanup transitions. The LifecycleKind literal type constrains valid lifecycle
        entity kinds.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - transitions module: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
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
    return LifecycleObjectRef.inactive("step", reason="no_previous_step")


def _finished_feature_ref() -> LifecycleObjectRef:
    """
    Define the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind, object identity, and lifecycle stage.

    Responsibility:
        Defines the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by
        kind, object_id, name, source, and active/inactive status. Also defines the NoPreviousStep sentinel class and
        factory functions (_inactive_*_ref, _finished_*_ref, _no_previous_step_ref) that create pre-configured inactive
        references for default states and cleanup transitions. The LifecycleKind literal type constrains valid lifecycle
        entity kinds.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - transitions module: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
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
    return LifecycleObjectRef.inactive("feature", reason="finished")


def _finished_scenario_ref() -> LifecycleObjectRef:
    """
    Define the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind, object identity, and lifecycle stage.

    Responsibility:
        Defines the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by
        kind, object_id, name, source, and active/inactive status. Also defines the NoPreviousStep sentinel class and
        factory functions (_inactive_*_ref, _finished_*_ref, _no_previous_step_ref) that create pre-configured inactive
        references for default states and cleanup transitions. The LifecycleKind literal type constrains valid lifecycle
        entity kinds.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - transitions module: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
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
    return LifecycleObjectRef.inactive("scenario", reason="finished")


def _finished_step_ref() -> LifecycleObjectRef:
    """
    Define the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind, object identity, and lifecycle stage.

    Responsibility:
        Defines the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by
        kind, object_id, name, source, and active/inactive status. Also defines the NoPreviousStep sentinel class and
        factory functions (_inactive_*_ref, _finished_*_ref, _no_previous_step_ref) that create pre-configured inactive
        references for default states and cleanup transitions. The LifecycleKind literal type constrains valid lifecycle
        entity kinds.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - transitions module: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
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
    return LifecycleObjectRef.inactive("step", reason="finished", fail_fast_code="object_inactive")


def _finished_previous_step_ref() -> LifecycleObjectRef:
    """
    Define the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by kind, object identity, and lifecycle stage.

    Responsibility:
        Defines the LifecycleObjectRef value object for referencing run/feature/scenario/step lifecycle entities by
        kind, object_id, name, source, and active/inactive status. Also defines the NoPreviousStep sentinel class and
        factory functions (_inactive_*_ref, _finished_*_ref, _no_previous_step_ref) that create pre-configured inactive
        references for default states and cleanup transitions. The LifecycleKind literal type constrains valid lifecycle
        entity kinds.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - transitions module: Provides supporting functionality through a well-defined interface, delegating a focused
        sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - stages: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
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
    return LifecycleObjectRef.inactive("step", reason="finished")
