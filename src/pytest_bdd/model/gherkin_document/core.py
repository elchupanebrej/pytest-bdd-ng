"""Feature.

The way of describing the behavior is based on Gherkin language.
"""

from __future__ import annotations

from functools import partial
from textwrap import dedent
from typing import TYPE_CHECKING, cast

from attr import Factory, attrib, attrs
from cucumber_messages import GherkinDocument, Pickle  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.const import TAG_PREFIX
from pytest_bdd.model.message_converter import message_converter
from pytest_bdd.util.toolz_extra import flip

from .lookup import (
    build_pickle_table_rows_breadcrumb,
    get_pickle_line_number,
    get_step_data_table,
    get_step_doc_string,
    get_step_keyword,
    get_step_line_number,
    get_step_prefix,
)
from .registry import build_registry

if TYPE_CHECKING:
    from collections.abc import Sequence


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
        return [*map(partial(flip(message_converter.from_dict), Pickle), scenarios_data)]  # type: ignore[attr-defined]

    def fill_registry(self):
        if self.gherkin_document.feature is not None:
            self.registry.update(build_registry(self.gherkin_document.feature))

    @staticmethod
    def load_gherkin_document(raw_gherkin_document):
        return message_converter.from_dict(raw_gherkin_document, GherkinDocument)

    @property
    def name(self) -> str | None:
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
        return build_pickle_table_rows_breadcrumb(self.registry, pickle)

    def _get_pickle_tag_names(self, pickle: Pickle):
        return sorted(tag.name.lstrip(TAG_PREFIX) for tag in pickle.tags)  # type: ignore[no-any-return]

    def _get_pickle_line_number(self, pickle: Pickle):
        return get_pickle_line_number(self.registry, pickle)

    def _get_step_keyword(self, step):
        return get_step_keyword(self.registry, step)

    def _get_step_prefix(self, step):
        return get_step_prefix(self.registry, step)

    def _get_step_line_number(self, step):
        return get_step_line_number(self.registry, step)

    def _get_step_doc_string(self, step):
        return get_step_doc_string(self.registry, step)

    def _get_step_data_table(self, step):
        return get_step_data_table(self.registry, step)
