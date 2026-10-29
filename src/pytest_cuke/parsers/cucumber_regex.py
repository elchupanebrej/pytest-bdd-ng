from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from cucumber_expressions.regular_expression import RegularExpression as CucumberRegularExpression

from pytest_cuke.model.message_extension import StepDefinitionPatternType
from pytest_cuke.parsers.base import RegistryMode, register_parser
from pytest_cuke.parsers.cucumber_expression import _CucumberExpression

if TYPE_CHECKING:
    from collections.abc import Collection

    from pytest_cuke.compatibility.pytest import FixtureRequest


class cucumber_regular_expression(_CucumberExpression):
    type = StepDefinitionPatternType.regular_expression
    expression_type = CucumberRegularExpression

    def __init__(
        self,
        expression: object,
        parameter_type_registry: Any = RegistryMode.FIXTURE,
    ) -> None:
        if isinstance(expression, str):
            self.pattern = expression
            self.parameter_type_registry_like = parameter_type_registry
        elif isinstance(expression, CucumberRegularExpression):
            self.pattern = expression.expression_regexp.pattern
            self.parameter_type_registry_like = expression.parameter_type_registry
        else:
            raise NotImplementedError

    @property
    def arguments(self) -> Collection[str]:
        return [*re.compile(self.pattern).groupindex.keys()]

    def rebuild_expression_in_test_context(self, request: FixtureRequest) -> CucumberRegularExpression:
        pat_str = self.pattern if isinstance(self.pattern, str) else self.pattern.pattern
        cleaned = re.sub(r"\(\?P<[a-zA-Z_][a-zA-Z0-9_]*>", "(", pat_str)
        return self.expression_type(re.compile(cleaned), self._get_parameter_type_registry(request))


register_parser(lambda parserlike: isinstance(parserlike, CucumberRegularExpression), cucumber_regular_expression)
