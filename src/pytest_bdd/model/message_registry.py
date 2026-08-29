from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

    import messages


def iter_object_graph(root: Any) -> Iterator[Any]:
    stack, seen = [root], set()
    while stack:
        cur = stack.pop()
        if id(cur) in seen:
            continue
        seen.add(id(cur))
        yield cur
        if cur is None or isinstance(cur, str | bytes | int | float | bool):
            continue
        if isinstance(cur, dict):
            stack.extend(cur.values())
        elif isinstance(cur, list | tuple | set):
            stack.extend(cur)
        else:
            stack.extend(getattr(cur, "__dict__", {}).values())


class EnvelopeRegistry:
    def __init__(self) -> None:
        self.envelopes: list[messages.Envelope] = []
        self.objects_by_id: dict[str, Any] = {}

    def add_envelope(self, envelope: messages.Envelope) -> None:
        self.envelopes.append(envelope)
        for node in iter_object_graph(envelope):
            node_id = getattr(node, "id", None)
            if isinstance(node_id, str) and node_id:
                self.objects_by_id[node_id] = node

    def resolve(self, object_id: str) -> Any | None:
        return self.objects_by_id.get(object_id)


__all__ = ["EnvelopeRegistry", "iter_object_graph"]
