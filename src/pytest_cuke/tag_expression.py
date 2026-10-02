from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from attrs import frozen
from cucumber_tag_expressions import TagExpressionError, TagExpressionParser

if TYPE_CHECKING:
    from collections.abc import Iterable


@runtime_checkable
class TagExpressionProtocol(Protocol):
    def evaluate(self, tags: Iterable[str | Any]) -> bool: ...


@frozen
class TagExpression:
    expression_str: str
    compiled: Any = None

    @classmethod
    def parse(cls, expression: str) -> TagExpression:
        cleaned = expression.strip()
        if not cleaned:
            return cls(expression_str="", compiled=None)
        try:
            compiled = TagExpressionParser.parse(cleaned)
            return cls(expression_str=cleaned, compiled=compiled)
        except TagExpressionError as e:
            raise ValueError(f"Unable to parse tag expression: {expression}: {e}") from e

    def evaluate(self, tags: Iterable[str | Any]) -> bool:
        if self.compiled is None:
            return True
        norm: set[str] = set()
        for t in tags:
            name = getattr(t, "name", str(t))
            clean = name.lstrip("@")
            norm.add(name)
            norm.add(clean)
            norm.add(f"@{clean}")
        return bool(self.compiled.evaluate(list(norm)))


def parse_tag_expression(expression: str) -> TagExpression:
    return TagExpression.parse(expression)


# Compatibility aliases
GherkinTagExpression = TagExpression
MarksTagExpression = TagExpression

__all__ = [
    "GherkinTagExpression",
    "MarksTagExpression",
    "TagExpression",
    "TagExpressionProtocol",
    "parse_tag_expression",
]
