from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast, runtime_checkable

from attrs import frozen
from cucumber_tag_expressions import TagExpressionError, TagExpressionParser

from pytest_cuke.compatibility.pytest import PYTEST83, Expression, Mark, MarkMatcher, ParseError, make_mark

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


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
            parse_expression = cast("Callable[[str], TagExpressionProtocol]", TagExpressionParser.parse)
            compiled = parse_expression(cleaned)
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


class GherkinTagExpression(TagExpression):
    """Match source tag names exactly, including their ``@`` prefix."""

    def evaluate(self, tags: Iterable[str | Any]) -> bool:
        if self.compiled is None:
            return True
        return bool(self.compiled.evaluate([getattr(tag, "name", str(tag)) for tag in tags]))


class MarksTagExpression(TagExpression):
    """Match pytest markers using the installed pytest expression grammar."""

    @classmethod
    def parse(cls, expression: str) -> MarksTagExpression:
        cleaned = expression.strip()
        try:
            compiled = Expression.compile(cleaned) if cleaned else None
        except ParseError as error:
            # Modern pytest raises SyntaxError; the compatibility fallback is
            # Exception, so only translate the older dedicated ParseError.
            if ParseError is Exception or not isinstance(error, ParseError):
                raise
            raise ValueError(f"Unable parse mark expression: {expression}: {error}") from error
        return cls(expression_str=cleaned, compiled=compiled)

    def evaluate(self, tags: Iterable[str | Any]) -> bool:
        if self.compiled is None:
            return True
        marks = [
            tag
            if isinstance(tag, Mark)
            else make_mark(
                getattr(tag, "name", str(tag)),
                args=getattr(tag, "args", ()),
                kwargs=getattr(tag, "kwargs", {}),
            )
            for tag in tags
        ]
        matcher = (
            MarkMatcher.from_markers(marks)
            if PYTEST83
            else MarkMatcher({getattr(mark, "name", str(mark)): [mark] for mark in marks})
        )
        return bool(self.compiled.evaluate(matcher))

__all__ = [
    "GherkinTagExpression",
    "MarksTagExpression",
    "TagExpression",
    "TagExpressionProtocol",
    "parse_tag_expression",
]
