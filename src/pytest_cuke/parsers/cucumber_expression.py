from __future__ import annotations

from operator import attrgetter
from re import compile as re_compile
from typing import TYPE_CHECKING, Any, cast

from cucumber_expressions.errors import CantEscape, UndefinedParameterTypeError
from cucumber_expressions.expression import CucumberExpression
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

from pytest_cuke.model.message_extension import StepDefinitionPatternType
from pytest_cuke.parsers.base import RegistryMode, StepParser, register_parser

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable

    from cucumber_expressions.parameter_type import ParameterType
    from cucumber_expressions.regular_expression import RegularExpression as CucumberRegularExpression

    from pytest_cuke.compatibility.pytest import FixtureRequest


UNDEFINED_PARAM_PATTERN = re_compile(r"Undefined parameter type ['{]?(?P<name>[^'}.\n]+)['}]?\.?")


def _new_parameter_type_registry() -> ParameterTypeRegistry:
    registry_factory = cast("Callable[[], ParameterTypeRegistry]", ParameterTypeRegistry)
    return registry_factory()


class _WildcardParameterTypeRegistry:
    def __init__(self, registry: ParameterTypeRegistry) -> None:
        self.registry = registry
        self.unresolved_parameter_names: list[str] = []
        self._unresolved_names: set[str] = set()
        self._anonymous_parameter_type = registry.lookup_by_type_name("")

    def lookup_by_type_name(self, name: str) -> ParameterType | None:
        parameter_type = self.registry.lookup_by_type_name(name)
        if parameter_type is not None:
            return parameter_type

        if name not in self._unresolved_names:
            self.unresolved_parameter_names.append(name)
            self._unresolved_names.add(name)
        return self._anonymous_parameter_type


class _CucumberExpression(StepParser):
    expression_type: type[CucumberExpression | CucumberRegularExpression]
    parameter_type_registry_like: ParameterTypeRegistry | RegistryMode | str | None
    pattern: str
    parameter_type_registry: ParameterTypeRegistry = _new_parameter_type_registry()
    last_undefined_parameter_type: tuple[str, str] | None = None
    last_undefined_parameter_types: tuple[tuple[str, str], ...] = ()
    last_undefined_parameter_type_error: UndefinedParameterTypeError | None = None

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        self.last_undefined_parameter_type = None
        self.last_undefined_parameter_types = ()
        self.last_undefined_parameter_type_error = None
        registry = self._get_parameter_type_registry(request)
        try:
            return bool(self._build_expression(registry).tree_regexp.match(name))
        except UndefinedParameterTypeError as exc:
            try:
                wildcard_registry = _WildcardParameterTypeRegistry(registry)
                candidate = self._build_expression(wildcard_registry)
                matches_step = candidate.tree_regexp.match(name) is not None
            except Exception:  # This diagnostic-only recompile must fail closed for custom registries.
                return False

            if matches_step and wildcard_registry.unresolved_parameter_names:
                self.last_undefined_parameter_types = tuple(
                    (self.pattern, parameter_name)
                    for parameter_name in wildcard_registry.unresolved_parameter_names
                )
                self.last_undefined_parameter_type = self.last_undefined_parameter_types[0]
                self.last_undefined_parameter_type_error = exc
            return False
        except CantEscape:
            return False

    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Iterable[str] | None = None
    ) -> dict[str, object] | None:
        expr = self.rebuild_expression_in_test_context(request)
        names: Iterable[str] = anonymous_group_names if anonymous_group_names is not None else self.arguments
        matched_arguments = cast("Iterable[Any]", expr.match(name) or ())
        return dict(zip(names, map(attrgetter("value"), matched_arguments), strict=False))

    def __str__(self) -> str:
        return str(self.pattern)

    def rebuild_expression_in_test_context(
        self, request: FixtureRequest
    ) -> CucumberExpression | CucumberRegularExpression:
        return self._build_expression(self._get_parameter_type_registry(request))

    def _build_expression(self, parameter_type_registry: Any) -> CucumberExpression | CucumberRegularExpression:
        expression_factory = cast("Callable[..., Any]", self.expression_type)
        expression = expression_factory(self.pattern, parameter_type_registry)
        return cast("CucumberExpression | CucumberRegularExpression", expression)

    def _get_parameter_type_registry(self, request: FixtureRequest) -> ParameterTypeRegistry:
        reg = self.parameter_type_registry_like
        if isinstance(reg, str | RegistryMode) or reg is None:
            mode = RegistryMode(reg)
            if mode == RegistryMode.NEW:
                return _new_parameter_type_registry()
            if mode == RegistryMode.FIXTURE and request is not None:
                return cast("ParameterTypeRegistry", request.getfixturevalue("parameter_type_registry"))
            return self.parameter_type_registry
        return reg


class cucumber_expression(_CucumberExpression):
    type = StepDefinitionPatternType.cucumber_expression
    expression_type = CucumberExpression

    def __init__(
        self,
        expression: object,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | str | None = RegistryMode.FIXTURE,
    ) -> None:
        if isinstance(expression, str):
            self.pattern, self.parameter_type_registry_like = expression, parameter_type_registry
        elif isinstance(expression, CucumberExpression):
            self.pattern, self.parameter_type_registry_like = expression.expression, expression.parameter_type_registry
        else:
            raise NotImplementedError

    @property
    def arguments(self) -> Collection[str]:
        return []


register_parser(lambda parserlike: isinstance(parserlike, CucumberExpression), cucumber_expression)
