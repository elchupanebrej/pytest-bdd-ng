"""
Provide the heuristic multi-parser step parser.

Responsibility:
    Provide the heuristic multi-parser step parser. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.parsers.heuristic` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - _build_parser_result: owns nested behavior below this boundary
    - heuristic: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/parsers/__init__.py: imports or references `heuristic`
    - src/pytest_bdd/parsers/facade.py: imports or references `heuristic`

State and side effects:
    mutates self.format, self.parsers_are_built, arguments, type, self.parameter_type_registry; depends on
    __future__.annotations, importlib, itertools.chain, operator.methodcaller, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.parsers.heuristic` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises ParserBuildValueError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import importlib
from itertools import chain
from operator import methodcaller
from typing import TYPE_CHECKING, cast

from returns.result import Failure, Result, Success

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.types.failure_reasons import ParserFailure
from pytest_bdd.util.other import StringRepresentable, normalize_to_string

from .base import (
    _EXPECTED_PARSER_BUILD_ERRORS,
    ParserBuildValueError,
    RegistryMode,
    StepParser,
    register_fallback_parser,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable, Sequence

    from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

    from pytest_bdd.compatibility.pytest import FixtureRequest
    from pytest_bdd.parsers.cucumber_expression import cucumber_expression as CucumberExpressionParser
    from pytest_bdd.parsers.parse_parser import cfparse as CfparseParser
    from pytest_bdd.parsers.re_parser import re as ReParser
    from pytest_bdd.parsers.string_parser import string as StringParser


def _build_parser_result(builder: Callable[[], StepParser]) -> Result[StepParser, ParserFailure]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.parsers.heuristic._build_parser_result` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.heuristic._build_parser_result` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Success: collaborator call used by this boundary
        - builder: collaborator call used by this boundary
        - Failure: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `_build_parser_result`
        - src/pytest_bdd/parsers/facade.py: imports or references `_build_parser_result`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    try:
        return Success(builder())
    except _EXPECTED_PARSER_BUILD_ERRORS:
        return Failure(ParserFailure.SYNTAX_ERROR)


class heuristic(StepParser):  # noqa: N801 intentional API
    """
    Represent heuristic state.

    Raises:
        ParserBuildValueError: If the operation cannot be completed.

    Responsibility:
        Represent heuristic state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.heuristic.heuristic` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - build_parsers: owns nested behavior below this boundary
        - parser_by_priorities: owns nested behavior below this boundary
        - is_matching: owns nested behavior below this boundary
        - parse_arguments: owns nested behavior below this boundary
        - arguments: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `heuristic`
        - src/pytest_bdd/parsers/facade.py: imports or references `heuristic`

    State and side effects:
        mutates self.format, self.parsers_are_built, arguments, type, self.parameter_type_registry.

    Invariants:
        - `pytest_bdd.parsers.heuristic.heuristic` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Failure semantics:
        Raises or re-raises ParserBuildValueError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    type = StepDefinitionPatternType.pytest_bdd_heuristic_expression  # type:ignore[attr-defined]  # upstream type stubs missing this attribute

    def __init__(
        self,
        format_: object,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | str | None = RegistryMode.FIXTURE,
    ) -> None:
        """
        Initialize the heuristic.

        Responsibility:
            Initialize the heuristic. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.heuristic.heuristic.__init__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - normalize_to_string: collaborator call used by this boundary
            - self.build_parsers: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates self.format, self.parameter_type_registry, self.parsers_are_built.

        Invariants:
            - `pytest_bdd.parsers.heuristic.heuristic.__init__` keeps its documented import path, ownership boundary,
              and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        if isinstance(format_, (StringRepresentable, str, bytes)):
            self.format = normalize_to_string(format_)
        else:
            self.format = format_
        self.parameter_type_registry = parameter_type_registry
        self.parsers_are_built = False
        self.build_parsers()

    def build_parsers(self) -> None:
        """
        Build parsers.

        Raises:
            ParserBuildValueError: If the operation cannot be completed.

        Responsibility:
            Build parsers. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.heuristic.heuristic.build_parsers` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - importlib.import_module: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - _build_parser_result.value_or: collaborator call used by this boundary
            - _build_parser_result: collaborator call used by this boundary
            - string_parser_cls: collaborator call used by this boundary
            - cucumber_expression_parser_cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/__init__.py: imports or references `build_parsers`
            - src/pytest_bdd/parsers/facade.py: imports or references `build_parsers`

        State and side effects:
            mutates cucumber_expression_parser_cls, cfparse_parser_cls, re_parser_cls, string_parser_cls,
            self.string_parser.

        Invariants:
            - `pytest_bdd.parsers.heuristic.heuristic.build_parsers` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ParserBuildValueError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        if self.parsers_are_built:
            return

        cucumber_expression_parser_cls = importlib.import_module(
            "pytest_bdd.parsers.cucumber_expression",
        ).cucumber_expression
        cfparse_parser_cls = importlib.import_module("pytest_bdd.parsers.parse_parser").cfparse
        re_parser_cls = importlib.import_module("pytest_bdd.parsers.re_parser").re
        string_parser_cls = importlib.import_module("pytest_bdd.parsers.string_parser").string

        self.string_parser = cast(
            "StringParser | None",
            _build_parser_result(lambda: string_parser_cls(self.format)).value_or(None),
        )
        self.cucumber_expression_parser = cast(
            "CucumberExpressionParser | None",
            _build_parser_result(
                lambda: cucumber_expression_parser_cls(
                    self.format,
                    parameter_type_registry=self.parameter_type_registry,
                ),
            ).value_or(None),
        )
        self.cfparse_parser = cast(
            "CfparseParser | None",
            _build_parser_result(lambda: cfparse_parser_cls(self.format)).value_or(None),
        )
        self.re_parser = cast(
            "ReParser | None",
            _build_parser_result(lambda: re_parser_cls(self.format)).value_or(None),
        )

        self.parsers_are_built = True
        if not any(self.parser_by_priorities):
            raise ParserBuildValueError(
                self.format,
            )  # pragma: no cover -- unreachable; at least one parser always matches for valid strings

    @property
    def parser_by_priorities(self) -> Sequence[StepParser | None]:
        """
        Get parsers by priority.

        Returns:
            List of parsers in priority order.

        Responsibility:
            Get parsers by priority. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.heuristic.heuristic.parser_by_priorities`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/__init__.py: imports or references `parser_by_priorities`
            - src/pytest_bdd/parsers/facade.py: imports or references `parser_by_priorities`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return [
            self.string_parser,
            self.cucumber_expression_parser,
            self.cfparse_parser,
            self.re_parser,
        ]

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """
        Check if name matches any parser.

        Returns:
            True if any parser matches, False otherwise.

        Responsibility:
            Check if name matches any parser. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.heuristic.heuristic.is_matching` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - any: collaborator call used by this boundary
            - map: collaborator call used by this boundary
            - methodcaller: collaborator call used by this boundary
            - filter: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `is_matching`
            - src/pytest_bdd/parsers/__init__.py: imports or references `is_matching`
            - src/pytest_bdd/parsers/facade.py: imports or references `is_matching`
            - src/pytest_bdd/steps/matcher.py: imports or references `is_matching`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        return any(
            map(
                methodcaller("is_matching", request, name),
                filter(bool, self.parser_by_priorities),
            ),
        )

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object] | None:
        """
        Parse arguments using matching parser.

        Returns:
            Parsed arguments or None.

        Responsibility:
            Parse arguments using matching parser. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.heuristic.heuristic.parse_arguments` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - parser.is_matching: collaborator call used by this boundary
            - parser.parse_arguments: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/__init__.py: imports or references `parse_arguments`
            - src/pytest_bdd/parsers/facade.py: imports or references `parse_arguments`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or
              references `parse_arguments`
            - src/pytest_bdd/steps/definition.py: imports or references `parse_arguments`

        State and side effects:
            mutates arguments.

        Invariants:
            - `pytest_bdd.parsers.heuristic.heuristic.parse_arguments` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        for parser in self.parser_by_priorities:
            if parser is not None and parser.is_matching(request, name):
                arguments = parser.parse_arguments(request, name, anonymous_group_names=anonymous_group_names)
                break
        else:
            arguments = None
        return arguments

    @property
    def arguments(self) -> Collection[str]:
        """
        Get all argument names from all parsers.

        Returns:
            Collection of argument names.

        Responsibility:
            Get all argument names from all parsers. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.heuristic.heuristic.arguments` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - chain.from_iterable: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/feature_locator.py: imports or references `arguments`
            - src/pytest_bdd/parsers/__init__.py: imports or references `arguments`
            - src/pytest_bdd/parsers/facade.py: imports or references `arguments`
            - src/pytest_bdd/plugin/cucumber_json/model.py: imports or references `arguments`
            - src/pytest_bdd/steps/definition.py: imports or references `arguments`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        return [
            *chain.from_iterable(
                (
                    []  # function may return untyped value
                    if (args := getattr(parser, "arguments", None)) is None
                    else args
                )
                for parser in self.parser_by_priorities
            ),
        ]

    def __str__(self) -> str:
        """
        Get parser format as string.

        Returns:
            Parser format string.

        Responsibility:
            Get parser format as string. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.heuristic.heuristic.__str__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/__init__.py: imports or references `__str__`
            - src/pytest_bdd/parsers/facade.py: imports or references `__str__`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        return str(self.format)


register_fallback_parser(heuristic)
