from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, ClassVar, Literal, Self, cast

from attrs import define, field
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    GherkinDocument,
    Pickle,
    PickleStep,
    Scenario,
    Source,
    Step,
    TableRow,
)
from gherkin.pickles.compiler import Compiler as PicklesCompiler

from pytest_bdd.compatibility.enum import StrEnum
from pytest_bdd.const import TAG_PREFIX
from pytest_bdd.model.message_converter import message_converter
from pytest_bdd.model.message_registry import EnvelopeRegistry, IdentifiableObjectRegistry
from pytest_bdd.model.stash_access import StashBound
from pytest_bdd.types.json import JSONArray, JSONObject, JSONValue
from pytest_bdd.types.protocol import Identifiable, MultiLinkedAST
from pytest_bdd.util.toolz_extra import deepattrgetter

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from gherkin.pickles.compiler import GherkinDocumentWithURI
    from gherkin.stream.id_generator import IdGenerator

    from pytest_bdd.compatibility.pytest import Config, FixtureRequest, Session, Stash

LifecycleKind = Literal["run", "feature", "scenario", "step"]
NodeKind = Literal["feature", "scenario", "step"]


class HookPhase(StrEnum):
    before_scenario = "pytest_bdd_before_scenario"
    run_scenario = "pytest_bdd_run_scenario"
    after_scenario = "pytest_bdd_after_scenario"
    run_step = "pytest_bdd_run_step"
    before_step = "pytest_bdd_before_step"
    before_step_call = "pytest_bdd_before_step_call"
    after_step = "pytest_bdd_after_step"
    step_error = "pytest_bdd_step_error"
    step_lookup_error = "pytest_bdd_step_lookup_error"


class RunStage(StrEnum):
    idle = "idle"
    scenario_setup = "scenario_setup"
    scenario_running = "scenario_running"
    step_running = "step_running"
    scenario_teardown = "scenario_teardown"
    finished = "finished"


class RunStatus(StrEnum):
    ok = "ok"
    failed = "failed"
    interrupted = "interrupted"


@define(slots=True)
class LifecycleObjectRef:
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
    id: str = "step:no_previous_step"
    text: str = ""
    keyword: str = ""


def _inactive_feature_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("feature", reason="idle")


def _inactive_scenario_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("scenario", reason="idle")


def _inactive_step_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("step", reason="idle", fail_fast_code="object_inactive")


def _no_previous_step_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("step", reason="no_previous_step")


def _finished_feature_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("feature", reason="finished")


def _finished_scenario_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("scenario", reason="finished")


def _finished_step_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("step", reason="finished", fail_fast_code="object_inactive")


def _finished_previous_step_ref() -> LifecycleObjectRef:
    return LifecycleObjectRef.inactive("step", reason="finished")


@define(slots=True)
class ActiveObjectSet:
    run: LifecycleObjectRef
    captured_at_stage: RunStage
    feature: LifecycleObjectRef = field(factory=_inactive_feature_ref)
    scenario: LifecycleObjectRef = field(factory=_inactive_scenario_ref)
    step: LifecycleObjectRef = field(factory=_inactive_step_ref)
    previous_step: LifecycleObjectRef = field(factory=_no_previous_step_ref)

    def as_dict(self) -> JSONObject:
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
        self.active_test_case_id = None
        self.active_test_case_started_id = None
        self.active_test_step_id = None
        self.runtime_step_to_pickle_step_id.clear()
        self.scenario_attempt_context = None
        self.step_started_timestamp = None
        self.step_finished_timestamp = None

    def as_dict(self) -> JSONObject:
        return {
            "run_started_id": self.run_started_id,
            "test_run_hook_started_id": self.test_run_hook_started_id,
            "active_test_case_id": self.active_test_case_id,
            "active_test_case_started_id": self.active_test_case_started_id,
            "active_test_step_id": self.active_test_step_id,
            "runtime_step_to_test_step_id": {
                str(key): value for key, value in self.runtime_step_to_pickle_step_id.items()
            },
            "scenario_attempt_context": cast(JSONObject, dict(self.scenario_attempt_context))
            if self.scenario_attempt_context is not None
            else None,
            "step_started_timestamp": self.step_started_timestamp,
            "step_finished_timestamp": self.step_finished_timestamp,
        }


@define(slots=True)
class ReferenceResolverState:
    missing_reference_diagnostics: list[str] = field(factory=list)

    def add_missing_reference(self, message: str) -> None:
        self.missing_reference_diagnostics.append(message)

    def clear(self) -> None:
        self.missing_reference_diagnostics.clear()

    def as_dict(self) -> JSONObject:
        return {
            "missing_reference_diagnostics": list(self.missing_reference_diagnostics),
        }


@define(slots=True)
class ContextErrorState:
    code: Literal["object_inactive", "transition_order_violation", "context_not_initialized", "binding_missing"]
    message: str
    hook_name: str
    stage: RunStage
    requested_kind: LifecycleKind | None = None

    def as_dict(self) -> JSONObject:
        return {
            "code": self.code,
            "message": self.message,
            "hook_name": self.hook_name,
            "stage": self.stage.value,
            "requested_kind": self.requested_kind,
        }


@define(slots=True)
class FeatureRuntimeBinding:
    uri: str
    filename: str
    gherkin_document: GherkinDocument
    run: Run = field(repr=False, eq=False)
    source: Source | None = None
    pickles: tuple[Pickle, ...] = ()

    @staticmethod
    def _feature_filename_from_uri(uri: str | None) -> str:
        if uri is None:
            return "<unknown>"
        if uri.startswith("file:"):
            return uri.removeprefix("file:")
        return str(Path(uri).as_posix())

    @staticmethod
    def load_gherkin_document(raw_gherkin_document: object) -> GherkinDocument:
        if isinstance(raw_gherkin_document, GherkinDocument):
            return raw_gherkin_document
        return message_converter.from_dict(raw_gherkin_document, GherkinDocument)

    @staticmethod
    def load_pickles(pickles_data: Iterable[object]) -> tuple[Pickle, ...]:
        return tuple(message_converter.from_dict(pickle_data, Pickle) for pickle_data in pickles_data)

    @classmethod
    def build(
        cls,
        *,
        run: Run,
        gherkin_document: GherkinDocument,
        source: Source | None = None,
        pickles: tuple[Pickle, ...] | list[Pickle] | None = None,
    ) -> FeatureRuntimeBinding:
        filename = getattr(gherkin_document, "_pytest_bdd_filename", None)
        if filename is None and source is not None:
            filename = cls._feature_filename_from_uri(source.uri)
        if filename is None:
            filename = cls._feature_filename_from_uri(getattr(gherkin_document, "uri", None))

        binding = cls(
            uri=str(gherkin_document.uri),
            filename=str(filename),
            gherkin_document=gherkin_document,
            run=run,
            source=source,
            pickles=tuple(pickles or ()),
        )
        binding.index_runtime_objects()
        return binding

    def ensure_pickles(self, *, id_generator: IdGenerator | None) -> tuple[Pickle, ...]:
        if self.pickles:
            return self.pickles

        gherkin_document_payload = cast(JSONObject, message_converter.to_dict(self.gherkin_document))
        pickles_data = PicklesCompiler(id_generator=id_generator).compile(
            cast("GherkinDocumentWithURI", gherkin_document_payload)
        )
        self.pickles = self.load_pickles(pickles_data)
        self.run.index_identifiable_tree(self.pickles)
        return self.pickles

    def index_runtime_objects(self) -> None:
        feature_message = getattr(self.gherkin_document, "feature", None)
        if feature_message is not None:
            self.run.index_identifiable_tree(feature_message)
        if self.pickles:
            self.run.index_identifiable_tree(self.pickles)

    def resolve_node(self, object_id: str) -> Identifiable:
        return self.run.identifiable_registry.resolve(object_id)

    def linked_ast_nodes_for(self, obj: object) -> Generator[Identifiable]:
        ast_node_ids: tuple[str, ...]
        if isinstance(obj, MultiLinkedAST):
            ast_node_ids = tuple(obj.ast_node_ids)
        else:
            ast_node_id = getattr(obj, "ast_node_id", None)
            ast_node_ids = (ast_node_id,) if isinstance(ast_node_id, str) else ()

        for ast_node_id in ast_node_ids:
            with suppress(KeyError):
                yield self.resolve_node(ast_node_id)

    def pickle_ast_table_rows(self, pickle: Pickle) -> list[TableRow]:
        return [node for node in self.linked_ast_nodes_for(pickle) if isinstance(node, TableRow)]

    def pickle_table_rows_breadcrumb(self, pickle: Pickle) -> str:
        table_rows_lines = ",".join(
            (
                f"line: {deepattrgetter('location.line', default=-1)(row)[0]}"
                for row in self.pickle_ast_table_rows(pickle)
            ),
        )
        return f"[table_rows:[{table_rows_lines}]]" if table_rows_lines else ""

    def pickle_ast_scenario(self, pickle: Pickle) -> Scenario | None:
        return next(
            (node for node in self.linked_ast_nodes_for(pickle) if isinstance(node, Scenario)),
            None,
        )

    def pickle_line_number(self, pickle: Pickle) -> int:
        scenario = self.pickle_ast_scenario(pickle)
        if scenario is None:
            return -1
        location = scenario.location
        line = getattr(location, "line", None)
        return int(line) if line is not None else -1

    def pickle_step_ast_step(self, pickle_step: PickleStep) -> Step | None:
        return next(
            (node for node in self.linked_ast_nodes_for(pickle_step) if isinstance(node, Step)),
            None,
        )

    def step_keyword(self, step: PickleStep) -> str | None:
        model_step = self.pickle_step_ast_step(step)
        if model_step is not None:
            keyword = getattr(model_step, "keyword", None)
            if isinstance(keyword, str):
                return keyword.strip()
        return None

    def step_prefix(self, step: PickleStep) -> str | None:
        keyword = self.step_keyword(step)
        return keyword.lower() if keyword is not None else None

    def step_line_number(self, step: PickleStep) -> int | None:
        model_step = self.pickle_step_ast_step(step)
        if model_step is not None:
            return model_step.location.line if model_step.location is not None else -1
        return None

    def step_doc_string(self, step: PickleStep) -> object | None:
        return getattr(self.pickle_step_ast_step(step), "doc_string", None)

    def step_data_table(self, step: PickleStep) -> object | None:
        return getattr(self.pickle_step_ast_step(step), "data_table", None)

    @property
    def rel_filename(self) -> str | None:
        if self.uri.startswith("file:"):
            return self.uri[len("file:") :]
        return None

    @property
    def name(self) -> str | None:
        feature_message = getattr(self.gherkin_document, "feature", None)
        return str(feature_message.name) if feature_message is not None else None

    @property
    def line_number(self) -> int | None:
        feature_message = getattr(self.gherkin_document, "feature", None)
        location = getattr(feature_message, "location", None)
        line = getattr(location, "line", None)
        return int(line) if line is not None else None

    @property
    def description(self) -> str | None:
        feature_message = getattr(self.gherkin_document, "feature", None)
        description = getattr(feature_message, "description", None)
        if description is None:
            return None
        return dedent(str(description))

    @property
    def tag_names(self) -> list[str]:
        feature_message = getattr(self.gherkin_document, "feature", None)
        tags = getattr(feature_message, "tags", None) or ()
        return sorted(str(tag.name).lstrip(TAG_PREFIX) for tag in tags)


@define(slots=True)
class Run(StashBound):
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
        if self.active_scenario_run is None:
            return None
        return self.active_scenario_run.feature_binding

    @property
    def active_scenario_id(self) -> str:
        scenario_run = self.active_scenario_run
        node = scenario_run.scenario_node if scenario_run is not None else None
        if node is not None and node.is_active:
            return str(node.id)
        msg = "No active scenario"
        raise AttributeError(msg)

    @property
    def active_step_id(self) -> str:
        scenario_run = self.active_scenario_run
        node = scenario_run.step_node if scenario_run is not None else None
        if node is not None and node.is_active:
            return str(node.id)
        msg = "No active step"
        raise AttributeError(msg)

    def require_active_scenario_run(self, *, hook_name: str) -> ScenarioRun:
        scenario_run = self.active_scenario_run
        if scenario_run is not None:
            return scenario_run
        msg = f"Active scenario run is unavailable for {hook_name}; lifecycle context is not initialized"
        raise RuntimeError(msg)

    def advance_transition(self) -> None:
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
        run = cls._build_for_owner(session)
        run.initialize_in_stash(stash)
        EnvelopeRegistry(identifiable=run.identifiable_registry).initialize_in_stash(stash)
        return run

    @classmethod
    def initialize_for_config(cls, *, stash: Stash, config: Config) -> Run:
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
        run = cls.find_in_stash(request.config.stash)
        if run is None:
            return None
        key = cls._request_key(request)
        return run.scenario_runs_by_request.get(key)

    @classmethod
    def set_scenario_run(cls, request: FixtureRequest, scenario_run: ScenarioRun) -> None:
        run = scenario_run.run
        if run is None:
            run = cls.from_stash(request.config.stash)
            scenario_run.run = run
        key = cls._request_key(request)
        run.scenario_runs_by_request[key] = scenario_run
        run.active_scenario_run = scenario_run

    @classmethod
    def pop_scenario_run(cls, request: FixtureRequest) -> ScenarioRun | None:
        config = getattr(request, "config", None)
        stash = getattr(config, "stash", None)
        run = cls.find_in_stash(stash) if stash is not None else None
        if run is None:
            return None
        key = cls._request_key(request)
        scenario_run = run.scenario_runs_by_request.pop(key, None)
        if scenario_run is None:
            return None

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
        from pytest_bdd.plugin.pickle_runner.run_transitions import (
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
        key = type(self)._request_key(request)
        run.scenario_runs_by_request[key] = scenario_run
        run.active_scenario_run = scenario_run
        return scenario_run

    def index_identifiable_tree(self, root: object) -> None:
        self.identifiable_registry.index_tree(root)

    def map_runtime_step_to_test_step_id(self, *, pickle_step: PickleStep, test_step_id: str) -> None:
        self.reporting_state.runtime_step_to_pickle_step_id[id(pickle_step)] = test_step_id

    def ensure_feature_binding(
        self,
        *,
        gherkin_document: GherkinDocument,
        source: Source | None = None,
        pickles: tuple[Pickle, ...] | list[Pickle] | None = None,
    ) -> FeatureRuntimeBinding:
        uri = str(gherkin_document.uri)
        binding = self.feature_bindings_by_uri.get(uri)
        if binding is None:
            binding = FeatureRuntimeBinding.build(
                run=self,
                gherkin_document=gherkin_document,
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
            binding.filename = FeatureRuntimeBinding._feature_filename_from_uri(uri)
        return binding

    def feature_binding_for_uri(self, uri: str | None) -> FeatureRuntimeBinding | None:
        if uri is None:
            return None
        return self.feature_bindings_by_uri.get(str(uri))

    def feature_binding_for_document(self, gherkin_document: GherkinDocument | None) -> FeatureRuntimeBinding | None:
        uri = getattr(gherkin_document, "uri", None) if gherkin_document is not None else None
        if uri is None:
            return None
        return self.feature_bindings_by_uri.get(str(uri))

    def resolve_test_step_id_for_runtime_step(self, *, pickle_step: PickleStep) -> str | None:
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
            "feature_bindings_by_uri": cast(JSONArray, sorted(self.feature_bindings_by_uri)),
            "active_feature_id": self.active_feature_id,
            "active_feature_uri": self.active_feature_uri,
            "active_scenario_id": active_scenario_id,
            "active_step_id": active_step_id,
            "last_error": self.last_error.as_dict() if self.last_error is not None else None,
            "reporting_state": self.reporting_state.as_dict(),
        }


@define(slots=True)
class RunNode:
    id: str
    parent_id: str
    kind: NodeKind
    object_ref: LifecycleObjectRef
    is_active: bool
    opened_at_transition: int
    closed_at_transition: int | None = None

    def close(self, at_transition: int) -> None:
        self.is_active = False
        self.closed_at_transition = at_transition

    def as_dict(self) -> JSONObject:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "kind": self.kind,
            "object_ref": self.object_ref.as_dict(),
            "is_active": self.is_active,
            "opened_at_transition": self.opened_at_transition,
            "closed_at_transition": self.closed_at_transition,
        }


@define(slots=True)
class StepRun:
    step: PickleStep | None = None
    keyword: str | None = None
    text: str = ""
    parameters: dict[str, object] = field(factory=dict)
    status: RunStatus = RunStatus.ok
    duration: float | None = None
    attachments: list[object] = field(factory=list)
    doc_string: object | None = None
    data_table: object | None = None
    line_number: int | None = None


@define(slots=True)
class ScenarioRun:
    id: str
    run_ref: LifecycleObjectRef
    active_hook: HookPhase
    stage: RunStage
    status: RunStatus
    active_set: ActiveObjectSet
    run: Run
    transition_index: int = 0
    feature_ref: LifecycleObjectRef = field(factory=_inactive_feature_ref)
    scenario_ref: LifecycleObjectRef = field(factory=_inactive_scenario_ref)
    step_ref: LifecycleObjectRef = field(factory=_inactive_step_ref)
    previous_step_ref: LifecycleObjectRef = field(factory=_no_previous_step_ref)
    last_error: ContextErrorState | None = None
    feature_uri: str | None = None
    feature_node: RunNode | None = None
    scenario_node: RunNode | None = None
    step_node: RunNode | None = None
    gherkin_document: GherkinDocument | None = None
    feature_source: Source | None = None
    pickle: Pickle | None = None
    step_object: PickleStep | None = None
    previous_step_object: PickleStep | NoPreviousStep = field(factory=NoPreviousStep)
    step_run: StepRun | None = None
    reference_resolver: ReferenceResolverState = field(factory=ReferenceResolverState)
    _active_kind_index: dict[LifecycleKind, LifecycleObjectRef] = field(init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        self._active_kind_index = {
            "run": self.active_set.run,
            "feature": self.active_set.feature,
            "scenario": self.active_set.scenario,
            "step": self.active_set.step,
        }

    def advance_transition(self) -> None:
        self.transition_index += 1

    def record_context_error(
        self,
        *,
        code: Literal["object_inactive", "transition_order_violation", "context_not_initialized", "binding_missing"],
        message: str,
        hook_name: str,
        requested_kind: LifecycleKind | None = None,
    ) -> ContextErrorState:
        error = ContextErrorState(
            code=code,
            message=message,
            hook_name=hook_name,
            stage=self.stage,
            requested_kind=requested_kind,
        )
        self.last_error = error
        self.run.last_error = error
        return error

    def set_active_set(self, active_set: ActiveObjectSet) -> None:
        self.active_set = active_set
        self._active_kind_index = {
            "run": self.active_set.run,
            "feature": self.active_set.feature,
            "scenario": self.active_set.scenario,
            "step": self.active_set.step,
        }

    def get_active_object(self, kind: LifecycleKind) -> LifecycleObjectRef | None:
        candidate = self._active_kind_index.get(kind)
        if candidate is None or not candidate.is_active:
            return None
        return candidate

    def require_feature_binding(self, *, hook_name: str) -> FeatureRuntimeBinding:
        binding = self.feature_binding
        if binding is not None:
            return binding
        error = self.record_context_error(
            code="binding_missing",
            message=f"Feature runtime binding is unavailable for {hook_name} at stage '{self.stage.value}'",
            hook_name=hook_name,
            requested_kind="feature",
        )
        raise RuntimeError(error.message)

    def require_gherkin_document(self, *, hook_name: str) -> GherkinDocument:
        binding = self.feature_binding
        if binding is not None:
            return binding.gherkin_document
        if self.gherkin_document is not None:
            return self.gherkin_document
        error = self.record_context_error(
            code="binding_missing",
            message=f"Feature object is unavailable for {hook_name} at stage '{self.stage.value}'",
            hook_name=hook_name,
            requested_kind="feature",
        )
        raise RuntimeError(error.message)

    def require_pickle(self, *, hook_name: str) -> Pickle:
        if self.pickle is not None:
            return self.pickle
        error = self.record_context_error(
            code="context_not_initialized",
            message=f"Pickle object is unavailable for {hook_name} at stage '{self.stage.value}'",
            hook_name=hook_name,
            requested_kind="scenario",
        )
        raise RuntimeError(error.message)

    def require_step_object(self, *, hook_name: str) -> PickleStep:
        if self.step_object is not None:
            return self.step_object
        error = self.record_context_error(
            code="context_not_initialized",
            message=f"Step object is unavailable for {hook_name} at stage '{self.stage.value}'",
            hook_name=hook_name,
            requested_kind="step",
        )
        raise RuntimeError(error.message)

    def ensure_finished_for_cleanup(self, *, at_transition: int) -> None:
        if self.step_node is not None and self.step_node.is_active:
            self.step_node.close(at_transition)
        if self.scenario_node is not None and self.scenario_node.is_active:
            self.scenario_node.close(at_transition)
        if self.feature_node is not None and self.feature_node.is_active:
            self.feature_node.close(at_transition)

        self.feature_ref = _finished_feature_ref()
        self.scenario_ref = _finished_scenario_ref()
        self.step_ref = _finished_step_ref()
        self.previous_step_ref = _finished_previous_step_ref()
        self.step_object = None
        self.previous_step_object = NoPreviousStep()
        self.stage = RunStage.finished
        self.set_active_set(
            ActiveObjectSet(
                run=self.run_ref,
                feature=self.feature_ref,
                scenario=self.scenario_ref,
                step=self.step_ref,
                previous_step=self.previous_step_ref,
                captured_at_stage=RunStage.finished,
            )
        )

    @property
    def feature_binding(self) -> FeatureRuntimeBinding | None:
        if self.feature_uri is not None:
            return self.run.feature_binding_for_uri(self.feature_uri)
        return self.run.feature_binding_for_document(self.gherkin_document)

    def as_dict(self) -> JSONObject:
        return {
            "id": self.id,
            "run_ref": self.run_ref.as_dict(),
            "feature_ref": self.feature_ref.as_dict(),
            "scenario_ref": self.scenario_ref.as_dict(),
            "step_ref": self.step_ref.as_dict(),
            "previous_step_ref": self.previous_step_ref.as_dict(),
            "active_hook": self.active_hook.value,
            "stage": self.stage.value,
            "status": self.status.value,
            "active_set": self.active_set.as_dict(),
            "transition_index": self.transition_index,
            "feature_uri": self.feature_uri,
            "last_error": self.last_error.as_dict() if self.last_error is not None else None,
            "run": self.run.as_dict(),
            "feature_node": self.feature_node.as_dict() if self.feature_node is not None else None,
            "scenario_node": self.scenario_node.as_dict() if self.scenario_node is not None else None,
            "step_node": self.step_node.as_dict() if self.step_node is not None else None,
            "reference_resolver": self.reference_resolver.as_dict(),
        }


@define(slots=True)
class ReportingContextSnapshot:
    run_id: str
    active_set: ActiveObjectSet
    stage: RunStage
    resolved_from_hierarchy: bool
    fallback_reason: str | None = None

    def as_dict(self) -> JSONObject:
        return {
            "run_id": self.run_id,
            "active_set": self.active_set.as_dict(),
            "stage": self.stage.value,
            "resolved_from_hierarchy": self.resolved_from_hierarchy,
            "fallback_reason": self.fallback_reason,
        }


@define(slots=True)
class ExternalApiCompatibilityRecord:
    api_surface_id: str
    baseline_reference: str
    changed_symbols: list[str]
    removed_symbols: list[str]
    renamed_symbols: list[str]
    additive_symbols: list[str]
    consumer_migration_required: bool

    def as_dict(self) -> JSONObject:
        return {
            "api_surface_id": self.api_surface_id,
            "baseline_reference": self.baseline_reference,
            "changed_symbols": cast(JSONArray, list(self.changed_symbols)),
            "removed_symbols": cast(JSONArray, list(self.removed_symbols)),
            "renamed_symbols": cast(JSONArray, list(self.renamed_symbols)),
            "additive_symbols": cast(JSONArray, list(self.additive_symbols)),
            "consumer_migration_required": self.consumer_migration_required,
        }
