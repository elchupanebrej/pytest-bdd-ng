from __future__ import annotations

from functools import singledispatchmethod
from operator import attrgetter
from re import compile as re_compile
from typing import TYPE_CHECKING, cast

from cucumber_expressions.errors import CantEscape, UndefinedParameterTypeError
from cucumber_expressions.expression import CucumberExpression
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers.base import RegistryMode, StepParser

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from cucumber_expressions.regular_expression import RegularExpression as CucumberRegularExpression

    from pytest_bdd.compatibility.pytest import FixtureRequest

UNDEFINED_PARAM_PATTERN = re_compile(r"Undefined parameter type ['{]?(?P<name>[^'}.\n]+)['}]?\.?")


class _CucumberExpression(StepParser):
    expression_type: type[CucumberExpression | CucumberRegularExpression]
    parameter_type_registry_like: ParameterTypeRegistry | RegistryMode | str | None
    parameter_type_registry = ParameterTypeRegistry()
    last_undefined_parameter_type: tuple[str, str] | None = None

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        self.last_undefined_parameter_type = None
        try:
            return bool(self.rebuild_expression_in_test_context(request).tree_regexp.match(name))
        except UndefinedParameterTypeError as exc:
            m = next(filter(None, map(UNDEFINED_PARAM_PATTERN.search, map(str, exc.args))), None)
            self.last_undefined_parameter_type = (self.pattern, m.group("name") if m else "")
            return False
        except CantEscape:
            return False

    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Iterable[str] | None = None
    ) -> dict[str, object] | None:
        expr = self.rebuild_expression_in_test_context(request)
        return dict(zip(anonymous_group_names or [], map(attrgetter("value"), expr.match(name) or []), strict=False))

    def __str__(self) -> str:
        return str(self.pattern)

    def rebuild_expression_in_test_context(
        self, request: FixtureRequest
    ) -> CucumberExpression | CucumberRegularExpression:
        return self.expression_type(self.pattern, self._get_parameter_type_registry(request))

    def _get_parameter_type_registry(self, request: FixtureRequest) -> ParameterTypeRegistry:
        reg = self.parameter_type_registry_like
        if isinstance(reg, str | RegistryMode) or reg is None:
            mode = RegistryMode(reg)
            if mode == RegistryMode.NEW:
                return ParameterTypeRegistry()
            if mode == RegistryMode.FIXTURE and request is not None:
                return cast("ParameterTypeRegistry", request.getfixturevalue("parameter_type_registry"))
            return self.parameter_type_registry
        return reg


class cucumber_expression(_CucumberExpression):
    type = StepDefinitionPatternType.cucumber_expression
    expression_type = CucumberExpression

    @singledispatchmethod
    def __init__(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError

    @__init__.register
    def _(
        self,
        expression: str,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | str | None = RegistryMode.FIXTURE,
    ) -> None:
        self.pattern, self.parameter_type_registry_like = expression, parameter_type_registry

    @__init__.register
    def _(self, expression: CucumberExpression) -> None:
        self.pattern, self.parameter_type_registry_like = expression.expression, expression.parameter_type_registry

    @property
    def arguments(self) -> Collection[str]:
        return []
