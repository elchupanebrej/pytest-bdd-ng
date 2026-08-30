from __future__ import annotations

from functools import singledispatchmethod
from re import compile as re_compile
from typing import TYPE_CHECKING, Any

from cucumber_expressions.regular_expression import RegularExpression as CucumberRegularExpression

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers.base import RegistryMode, register_parser
from pytest_bdd.parsers.cucumber_expression import _CucumberExpression

if TYPE_CHECKING:
    from collections.abc import Collection

    from pytest_bdd.compatibility.pytest import FixtureRequest


class cucumber_regular_expression(_CucumberExpression):
    type = StepDefinitionPatternType.regular_expression
    expression_type = CucumberRegularExpression

    @singledispatchmethod
    def __init__(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError

    @__init__.register
    def _(
        self,
        expression: str,
        parameter_type_registry: Any = RegistryMode.FIXTURE,
    ) -> None:
        self.pattern = expression
        self.parameter_type_registry_like = parameter_type_registry

    @__init__.register
    def _(
        self,
        expression: CucumberRegularExpression,
    ) -> None:
        self.pattern = expression.expression_regexp.pattern
        self.parameter_type_registry_like = expression.parameter_type_registry

    @property
    def arguments(self) -> Collection[str]:
        return [*re_compile(self.pattern).groupindex.keys()]

    def rebuild_expression_in_test_context(self, request: FixtureRequest) -> CucumberRegularExpression:
        import re

        pat_str = self.pattern if isinstance(self.pattern, str) else self.pattern.pattern
        cleaned = re.sub(r"\(\?P<[a-zA-Z_][a-zA-Z0-9_]*>", "(", pat_str)
        return self.expression_type(re.compile(cleaned), self._get_parameter_type_registry(request))


register_parser(lambda parserlike: isinstance(parserlike, CucumberRegularExpression), cucumber_regular_expression)
