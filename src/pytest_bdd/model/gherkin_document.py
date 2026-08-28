"""Feature legacy shim."""

from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, cast

from attr import Factory, attrib, attrs

from messages import (
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
from messages import Feature as FeatureMessage

if TYPE_CHECKING:
    from collections.abc import Sequence


@attrs
class Feature:
    gherkin_document: GherkinDocument | None = attrib(default=None)
    uri: str = attrib(default="")
    filename: str = attrib(default="")

    registry: dict = attrib(default=Factory(dict))
    pickles: Sequence[Pickle] = attrib(default=Factory(list))

    @classmethod
    def get_child_ids_gen(cls, obj):
        if isinstance(obj, FeatureMessage):
            yield from chain.from_iterable(
                cls.get_child_ids_gen(c)
                for c in chain(
                    obj.tags,
                    chain.from_iterable(
                        filter(None, [child.rule, child.background, child.scenario]) for child in obj.children
                    ),
                )
            )
        elif isinstance(obj, Tag):
            yield obj.id, obj
        elif isinstance(obj, Rule):
            yield obj.id, obj
            yield from chain.from_iterable(
                cls.get_child_ids_gen(c)
                for c in chain(
                    obj.tags,
                    chain.from_iterable(filter(None, [child.background, child.scenario]) for child in obj.children),
                )
            )
        elif isinstance(obj, Background):
            yield obj.id, obj
            yield from chain.from_iterable(map(cls.get_child_ids_gen, obj.steps))
        elif isinstance(obj, Scenario):
            yield obj.id, obj
            yield from chain.from_iterable(
                cls.get_child_ids_gen(c)
                for c in chain(
                    obj.tags,
                    obj.steps,
                    obj.examples,
                )
            )
        elif isinstance(obj, Examples):
            yield obj.id, obj
            yield from chain.from_iterable(
                cls.get_child_ids_gen(c) for c in chain(obj.tags, [obj.table_header], obj.table_body)
            )
        elif isinstance(obj, TableRow | Step):
            yield obj.id, obj

    @property
    def name(self) -> str | None:
        if self.gherkin_document and self.gherkin_document.feature is not None:
            return cast("str", self.gherkin_document.feature.name)
        return None

    @property
    def rel_filename(self):
        file_schema = "file"
        if self.uri.startswith(file_schema):
            return self.uri[len(file_schema) + 1 :]
        return None

    @property
    def description(self):
        if self.gherkin_document and self.gherkin_document.feature:
            return self.gherkin_document.feature.description
        return ""
