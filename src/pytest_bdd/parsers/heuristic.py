from __future__ import annotations

import importlib
from itertools import chain
from operator import methodcaller
from re import error as regex_error
from typing import TYPE_CHECKING, cast

from cucumber_expressions.errors import CantEscape, UndefinedParameterTypeError

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers.base import ParserBuildValueError, RegistryMode, StepParser, register_fallback_parser
from pytest_bdd.utils import StringableProtocol, stringify

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable, Sequence

    from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

    from pytest_bdd.compatibility.pytest import FixtureRequest

_ERRS = (
    AttributeError,
    CantEscape,
    KeyError,
    ParserBuildValueError,
    regex_error,
    TypeError,
    UndefinedParameterTypeError,
    ValueError,
)


def _build(builder: Callable[[], StepParser]) -> StepParser | None:
    try:
        return builder()
    except _ERRS:
        return None


class heuristic(StepParser):
    type = StepDefinitionPatternType.pytest_bdd_heuristic_expression

    def __init__(
        self,
        format_: object,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | str | None = RegistryMode.FIXTURE,
    ) -> None:
        self.format = stringify(format_) if isinstance(format_, StringableProtocol | str | bytes) else format_
        self.parameter_type_registry, self.parsers_are_built = parameter_type_registry, False
        self.string_parser: StepParser | None = None
        self.cucumber_expression_parser: StepParser | None = None
        self.cfparse_parser: StepParser | None = None
        self.re_parser: StepParser | None = None
        self.build_parsers()

    def build_parsers(self) -> None:
        if self.parsers_are_built:
            return
        m_cuke = importlib.import_module("pytest_bdd.parsers.cucumber_expression").cucumber_expression
        m_cf = importlib.import_module("pytest_bdd.parsers.parse_parser").cfparse
        m_re = importlib.import_module("pytest_bdd.parsers.re_parser").re
        m_str = importlib.import_module("pytest_bdd.parsers.string_parser").string
        self.string_parser = cast("StepParser | None", _build(lambda: m_str(self.format)))
        self.cucumber_expression_parser = cast(
            "StepParser | None",
            _build(lambda: m_cuke(self.format, parameter_type_registry=self.parameter_type_registry)),
        )
        self.cfparse_parser = cast("StepParser | None", _build(lambda: m_cf(self.format)))
        self.re_parser = cast("StepParser | None", _build(lambda: m_re(self.format)))
        self.parsers_are_built = True
        if not any(self.parser_by_priorities):
            raise ParserBuildValueError(self.format)

    @property
    def parser_by_priorities(self) -> Sequence[StepParser | None]:
        return [self.string_parser, self.cucumber_expression_parser, self.cfparse_parser, self.re_parser]

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        return any(map(methodcaller("is_matching", request, name), filter(None, self.parser_by_priorities)))

    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Iterable[str] | None = None
    ) -> dict[str, object] | None:
        for parser in self.parser_by_priorities:
            if parser is not None and parser.is_matching(request, name):
                return parser.parse_arguments(request, name, anonymous_group_names=anonymous_group_names)
        return None

    @property
    def arguments(self) -> Collection[str]:
        return [
            *chain.from_iterable(
                ([] if (a := getattr(p, "arguments", None)) is None else a) for p in self.parser_by_priorities
            )
        ]

    def __str__(self) -> str:
        return str(self.format)


register_fallback_parser(heuristic)
