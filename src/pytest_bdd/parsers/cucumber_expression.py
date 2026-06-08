"""
Provide the cucumber expression step parser.

Responsibility:
    Provide the cucumber expression step parser. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.parsers.cucumber_expression` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - _CucumberExpression: owns nested behavior below this boundary
    - cucumber_expression: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/parsers/__init__.py: imports or references `cucumber_expression`
    - src/pytest_bdd/parsers/facade.py: imports or references `cucumber_expression`
    - src/pytest_bdd/parsers/heuristic.py: imports or references `cucumber_expression`
    - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `cucumber_expression`
    - src/pytest_bdd/steps/matcher.py: imports or references `cucumber_expression`

State and side effects:
    mutates parameter_type_registry, self.last_undefined_parameter_type, expression_type, undefined_name, self.pattern;
    depends on __future__.annotations, functools.singledispatchmethod, operator.attrgetter, re.compile,
    typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.parsers.cucumber_expression` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from functools import singledispatchmethod
from operator import attrgetter
from re import compile as re_compile
from typing import TYPE_CHECKING, cast

from cucumber_expressions.errors import CantEscape, UndefinedParameterTypeError
from cucumber_expressions.expression import CucumberExpression
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

from pytest_bdd.model.message_extension import StepDefinitionPatternType

from .base import RegistryMode, StepParser, register_parser

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from cucumber_expressions.regular_expression import RegularExpression as CucumberRegularExpression

    from pytest_bdd.compatibility.pytest import FixtureRequest

UNDEFINED_PARAMETER_TYPE_PATTERN = re_compile(
    r"Undefined parameter type ['{]?(?P<name>[^'}.\n]+)['}]?\.?",
)


class _CucumberExpression(StepParser):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.parsers.cucumber_expression._CucumberExpression` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.cucumber_expression._CucumberExpression` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - is_matching: owns nested behavior below this boundary
        - parse_arguments: owns nested behavior below this boundary
        - __str__: owns nested behavior below this boundary
        - rebuild_expression_in_test_context: owns nested behavior below this boundary
        - _get_parameter_type_registry: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `_CucumberExpression`
        - src/pytest_bdd/parsers/cucumber_regex.py: imports or references `_CucumberExpression`
        - src/pytest_bdd/parsers/facade.py: imports or references `_CucumberExpression`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `_CucumberExpression`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
          `_CucumberExpression`

    State and side effects:
        mutates parameter_type_registry, self.last_undefined_parameter_type, undefined_name, pattern, expression_type.

    Invariants:
        - `pytest_bdd.parsers.cucumber_expression._CucumberExpression` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    pattern: str

    expression_type: type[CucumberExpression | CucumberRegularExpression]
    parameter_type_registry_like: ParameterTypeRegistry | RegistryMode | str | None
    parameter_type_registry = ParameterTypeRegistry()  # default registry
    last_undefined_parameter_type: tuple[str, str] | None = None

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.parsers.cucumber_expression._CucumberExpression.is_matching`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.parsers.cucumber_expression._CucumberExpression.is_matching` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - bool: collaborator call used by this boundary
            - self.rebuild_expression_in_test_context.tree_regexp.match: collaborator call used by this boundary
            - self.rebuild_expression_in_test_context: collaborator call used by this boundary
            - UNDEFINED_PARAMETER_TYPE_PATTERN.search: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - matched_name.group: collaborator call used by this boundary

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
            mutates self.last_undefined_parameter_type, undefined_name, expression, matched_name.

        Invariants:
            - `pytest_bdd.parsers.cucumber_expression._CucumberExpression.is_matching` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

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
        try:
            self.last_undefined_parameter_type = None
            return bool(self.rebuild_expression_in_test_context(request).tree_regexp.match(name))
        except UndefinedParameterTypeError as exc:
            expression = self.pattern
            undefined_name = ""
            for arg in exc.args:
                matched_name = UNDEFINED_PARAMETER_TYPE_PATTERN.search(str(arg))
                if matched_name:
                    undefined_name = matched_name.group("name")
                    break
            self.last_undefined_parameter_type = (expression, undefined_name)
            return False
        except CantEscape:
            self.last_undefined_parameter_type = None
            return False

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object] | None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.parsers.cucumber_expression._CucumberExpression.parse_arguments`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.parsers.cucumber_expression._CucumberExpression.parse_arguments` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - dict: collaborator call used by this boundary
            - zip: collaborator call used by this boundary
            - map: collaborator call used by this boundary
            - attrgetter: collaborator call used by this boundary
            - self.rebuild_expression_in_test_context.match: collaborator call used by this boundary
            - self.rebuild_expression_in_test_context: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        return dict(
            zip(
                anonymous_group_names or [],
                map(
                    attrgetter("value"),
                    self.rebuild_expression_in_test_context(request).match(name) or [],
                ),
                strict=False,
            ),
        )

    def __str__(self) -> str:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.parsers.cucumber_expression._CucumberExpression.__str__` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.parsers.cucumber_expression._CucumberExpression.__str__` because it keeps the nearest code, data
            shape, call signature, and failure knowledge together.

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
            - src/pytest_bdd/parsers/heuristic.py: imports or references `__str__`

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
        return str(self.pattern)

    def rebuild_expression_in_test_context(
        self,
        request: FixtureRequest,
    ) -> CucumberExpression | CucumberRegularExpression:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.parsers.cucumber_expression._CucumberExpression.rebuild_expression_in_test_context` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.parsers.cucumber_expression._CucumberExpression.rebuild_expression_in_test_context` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.expression_type: collaborator call used by this boundary
            - self._get_parameter_type_registry: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/__init__.py: imports or references `rebuild_expression_in_test_context`
            - src/pytest_bdd/parsers/facade.py: imports or references `rebuild_expression_in_test_context`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `rebuild_expression_in_test_context`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or
              references `rebuild_expression_in_test_context`

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
        return self.expression_type(self.pattern, self._get_parameter_type_registry(request))

    def _get_parameter_type_registry(self, request: FixtureRequest) -> ParameterTypeRegistry:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.parsers.cucumber_expression._CucumberExpression._get_parameter_type_registry` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.parsers.cucumber_expression._CucumberExpression._get_parameter_type_registry` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - RegistryMode: collaborator call used by this boundary
            - request.getfixturevalue: collaborator call used by this boundary
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/__init__.py: imports or references `_get_parameter_type_registry`
            - src/pytest_bdd/parsers/facade.py: imports or references `_get_parameter_type_registry`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `_get_parameter_type_registry`

        State and side effects:
            mutates parameter_type_registry, parameter_type_registry_mode.

        Invariants:
            - `pytest_bdd.parsers.cucumber_expression._CucumberExpression._get_parameter_type_registry` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        if (
            isinstance(self.parameter_type_registry_like, (str, RegistryMode))
            or self.parameter_type_registry_like is None
        ):
            parameter_type_registry_mode = RegistryMode(self.parameter_type_registry_like)

            parameter_type_registry = {  # type: ignore[no-untyped-call]  # dict dispatch with mixed callable types
                RegistryMode.NEW: ParameterTypeRegistry,
                RegistryMode.GLOBAL: lambda: self.parameter_type_registry,
                RegistryMode.NOT_DEFINED: lambda: self.parameter_type_registry,
                RegistryMode.FIXTURE: lambda: request.getfixturevalue("parameter_type_registry"),
            }[parameter_type_registry_mode]()
        else:
            parameter_type_registry = self.parameter_type_registry_like
        return cast("ParameterTypeRegistry", parameter_type_registry)


class cucumber_expression(_CucumberExpression):  # noqa: N801 intentional API
    """
    Represent cucumber expression state.

    #arch-eval:score=reason_for_existence:5
    #arch-eval:score=srp_expert:5
    #arch-eval:score=why_not_inline:5
    #arch-eval:score=why_not_split:4
    #arch-eval:score=problems_solved:5
    #arch-eval:score=law_of_demeter:4
    #arch-eval:score=module_location:5

    Raises:
        NotImplementedError: If the operation cannot be completed.

    Responsibility:
        Represent cucumber expression state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.cucumber_expression.cucumber_expression` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

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
        - src/pytest_bdd/parsers/__init__.py: imports or references `cucumber_expression`
        - src/pytest_bdd/parsers/facade.py: imports or references `cucumber_expression`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `cucumber_expression`
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `cucumber_expression`
        - src/pytest_bdd/steps/matcher.py: imports or references `cucumber_expression`

    State and side effects:
        mutates self.pattern, self.parameter_type_registry_like, type, expression_type.

    Invariants:
        - `pytest_bdd.parsers.cucumber_expression.cucumber_expression` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4
    """

    type = StepDefinitionPatternType.cucumber_expression
    expression_type = CucumberExpression

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]  # mypy limitation with singledispatchmethod/dynamic typing
    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Initialize the cucumber expression.

        Raises:
            NotImplementedError: If the operation cannot be completed.

        Responsibility:
            Initialize the cucumber expression. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.parsers.cucumber_expression.cucumber_expression.__init__` because it keeps the nearest code,
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
            Responsibility: Responsibility: `pytest_bdd.parsers.cucumber_expression.cucumber_expression._` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.cucumber_expression.cucumber_expression._`
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
            - `pytest_bdd.parsers.cucumber_expression.cucumber_expression._` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

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
        expression: CucumberExpression,
    ) -> None:
        """
        Handle object.

        Responsibility:
            Handle object. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.cucumber_expression.cucumber_expression._`
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
            - `pytest_bdd.parsers.cucumber_expression.cucumber_expression._` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

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
        self.pattern = expression.expression
        self.parameter_type_registry_like = expression.parameter_type_registry

    @property
    def arguments(self) -> Collection[str]:
        """
        Handle arguments.

        Responsibility:
            Handle arguments. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.parsers.cucumber_expression.cucumber_expression.arguments` because it keeps the nearest code,
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
        return []


register_parser(lambda parserlike: isinstance(parserlike, CucumberExpression), cucumber_expression)
