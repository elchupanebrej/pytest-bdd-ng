from __future__ import annotations

from itertools import chain
from typing import Any

from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    Background,
    Examples,
    Rule,
    Scenario,
    Step,
    TableRow,
    Tag,
)
from cucumber_messages import Feature as FeatureMessage  # type:ignore[attr-defined, import-untyped]


def iter_child_ids(obj: Any):
    if isinstance(obj, FeatureMessage):
        yield from chain.from_iterable(
            map(
                iter_child_ids,
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
                iter_child_ids,
                chain(
                    obj.tags,
                    chain.from_iterable(
                        (
                            filter(
                                None,
                                [
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
        yield from chain.from_iterable(map(iter_child_ids, obj.steps))
    elif isinstance(obj, Scenario):
        yield obj.id, obj
        yield from chain.from_iterable(
            map(
                iter_child_ids,
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
                iter_child_ids,
                chain(obj.tags, [obj.table_header], obj.table_body),
            ),
        )
    elif isinstance(obj, (TableRow, Step)):
        yield obj.id, obj


def build_registry(feature_message: FeatureMessage) -> dict[str, Any]:
    return dict(iter_child_ids(feature_message))
