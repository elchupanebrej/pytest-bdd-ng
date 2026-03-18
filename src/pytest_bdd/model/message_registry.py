from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import suppress
from typing import TYPE_CHECKING, Any, ClassVar

from attrs import define, field

from pytest_bdd.model.stash_access import StashBound
from pytest_bdd.types.protocol import Identifiable

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Stash
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


@define(slots=True)
class IdentifiableObjectRegistry:
    objects_by_id: dict[str, Identifiable] = field(factory=dict)

    def index_tree(self, root: Any) -> None:
        for candidate in _iter_object_graph(root):
            identifier = _resolve_identifiable_id(candidate)
            if identifier is None:
                continue
            self.objects_by_id[identifier] = candidate

    def resolve(self, object_id: str) -> Identifiable:
        return self.objects_by_id[object_id]


@define(slots=True)
class EnvelopeRegistry(StashBound):
    STASH_KEY: ClassVar[str] = "_pytest_bdd_envelope_registry"

    envelopes: list[EventEnvelope] = field(factory=list)
    identifiable: IdentifiableObjectRegistry = field(factory=IdentifiableObjectRegistry)

    def add_envelope(self, envelope: EventEnvelope) -> None:
        self.envelopes.append(envelope)
        self.identifiable.index_tree(envelope)

    def resolve(self, object_id: str) -> Any | None:
        return self.identifiable.resolve(object_id)

    @classmethod
    def stash_missing_message(cls) -> str:
        return (
            "`EnvelopeRegistry` is unavailable in config.stash. "
            "Execution plugins must initialize envelope tracking before reporter emission."
        )

    @classmethod
    def register_envelope_in_pytest_stash(
        cls,
        stash: Stash,
        envelope: EventEnvelope,
    ) -> EnvelopeRegistry:
        registry = cls.from_stash(stash)
        registry.add_envelope(envelope)
        return registry
