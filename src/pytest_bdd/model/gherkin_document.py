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
from functools import partial
from itertools import chain
from textwrap import dedent
from typing import Union, cast

from attr import Factory, attrib, attrs
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]  # type:ignore[attr-defined, import-untyped]
    Background,
    Examples,
    GherkinDocument,
    Location,
    Pickle,
    PickleStep,
    Rule,
    Scenario,
    Step,
    TableRow,
    Tag,
)
from cucumber_messages import Feature as FeatureMessage  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.const import TAG_PREFIX
from pytest_bdd.model.message_converter import message_converter
from pytest_bdd.util.toolz_extra import deepattrgetter, flip, itemgetter_


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
        return [*map(partial(flip(message_converter.from_dict), Pickle), scenarios_data)]  # type: ignore[attr-defined] # migration to pydantic2

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
                            (filter(None, [child.rule, child.background, child.scenario]) for child in obj.children),
                        ),
                    ),
                ),
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
                        chain.from_iterable(
                            (
                                filter(
                                    None,
                                    [
                                        # TODO Check why we don't support nested Rules;
                                        # https://github.com/cucumber/gherkin/issues/126
                                        # child.rule,
                                        child.background,
                                        child.scenario,
                                    ],
                                )
                                for child in obj.children
                            ),
                        ),
                    ),
                ),
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
                ),
            )
        elif isinstance(obj, Examples):
            yield obj.id, obj
            yield from chain.from_iterable(
                map(
                    cls.get_child_ids_gen,
                    chain(obj.tags, [obj.table_header], obj.table_body),
                ),
            )
        elif isinstance(obj, (TableRow, Step)):
            yield obj.id, obj

    @staticmethod
    def load_gherkin_document(raw_gherkin_document):
        return message_converter.from_dict(raw_gherkin_document, GherkinDocument)

    @property
    def name(self) -> Union[str, None]:
        if self.gherkin_document.feature is not None:
            return cast(str, self.gherkin_document.feature.name)
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
        table_rows_lines = ",".join(
            (
                f"line: {deepattrgetter('location.line', default=-1)(row)[0]}"
                for row in self._get_pickle_ast_table_rows(pickle)
            ),
        )
        return f"[table_rows:[{table_rows_lines}]]" if table_rows_lines else ""

    def _get_pickle_ast_table_rows(self, pickle):
        return list(filter(lambda node: type(node) is TableRow, self._get_linked_ast_nodes(pickle)))

    def _get_linked_ast_nodes(self, obj):
        items = [
            *filter(
                lambda _: _ != "",
                ((obj.ast_node_id,) if hasattr(obj, "ast_node_id") else ()),
            ),
            *filter(lambda _: _ != "", getattr(obj, "ast_node_ids", ())),
        ]
        return itemgetter_(*items)(self.registry)

    def _get_pickle_tag_names(self, pickle: Pickle):
        return sorted(tag.name.lstrip(TAG_PREFIX) for tag in pickle.tags)  # type: ignore[no-any-return]

    def _get_pickle_ast_scenario(self, pickle: Pickle) -> Scenario:
        return cast(
            Scenario,
            next(
                filter(
                    lambda node: type(node) is Scenario,
                    self._get_linked_ast_nodes(pickle),
                )
            ),
        )

    def _get_pickle_line_number(self, pickle: Pickle):
        return (
            cast(Location, location).line
            if (location := self._get_pickle_ast_scenario(pickle).location) is not None
            else -1
        )

    def _get_pickle_step_model_step(self, pickle_step: PickleStep):
        return cast(
            Step,
            next(
                filter(
                    lambda node: type(node) is Step,
                    self._get_linked_ast_nodes(pickle_step),
                ),
                None,
            ),
        )

    def _get_step_keyword(self, step: PickleStep):
        model_step: Union[Step, None] = self._get_pickle_step_model_step(step)
        if model_step is not None:
            return model_step.keyword.strip()
        return None

    def _get_step_prefix(self, step: PickleStep):
        step_keyword = self._get_step_keyword(step)
        if step_keyword is not None:
            return step_keyword.lower()
        return None

    def _get_step_line_number(self, step: PickleStep):
        model_step: Union[Step, None] = self._get_pickle_step_model_step(step)
        if model_step is not None:
            return location.line if (location := model_step.location) is not None else -1
        return None

    def _get_step_doc_string(self, step: PickleStep):
        return getattr(self._get_pickle_step_model_step(step), "doc_string", None)

    def _get_step_data_table(self, step: PickleStep):
        return getattr(self._get_pickle_step_model_step(step), "data_table", None)
