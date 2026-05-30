"""Run class and lifecycle state management for the run model."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal, Self, cast

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

if TYPE_CHECKING:
    from cucumber_messages import GherkinDocument, Pickle, PickleStep, Source

    from pytest_bdd.compatibility.pytest import Config, FixtureRequest, Session, Stash
    from pytest_bdd.model.scenario_run import ScenarioRun
    from pytest_bdd.types.json import JSONArray, JSONObject, JSONValue

ScenarioRunResult = Result[object, ScenarioRunFailure]

NodeKind = Literal["feature", "scenario", "step"]


@define(slots=True)
class ActiveObjectSet:
    """Store contextual variables representing the current execution parameters for a specific scenario attempt."""

    run: LifecycleObjectRef
    captured_at_stage: RunStage
    feature: LifecycleObjectRef = field(factory=_inactive_feature_ref)
    scenario: LifecycleObjectRef = field(factory=_inactive_scenario_ref)
    step: LifecycleObjectRef = field(factory=_inactive_step_ref)
    previous_step: LifecycleObjectRef = field(factory=_no_previous_step_ref)

    def as_dict(self) -> JSONObject:
        """
        Serialize the entire active object set into a JSON-compatible dictionary.

        Returns:
            A dictionary representing the current active states for run, feature, scenario, and step.

        """
        return {
            "run": self.run.as_dict(),
            "feature": self.feature.as_dict(),
            "scenario": self.scenario.as_dict(),
            "step": self.step.as_dict(),
            "previous_step": self.previous_step.as_dict(),
            "captured_at_stage": self.captured_at_stage.value,
        }


@define(slots=True)
class ReportingLifecycleState:
    """Represent reporting lifecycle state state."""

    run_started_id: str | None = None
    test_run_hook_started_id: str | None = None
    active_test_case_id: str | None = None
    active_test_case_started_id: str | None = None
    active_test_step_id: str | None = None
    runtime_step_to_pickle_step_id: dict[int, str] = field(factory=dict)
    scenario_attempt_context: dict[str, str | int] | None = None
    step_started_timestamp: JSONValue = None
    step_finished_timestamp: JSONValue = None

    def reset_scenario_scope(self) -> None:
        """Clear scenario-level reporting state variables to prepare for a new scenario or clean up."""
        self.active_test_case_id = None
        self.active_test_case_started_id = None
        self.active_test_step_id = None
        self.runtime_step_to_pickle_step_id.clear()
        self.scenario_attempt_context = None
        self.step_started_timestamp = None
        self.step_finished_timestamp = None

    def as_dict(self) -> JSONObject:
        """
        Serialize the reporting lifecycle state into a JSON-compatible dictionary.

        Returns:
            A dictionary representing the reporting identifiers and timestamps.

        """
        return {
            "run_started_id": self.run_started_id,
            "test_run_hook_started_id": self.test_run_hook_started_id,
            "active_test_case_id": self.active_test_case_id,
            "active_test_case_started_id": self.active_test_case_started_id,
            "active_test_step_id": self.active_test_step_id,
            "runtime_step_to_test_step_id": {
                str(key): value for key, value in self.runtime_step_to_pickle_step_id.items()
            },
            "scenario_attempt_context": cast("JSONObject", dict(self.scenario_attempt_context))
            if self.scenario_attempt_context is not None
            else None,
            "step_started_timestamp": self.step_started_timestamp,
            "step_finished_timestamp": self.step_finished_timestamp,
        }


@define(slots=True)
class ReferenceResolverState:
    """Represent reference resolver state state."""

    missing_reference_diagnostics: list[str] = field(factory=list)

    def add_missing_reference(self, message: str) -> None:
        """Record a diagnostic message regarding a missing reference encountered during validation."""
        self.missing_reference_diagnostics.append(message)

    def clear(self) -> None:
        """Clear all accumulated missing reference diagnostic messages."""
        self.missing_reference_diagnostics.clear()

    def as_dict(self) -> JSONObject:
        """
        Serialize the reference resolver state into a dictionary format.

        Returns:
            A dictionary containing the list of missing reference diagnostics.

        """
        return {
            "missing_reference_diagnostics": list(self.missing_reference_diagnostics),
        }


@define(slots=True)
class ContextErrorState:
    """Represent context error state state."""

    code: Literal["object_inactive", "transition_order_violation", "context_not_initialized", "binding_missing"]
    message: str
    hook_name: str
    stage: RunStage
    requested_kind: LifecycleObjectRef.kind | None = None

    def as_dict(self) -> JSONObject:
        """
        Serialize the context error state into a dictionary format.

        Returns:
            A dictionary describing the error code, message, and related lifecycle context.

        """
        return {
            "code": self.code,
            "message": self.message,
            "hook_name": self.hook_name,
            "stage": self.stage.value,
            "requested_kind": self.requested_kind,
        }


@define(slots=True)
class Run(StashBound):
    """
    Represent run state.

    Raises:
        AttributeError: If the operation cannot be completed.
        RuntimeError: If the operation cannot be completed.

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

        """
        scenario_run = self.active_scenario_run
        if scenario_run is not None:
            return scenario_run
        msg = f"Active scenario run is unavailable for {hook_name}; lifecycle context is not initialized"
        raise RuntimeError(msg)

    def advance_transition(self) -> None:
        """Increment the internal transition index counter to represent state progression."""
        self.transition_index += 1

    @classmethod
    def _build_for_owner(cls, owner: object) -> Run:
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

        """
        run = cls._build_for_owner(config)
        run.initialize_in_stash(stash)
        EnvelopeRegistry(identifiable=run.identifiable_registry).initialize_in_stash(stash)
        return run

    @staticmethod
    def _request_key(request: FixtureRequest) -> str:
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

        """
        run = cls.find_in_stash(request.config.stash).value_or(None)
        if run is None:
            return Nothing.value_or(None)
        key = cls._request_key(request)
        return run.scenario_runs_by_request.get(key)

    @classmethod
    def set_scenario_run(cls, request: FixtureRequest, scenario_run: ScenarioRun) -> None:
        """Register a ScenarioRun instance against a pytest FixtureRequest in the active Run state."""
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

        """
        from pytest_bdd.model.scenario_run import RunNode, ScenarioRun  # noqa: PLC0415 -- circular import with Run
        from pytest_bdd.plugin.pickle_runner.run_transitions import (  # noqa: PLC0415 -- circular import with run_transitions
            build_lifecycle_ref,
            initial_scenario_run_id,
            runtime_object_id,
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
        key = type(self)._request_key(request)  # noqa: SLF001
        run.scenario_runs_by_request[key] = scenario_run
        run.active_scenario_run = scenario_run
        return scenario_run

    def index_identifiable_tree(self, root: object) -> None:
        """Recursively scan and register all identifiable objects within a tree into the registry."""
        self.identifiable_registry.index_tree(root)

    def map_runtime_step_to_test_step_id(self, *, pickle_step: PickleStep, test_step_id: str) -> None:
        """Record a mapping from a runtime PickleStep object identity to its corresponding executed test step ID."""
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

        """
        if uri is None:
            return Nothing.value_or(None)
        return self.feature_bindings_by_uri.get(str(uri))

    def feature_binding_for_document(self, gherkin_document: GherkinDocument | None) -> FeatureRuntimeBinding | None:
        """
        Look up a previously registered feature binding using a Gherkin document reference.

        Returns:
            The FeatureRuntimeBinding if found, or None.

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


@define(slots=True)
class ReportingContextSnapshot:
    """Capture an immutable, point-in-time snapshot of the active execution context for reporting purposes."""

    run_id: str
    active_set: ActiveObjectSet
    stage: RunStage
    resolved_from_hierarchy: bool
    fallback_reason: str | None = None

    def as_dict(self) -> JSONObject:
        """
        Serialize the reporting context snapshot into a dictionary format.

        Returns:
            A dictionary containing the active object references and resolution metadata.

        """
        return {
            "run_id": self.run_id,
            "active_set": self.active_set.as_dict(),
            "stage": self.stage.value,
            "resolved_from_hierarchy": self.resolved_from_hierarchy,
            "fallback_reason": self.fallback_reason,
        }


@define(slots=True)
class ExternalApiCompatibilityRecord:
    """Log structural changes and migration requirements for an exposed API surface relative to a baseline."""

    api_surface_id: str
    baseline_reference: str
    changed_symbols: list[str]
    removed_symbols: list[str]
    renamed_symbols: list[str]
    additive_symbols: list[str]
    consumer_migration_required: bool

    def as_dict(self) -> JSONObject:
        """
        Serialize the compatibility record into a dictionary format.

        Returns:
            A dictionary detailing the symbol changes and consumer migration requirements.

        """
        return {
            "api_surface_id": self.api_surface_id,
            "baseline_reference": self.baseline_reference,
            "changed_symbols": cast("JSONArray", list(self.changed_symbols)),
            "removed_symbols": cast("JSONArray", list(self.removed_symbols)),
            "renamed_symbols": cast("JSONArray", list(self.renamed_symbols)),
            "additive_symbols": cast("JSONArray", list(self.additive_symbols)),
            "consumer_migration_required": self.consumer_migration_required,
        }
