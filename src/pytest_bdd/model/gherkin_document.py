"""Feature.

The way of describing the behavior is based on Gherkin language

Syntax example:

    Feature: Articles
        Scenario: Publishing the article
            Given I'm an author user
            And I have an article
            When I go to the article page
            And I press the publish button
            Then I should not see the error message

            # Note: will query the database
            And the article should be published

:note: The "#" symbol is used for comments.
:note: There are no multiline steps, the description of the step must fit in
one line.
"""

from collections.abc import Sequence
from itertools import chain
from textwrap import dedent
from typing import cast

from attr import Factory, attrib, attrs

from messages import (  # type:ignore[attr-defined, import-untyped]  # type:ignore[attr-defined, import-untyped]
    Background,
    Examples,
    GherkinDocument,
    Pickle,
    Rule,
    Scenario,
    Step,
    TableRow,
    Tag,
)
from messages import Feature as FeatureMessage  # type:ignore[attr-defined]
from pytest_bdd.const import TAG_PREFIX
from pytest_bdd.utils import _itemgetter, deepattrgetter


@attrs
class Feature:
    gherkin_document: GherkinDocument = attrib()
    uri = attrib()
    filename: str = attrib()

    registry: dict = attrib(default=Factory(dict))
    pickles: Sequence[Pickle] = attrib(default=Factory(list))

    def __attrs_post_init__(self):
        self.fill_registry()

    @staticmethod
    def load_pickles(scenarios_data) -> Sequence[Pickle]:
        return [*map(Pickle.model_validate, scenarios_data)]  # type: ignore[attr-defined] # migration to pydantic2

    def fill_registry(self):
        self.registry.update(self.get_child_ids_gen(self.gherkin_document.feature))

    @classmethod
    def get_child_ids_gen(cls, obj):
        if isinstance(obj, FeatureMessage):
            yield from chain.from_iterable(
                map(
                    cls.get_child_ids_gen,
                    chain(
                        obj.tags,
                        chain.from_iterable(
                            filter(None, [child.rule, child.background, child.scenario]) for child in obj.children
                        ),
                    ),
                )
            )
        elif isinstance(obj, Tag):
            yield obj.id, obj
        elif isinstance(obj, Rule):
            yield obj.id, obj
            yield from chain.from_iterable(
                map(
                    cls.get_child_ids_gen,
                    chain(
                        obj.tags,
                        chain.from_iterable(filter(None, [child.background, child.scenario]) for child in obj.children),
                    ),
                )
            )
        elif isinstance(obj, Background):
            yield obj.id, obj
            yield from chain.from_iterable(map(cls.get_child_ids_gen, obj.steps))
        elif isinstance(obj, Scenario):
            yield obj.id, obj
            yield from chain.from_iterable(
                map(
                    cls.get_child_ids_gen,
                    chain(
                        obj.tags,
                        obj.steps,
                        obj.examples,
                    ),
                )
            )
        elif isinstance(obj, Examples):
            yield obj.id, obj
            yield from chain.from_iterable(
                map(cls.get_child_ids_gen, chain(obj.tags, [obj.table_header], obj.table_body))
            )
        elif isinstance(obj, TableRow | Step):
            yield obj.id, obj

    load_gherkin_document = staticmethod(GherkinDocument.model_validate)  # type: ignore[attr-defined] # migration to pydantic2

    @property
    def name(self) -> str | None:
        if self.gherkin_document.feature is not None:
            return cast("str", self.gherkin_document.feature.name)
        return None

    @property
    def rel_filename(self):
        file_schema = "file"
        if self.uri.startswith(file_schema):
            return self.uri[len(file_schema) + 1 :]
        return None

    @property
    def line_number(self):
        return self.gherkin_document.feature.location.line

    @property
    def description(self):
        return dedent(self.gherkin_document.feature.description)

    @property
    def tag_names(self):
        return sorted(tag.name.lstrip(TAG_PREFIX) for tag in self.gherkin_document.feature.tags)

    def build_pickle_table_rows_breadcrumb(self, pickle):
        getter = deepattrgetter("location.line", default=-1)
        table_rows_lines = ",".join(f"line: {getter(row)[0]}" for row in self._get_pickle_ast_table_rows(pickle))
        return f"[table_rows:[{table_rows_lines}]]" if table_rows_lines else ""

    def _get_pickle_ast_table_rows(self, pickle):
        return [node for node in self._get_linked_ast_nodes(pickle) if type(node) is TableRow]

    def _get_linked_ast_nodes(self, obj):
        return _itemgetter(
            *((obj.ast_node_id,) if hasattr(obj, "ast_node_id") else ()),
            *getattr(obj, "ast_node_ids", ()),
        )(self.registry)
