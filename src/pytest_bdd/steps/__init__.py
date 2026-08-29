from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.const import Steps
from pytest_bdd.model.step import Step, StepType
from pytest_bdd.steps.decorators import given, not_implemented, step, then, tolerant, when
from pytest_bdd.steps.definition import Definition, StepDefinitionAlias
from pytest_bdd.steps.manager import StepDefinitionManager
from pytest_bdd.steps.matcher import Matcher
from pytest_bdd.steps.registry import Registry, StepProtocol, StepRegistryProtocol
from pytest_bdd.steps.types import (
    ConverterT,
    ParamsFixturesMapping,
    StepDecorator,
    StepFunc,
    _parser_specificity,
    _resolve_callable_source_location,
    _step_text,
)

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Parser

StepHandler = StepDefinitionManager


def add_options(parser: Parser) -> None:
    """Add pytest-bdd step options."""
    group = parser.getgroup("bdd", "Steps")
    help_ = "Allow use different keywords with same step definition"
    group.addoption(
        "--liberal-steps",
        action="store_true",
        dest=Steps.Cli.LIBERAL_OPTION.value,
        default=None,
        help=help_,
    )
    parser.addini(
        Steps.Ini.LIBERAL_OPTION.value,
        default=False,
        type="bool",
        help=help_,
    )


__all__ = [
    "ConverterT",
    "Definition",
    "Matcher",
    "ParamsFixturesMapping",
    "Registry",
    "Step",
    "StepDecorator",
    "StepDefinitionAlias",
    "StepDefinitionManager",
    "StepFunc",
    "StepHandler",
    "StepProtocol",
    "StepRegistryProtocol",
    "StepType",
    "_parser_specificity",
    "_resolve_callable_source_location",
    "_step_text",
    "add_options",
    "given",
    "not_implemented",
    "step",
    "then",
    "tolerant",
    "when",
]
