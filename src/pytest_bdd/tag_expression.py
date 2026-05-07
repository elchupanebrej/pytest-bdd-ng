from operator import attrgetter
from typing import Protocol, runtime_checkable

from attrs import define, field
from cucumber_tag_expressions import TagExpressionError, TagExpressionParser
from typing_extensions import Self

from pytest_bdd.compatibility.pytest import PYTEST83, Expression, Mark, MarkMatcher, ParseError


@runtime_checkable
class TagExpression(Protocol):
    @classmethod
    def parse(cls, expression: str) -> Self:
        raise NotImplementedError  # pragma: no cover

    def evaluate(self, marks: list[Mark]) -> bool:
        raise NotImplementedError  # pragma: no cover


@define
class _ModernTagExpression(TagExpression):
    expression: Expression | None = field()

    @classmethod
    def parse(cls, expression: str) -> Self:
        try:
            return cls(expression=Expression.compile(expression) if expression else None)
        except ParseError as e:
            msg = f"Unable parse mark expression: {expression}: {e}"
            raise ValueError(msg) from e


@define
class _EnhancedMarksTagExpression(_ModernTagExpression):
    """Used for 8.3<=pytest"""

    def evaluate(self, marks: list[Mark]) -> bool:
        return self.expression.evaluate(MarkMatcher.from_markers(marks)) if self.expression is not None else True


@define
class _MarksTagExpression(_ModernTagExpression):
    """Used for 6.0<=pytest<8.3"""

    def evaluate(self, marks: list[Mark]) -> bool:
        return (
            self.expression.evaluate(MarkMatcher({mark.name: [mark] for mark in marks}))
            if self.expression is not None
            else True
        )


MarksTagExpression: type[_EnhancedMarksTagExpression | _MarksTagExpression]
MarksTagExpression = _EnhancedMarksTagExpression if PYTEST83 else _MarksTagExpression


@define
class GherkinTagExpression(TagExpression):
    expression: TagExpressionParser = field()

    @classmethod
    def parse(cls, expression: str) -> Self:
        try:
            return cls(expression=TagExpressionParser.parse(expression))
        except TagExpressionError as e:
            msg = f"Unable parse tag expression: {expression}: {e}"
            raise ValueError(msg) from e

    def evaluate(self, marks: list[Mark]) -> bool:
        return bool(self.expression.evaluate(map(attrgetter("name"), marks)))


TagExpressionType = _EnhancedMarksTagExpression | _MarksTagExpression | GherkinTagExpression
