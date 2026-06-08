"""
Provide the cucumber regular expression step parser.

Responsibility:
    Provide the cucumber regular expression step parser. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.parsers.cucumber_regex` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - cucumber_regular_expression: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/parsers/facade.py: imports or references `cucumber_regex`

State and side effects:
    mutates self.pattern, self.parameter_type_registry_like, type, expression_type; depends on __future__.annotations,
    functools.singledispatchmethod, re.compile, typing.TYPE_CHECKING,
    cucumber_expressions.parameter_type_registry.ParameterTypeRegistry.

Invariants:
    - `pytest_bdd.parsers.cucumber_regex` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from functools import singledispatchmethod
from re import compile as re_compile
from typing import TYPE_CHECKING

from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
from cucumber_expressions.regular_expression import RegularExpression as CucumberRegularExpression

from pytest_bdd.model.message_extension import StepDefinitionPatternType

from .base import RegistryMode, register_parser
from .cucumber_expression import _CucumberExpression

if TYPE_CHECKING:
    from collections.abc import Collection


class cucumber_regular_expression(_CucumberExpression):  # noqa: N801 intentional API
    """
    Represent cucumber regular expression state.

    Raises:
        NotImplementedError: If the operation cannot be completed.

    Responsibility:
        Represent cucumber regular expression state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.cucumber_regex.cucumber_regular_expression`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _: owns nested behavior below this boundary
        - _: owns nested behavior below this boundary
        - arguments: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `cucumber_regular_expression`
        - src/pytest_bdd/parsers/facade.py: imports or references `cucumber_regular_expression`

    State and side effects:
        mutates self.pattern, self.parameter_type_registry_like, type, expression_type.

    Invariants:
        - `pytest_bdd.parsers.cucumber_regex.cucumber_regular_expression` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

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

    type = StepDefinitionPatternType.regular_expression
    expression_type = CucumberRegularExpression
    # https://bugs.python.org/issue45684

    @singledispatchmethod  # type:ignore[misc]  # mypy limitation with singledispatchmethod/dynamic typing
    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Initialize the cucumber regular expression.

        Raises:
            NotImplementedError: If the operation cannot be completed.

        Responsibility:
            Initialize the cucumber regular expression. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.parsers.cucumber_regex.cucumber_regular_expression.__init__` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

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

    @__init__.register
    def _(
        self,
        expression: str,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | str | None = RegistryMode.FIXTURE,
    ) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.parsers.cucumber_regex.cucumber_regular_expression._` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.cucumber_regex.cucumber_regular_expression._`
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
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `_`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `_`
            - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `_`
            - src/pytest_bdd/collector_batch.py: imports or references `_`
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `_`

        State and side effects:
            mutates self.pattern, self.parameter_type_registry_like.

        Invariants:
            - `pytest_bdd.parsers.cucumber_regex.cucumber_regular_expression._` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

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
        self.pattern = expression
        self.parameter_type_registry_like = parameter_type_registry

    @__init__.register
    def _(
        self,
        expression: CucumberRegularExpression,
    ) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.parsers.cucumber_regex.cucumber_regular_expression._` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.cucumber_regex.cucumber_regular_expression._`
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
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `_`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `_`
            - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `_`
            - src/pytest_bdd/collector_batch.py: imports or references `_`
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `_`

        State and side effects:
            mutates self.pattern, self.parameter_type_registry_like.

        Invariants:
            - `pytest_bdd.parsers.cucumber_regex.cucumber_regular_expression._` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

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
        self.pattern = expression.expression_regexp.pattern
        self.parameter_type_registry_like = expression.parameter_type_registry

    @property
    def arguments(self) -> Collection[str]:
        """
        Get argument names from the compiled regular expression.

        Responsibility:
            Get argument names from the compiled regular expression. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.parsers.cucumber_regex.cucumber_regular_expression.arguments` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - re_compile.groupindex.keys: collaborator call used by this boundary
            - re_compile: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/feature_locator.py: imports or references `arguments`
            - src/pytest_bdd/parsers/facade.py: imports or references `arguments`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `arguments`
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
        return [*re_compile(self.pattern).groupindex.keys()]


register_parser(
    lambda parserlike: isinstance(parserlike, CucumberRegularExpression),
    cucumber_regular_expression,
)
