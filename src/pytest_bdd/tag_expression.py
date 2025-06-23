from itertools import cycle
from operator import attrgetter
from typing import Optional, Protocol, Union, runtime_checkable

from _pytest.mark import Mark
from attr import attrib, attrs
from cucumber_tag_expressions import TagExpressionError, TagExpressionParser
from typing_extensions import Self

from pytest_bdd.compatibility.pytest import PYTEST6, PYTEST83

if PYTEST6:
    from pytest_bdd.compatibility.pytest import Expression, MarkMatcher, ParseError


@runtime_checkable
class TagExpression(Protocol):
    @classmethod
    def parse(cls, expression: str) -> Self:
        raise NotImplementedError  # pragma: no cover

    def evaluate(self, marks: list[Mark]) -> bool:
        raise NotImplementedError  # pragma: no cover


@attrs
class _ModernTagExpression(TagExpression):
    expression: Optional["Expression"] = attrib()

    @classmethod
    def parse(cls, expression: str):
        try:
            return cls(expression=Expression.compile(expression) if expression else None)
        except ParseError as e:
            msg = f"Unable parse mark expression: {expression}: {e}"
            raise ValueError(msg) from e


@attrs
class _EnhancedMarksTagExpression(_ModernTagExpression):
    """Used for 8.3<=pytest"""

    def evaluate(self, marks):
        return self.expression.evaluate(MarkMatcher.from_markers(marks)) if self.expression is not None else True


@attrs
class _MarksTagExpression(_ModernTagExpression):
    """Used for 6.0<=pytest<8.3"""

    def evaluate(self, marks):
        return (
            self.expression.evaluate(MarkMatcher(map(attrgetter("name"), marks)))
            if self.expression is not None
            else True
        )


@attrs
class _FallbackMarksTagExpression(TagExpression):
    """Used for pytest<6.0"""

    expression: Optional[str] = attrib()

    @classmethod
    def parse(cls, expression: str):
        try:
            if expression:
                eval(expression, {})  # noqa:S307 intentional
        except SyntaxError as e:
            msg = f"Unable parse mark expression: {expression}: {e}"
            raise ValueError(msg) from e
        except NameError:
            pass
        return cls(expression=expression or None)

    def evaluate(self, marks):
        if self.expression is None:
            return True
        return eval(  # noqa:S307 intentional
            self.expression,
            {},
            dict(zip(map(attrgetter("name"), marks), cycle([True]))),
        )


MarksTagExpression: type[Union[_EnhancedMarksTagExpression, _MarksTagExpression, _FallbackMarksTagExpression]]
if PYTEST83:
    MarksTagExpression = _EnhancedMarksTagExpression
elif PYTEST6:
    MarksTagExpression = _MarksTagExpression
else:
    MarksTagExpression = _FallbackMarksTagExpression


@attrs
class GherkinTagExpression(TagExpression):
    expression: TagExpressionParser = attrib()

    @classmethod
    def parse(cls, expression):
        try:
            return cls(expression=TagExpressionParser.parse(expression))
        except TagExpressionError as e:
            msg = f"Unable parse tag expression: {expression}: {e}"
            raise ValueError(msg) from e

    def evaluate(self, marks):
        return self.expression.evaluate(map(attrgetter("name"), marks))


TagExpressionType = Union[
    _EnhancedMarksTagExpression, _MarksTagExpression, _FallbackMarksTagExpression, GherkinTagExpression
]
