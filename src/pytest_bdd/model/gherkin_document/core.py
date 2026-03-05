"""Feature.

The way of describing the behavior is based on Gherkin language.
"""

from __future__ import annotations

from functools import partial
from textwrap import dedent
from typing import TYPE_CHECKING, Any, cast

from attr import Factory, attrib, attrs
from cucumber_messages import GherkinDocument, Pickle  # type:ignore[attr-defined, import-untyped]
from gherkin.pickles.compiler import Compiler as PicklesCompiler

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

    pickles: Sequence[Pickle] = attrib(default=Factory(list))

    @staticmethod
    def load_pickles(pickles_data) -> Sequence[Pickle]:
        return [*map(partial(flip(message_converter.from_dict), Pickle), pickles_data)]  # type: ignore[attr-defined]

    def materialize_pickles(self, *, id_generator: Any) -> Sequence[Pickle]:
        if self.pickles:
            return self.pickles

        gherkin_document_payload = message_converter.to_dict(self.gherkin_document)
        pickles_data = PicklesCompiler(id_generator=id_generator).compile(gherkin_document_payload)
        self.pickles = self.load_pickles(pickles_data)
        return self.pickles

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

    def build_pickle_table_rows_breadcrumb(self, pickle, *, config: Any | None = None):
        return build_pickle_table_rows_breadcrumb(_resolve_registry_for_feature(self, config=config), pickle)

    @staticmethod
    def get_pickle_tag_names(pickle: Pickle):
        return sorted(tag.name.lstrip(TAG_PREFIX) for tag in pickle.tags)  # type: ignore[no-any-return]

    def _get_pickle_line_number(self, pickle: Pickle, *, config: Any | None = None):
        return get_pickle_line_number(_resolve_registry_for_feature(self, config=config), pickle)

    def _get_step_keyword(self, step, *, config: Any | None = None):
        return get_step_keyword(_resolve_registry_for_feature(self, config=config), step)

    def _get_step_prefix(self, step, *, config: Any | None = None):
        return get_step_prefix(_resolve_registry_for_feature(self, config=config), step)

    def _get_step_line_number(self, step, *, config: Any | None = None):
        return get_step_line_number(_resolve_registry_for_feature(self, config=config), step)

    def _get_step_doc_string(self, step, *, config: Any | None = None):
        return get_step_doc_string(_resolve_registry_for_feature(self, config=config), step)

    def _get_step_data_table(self, step, *, config: Any | None = None):
        return get_step_data_table(_resolve_registry_for_feature(self, config=config), step)

    def _get_scenario_description(self, scenario: Any, *, config: Any | None = None) -> str | None:
        ast_node_ids = getattr(scenario, "ast_node_ids", None) or ()
        if not ast_node_ids:
            return None
        scenario_node = _resolve_registry_for_feature(self, config=config).get(str(ast_node_ids[0]))
        if scenario_node is None:
            return None
        description = getattr(scenario_node, "description", None)
        return str(description) if description is not None else None


def _resolve_registry_for_feature(feature: Feature, *, config: Any | None = None) -> dict[str, Any]:
    fallback_registry: dict[str, Any] = {}
    feature_message = getattr(getattr(feature, "gherkin_document", None), "feature", None)
    if feature_message is not None:
        fallback_registry = build_registry(feature_message)

    if config is not None:
        from pytest_bdd.plugin.scenario_runner.context_store import ExecutionContextStore

        envelope_registry = ExecutionContextStore.get_envelope_registry_from_config(config)
        if envelope_registry is not None:
            combined_registry = dict(fallback_registry)
            combined_registry.update(envelope_registry.identifiable.objects_by_id)
            return combined_registry

    return fallback_registry
