"""Preserve parser source metadata without reparsing or replacing edited models."""

from __future__ import annotations

import json
from bisect import bisect_left
from typing import TYPE_CHECKING, Any

from attrs import frozen

from pytest_cuke.model import message_types as messages

if TYPE_CHECKING:
    from pytest_cuke.model.feature import Feature


def _structure(feature: Feature) -> tuple[object, ...]:
    return (
        feature.name,
        feature.line,
        feature.tags,
        feature.description,
        feature.background,
        feature.scenarios,
        feature.rules,
        feature.id,
        feature.keyword,
        feature.language,
    )


@frozen
class SourceProjection:
    document_json: str
    structure: tuple[object, ...]
    positions: tuple[tuple[str, int, int | None], ...]

    def matches(self, feature: Feature) -> bool:
        return self.structure == _structure(feature)

    def remap_lines(self, feature: Feature, source_lines: tuple[int | None, ...]) -> SourceProjection:
        """Retain source nodes and discard generated nodes with no source position."""

        def restore(value: Any) -> Any:
            if isinstance(value, dict):
                location = value.get("location")
                if isinstance(location, dict):
                    line = location.get("line")
                    if isinstance(line, int) and 1 <= line <= len(source_lines):
                        original_line = source_lines[line - 1]
                        if original_line is None:
                            return None
                        value = {**value, "location": {**location, "line": original_line}}
                return {key: restored for key, item in value.items() if (restored := restore(item)) is not None}
            if isinstance(value, list):
                return [restored for item in value if (restored := restore(item)) is not None]
            return value

        return capture_source_projection(restore(json.loads(self.document_json)), feature)

    def document(self, uri: str) -> messages.GherkinDocument:
        document = messages.message_from_dict(json.loads(self.document_json), messages.GherkinDocument)
        document.uri = uri
        return document

    def location(self, node_id: str) -> messages.Location | None:
        index = bisect_left(self.positions, node_id, key=lambda item: item[0])
        if index == len(self.positions) or self.positions[index][0] != node_id:
            return None
        _, line, column = self.positions[index]
        return messages.Location(line=line, column=column)


def capture_source_projection(raw: dict[str, Any], feature: Feature) -> SourceProjection:
    positions: dict[str, tuple[str, int, int | None]] = {}

    def visit(value: object) -> None:
        if isinstance(value, dict):
            node_id = value.get("id")
            location = value.get("location")
            if isinstance(node_id, str) and isinstance(location, dict):
                line, column = location.get("line"), location.get("column")
                if isinstance(line, int) and line > 0:
                    positions[node_id] = (node_id, line, column if isinstance(column, int) else None)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(raw)
    return SourceProjection(
        document_json=json.dumps(raw, ensure_ascii=False),
        structure=_structure(feature),
        positions=tuple(sorted(positions.values())),
    )
