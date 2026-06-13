"""
Defines the Run class, the root of the scenario execution hierarchy stored in pytest.config.stash under STASH_KEY _py.

Responsibility:
    Defines the Run class, the root of the scenario execution hierarchy stored in pytest.config.stash under STASH_KEY
    _pytest_bdd_run. Run manages feature bindings by URI, scenario runs by request, active scenario/step tracking,
    transition indexing, runtime-step-to-test-step-id mapping, pickles compilation, and identifiable object tree
    indexing. It inherits StashBound for stash lifecycle and provides factory constructors for session-based and config-
    based initialization as well as create_scenario_run orchestration.

Reason for existence:
    This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It is
    kept here rather than merged elsewhere because it owns specific data structures, state transitions, validation
    rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control flow confirms this
    module is the single source of truth for its owned concepts

Delegates:
    - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a focused
    sub-task to keep this entity cohesive and its responsibility boundary clean

Cohesion:
    All functions, methods, and data within this entity operate on the same local state, share identical import
    dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
    dispersing unrelated utilities across separate modules

Separation:
    - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain boundaries
    at once, ensuring each concept can evolve independently without cascading changes across the codebase

Main consumers:
    - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model public
    API, defining a stable contract that downstream layers depend on for scenario execution state, message handling, and
    stash access

State and side effects:
    Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
    operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for type-safe
    boundary enforcement

Invariants:
    - Run must be stored under STASH_KEY _pytest_bdd_run; scenario_runs_by_request must be keyed by request nodeid;
    active_scenario_run must be set/cleared consistently during scenario lifecycle methods; feature_bindings_by_uri must
    be keyed by gherkin document URI

Failure semantics:
    Raises RuntimeError for context-not-initialized or binding-missing conditions when required lifecycle objects are
    unavailable; raises TypeError for malformed envelopes violating single-payload or type constraints; raises
    ValueError for missing required fields in deserialized transport payloads; callers must handle these exceptions at
    hook or plugin boundaries to prevent test session crashes

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

from typing import TYPE_CHECKING, ClassVar, Literal, cast

from attrs import define, field
from returns.maybe import Nothing
from returns.result import Result

from pytest_bdd.model.feature_binding import FeatureRuntimeBinding
from pytest_bdd.model.message_registry import EnvelopeRegistry, IdentifiableObjectRegistry
from pytest_bdd.model.run.refs import (
    LifecycleObjectRef,
    NoPreviousStep,
    _inactive_feature_ref,
    _inactive_scenario_ref,
    _inactive_step_ref,
    _no_previous_step_ref,
)
from pytest_bdd.model.run.stages import HookPhase, RunStage, RunStatus
from pytest_bdd.model.stash_access import StashBound
from pytest_bdd.types.failure_reasons import ScenarioRunFailure
from pytest_bdd.types.protocol import Identifiable

from ._states import (
    ActiveObjectSet,
    ContextErrorState,
    ReportingLifecycleState,
)

if TYPE_CHECKING:
    from cucumber_messages import GherkinDocument, Pickle, PickleStep, Source

    from pytest_bdd.compatibility.pytest import Config, FixtureRequest, Session, Stash
    from pytest_bdd.compatibility.typing import Self
    from pytest_bdd.model.scenario_run import ScenarioRun
    from pytest_bdd.types.json import JSONArray, JSONObject

ScenarioRunResult = Result[object, ScenarioRunFailure]

NodeKind = Literal["feature", "scenario", "step"]


@define(slots=True)
class Run(StashBound):
    """
    Defines the Run class, the root of the scenario execution hierarchy stored in pytest.config.stash under STASH_KEY _py.

    Responsibility:
        Defines the Run class, the root of the scenario execution hierarchy stored in pytest.config.stash under
        STASH_KEY _pytest_bdd_run. Run manages feature bindings by URI, scenario runs by request, active scenario/step
        tracking, transition indexing, runtime-step-to-test-step-id mapping, pickles compilation, and identifiable
        object tree indexing. It inherits StashBound for stash lifecycle and provides factory constructors for session-
        based and config-based initialization as well as create_scenario_run orchestration.

    Reason for existence:
        This code is the authoritative information expert for its domain boundary within the pytest-bdd model layer. It
        is kept here rather than merged elsewhere because it owns specific data structures, state transitions,
        validation rules, and lookup semantics that are only coherent when collocated. Analyzing imports and control
        flow confirms this module is the single source of truth for its owned concepts

    Delegates:
        - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
        focused sub-task to keep this entity cohesive and its responsibility boundary clean

    Cohesion:
        All functions, methods, and data within this entity operate on the same local state, share identical import
        dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather than
        dispersing unrelated utilities across separate modules

    Separation:
        - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
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
        - Run must be stored under STASH_KEY _pytest_bdd_run; scenario_runs_by_request must be keyed by request nodeid;
        active_scenario_run must be set/cleared consistently during scenario lifecycle methods; feature_bindings_by_uri
        must be keyed by gherkin document URI

    Failure semantics:
        Raises RuntimeError for context-not-initialized or binding-missing conditions when required lifecycle objects
        are unavailable; raises TypeError for malformed envelopes violating single-payload or type constraints; raises
        ValueError for missing required fields in deserialized transport payloads; callers must handle these exceptions
        at hook or plugin boundaries to prevent test session crashes

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

    STASH_KEY: ClassVar[str] = "_pytest_bdd_run"

    id: str
    run_ref: LifecycleObjectRef
    status: RunStatus
    transition_index: int = 0
    identifiable_registry: IdentifiableObjectRegistry = field(factory=IdentifiableObjectRegistry, repr=False)
    feature_bindings_by_uri: dict[str, FeatureRuntimeBinding] = field(factory=dict, repr=False)
    active_feature_id: str | None = None
    active_feature_uri: str | None = None
    scenario_runs_by_request: dict[str, ScenarioRun] = field(factory=dict, repr=False)
    active_scenario_run: ScenarioRun | None = field(default=None, repr=False)
    last_error: ContextErrorState | None = None
    reporting_state: ReportingLifecycleState = field(factory=ReportingLifecycleState)

    @property
    def active_feature_binding(self: Self) -> FeatureRuntimeBinding | None:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        if self.active_scenario_run is None:
            return Nothing.value_or(None)
        return self.active_scenario_run.feature_binding

    @property
    def active_scenario_id(self) -> str:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
            public API, defining a stable contract that downstream layers depend on for scenario execution state,
            message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Failure semantics:
            Raises AttributeError with a descriptive message when no active scenario or step node exists. Callers should
            check for active state via optional accessors or ensure lifecycle initialization has completed.

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
        scenario_run = self.active_scenario_run
        node = scenario_run.scenario_node if scenario_run is not None else None
        if node is not None and node.is_active:
            return str(node.id)
        msg = "No active scenario"
        raise AttributeError(msg)

    @property
    def active_step_id(self) -> str:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
            public API, defining a stable contract that downstream layers depend on for scenario execution state,
            message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Failure semantics:
            Raises AttributeError with a descriptive message when no active scenario or step node exists. Callers should
            check for active state via optional accessors or ensure lifecycle initialization has completed.

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
        scenario_run = self.active_scenario_run
        node = scenario_run.step_node if scenario_run is not None else None
        if node is not None and node.is_active:
            return str(node.id)
        msg = "No active step"
        raise AttributeError(msg)

    def require_active_scenario_run(self, *, hook_name: str) -> ScenarioRun:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
            public API, defining a stable contract that downstream layers depend on for scenario execution state,
            message handling, and stash access

        State and side effects:
            Maintains in-memory state via attrs-defined fields with factory defaults, performing no file I/O, network
            operations, or direct pytest stash access; stash interaction is delegated to StashAccess class methods for
            type-safe boundary enforcement

        Failure semantics:
            Raises RuntimeError with a descriptive message when required lifecycle objects are unavailable at the
            current stage. Callers in hooks and plugins should catch RuntimeError and report the error through the
            appropriate reporting channel.

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
        scenario_run = self.active_scenario_run
        if scenario_run is not None:
            return scenario_run
        msg = f"Active scenario run is unavailable for {hook_name}; lifecycle context is not initialized"
        raise RuntimeError(msg)

    def advance_transition(self) -> None:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        self.transition_index += 1

    @classmethod
    def _build_for_owner(cls, owner: object) -> Run:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        object_id = getattr(owner, "name", None) or getattr(owner, "nodeid", None) or str(id(owner))
        run_ref = LifecycleObjectRef(kind="run", object_id=str(object_id), name="run", is_active=True)
        return Run(
            id=f"run-{id(owner)}",
            run_ref=run_ref,
            status=RunStatus.ok,
            transition_index=0,
        )

    @classmethod
    def initialize_for_session(cls, *, stash: Stash, session: Session) -> Run:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        run = cls._build_for_owner(session)
        run.initialize_in_stash(stash)
        EnvelopeRegistry(identifiable=run.identifiable_registry).initialize_in_stash(stash)
        return run

    @classmethod
    def initialize_for_config(cls, *, stash: Stash, config: Config) -> Run:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        run = cls._build_for_owner(config)
        run.initialize_in_stash(stash)
        EnvelopeRegistry(identifiable=run.identifiable_registry).initialize_in_stash(stash)
        return run

    @staticmethod
    def _request_key(request: FixtureRequest) -> str:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        node = getattr(request, "node", None)
        node_id = getattr(node, "nodeid", None)
        if node_id is not None:
            return str(node_id)
        return f"request-{id(request)}"

    @classmethod
    def get_scenario_run(cls, request: FixtureRequest) -> ScenarioRun | None:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        run = cls.find_in_stash(request.config.stash).value_or(None)
        if run is None:
            return Nothing.value_or(None)
        key = cls._request_key(request)
        return run.scenario_runs_by_request.get(key)

    @classmethod
    def set_scenario_run(cls, request: FixtureRequest, scenario_run: ScenarioRun) -> None:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        run = scenario_run.run
        if run is None:
            run = cls.from_stash(request.config.stash)
            scenario_run.run = run
        key = cls._request_key(request)
        run.scenario_runs_by_request[key] = scenario_run
        run.active_scenario_run = scenario_run

    @classmethod
    def pop_scenario_run(cls, request: FixtureRequest) -> ScenarioRun | None:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        config = getattr(request, "config", None)
        stash = getattr(config, "stash", None)
        run = cls.find_in_stash(stash).value_or(None) if stash is not None else None
        if run is None:
            return Nothing.value_or(None)
        key = cls._request_key(request)
        scenario_run = run.scenario_runs_by_request.pop(key, None)
        if scenario_run is None:
            return Nothing.value_or(None)

        run_root = scenario_run.run
        if run_root is not None:
            scenario_run.ensure_finished_for_cleanup(at_transition=run_root.transition_index)
            if run_root.active_scenario_run is scenario_run:
                run_root.active_scenario_run = None
            if run_root.active_feature_uri == scenario_run.feature_uri:
                run_root.active_feature_uri = None
            run_root.reporting_state.reset_scenario_scope()

        scenario_run.reference_resolver.clear()
        return scenario_run

    def create_scenario_run(
        self,
        request: FixtureRequest,
        *,
        gherkin_document: GherkinDocument | None = None,
        pickle: Pickle | None = None,
        feature_source: Source | None = None,
    ) -> ScenarioRun:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        from pytest_bdd.model.run.transitions import (
            build_lifecycle_ref,
            initial_scenario_run_id,
            runtime_object_id,
        )
        from pytest_bdd.model.scenario_run import (
            RunNode,
            ScenarioRun,
        )

        run_ref = build_lifecycle_ref("run", request.session, is_active=True)
        if run_ref is None:
            run_ref = LifecycleObjectRef(kind="run", object_id="run", name="run", is_active=True)

        run = self
        feature_binding = None
        feature_uri = None
        if gherkin_document is not None and getattr(gherkin_document, "uri", None) is not None:
            feature_binding = run.ensure_feature_binding(
                gherkin_document=gherkin_document,
                source=feature_source,
                pickles=(pickle,) if pickle is not None else None,
            )
            feature_uri = feature_binding.uri
            if feature_source is None:
                feature_source = feature_binding.source

        feature_ref = build_lifecycle_ref("feature", gherkin_document, is_active=gherkin_document is not None)
        if feature_ref is None:
            feature_ref = _inactive_feature_ref()
        scenario_ref = build_lifecycle_ref("scenario", pickle, is_active=pickle is not None)
        if scenario_ref is None:
            scenario_ref = _inactive_scenario_ref()
        active_set = ActiveObjectSet(
            run=run_ref,
            feature=feature_ref,
            scenario=scenario_ref,
            captured_at_stage=RunStage.idle,
        )

        run_node_id = initial_scenario_run_id(request)
        feature_node = None
        if feature_ref.is_active and gherkin_document is not None:
            feature_node = RunNode(
                id=f"feature-{runtime_object_id(gherkin_document)}-{run_node_id}",
                parent_id=run.id,
                kind="feature",
                object_ref=feature_ref,
                is_active=True,
                opened_at_transition=run.transition_index,
            )
            run.active_feature_id = feature_node.id
            run.active_feature_uri = feature_uri

        scenario_node = None
        if scenario_ref.is_active and pickle is not None:
            scenario_node = RunNode(
                id=run_node_id,
                parent_id=feature_node.id if feature_node is not None else run.id,
                kind="scenario",
                object_ref=scenario_ref,
                is_active=True,
                opened_at_transition=run.transition_index,
            )

        scenario_run = ScenarioRun(
            id=run_node_id,
            run_ref=run_ref,
            feature_ref=feature_ref,
            scenario_ref=scenario_ref,
            step_ref=_inactive_step_ref(),
            previous_step_ref=_no_previous_step_ref(),
            active_hook=HookPhase.before_scenario,
            stage=RunStage.idle,
            status=RunStatus.ok,
            active_set=active_set,
            transition_index=0,
            run=run,
            feature_uri=feature_uri,
            feature_node=feature_node,
            scenario_node=scenario_node,
            step_node=None,
            gherkin_document=gherkin_document,
            feature_source=feature_source,
            pickle=pickle,
            step_object=None,
            previous_step_object=NoPreviousStep(),
        )
        key = type(self)._request_key(request)  # noqa: SLF001  -- suppressed warning
        run.scenario_runs_by_request[key] = scenario_run
        run.active_scenario_run = scenario_run
        return scenario_run

    def index_identifiable_tree(self, root: object) -> None:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        self.identifiable_registry.index_tree(root)

    def map_runtime_step_to_test_step_id(self, *, pickle_step: PickleStep, test_step_id: str) -> None:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        self.reporting_state.runtime_step_to_pickle_step_id[id(pickle_step)] = test_step_id

    def ensure_feature_binding(
        self,
        *,
        gherkin_document: GherkinDocument,
        source: Source | None = None,
        filename: str | None = None,
        pickles: tuple[Pickle, ...] | list[Pickle] | None = None,
    ) -> FeatureRuntimeBinding:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        uri = str(gherkin_document.uri)
        binding = self.feature_bindings_by_uri.get(uri)
        if binding is None:
            binding = FeatureRuntimeBinding.build(
                run=self,
                gherkin_document=gherkin_document,
                filename=filename,
                source=source,
                pickles=pickles,
            )
            self.feature_bindings_by_uri[uri] = binding
            return binding

        binding.run = self
        binding.gherkin_document = gherkin_document
        if source is not None:
            binding.source = source
        if pickles and (not binding.pickles or len(pickles) >= len(binding.pickles)):
            binding.pickles = tuple(pickles)
        binding.index_runtime_objects()
        if not binding.filename:
            binding.filename = FeatureRuntimeBinding._feature_filename_from_uri(uri)  # noqa: SLF001  -- suppressed warning
        return binding

    def feature_binding_for_uri(self, uri: str | None) -> FeatureRuntimeBinding | None:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        if uri is None:
            return Nothing.value_or(None)
        return self.feature_bindings_by_uri.get(str(uri))

    def feature_binding_for_document(self, gherkin_document: GherkinDocument | None) -> FeatureRuntimeBinding | None:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        uri = getattr(gherkin_document, "uri", None) if gherkin_document is not None else None
        if uri is None:
            return Nothing.value_or(None)
        return self.feature_bindings_by_uri.get(str(uri))

    def resolve_test_step_id_for_runtime_step(self, *, pickle_step: PickleStep) -> str | None:
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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        reporting_state = self.reporting_state
        mapped = reporting_state.runtime_step_to_pickle_step_id.get(id(pickle_step))
        if mapped is not None:
            return mapped
        if isinstance(pickle_step, Identifiable) and pickle_step.id is not None:
            runtime_step_id_text = str(pickle_step.id)
            for candidate in reporting_state.runtime_step_to_pickle_step_id.values():
                if candidate == runtime_step_id_text:
                    return candidate
        return reporting_state.active_test_step_id

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
            - FeatureRuntimeBinding: Provides supporting functionality through a well-defined interface, delegating a
            focused sub-task to keep this entity cohesive and its responsibility boundary clean

        Cohesion:
            All functions, methods, and data within this entity operate on the same local state, share identical import
            dependencies and control flow patterns, and collectively implement a single cohesive responsibility rather
            than dispersing unrelated utilities across separate modules

        Separation:
            - _states: This entity is kept distinct from its peer to prevent callers from coupling to multiple domain
            boundaries at once, ensuring each concept can evolve independently without cascading changes across the
            codebase

        Main consumers:
            - pickle_runner: Referenced by collection, runtime, and reporting layer plugins through the pytest_bdd.model
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
        try:
            active_scenario_id = self.active_scenario_id
        except AttributeError:
            active_scenario_id = None

        try:
            active_step_id = self.active_step_id
        except AttributeError:
            active_step_id = None

        return {
            "run_id": self.id,
            "run_ref": self.run_ref.as_dict(),
            "status": self.status.value,
            "transition_index": self.transition_index,
            "feature_bindings_by_uri": cast("JSONArray", sorted(self.feature_bindings_by_uri)),
            "active_feature_id": self.active_feature_id,
            "active_feature_uri": self.active_feature_uri,
            "active_scenario_id": active_scenario_id,
            "active_step_id": active_step_id,
            "last_error": self.last_error.as_dict() if self.last_error is not None else None,
            "reporting_state": self.reporting_state.as_dict(),
        }
