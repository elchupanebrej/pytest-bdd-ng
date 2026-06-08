"""
Run class for the run lifecycle state management.

Responsibility:
    Run class for the run lifecycle state management. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.run.lifecycle._run` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - Run: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `_run`

State and side effects:
    mutates run, scenario_run, run_ref, key, node; depends on __future__.annotations, typing.TYPE_CHECKING,
    typing.ClassVar, typing.Literal, typing.cast.

Invariants:
    - `pytest_bdd.model.run.lifecycle._run` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises AttributeError, RuntimeError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
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
    Represent run state.

    Raises:
        AttributeError: If the operation cannot be completed.
        RuntimeError: If the operation cannot be completed.

    Responsibility:
        Represent run state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - active_feature_binding: owns nested behavior below this boundary
        - active_scenario_id: owns nested behavior below this boundary
        - active_step_id: owns nested behavior below this boundary
        - require_active_scenario_run: owns nested behavior below this boundary
        - advance_transition: owns nested behavior below this boundary
        - _build_for_owner: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `Run`
        - src/pytest_bdd/model/__init__.py: imports or references `Run`
        - src/pytest_bdd/model/feature_binding.py: imports or references `Run`
        - src/pytest_bdd/model/run/__init__.py: imports or references `Run`
        - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `Run`

    State and side effects:
        mutates run, scenario_run, run_ref, key, node; depends on pytest_bdd.model.run.transitions.build_lifecycle_ref,
        pytest_bdd.model.run.transitions.initial_scenario_run_id, pytest_bdd.model.run.transitions.runtime_object_id,
        pytest_bdd.model.scenario_run.RunNode, pytest_bdd.model.scenario_run.ScenarioRun.

    Invariants:
        - `pytest_bdd.model.run.lifecycle._run.Run` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Failure semantics:
        Raises or re-raises AttributeError, RuntimeError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
        Retrieve the feature binding associated with the currently executing scenario.

        Returns:
            The FeatureRuntimeBinding instance, or None if no scenario is active.

        Responsibility:
            Retrieve the feature binding associated with the currently executing scenario. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.active_feature_binding`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Nothing.value_or: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `active_feature_binding`
            - src/pytest_bdd/model/run_access.py: imports or references `active_feature_binding`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        if self.active_scenario_run is None:
            return Nothing.value_or(None)
        return self.active_scenario_run.feature_binding

    @property
    def active_scenario_id(self) -> str:
        """
        Retrieve the unique identifier of the currently executing scenario node.

        Returns:
            The active scenario's ID string.

        Raises:
            AttributeError: If no scenario is currently active or initialized.

        Responsibility:
            Retrieve the unique identifier of the currently executing scenario node. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.active_scenario_id`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - AttributeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `active_scenario_id`

        State and side effects:
            mutates scenario_run, node, msg.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.active_scenario_id` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises AttributeError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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
        Retrieve the unique identifier of the currently executing step node.

        Returns:
            The active step's ID string.

        Raises:
            AttributeError: If no step is currently active or initialized.

        Responsibility:
            Retrieve the unique identifier of the currently executing step node. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.active_step_id` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - AttributeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `active_step_id`

        State and side effects:
            mutates scenario_run, node, msg.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.active_step_id` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises AttributeError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        scenario_run = self.active_scenario_run
        node = scenario_run.step_node if scenario_run is not None else None
        if node is not None and node.is_active:
            return str(node.id)
        msg = "No active step"
        raise AttributeError(msg)

    def require_active_scenario_run(self, *, hook_name: str) -> ScenarioRun:
        """
        Fetch the active scenario run, ensuring it exists before proceeding.

        Returns:
            The currently active ScenarioRun instance.

        Raises:
            RuntimeError: If the scenario run is unavailable or the lifecycle context is not initialized.

        Responsibility:
            Fetch the active scenario run, ensuring it exists before proceeding. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.run.lifecycle._run.Run.require_active_scenario_run` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `require_active_scenario_run`
            - src/pytest_bdd/model/run_access.py: imports or references `require_active_scenario_run`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references
              `require_active_scenario_run`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `require_active_scenario_run`

        State and side effects:
            mutates scenario_run, msg.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.require_active_scenario_run` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        scenario_run = self.active_scenario_run
        if scenario_run is not None:
            return scenario_run
        msg = f"Active scenario run is unavailable for {hook_name}; lifecycle context is not initialized"
        raise RuntimeError(msg)

    def advance_transition(self) -> None:
        """
        Increment the internal transition index counter to represent state progression.

        Responsibility:
            Increment the internal transition index counter to represent state progression. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.advance_transition`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `advance_transition`
            - src/pytest_bdd/plugin/pickle_runner/run_transitions.py: imports or references `advance_transition`

        State and side effects:
            mutates self.transition_index.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.advance_transition` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        self.transition_index += 1

    @classmethod
    def _build_for_owner(cls, owner: object) -> Run:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.model.run.lifecycle._run.Run._build_for_owner` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run._build_for_owner` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - id: collaborator call used by this boundary
            - LifecycleObjectRef: collaborator call used by this boundary
            - Run: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `_build_for_owner`

        State and side effects:
            mutates object_id, run_ref.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run._build_for_owner` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
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
        Initialize and bind a new Run state object to the pytest Session context via the stash.

        Returns:
            The newly initialized Run instance.

        Responsibility:
            Initialize and bind a new Run state object to the pytest Session context via the stash. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.initialize_for_session`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls._build_for_owner: collaborator call used by this boundary
            - run.initialize_in_stash: collaborator call used by this boundary
            - EnvelopeRegistry.initialize_in_stash: collaborator call used by this boundary
            - EnvelopeRegistry: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `initialize_for_session`

        State and side effects:
            mutates run.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.initialize_for_session` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        run = cls._build_for_owner(session)
        run.initialize_in_stash(stash)
        EnvelopeRegistry(identifiable=run.identifiable_registry).initialize_in_stash(stash)
        return run

    @classmethod
    def initialize_for_config(cls, *, stash: Stash, config: Config) -> Run:
        """
        Initialize and bind a new Run state object to the pytest Config context via the stash.

        Returns:
            The newly initialized Run instance.

        Responsibility:
            Initialize and bind a new Run state object to the pytest Config context via the stash. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.initialize_for_config`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls._build_for_owner: collaborator call used by this boundary
            - run.initialize_in_stash: collaborator call used by this boundary
            - EnvelopeRegistry.initialize_in_stash: collaborator call used by this boundary
            - EnvelopeRegistry: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `initialize_for_config`
            - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `initialize_for_config`

        State and side effects:
            mutates run.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.initialize_for_config` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        run = cls._build_for_owner(config)
        run.initialize_in_stash(stash)
        EnvelopeRegistry(identifiable=run.identifiable_registry).initialize_in_stash(stash)
        return run

    @staticmethod
    def _request_key(request: FixtureRequest) -> str:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.model.run.lifecycle._run.Run._request_key` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run._request_key` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - id: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `_request_key`

        State and side effects:
            mutates node, node_id.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run._request_key` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        node = getattr(request, "node", None)
        node_id = getattr(node, "nodeid", None)
        if node_id is not None:
            return str(node_id)
        return f"request-{id(request)}"

    @classmethod
    def get_scenario_run(cls, request: FixtureRequest) -> ScenarioRun | None:
        """
        Retrieve the ScenarioRun associated with a given pytest FixtureRequest, if it exists.

        Returns:
            The ScenarioRun instance linked to the request, or None if not found.

        Responsibility:
            Retrieve the ScenarioRun associated with a given pytest FixtureRequest, if it exists. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.get_scenario_run` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls.find_in_stash.value_or: collaborator call used by this boundary
            - cls.find_in_stash: collaborator call used by this boundary
            - Nothing.value_or: collaborator call used by this boundary
            - cls._request_key: collaborator call used by this boundary
            - run.scenario_runs_by_request.get: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `get_scenario_run`

        State and side effects:
            mutates run, key.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.get_scenario_run` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        run = cls.find_in_stash(request.config.stash).value_or(None)
        if run is None:
            return Nothing.value_or(None)
        key = cls._request_key(request)
        return run.scenario_runs_by_request.get(key)

    @classmethod
    def set_scenario_run(cls, request: FixtureRequest, scenario_run: ScenarioRun) -> None:
        """
        Register a ScenarioRun instance against a pytest FixtureRequest in the active Run state.

        Responsibility:
            Register a ScenarioRun instance against a pytest FixtureRequest in the active Run state. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.set_scenario_run` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls.from_stash: collaborator call used by this boundary
            - cls._request_key: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `set_scenario_run`

        State and side effects:
            mutates run, scenario_run.run, key, run.active_scenario_run.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.set_scenario_run` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
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
        Remove and finalize a ScenarioRun associated with a pytest FixtureRequest, performing necessary cleanup.

        Returns:
            The removed ScenarioRun instance, or None if it was not found.

        Responsibility:
            Remove and finalize a ScenarioRun associated with a pytest FixtureRequest, performing necessary cleanup. It
            directly owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.pop_scenario_run` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - Nothing.value_or: collaborator call used by this boundary
            - cls.find_in_stash.value_or: collaborator call used by this boundary
            - cls.find_in_stash: collaborator call used by this boundary
            - cls._request_key: collaborator call used by this boundary
            - run.scenario_runs_by_request.pop: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `pop_scenario_run`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `pop_scenario_run`

        State and side effects:
            mutates config, stash, run, key, scenario_run.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.pop_scenario_run` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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
        Instantiate a new ScenarioRun context for a specific test request.

        Optionally binds a Gherkin document and pickle.

        Returns:
            The newly created ScenarioRun context.

        Responsibility:
            Instantiate a new ScenarioRun context for a specific test request. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.create_scenario_run`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - build_lifecycle_ref: collaborator call used by this boundary
            - RunNode: collaborator call used by this boundary
            - LifecycleObjectRef: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - run.ensure_feature_binding: collaborator call used by this boundary
            - _inactive_feature_ref: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `create_scenario_run`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `create_scenario_run`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `create_scenario_run`

        State and side effects:
            mutates run_ref, feature_binding, feature_uri, feature_ref, scenario_ref; depends on
            pytest_bdd.model.run.transitions.build_lifecycle_ref,
            pytest_bdd.model.run.transitions.initial_scenario_run_id,
            pytest_bdd.model.run.transitions.runtime_object_id, pytest_bdd.model.scenario_run.RunNode,
            pytest_bdd.model.scenario_run.ScenarioRun.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.create_scenario_run` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        from pytest_bdd.model.run.transitions import (  # noqa: PLC0415
            build_lifecycle_ref,
            initial_scenario_run_id,
            runtime_object_id,
        )
        from pytest_bdd.model.scenario_run import RunNode, ScenarioRun  # noqa: PLC0415

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
        key = type(self)._request_key(request)  # noqa: SLF001
        run.scenario_runs_by_request[key] = scenario_run
        run.active_scenario_run = scenario_run
        return scenario_run

    def index_identifiable_tree(self, root: object) -> None:
        """
        Recursively scan and register all identifiable objects within a tree into the registry.

        Responsibility:
            Recursively scan and register all identifiable objects within a tree into the registry. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.index_identifiable_tree`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.identifiable_registry.index_tree: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/feature_binding.py: imports or references `index_identifiable_tree`
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `index_identifiable_tree`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        self.identifiable_registry.index_tree(root)

    def map_runtime_step_to_test_step_id(self, *, pickle_step: PickleStep, test_step_id: str) -> None:
        """
        Record a mapping from a runtime PickleStep object identity to its corresponding executed test step ID.

        Responsibility:
            Record a mapping from a runtime PickleStep object identity to its corresponding executed test step ID. It
            directly owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.run.lifecycle._run.Run.map_runtime_step_to_test_step_id` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - id: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `map_runtime_step_to_test_step_id`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `map_runtime_step_to_test_step_id`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
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
        Retrieve an existing feature binding for a document or construct a new one if it doesn't exist.

        Returns:
            The resolved or newly constructed FeatureRuntimeBinding.

        Responsibility:
            Retrieve an existing feature binding for a document or construct a new one if it doesn't exist. It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.ensure_feature_binding`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - self.feature_bindings_by_uri.get: collaborator call used by this boundary
            - FeatureRuntimeBinding.build: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - binding.index_runtime_objects: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `ensure_feature_binding`
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `ensure_feature_binding`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `ensure_feature_binding`
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `ensure_feature_binding`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `ensure_feature_binding`

        State and side effects:
            mutates binding, uri, binding.run, binding.gherkin_document, binding.source.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.ensure_feature_binding` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
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
            binding.filename = FeatureRuntimeBinding._feature_filename_from_uri(uri)  # noqa: SLF001
        return binding

    def feature_binding_for_uri(self, uri: str | None) -> FeatureRuntimeBinding | None:
        """
        Look up a previously registered feature binding using its URI.

        Returns:
            The FeatureRuntimeBinding if found, or None.

        Responsibility:
            Look up a previously registered feature binding using its URI. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.feature_binding_for_uri`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Nothing.value_or: collaborator call used by this boundary
            - self.feature_bindings_by_uri.get: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `feature_binding_for_uri`
            - src/pytest_bdd/model/scenario_run.py: imports or references `feature_binding_for_uri`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        if uri is None:
            return Nothing.value_or(None)
        return self.feature_bindings_by_uri.get(str(uri))

    def feature_binding_for_document(self, gherkin_document: GherkinDocument | None) -> FeatureRuntimeBinding | None:
        """
        Look up a previously registered feature binding using a Gherkin document reference.

        Returns:
            The FeatureRuntimeBinding if found, or None.

        Responsibility:
            Look up a previously registered feature binding using a Gherkin document reference. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.run.lifecycle._run.Run.feature_binding_for_document` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - Nothing.value_or: collaborator call used by this boundary
            - self.feature_bindings_by_uri.get: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `feature_binding_for_document`
            - src/pytest_bdd/model/scenario_run.py: imports or references `feature_binding_for_document`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `feature_binding_for_document`

        State and side effects:
            mutates uri.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.feature_binding_for_document` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        uri = getattr(gherkin_document, "uri", None) if gherkin_document is not None else None
        if uri is None:
            return Nothing.value_or(None)
        return self.feature_bindings_by_uri.get(str(uri))

    def resolve_test_step_id_for_runtime_step(self, *, pickle_step: PickleStep) -> str | None:
        """
        Retrieve the generated test step ID mapped to a specific PickleStep instance.

        Returns:
            The mapped test step ID string, or None if not registered.

        Responsibility:
            Retrieve the generated test step ID mapped to a specific PickleStep instance. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.run.lifecycle._run.Run.resolve_test_step_id_for_runtime_step` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - reporting_state.runtime_step_to_pickle_step_id.get: collaborator call used by this boundary
            - id: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - reporting_state.runtime_step_to_pickle_step_id.values: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references
              `resolve_test_step_id_for_runtime_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `resolve_test_step_id_for_runtime_step`

        State and side effects:
            mutates reporting_state, mapped, runtime_step_id_text.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.resolve_test_step_id_for_runtime_step` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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
        Serialize the complete Run state, including its execution stage, configuration, and registered nodes.

        Returns:
            A dictionary containing the full state of the active run.

        Responsibility:
            Serialize the complete Run state, including its execution stage, configuration, and registered nodes. It
            directly owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.run.lifecycle._run.Run.as_dict` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.run_ref.as_dict: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - sorted: collaborator call used by this boundary
            - self.last_error.as_dict: collaborator call used by this boundary
            - self.reporting_state.as_dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/message_transport.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_snapshots.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/_states.py: imports or references `as_dict`
            - src/pytest_bdd/model/run/lifecycle/facade.py: imports or references `as_dict`
            - src/pytest_bdd/model/scenario_run.py: imports or references `as_dict`

        State and side effects:
            mutates active_scenario_id, active_step_id.

        Invariants:
            - `pytest_bdd.model.run.lifecycle._run.Run.as_dict` keeps its documented import path, ownership boundary,
              and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
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
