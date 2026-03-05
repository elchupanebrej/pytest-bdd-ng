from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pytest_bdd.types.protocol import Identifiable

if TYPE_CHECKING:
    from pytest_bdd.model.message_extension import EventEnvelope


def _iter_object_graph(root: Any) -> Iterator[Any]:
    stack = [root]
    seen: set[int] = set()

    while stack:
        current = stack.pop()
        current_ref = id(current)
        if current_ref in seen:
            continue
        seen.add(current_ref)
        yield current

        if current is None or isinstance(current, (str, bytes, int, float, bool, complex)):
            continue

        if isinstance(current, Mapping):
            stack.extend(current.values())
            continue

        if isinstance(current, (list, tuple, set, frozenset)):
            stack.extend(current)
            continue

        annotations = getattr(type(current), "__annotations__", None)
        if isinstance(annotations, dict):
            for field_name in annotations:
                with suppress(AttributeError, TypeError):
                    value = getattr(current, field_name)
                    stack.append(value)
            continue

        values = getattr(current, "__dict__", None)
        if isinstance(values, dict):
            stack.extend(values.values())


def _resolve_identifiable_id(candidate: Any) -> str | None:
    if not isinstance(candidate, Identifiable):
        return None

    raw_identifier = getattr(candidate, "id", None)
    if raw_identifier is None:
        return None

    identifier = str(raw_identifier).strip()
    return identifier or None


@dataclass(slots=True)
class IdentifiableObjectRegistry:
    objects_by_id: dict[str, Identifiable] = field(default_factory=dict)

    def index_tree(self, root: Any) -> None:
        for candidate in _iter_object_graph(root):
            identifier = _resolve_identifiable_id(candidate)
            if identifier is None:
                continue
            self.objects_by_id[identifier] = candidate

    def resolve(self, object_id: str) -> Identifiable | None:
        return self.objects_by_id.get(str(object_id))


@dataclass(slots=True)
class EnvelopeRegistry:
    envelopes: list[EventEnvelope] = field(default_factory=list)
    identifiable: IdentifiableObjectRegistry = field(default_factory=IdentifiableObjectRegistry)

    def add_envelope(self, envelope: EventEnvelope) -> None:
        self.envelopes.append(envelope)
        self.identifiable.index_tree(envelope)

    def resolve(self, object_id: str) -> Any | None:
        return self.identifiable.resolve(object_id)
