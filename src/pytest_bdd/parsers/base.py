"""
Provide the base step parser definitions.

Responsibility:
    Provide the base step parser definitions. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.parsers.base` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - register_parser: owns nested behavior below this boundary
    - register_fallback_parser: owns nested behavior below this boundary
    - _load_parser_modules: owns nested behavior below this boundary
    - _ParseMatchProtocol: owns nested behavior below this boundary
    - _ParserBuilder: owns nested behavior below this boundary
    - _RegexCompiler: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/parsers/__init__.py: imports or references `base`
    - src/pytest_bdd/parsers/facade.py: imports or references `base`
    - src/pytest_bdd/script/message_capability_governance/schema.py: imports or references `base`

State and side effects:
    mutates _FALLBACK_PARSER_BUILDER, _PARSER_MODULES_LOADED, StepParserLike, _PARSER_MODULES, _PARSER_REGISTRY; depends
    on __future__.annotations, importlib, abc.ABC, abc.abstractmethod, collections.abc.Callable.

Invariants:
    - `pytest_bdd.parsers.base` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Failure semantics:
    Raises or re-raises NotImplementedError, ParserBuildValueError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import importlib
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from re import Pattern as _RePattern
from re import error as regex_error
from typing import TYPE_CHECKING, Final, Protocol, TypeAlias, cast, runtime_checkable

from cucumber_expressions.errors import CantEscape, UndefinedParameterTypeError

from pytest_bdd.model.message_extension import StepDefinitionPatternType

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Sequence

    from pytest_bdd.compatibility.pytest import FixtureRequest

StepParserLike: TypeAlias = object

_PARSER_MODULES: Final = (
    "pytest_bdd.parsers.re_parser",
    "pytest_bdd.parsers.parse_parser",
    "pytest_bdd.parsers.cucumber_expression",
    "pytest_bdd.parsers.cucumber_regex",
    "pytest_bdd.parsers.heuristic",
)
_PARSER_REGISTRY: list[tuple[Callable[[StepParserLike], bool], Callable[[StepParserLike], object]]] = []
_FALLBACK_PARSER_BUILDER: Callable[[StepParserLike], object] | None = None
_PARSER_MODULES_LOADED = False


def register_parser(
    predicate: Callable[[StepParserLike], bool],
    builder: Callable[[StepParserLike], object],
) -> None:
    """
    Responsibility:
        Responsibility: `pytest_bdd.parsers.base.register_parser` owns documented function behavior. It directly owns
        the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.base.register_parser` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _PARSER_REGISTRY.append: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `register_parser`
        - src/pytest_bdd/parsers/cucumber_expression.py: imports or references `register_parser`
        - src/pytest_bdd/parsers/cucumber_regex.py: imports or references `register_parser`
        - src/pytest_bdd/parsers/facade.py: imports or references `register_parser`
        - src/pytest_bdd/parsers/parse_parser.py: imports or references `register_parser`

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
    _PARSER_REGISTRY.append((predicate, builder))


def register_fallback_parser(builder: Callable[[StepParserLike], object]) -> None:
    """
    Responsibility:
        Responsibility: `pytest_bdd.parsers.base.register_fallback_parser` owns documented function behavior. It
        directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.base.register_fallback_parser` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `register_fallback_parser`
        - src/pytest_bdd/parsers/facade.py: imports or references `register_fallback_parser`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `register_fallback_parser`

    State and side effects:
        mutates _FALLBACK_PARSER_BUILDER.

    Invariants:
        - `pytest_bdd.parsers.base.register_fallback_parser` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    global _FALLBACK_PARSER_BUILDER
    _FALLBACK_PARSER_BUILDER = builder


def _load_parser_modules() -> None:
    """
    Responsibility:
        Responsibility: `pytest_bdd.parsers.base._load_parser_modules` owns documented function behavior. It directly
        owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.base._load_parser_modules` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - importlib.import_module: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `_load_parser_modules`
        - src/pytest_bdd/parsers/facade.py: imports or references `_load_parser_modules`

    State and side effects:
        mutates _PARSER_MODULES_LOADED.

    Invariants:
        - `pytest_bdd.parsers.base._load_parser_modules` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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
    global _PARSER_MODULES_LOADED
    if _PARSER_MODULES_LOADED:
        return
    for module_name in _PARSER_MODULES:
        importlib.import_module(module_name)
    _PARSER_MODULES_LOADED = True


class _ParseMatchProtocol(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.parsers.base._ParseMatchProtocol` owns documented class behavior. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.base._ParseMatchProtocol` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `_ParseMatchProtocol`
        - src/pytest_bdd/parsers/facade.py: imports or references `_ParseMatchProtocol`
        - src/pytest_bdd/parsers/parse_parser.py: imports or references `_ParseMatchProtocol`

    State and side effects:
        mutates named, fixed.

    Invariants:
        - `pytest_bdd.parsers.base._ParseMatchProtocol` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    named: dict[str, object]
    fixed: Sequence[object]


class _ParserBuilder(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.parsers.base._ParserBuilder` owns documented class behavior. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.base._ParserBuilder` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `_ParserBuilder`
        - src/pytest_bdd/parsers/facade.py: imports or references `_ParserBuilder`
        - src/pytest_bdd/parsers/parse_parser.py: imports or references `_ParserBuilder`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.parsers.base._ParserBuilder` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __call__(self, format_: str, *args: object, **kwargs: object) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.parsers.base._ParserBuilder.__call__` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base._ParserBuilder.__call__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/__init__.py: imports or references `__call__`
            - src/pytest_bdd/parsers/facade.py: imports or references `__call__`

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
        ...


class _RegexCompiler(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.parsers.base._RegexCompiler` owns documented class behavior. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.base._RegexCompiler` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `_RegexCompiler`
        - src/pytest_bdd/parsers/facade.py: imports or references `_RegexCompiler`
        - src/pytest_bdd/parsers/re_parser.py: imports or references `_RegexCompiler`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.parsers.base._RegexCompiler` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __call__(self, pattern: str, *args: object, **kwargs: object) -> _RePattern[str]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.parsers.base._RegexCompiler.__call__` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base._RegexCompiler.__call__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/__init__.py: imports or references `__call__`
            - src/pytest_bdd/parsers/facade.py: imports or references `__call__`

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
        ...


class ParserBuildValueError(ValueError):
    """
    Represent parser build value error failures.

    Responsibility:
        Represent parser build value error failures. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.base.ParserBuildValueError` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `ParserBuildValueError`
        - src/pytest_bdd/parsers/facade.py: imports or references `ParserBuildValueError`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `ParserBuildValueError`
        - src/pytest_bdd/parsers/parse_parser.py: imports or references `ParserBuildValueError`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.parsers.base.ParserBuildValueError` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    def __init__(self, format_: object) -> None:
        """
        Initialize the parser build value error.

        Responsibility:
            Initialize the parser build value error. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base.ParserBuildValueError.__init__` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

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
        super().__init__(f"Unable build parser for format {format_}")


@runtime_checkable
class StepParserProtocol(Protocol):
    """
    Define the step parser protocol contract.

    Responsibility:
        Define the step parser protocol contract. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.base.StepParserProtocol` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parse_arguments: owns nested behavior below this boundary
        - arguments: owns nested behavior below this boundary
        - is_matching: owns nested behavior below this boundary
        - __str__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `StepParserProtocol`
        - src/pytest_bdd/parsers/facade.py: imports or references `StepParserProtocol`

    State and side effects:
        mutates type.

    Invariants:
        - `pytest_bdd.parsers.base.StepParserProtocol` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    type: StepDefinitionPatternType | str = StepDefinitionPatternType.pytest_bdd_other_expression  # type:ignore[attr-defined]  # upstream type stubs missing this attribute

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object] | None:
        """
        Parse arguments.

        Responsibility:
            Parse arguments. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base.StepParserProtocol.parse_arguments`
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
            - src/pytest_bdd/parsers/__init__.py: imports or references `parse_arguments`
            - src/pytest_bdd/parsers/facade.py: imports or references `parse_arguments`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `parse_arguments`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or
              references `parse_arguments`
            - src/pytest_bdd/steps/definition.py: imports or references `parse_arguments`

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
            #arch-eval:locational_stability=4
        """
        ...  # pragma: no cover -- abstract protocol method

    @property
    def arguments(self) -> Collection[str]:
        """
        Handle arguments.

        Responsibility:
            Handle arguments. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base.StepParserProtocol.arguments` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

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
            - src/pytest_bdd/parsers/heuristic.py: imports or references `arguments`
            - src/pytest_bdd/plugin/cucumber_json/model.py: imports or references `arguments`

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
            #arch-eval:locational_stability=4
        """
        ...  # pragma: no cover -- abstract protocol method

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """
        Return matching.

        Responsibility:
            Return matching. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base.StepParserProtocol.is_matching` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

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
            - src/pytest_bdd/parsers/heuristic.py: imports or references `is_matching`
            - src/pytest_bdd/steps/matcher.py: imports or references `is_matching`

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
            #arch-eval:locational_stability=4
        """
        ...  # pragma: no cover -- abstract protocol method

    def __str__(self) -> str:
        """
        Return parser pattern as a string.

        Responsibility:
            Return parser pattern as a string. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base.StepParserProtocol.__str__` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

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
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        ...  # pragma: no cover -- abstract protocol method


class RegistryMode(Enum):
    """
    Represent registry mode state.

    Responsibility:
        Represent registry mode state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.base.RegistryMode` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `RegistryMode`
        - src/pytest_bdd/parsers/cucumber_expression.py: imports or references `RegistryMode`
        - src/pytest_bdd/parsers/cucumber_regex.py: imports or references `RegistryMode`
        - src/pytest_bdd/parsers/facade.py: imports or references `RegistryMode`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `RegistryMode`

    State and side effects:
        mutates NEW, GLOBAL, FIXTURE, NOT_DEFINED.

    Invariants:
        - `pytest_bdd.parsers.base.RegistryMode` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    NEW = "NEW"
    GLOBAL = "GLOBAL"
    FIXTURE = "FIXTURE"
    NOT_DEFINED = None


class StepParser(StepParserProtocol, ABC):
    """
    Parser of the individual step.

    #arch-eval:score=reason_for_existence:5
    #arch-eval:score=srp_expert:5
    #arch-eval:score=why_not_inline:5
    #arch-eval:score=why_not_split:5
    #arch-eval:score=problems_solved:5
    #arch-eval:score=law_of_demeter:4
    #arch-eval:score=module_location:5

    Responsibility:
        Parser of the individual step. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.base.StepParser` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parse_arguments: owns nested behavior below this boundary
        - arguments: owns nested behavior below this boundary
        - is_matching: owns nested behavior below this boundary
        - __str__: owns nested behavior below this boundary
        - build: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `StepParser`
        - src/pytest_bdd/parsers/cucumber_expression.py: imports or references `StepParser`
        - src/pytest_bdd/parsers/facade.py: imports or references `StepParser`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `StepParser`
        - src/pytest_bdd/parsers/parse_parser.py: imports or references `StepParser`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.parsers.base.StepParser` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Failure semantics:
        Raises or re-raises NotImplementedError, ParserBuildValueError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    @abstractmethod
    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object] | None:
        """
        Get step arguments from the given step name.

        :return: `dict` of step arguments

        Responsibility:
            Get step arguments from the given step name. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base.StepParser.parse_arguments` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/__init__.py: imports or references `parse_arguments`
            - src/pytest_bdd/parsers/facade.py: imports or references `parse_arguments`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `parse_arguments`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or
              references `parse_arguments`
            - src/pytest_bdd/steps/definition.py: imports or references `parse_arguments`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Failure semantics:
            Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        raise NotImplementedError  # pragma: no cover -- abstract subclass hook

    @property
    @abstractmethod
    def arguments(self) -> Collection[str]:
        """
        Get step argument names from the given step name.

        Responsibility:
            Get step argument names from the given step name. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base.StepParser.arguments` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

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
            - src/pytest_bdd/parsers/heuristic.py: imports or references `arguments`
            - src/pytest_bdd/plugin/cucumber_json/model.py: imports or references `arguments`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Failure semantics:
            Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        raise NotImplementedError  # pragma: no cover -- abstract subclass hook

    @abstractmethod
    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """
        Match given name with the step name.

        Responsibility:
            Match given name with the step name. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base.StepParser.is_matching` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

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
            - src/pytest_bdd/parsers/heuristic.py: imports or references `is_matching`
            - src/pytest_bdd/steps/matcher.py: imports or references `is_matching`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Failure semantics:
            Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        raise NotImplementedError  # pragma: no cover -- abstract subclass hook

    @abstractmethod
    def __str__(self) -> str:
        """
        Match given name with the step name.

        Responsibility:
            Match given name with the step name. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base.StepParser.__str__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

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

        Failure semantics:
            Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        raise NotImplementedError  # pragma: no cover -- abstract subclass hook

    @classmethod
    def build(cls, parserlike: StepParserLike) -> StepParser:
        """
        Get parser by given name.

        Args:
            parserlike: Step parser-like object (string, regex, Parser, etc).

        Returns:
            StepParser instance.

        Responsibility:
            Get parser by given name. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.base.StepParser.build` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - _load_parser_modules: collaborator call used by this boundary
            - predicate: collaborator call used by this boundary
            - builder: collaborator call used by this boundary
            - ParserBuildValueError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `build`
            - src/pytest_bdd/parsers/__init__.py: imports or references `build`
            - src/pytest_bdd/parsers/facade.py: imports or references `build`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `build`
            - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `build`

        State and side effects:
            keeps no local persistent state beyond call-local values.

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
            #arch-eval:locational_stability=4
        """
        if isinstance(parserlike, StepParserProtocol):
            return cast("StepParser", parserlike)

        _load_parser_modules()
        for predicate, builder in _PARSER_REGISTRY:
            if predicate(parserlike):
                return cast("StepParser", builder(parserlike))

        if _FALLBACK_PARSER_BUILDER is None:
            raise ParserBuildValueError(parserlike)
        return cast("StepParser", _FALLBACK_PARSER_BUILDER(parserlike))


_EXPECTED_PARSER_BUILD_ERRORS = (
    AttributeError,
    CantEscape,
    KeyError,
    ParserBuildValueError,
    regex_error,
    TypeError,
    UndefinedParameterTypeError,
    ValueError,
)
