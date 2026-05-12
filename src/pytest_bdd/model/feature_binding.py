"""Provide feature runtime binding helpers."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, cast

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
from returns.maybe import Nothing

from pytest_bdd.const import TAG_PREFIX
from pytest_bdd.model.message_converter import message_converter
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

    """

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
        """
        Parse or pass through a Gherkin document object from raw input.

        Returns:
            The loaded GherkinDocument instance.

        """
        if isinstance(raw_gherkin_document, GherkinDocument):
            return raw_gherkin_document
        return message_converter.from_dict(raw_gherkin_document, GherkinDocument)

    @staticmethod
    def load_pickles(pickles_data: Iterable[object]) -> tuple[Pickle, ...]:
        """
        Convert a collection of raw pickle data representations into a tuple of Pickle instances.

        Returns:
            A tuple of loaded Pickle objects.

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
        """Index the Gherkin document and its associated pickles into the run's identifiable registry."""
        feature_message = getattr(self.gherkin_document, "feature", None)
        if feature_message is not None:
            self.run.index_identifiable_tree(feature_message)
        if self.pickles:
            self.run.index_identifiable_tree(self.pickles)

    def resolve_node(self, object_id: str) -> Identifiable:
        """
        Look up a generic identifiable object by its ID within the current run registry.

        Returns:
            The resolved Identifiable object instance.

        """
        return self.run.identifiable_registry.resolve(object_id)

    def linked_ast_nodes_for(self, obj: object) -> Generator[Identifiable]:
        """
        Handle linked ast nodes for.

        Yields:
            Generated values.

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

        """
        return [node for node in self.linked_ast_nodes_for(pickle) if isinstance(node, TableRow)]

    def pickle_table_rows_breadcrumb(self, pickle: Pickle) -> str:
        """
        Generate a human-readable breadcrumb string representing table row locations for a Pickle.

        Returns:
            A string containing line information for the table rows, or empty string if none.

        """
        table_rows_lines = ",".join(
            (
                f"line: {deepattrgetter('location.line', default=-1)(row)[0]}"
                for row in self.pickle_ast_table_rows(pickle)
            ),
        )
        return f"[table_rows:[{table_rows_lines}]]" if table_rows_lines else ""

    def pickle_ast_scenario(self, pickle: Pickle) -> Scenario | None:
        """
        Locate the original Scenario AST node corresponding to a compiled Pickle.

        Returns:
            The associated Scenario instance, or None if it cannot be found.

        """
        return next(
            (node for node in self.linked_ast_nodes_for(pickle) if isinstance(node, Scenario)),
            None,
        )

    def pickle_line_number(self, pickle: Pickle) -> int:
        """
        Determine the starting line number in the source file for a given Pickle.

        Returns:
            The integer line number, or -1 if the location cannot be resolved.

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

        """
        keyword = self.step_keyword(step)
        return keyword.lower() if keyword is not None else None

    def step_line_number(self, step: PickleStep) -> int | None:
        """
        Identify the source line number where a PickleStep is defined.

        Returns:
            The integer line number, or -1/None if the location cannot be resolved.

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

        """
        return getattr(self.pickle_step_ast_step(step), "doc_string", None)

    def step_data_table(self, step: PickleStep) -> object | None:
        """
        Retrieve the DataTable payload attached to a PickleStep, if any.

        Returns:
            The data table object, or None if not present.

        """
        return getattr(self.pickle_step_ast_step(step), "data_table", None)

    @property
    def rel_filename(self) -> str | None:
        """
        Extract a relative filename path from the binding's URI if it uses a 'file:' scheme.

        Returns:
            The relative path string, or None if the URI is not file-based.

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

        """
        feature_message = getattr(self.gherkin_document, "feature", None)
        return str(feature_message.name) if feature_message is not None else None

    @property
    def line_number(self) -> int | None:
        """
        Retrieve the starting line number of the bound Feature declaration.

        Returns:
            The integer line number, or None if unavailable.

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

        """
        feature_message = getattr(self.gherkin_document, "feature", None)
        tags = getattr(feature_message, "tags", None) or ()
        return sorted(str(tag.name).lstrip(TAG_PREFIX) for tag in tags)
