"""
Provide feature runtime binding helpers.

Responsibility:
    Provide feature runtime binding helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.feature_binding` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - FeatureRuntimeBinding: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `feature_binding`
    - src/pytest_bdd/model/run_access.py: imports or references `feature_binding`
    - src/pytest_bdd/model/scenario_report.py: imports or references `feature_binding`
    - src/pytest_bdd/model/scenario_run.py: imports or references `feature_binding`
    - src/pytest_bdd/parser.py: imports or references `feature_binding`

State and side effects:
    mutates feature_message, ast_node_ids, filename, scenario_ast_id, row_ast_id; depends on __future__.annotations,
    contextlib.suppress, pathlib.Path, textwrap.dedent, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.model.feature_binding` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, cast

from attrs import define, field
from cucumber_messages import (  # type:ignore[attr-defined]  # upstream library missing type stubs
    GherkinDocument,
    Pickle,
    PickleStep,
    Scenario,
    Source,
    Step,
    TableRow,
)
from gherkin.pickles.compiler import Compiler as PicklesCompiler
from returns.maybe import Nothing

from pytest_bdd.const import TAG_PREFIX
from pytest_bdd.model.message_converter import message_converter
from pytest_bdd.model.message_registry import IdentifiableObjectRegistry
from pytest_bdd.types.protocol import Identifiable, MultiLinkedAST
from pytest_bdd.util.toolz_extra import deepattrgetter

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from gherkin.pickles.compiler import GherkinDocumentWithURI
    from gherkin.stream.id_generator import IdGenerator

    from pytest_bdd.model.run import Run
    from pytest_bdd.types.json import JSONObject


@define(slots=True)  # noqa: PLR0904
class FeatureRuntimeBinding:
    """
    Represent feature runtime binding state.

    Yields:
        Generated values.

    Responsibility:
        Represent feature runtime binding state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.feature_binding.FeatureRuntimeBinding` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _feature_filename_from_uri: owns nested behavior below this boundary
        - load_gherkin_document: owns nested behavior below this boundary
        - load_pickles: owns nested behavior below this boundary
        - build: owns nested behavior below this boundary
        - ensure_pickles: owns nested behavior below this boundary
        - index_runtime_objects: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/__init__.py: imports or references `FeatureRuntimeBinding`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `FeatureRuntimeBinding`
        - src/pytest_bdd/model/run_access.py: imports or references `FeatureRuntimeBinding`
        - src/pytest_bdd/model/scenario_report.py: imports or references `FeatureRuntimeBinding`
        - src/pytest_bdd/model/scenario_run.py: imports or references `FeatureRuntimeBinding`

    State and side effects:
        mutates feature_message, ast_node_ids, filename, scenario_ast_id, row_ast_id.

    Invariants:
        - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

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

    uri: str
    filename: str
    gherkin_document: GherkinDocument
    run: Run = field(repr=False, eq=False)
    source: Source | None = None
    pickles: tuple[Pickle, ...] = ()
    ast_registry: IdentifiableObjectRegistry = field(factory=IdentifiableObjectRegistry, repr=False, eq=False)

    @staticmethod
    def _feature_filename_from_uri(uri: str | None) -> str:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding._feature_filename_from_uri` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding._feature_filename_from_uri` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Path.as_posix: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - uri.startswith: collaborator call used by this boundary
            - uri.removeprefix: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_feature_filename_from_uri`
            - src/pytest_bdd/model/run_access.py: imports or references `_feature_filename_from_uri`
            - src/pytest_bdd/model/scenario_report.py: imports or references `_feature_filename_from_uri`
            - src/pytest_bdd/model/scenario_run.py: imports or references `_feature_filename_from_uri`
            - src/pytest_bdd/parser.py: imports or references `_feature_filename_from_uri`

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
            #arch-eval:locational_stability=4
        """
        if uri is None:
            return "<unknown>"
        if uri.startswith("file:"):
            return Path(uri.removeprefix("file:")).as_posix()
        return str(Path(uri).as_posix())

    @staticmethod
    def load_gherkin_document(raw_gherkin_document: object) -> GherkinDocument:
        """
        Parse or pass through a Gherkin document object from raw input.

        Returns:
            The loaded GherkinDocument instance.

        Responsibility:
            Parse or pass through a Gherkin document object from raw input. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.load_gherkin_document` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - message_converter.from_dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `load_gherkin_document`
            - src/pytest_bdd/model/run_access.py: imports or references `load_gherkin_document`
            - src/pytest_bdd/model/scenario_report.py: imports or references `load_gherkin_document`
            - src/pytest_bdd/model/scenario_run.py: imports or references `load_gherkin_document`
            - src/pytest_bdd/parser.py: imports or references `load_gherkin_document`

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
            #arch-eval:locational_stability=4

        """
        if isinstance(raw_gherkin_document, GherkinDocument):
            return raw_gherkin_document
        return cast("GherkinDocument", message_converter.from_dict(raw_gherkin_document, GherkinDocument))

    @staticmethod
    def load_pickles(pickles_data: Iterable[object]) -> tuple[Pickle, ...]:
        """
        Convert a collection of raw pickle data representations into a tuple of Pickle instances.

        Returns:
            A tuple of loaded Pickle objects.

        Responsibility:
            Convert a collection of raw pickle data representations into a tuple of Pickle instances. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.load_pickles` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - tuple: collaborator call used by this boundary
            - message_converter.from_dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `load_pickles`
            - src/pytest_bdd/model/run_access.py: imports or references `load_pickles`
            - src/pytest_bdd/model/scenario_report.py: imports or references `load_pickles`
            - src/pytest_bdd/model/scenario_run.py: imports or references `load_pickles`
            - src/pytest_bdd/parser.py: imports or references `load_pickles`

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
            #arch-eval:locational_stability=4

        """
        return tuple(message_converter.from_dict(pickle_data, Pickle) for pickle_data in pickles_data)

    @classmethod
    def build(
        cls,
        *,
        run: Run,
        gherkin_document: GherkinDocument,
        filename: str | None = None,
        source: Source | None = None,
        pickles: tuple[Pickle, ...] | list[Pickle] | None = None,
    ) -> FeatureRuntimeBinding:
        """
        Construct a new FeatureRuntimeBinding, inferring filenames and indexing contents.

        Returns:
            A fully initialized FeatureRuntimeBinding instance.

        Responsibility:
            Construct a new FeatureRuntimeBinding, inferring filenames and indexing contents. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.build`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls._feature_filename_from_uri: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - cls: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - binding.index_runtime_objects: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `build`
            - src/pytest_bdd/model/run_access.py: imports or references `build`
            - src/pytest_bdd/model/scenario_report.py: imports or references `build`
            - src/pytest_bdd/model/scenario_run.py: imports or references `build`
            - src/pytest_bdd/parser.py: imports or references `build`

        State and side effects:
            mutates filename, binding.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.build` keeps its documented import path, ownership
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
        """
        Retrieve compiled pickles for the feature, compiling them on demand if not already present.

        Returns:
            A tuple of Pickle objects associated with the feature document.

        Responsibility:
            Retrieve compiled pickles for the feature, compiling them on demand if not already present. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.ensure_pickles` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - message_converter.to_dict: collaborator call used by this boundary
            - PicklesCompiler.compile: collaborator call used by this boundary
            - PicklesCompiler: collaborator call used by this boundary
            - self.load_pickles: collaborator call used by this boundary
            - self.run.index_identifiable_tree: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `ensure_pickles`
            - src/pytest_bdd/model/run_access.py: imports or references `ensure_pickles`
            - src/pytest_bdd/model/scenario_report.py: imports or references `ensure_pickles`
            - src/pytest_bdd/model/scenario_run.py: imports or references `ensure_pickles`
            - src/pytest_bdd/parser.py: imports or references `ensure_pickles`

        State and side effects:
            mutates gherkin_document_payload, pickles_data, self.pickles.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.ensure_pickles` keeps its documented import path,
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
        if self.pickles:
            return self.pickles

        gherkin_document_payload = cast("JSONObject", message_converter.to_dict(self.gherkin_document))
        pickles_data = PicklesCompiler(id_generator=id_generator).compile(
            cast("GherkinDocumentWithURI", gherkin_document_payload),
        )
        self.pickles = self.load_pickles(pickles_data)
        self.run.index_identifiable_tree(self.pickles)
        return self.pickles

    def index_runtime_objects(self) -> None:
        """
        Index the Gherkin document and its associated pickles into the run's identifiable registry.

        Responsibility:
            Index the Gherkin document and its associated pickles into the run's identifiable registry. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.index_runtime_objects` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.run.index_identifiable_tree: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - IdentifiableObjectRegistry: collaborator call used by this boundary
            - self.ast_registry.index_tree: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `index_runtime_objects`
            - src/pytest_bdd/model/run_access.py: imports or references `index_runtime_objects`
            - src/pytest_bdd/model/scenario_report.py: imports or references `index_runtime_objects`
            - src/pytest_bdd/model/scenario_run.py: imports or references `index_runtime_objects`
            - src/pytest_bdd/parser.py: imports or references `index_runtime_objects`

        State and side effects:
            mutates feature_message, self.ast_registry.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.index_runtime_objects` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        feature_message = getattr(self.gherkin_document, "feature", None)
        self.ast_registry = IdentifiableObjectRegistry()
        if feature_message is not None:
            self.ast_registry.index_tree(feature_message)
            self.run.index_identifiable_tree(feature_message)
        if self.pickles:
            self.run.index_identifiable_tree(self.pickles)

    def resolve_node(self, object_id: str) -> Identifiable:
        """
        Look up a generic identifiable object by its ID within the current run registry.

        Returns:
            The resolved Identifiable object instance.

        Responsibility:
            Look up a generic identifiable object by its ID within the current run registry. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.resolve_node` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.ast_registry.resolve: collaborator call used by this boundary
            - self.run.identifiable_registry.resolve: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `resolve_node`
            - src/pytest_bdd/model/run_access.py: imports or references `resolve_node`
            - src/pytest_bdd/model/scenario_report.py: imports or references `resolve_node`
            - src/pytest_bdd/model/scenario_run.py: imports or references `resolve_node`
            - src/pytest_bdd/parser.py: imports or references `resolve_node`

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
            #arch-eval:locational_stability=4

        """
        try:
            return self.ast_registry.resolve(object_id)
        except KeyError:
            return self.run.identifiable_registry.resolve(object_id)

    def linked_ast_nodes_for(self, obj: object) -> Generator[Identifiable]:
        """
        Handle linked ast nodes for.

        Yields:
            Generated values.

        Responsibility:
            Handle linked ast nodes for. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.linked_ast_nodes_for` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - tuple: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - suppress: collaborator call used by this boundary
            - self.resolve_node: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `linked_ast_nodes_for`
            - src/pytest_bdd/model/run_access.py: imports or references `linked_ast_nodes_for`
            - src/pytest_bdd/model/scenario_report.py: imports or references `linked_ast_nodes_for`
            - src/pytest_bdd/model/scenario_run.py: imports or references `linked_ast_nodes_for`
            - src/pytest_bdd/parser.py: imports or references `linked_ast_nodes_for`

        State and side effects:
            mutates ast_node_ids, ast_node_id.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.linked_ast_nodes_for` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        """
        Locate and return all TableRow AST nodes linked to a given Pickle.

        Returns:
            A list of TableRow instances associated with the Pickle.

        Responsibility:
            Locate and return all TableRow AST nodes linked to a given Pickle. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.pickle_ast_table_rows` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.linked_ast_nodes_for: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `pickle_ast_table_rows`
            - src/pytest_bdd/model/run_access.py: imports or references `pickle_ast_table_rows`
            - src/pytest_bdd/model/scenario_report.py: imports or references `pickle_ast_table_rows`
            - src/pytest_bdd/model/scenario_run.py: imports or references `pickle_ast_table_rows`
            - src/pytest_bdd/parser.py: imports or references `pickle_ast_table_rows`

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
            #arch-eval:locational_stability=4

        """
        return [node for node in self.linked_ast_nodes_for(pickle) if isinstance(node, TableRow)]  # type: ignore[misc]  # mypy narrows via isinstance but the list comp loses it

    def pickle_table_rows_breadcrumb(self, pickle: Pickle) -> str:
        """
        Generate a human-readable breadcrumb string representing table row locations for a Pickle.

        Returns:
            A string containing line information for the table rows, or empty string if none.

        Responsibility:
            Generate a human-readable breadcrumb string representing table row locations for a Pickle. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.pickle_table_rows_breadcrumb` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - deepattrgetter: collaborator call used by this boundary
            - join: collaborator call used by this boundary
            - self.pickle_ast_table_rows: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `pickle_table_rows_breadcrumb`
            - src/pytest_bdd/model/run_access.py: imports or references `pickle_table_rows_breadcrumb`
            - src/pytest_bdd/model/scenario_report.py: imports or references `pickle_table_rows_breadcrumb`
            - src/pytest_bdd/model/scenario_run.py: imports or references `pickle_table_rows_breadcrumb`
            - src/pytest_bdd/parser.py: imports or references `pickle_table_rows_breadcrumb`

        State and side effects:
            mutates table_rows_lines.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.pickle_table_rows_breadcrumb` keeps its documented
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
            #arch-eval:locational_stability=4

        """
        table_rows_lines = ",".join(
            (
                f"line: {deepattrgetter('location.line', default=-1)(row)[0]}"
                for row in self.pickle_ast_table_rows(pickle)
            ),
        )
        return f"[table_rows:[{table_rows_lines}]]" if table_rows_lines else ""

    def get_source_identity(self, pickle: Pickle) -> dict[str, object]:
        """
        Get stable source identity for a pickle.

        Returns:
            A dictionary containing uri, scenarioAstNodeId, and optional rowAstNodeId / rowBreadcrumb.

        Responsibility:
            Get stable source identity for a pickle. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.get_source_identity` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - self.pickle_ast_scenario: collaborator call used by this boundary
            - self.pickle_ast_table_rows: collaborator call used by this boundary
            - len: collaborator call used by this boundary
            - self.pickle_table_rows_breadcrumb: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `get_source_identity`
            - src/pytest_bdd/model/run_access.py: imports or references `get_source_identity`
            - src/pytest_bdd/model/scenario_report.py: imports or references `get_source_identity`
            - src/pytest_bdd/model/scenario_run.py: imports or references `get_source_identity`
            - src/pytest_bdd/parser.py: imports or references `get_source_identity`

        State and side effects:
            mutates scenario_ast_id, row_ast_id, ast_node_ids, scenario, table_rows.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.get_source_identity` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        ast_node_ids = [str(ast_node_id) for ast_node_id in (getattr(pickle, "ast_node_ids", None) or ())]
        scenario_ast_id = None
        row_ast_id = None

        scenario = self.pickle_ast_scenario(pickle)
        if scenario is not None:
            scenario_ast_id = scenario.id
        elif ast_node_ids:
            scenario_ast_id = ast_node_ids[0]

        table_rows = self.pickle_ast_table_rows(pickle)
        if table_rows:
            row_ast_id = table_rows[0].id
        elif len(ast_node_ids) > 1:
            row_ast_id = ast_node_ids[1]

        source_identity = {
            "uri": self.uri,
            "scenarioAstNodeId": scenario_ast_id,
        }
        if row_ast_id is not None:
            source_identity["rowAstNodeId"] = row_ast_id
            breadcrumb = self.pickle_table_rows_breadcrumb(pickle)
            if breadcrumb:
                source_identity["rowBreadcrumb"] = breadcrumb
        return source_identity  # type: ignore[return-value]  # scenariodAstNodeId allows None, dict value type is str|None

    def pickle_ast_scenario(self, pickle: Pickle) -> Scenario | None:
        """
        Locate the original Scenario AST node corresponding to a compiled Pickle.

        Returns:
            The associated Scenario instance, or None if it cannot be found.

        Responsibility:
            Locate the original Scenario AST node corresponding to a compiled Pickle. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.pickle_ast_scenario` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - next: collaborator call used by this boundary
            - self.linked_ast_nodes_for: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `pickle_ast_scenario`
            - src/pytest_bdd/model/run_access.py: imports or references `pickle_ast_scenario`
            - src/pytest_bdd/model/scenario_report.py: imports or references `pickle_ast_scenario`
            - src/pytest_bdd/model/scenario_run.py: imports or references `pickle_ast_scenario`
            - src/pytest_bdd/parser.py: imports or references `pickle_ast_scenario`

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
            #arch-eval:locational_stability=4

        """
        return next(  # type: ignore[return-value]  # mypy loses isinstance narrowing in generator
            (node for node in self.linked_ast_nodes_for(pickle) if isinstance(node, Scenario)),
            None,
        )

    def pickle_line_number(self, pickle: Pickle) -> int:
        """
        Determine the starting line number in the source file for a given Pickle.

        Returns:
            The integer line number, or -1 if the location cannot be resolved.

        Responsibility:
            Determine the starting line number in the source file for a given Pickle. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.pickle_line_number` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.pickle_ast_scenario: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - int: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `pickle_line_number`
            - src/pytest_bdd/model/run_access.py: imports or references `pickle_line_number`
            - src/pytest_bdd/model/scenario_report.py: imports or references `pickle_line_number`
            - src/pytest_bdd/model/scenario_run.py: imports or references `pickle_line_number`
            - src/pytest_bdd/parser.py: imports or references `pickle_line_number`

        State and side effects:
            mutates scenario, location, line.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.pickle_line_number` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        scenario = self.pickle_ast_scenario(pickle)
        if scenario is None:
            return -1
        location = scenario.location
        line = getattr(location, "line", None)
        return int(line) if line is not None else -1

    def pickle_step_ast_step(self, pickle_step: PickleStep) -> Step | None:
        """
        Find the original Step AST node corresponding to a compiled PickleStep.

        Returns:
            The Step instance, or None if it cannot be found.

        Responsibility:
            Find the original Step AST node corresponding to a compiled PickleStep. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.pickle_step_ast_step` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - next: collaborator call used by this boundary
            - self.linked_ast_nodes_for: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `pickle_step_ast_step`
            - src/pytest_bdd/model/run_access.py: imports or references `pickle_step_ast_step`
            - src/pytest_bdd/model/scenario_report.py: imports or references `pickle_step_ast_step`
            - src/pytest_bdd/model/scenario_run.py: imports or references `pickle_step_ast_step`
            - src/pytest_bdd/parser.py: imports or references `pickle_step_ast_step`

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
            #arch-eval:locational_stability=4

        """
        return next(
            (node for node in self.linked_ast_nodes_for(pickle_step) if isinstance(node, Step)),
            None,
        )

    def step_keyword(self, step: PickleStep) -> str | None:
        """
        Extract the specific Gherkin keyword (e.g., 'Given', 'When') used for a PickleStep.

        Returns:
            The stripped keyword string, or None if unavailable.

        Responsibility:
            Extract the specific Gherkin keyword (e.g., 'Given', 'When') used for a PickleStep. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.step_keyword` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.pickle_step_ast_step: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - keyword.strip: collaborator call used by this boundary
            - Nothing.value_or: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `step_keyword`
            - src/pytest_bdd/model/run_access.py: imports or references `step_keyword`
            - src/pytest_bdd/model/scenario_report.py: imports or references `step_keyword`
            - src/pytest_bdd/model/scenario_run.py: imports or references `step_keyword`
            - src/pytest_bdd/parser.py: imports or references `step_keyword`

        State and side effects:
            mutates model_step, keyword.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.step_keyword` keeps its documented import path,
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
        model_step = self.pickle_step_ast_step(step)
        if model_step is not None:
            keyword = getattr(model_step, "keyword", None)
            if isinstance(keyword, str):
                return keyword.strip()
        return Nothing.value_or(None)

    def step_prefix(self, step: PickleStep) -> str | None:
        """
        Determine the lowercase prefix (keyword equivalent) for a PickleStep.

        Returns:
            The lowercase keyword string, or None if unavailable.

        Responsibility:
            Determine the lowercase prefix (keyword equivalent) for a PickleStep. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.step_prefix` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - self.step_keyword: collaborator call used by this boundary
            - keyword.lower: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `step_prefix`
            - src/pytest_bdd/model/run_access.py: imports or references `step_prefix`
            - src/pytest_bdd/model/scenario_report.py: imports or references `step_prefix`
            - src/pytest_bdd/model/scenario_run.py: imports or references `step_prefix`
            - src/pytest_bdd/parser.py: imports or references `step_prefix`

        State and side effects:
            mutates keyword.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.step_prefix` keeps its documented import path,
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
        keyword = self.step_keyword(step)
        return keyword.lower() if keyword is not None else None

    def step_line_number(self, step: PickleStep) -> int | None:
        """
        Identify the source line number where a PickleStep is defined.

        Returns:
            The integer line number, or -1/None if the location cannot be resolved.

        Responsibility:
            Identify the source line number where a PickleStep is defined. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.step_line_number` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.pickle_step_ast_step: collaborator call used by this boundary
            - Nothing.value_or: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `step_line_number`
            - src/pytest_bdd/model/run_access.py: imports or references `step_line_number`
            - src/pytest_bdd/model/scenario_report.py: imports or references `step_line_number`
            - src/pytest_bdd/model/scenario_run.py: imports or references `step_line_number`
            - src/pytest_bdd/parser.py: imports or references `step_line_number`

        State and side effects:
            mutates model_step.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.step_line_number` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        model_step = self.pickle_step_ast_step(step)
        if model_step is not None:
            return model_step.location.line if model_step.location is not None else -1
        return Nothing.value_or(None)

    def step_doc_string(self, step: PickleStep) -> object | None:
        """
        Retrieve the DocString payload attached to a PickleStep, if any.

        Returns:
            The doc string object, or None if not present.

        Responsibility:
            Retrieve the DocString payload attached to a PickleStep, if any. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.step_doc_string` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - self.pickle_step_ast_step: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `step_doc_string`
            - src/pytest_bdd/model/run_access.py: imports or references `step_doc_string`
            - src/pytest_bdd/model/scenario_report.py: imports or references `step_doc_string`
            - src/pytest_bdd/model/scenario_run.py: imports or references `step_doc_string`
            - src/pytest_bdd/parser.py: imports or references `step_doc_string`

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
            #arch-eval:locational_stability=4

        """
        return getattr(self.pickle_step_ast_step(step), "doc_string", None)

    def step_data_table(self, step: PickleStep) -> object | None:
        """
        Retrieve the DataTable payload attached to a PickleStep, if any.

        Returns:
            The data table object, or None if not present.

        Responsibility:
            Retrieve the DataTable payload attached to a PickleStep, if any. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.step_data_table` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - self.pickle_step_ast_step: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `step_data_table`
            - src/pytest_bdd/model/run_access.py: imports or references `step_data_table`
            - src/pytest_bdd/model/scenario_report.py: imports or references `step_data_table`
            - src/pytest_bdd/model/scenario_run.py: imports or references `step_data_table`
            - src/pytest_bdd/parser.py: imports or references `step_data_table`

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
            #arch-eval:locational_stability=4

        """
        return getattr(self.pickle_step_ast_step(step), "data_table", None)

    @property
    def rel_filename(self) -> str | None:
        """
        Extract a relative filename path from the binding's URI if it uses a 'file:' scheme.

        Returns:
            The relative path string, or None if the URI is not file-based.

        Responsibility:
            Extract a relative filename path from the binding's URI if it uses a 'file:' scheme. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.rel_filename` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - self.uri.startswith: collaborator call used by this boundary
            - len: collaborator call used by this boundary
            - Nothing.value_or: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `rel_filename`
            - src/pytest_bdd/model/run_access.py: imports or references `rel_filename`
            - src/pytest_bdd/model/scenario_report.py: imports or references `rel_filename`
            - src/pytest_bdd/model/scenario_run.py: imports or references `rel_filename`
            - src/pytest_bdd/parser.py: imports or references `rel_filename`

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
            #arch-eval:locational_stability=4

        """
        if self.uri.startswith("file:"):
            return self.uri[len("file:") :]
        return Nothing.value_or(None)

    @property
    def name(self) -> str | None:
        """
        Retrieve the human-readable name of the bound Feature.

        Returns:
            The feature name string, or None if unavailable.

        Responsibility:
            Retrieve the human-readable name of the bound Feature. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.name`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/__init__.py: imports or references `name`
            - src/pytest_bdd/_pylint/checkers/file_size_rules.py: imports or references `name`
            - src/pytest_bdd/_pylint/checkers/init_rules.py: imports or references `name`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `name`
            - src/pytest_bdd/_pylint/checkers/noqa_rules.py: imports or references `name`

        State and side effects:
            mutates feature_message.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.name` keeps its documented import path, ownership
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
        feature_message = getattr(self.gherkin_document, "feature", None)
        return str(feature_message.name) if feature_message is not None else None

    @property
    def line_number(self) -> int | None:
        """
        Retrieve the starting line number of the bound Feature declaration.

        Returns:
            The integer line number, or None if unavailable.

        Responsibility:
            Retrieve the starting line number of the bound Feature declaration. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.line_number` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - int: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `line_number`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `line_number`
            - src/pytest_bdd/model/run_access.py: imports or references `line_number`
            - src/pytest_bdd/model/scenario_report.py: imports or references `line_number`
            - src/pytest_bdd/model/scenario_run.py: imports or references `line_number`

        State and side effects:
            mutates feature_message, location, line.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.line_number` keeps its documented import path,
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
        feature_message = getattr(self.gherkin_document, "feature", None)
        location = getattr(feature_message, "location", None)
        line = getattr(location, "line", None)
        return int(line) if line is not None else None

    @property
    def description(self) -> str | None:
        """
        Retrieve and dedent the descriptive text block associated with the Feature.

        Returns:
            The dedented description string, or None if no description exists.

        Responsibility:
            Retrieve and dedent the descriptive text block associated with the Feature. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.description` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - Nothing.value_or: collaborator call used by this boundary
            - dedent: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_build.py: imports or references `description`
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `description`
            - src/pytest_bdd/model/message_baseline_diff.py: imports or references `description`
            - src/pytest_bdd/model/message_capability.py: imports or references `description`
            - src/pytest_bdd/model/message_capability_inventory.py: imports or references `description`

        State and side effects:
            mutates feature_message, description.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.description` keeps its documented import path,
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
        feature_message = getattr(self.gherkin_document, "feature", None)
        description = getattr(feature_message, "description", None)
        if description is None:
            return Nothing.value_or(None)
        return dedent(str(description))

    @property
    def tag_names(self) -> list[str]:
        """
        Extract a sorted list of tag names applied to the Feature, stripping any defined tag prefix.

        Returns:
            A list of normalized tag name strings.

        Responsibility:
            Extract a sorted list of tag names applied to the Feature, stripping any defined tag prefix. It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.tag_names`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - sorted: collaborator call used by this boundary
            - str.lstrip: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `tag_names`
            - src/pytest_bdd/model/run_access.py: imports or references `tag_names`
            - src/pytest_bdd/model/scenario_report.py: imports or references `tag_names`
            - src/pytest_bdd/model/scenario_run.py: imports or references `tag_names`
            - src/pytest_bdd/parser.py: imports or references `tag_names`

        State and side effects:
            mutates feature_message, tags.

        Invariants:
            - `pytest_bdd.model.feature_binding.FeatureRuntimeBinding.tag_names` keeps its documented import path,
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
        feature_message = getattr(self.gherkin_document, "feature", None)
        tags = getattr(feature_message, "tags", None) or ()
        return sorted(str(tag.name).lstrip(TAG_PREFIX) for tag in tags)
