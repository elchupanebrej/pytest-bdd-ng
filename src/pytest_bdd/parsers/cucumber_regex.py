"""
Owns the Cucumber Regular Expression-based step parser: the `cucumber_regular_expression` class that specializes _Cuc.

Responsibility:
    Owns the Cucumber Regular Expression-based step parser: the `cucumber_regular_expression` class that specializes
    _CucumberExpression with expression_type=CucumberRegularExpression (from cucumber-expressions library), providing
    regex-based Cucumber pattern matching with parameter type conversion. Provides a singledispatchmethod-based dual
    constructor (string expression or pre-compiled CucumberRegularExpression) and a meaningful `arguments` property that
    extracts named capture group names from the compiled regex pattern via re_compile(self.pattern).groupindex.keys().
    Registered as the parser wrapper for pre-compiled CucumberRegularExpression objects via register_parser().

Reason for existence:
    Cucumber Regular Expressions are the regex-based counterpart to Cucumber Expressions — they use standard regex
    syntax but benefit from Cucumber's parameter type system for type conversion. For example, a regex pattern with a
    named group can have its value converted using a registered parameter type. This module provides pytest-bdd users
    access to this hybrid parsing strategy. The `arguments` property is meaningful here (unlike cucumber_expression
    which returns empty) because regex patterns have explicit named capture groups that the step manager needs to know
    about.

Delegates:
    - _CucumberExpression (parent from cucumber_expression module): Inherits all matching logic, registry resolution,
    and error handling.
    - CucumberRegularExpression (cucumber_expressions): The regex-based Cucumber expression parser — expression_type
    class attribute.
    - re_compile (stdlib): Used in the `arguments` property to extract named capture group names from the regex pattern.
    - singledispatchmethod: Enables dual-constructor pattern.
    - register_parser: Registers this class as the parser wrapper for pre-compiled CucumberRegularExpression objects.

Cohesion:
    Every method in this class serves the Cucumber Regular Expression specialization. The constructors store the pattern
    and registry config, expression_type=CucumberRegularExpression selects the regex-based parser engine, and the
    `arguments` property uses re_compile to extract named groups from the regex pattern. All behavior extends or
    specializes the base class.

Separation:
    - cucumber_expression (from cucumber_expression module): Kept separate because that class uses CucumberExpression
    (expression-based) while this uses CucumberRegularExpression (regex-based) — different parser engines, different
    pattern syntaxes, shared base class.
    - re (from re_parser): Kept separate because re uses stdlib re.Pattern directly (no parameter types), while
    cucumber_regular_expression uses cucumber-expressions' RegularExpression (stdlib regex + parameter type conversion)
    — raw regex vs type-enriched regex.

Main consumers:
    - End-user test code via parsers.cucumber_regular_expression(r"pattern").
    - pytest_bdd.steps.manager: Uses the StepParser protocol for matching.

State and side effects:
    Inherits mutable state from _CucumberExpression (last_undefined_parameter_type, parameter_type_registry).

Invariants:
    - expression_type must be CucumberRegularExpression — never CucumberExpression.
    - The `arguments` property must use re_compile(self.pattern) to extract group names, since the pattern is a regex
    string.

Failure semantics:
    Raises NotImplementedError from base singledispatchmethod __init__ — dead code path.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
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
    Concrete Cucumber Regular Expression parser class specializing _CucumberExpression with expression_type=CucumberRegul.

    Responsibility:
        Concrete Cucumber Regular Expression parser class specializing _CucumberExpression with
        expression_type=CucumberRegularExpression for regex-based Cucumber pattern matching with parameter type
        conversion. Provides singledispatchmethod-based dual constructor (string regex pattern with optional registry
        config or pre-compiled CucumberRegularExpression) and a meaningful `arguments` property that extracts named
        capture group names from the regex pattern via re_compile(self.pattern).groupindex.keys(). Registered as the
        parser wrapper for pre-compiled CucumberRegularExpression objects.

    Reason for existence:
        Cucumber Regular Expressions bridge the gap between raw regex (powerful but no type conversion) and Cucumber
        Expressions (readable but less expressive for complex patterns). They allow users to write standard regex
        patterns with named groups while benefiting from Cucumber's parameter type system (e.g., a regex group matching
        a number can be auto-converted to int via the {int} type). The arguments property is implemented (unlike
        cucumber_expression which returns empty) because regex patterns explicitly define named capture groups.

    Delegates:
        - _CucumberExpression: Inherits all matching, registry resolution, and error handling logic.
        - CucumberRegularExpression: The regex-based expression parser — set as expression_type.
        - re_compile(self.pattern).groupindex.keys(): Extracts named capture group names from the regex pattern for the
        arguments property.
        - singledispatchmethod: Enables dual-constructor pattern.
        - register_parser: Registers parser wrapper.

    Cohesion:
        Every method specializes for regex-based Cucumber patterns: expression_type selects the regex engine,
        constructors handle string/regex patterns and pre-compiled objects, arguments extracts named regex groups. All
        behavior is consistent with "regex-based Cucumber expression matching."

    Separation:
        - cucumber_expression: Kept separate because that class uses CucumberExpression (expression syntax), while this
        uses CucumberRegularExpression (regex syntax) — different parser engines within the same cucumber-expressions
        library.
        - re (from re_parser): Kept separate because re uses raw stdlib re.Pattern (no parameter type system), while
        cucumber_regular_expression uses cucumber-expressions' RegularExpression (stdlib regex + Cucumber parameter
        types) — plain regex vs type-enriched regex.

    Main consumers:
        - End-user code: parsers.cucumber_regular_expression(r"pattern").
        - pytest_bdd.steps.manager: Uses StepParser protocol for matching.

    State and side effects:
        Inherits mutable diagnostic state from _CucumberExpression.

    Invariants:
        - expression_type must be CucumberRegularExpression.
        - StepDefinitionPatternType must be regular_expression for proper classification.

    Failure semantics:
        Raises NotImplementedError from base singledispatchmethod __init__.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    type = StepDefinitionPatternType.regular_expression
    expression_type = CucumberRegularExpression
    # https://bugs.python.org/issue45684

    @singledispatchmethod  # type:ignore[misc]  # mypy limitation with singledispatchmethod/dynamic typing
    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Serve as the base singledispatchmethod constructor (abstract hook raising NotImplementedError).

        Responsibility:
            Base singledispatchmethod constructor — abstract hook raising NotImplementedError. The two registered
            methods handle string regex patterns and pre-compiled CucumberRegularExpression objects. This base method is
            never reached in normal usage; it exists to satisfy the singledispatchmethod pattern requirements.

        Reason for existence:
            singledispatchmethod requires a base method that the register methods override. Raising NotImplementedError
            clearly signals that unregistered argument types are programmer errors, following the same pattern used by
            cucumber_expression, parse, and re constructor bases.

        Delegates:
            - singledispatchmethod: Dispatches to registered handlers based on argument types.

        Cohesion:
            Pure guard — no logic beyond the raise.

        Separation:
            - The register methods: Handle actual initialization for string and CucumberRegularExpression inputs.

        Main consumers:
            - singledispatchmethod dispatch system: Automatically invoked for unmatched argument types.

        State and side effects:
            None. Immediately raises.

        Failure semantics:
            Raises NotImplementedError for unsupported constructor argument types — indicates a programming error.

        Architecture score:
            #arch-eval:reason_for_existence=2
            #arch-eval:owned_responsibility=2
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
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
        Handle registered singledispatch for string regex pattern inputs: store the pattern string and parameter_type_registry configuration.

        Responsibility:
            Registered singledispatch handler for string regex pattern inputs: stores the pattern string and
            parameter_type_registry configuration (defaulting to FIXTURE mode). Like cucumber_expression, the actual
            expression compilation is deferred to rebuild_expression_in_test_context for per-test registry resolution.

        Reason for existence:
            Users create Cucumber regular expression parsers by passing regex pattern strings. This handler stores the
            raw inputs; the expression is lazily constructed when per-test registry information becomes available via
            the fixture system. The FIXTURE default preserves per-test parameter type isolation.

        Delegates:
            - None. Simply stores self.pattern = expression and self.parameter_type_registry_like = parameter_type_registry.

        Cohesion:
            Performs one operation: store pattern and registry config. No compilation, no validation.

        Separation:
            - The CucumberRegularExpression register method: Kept separate because that method extracts pattern and
            registry from pre-compiled objects — extraction vs storage.

        Main consumers:
            - User code via parsers.cucumber_regular_expression(r"pattern").

        State and side effects:
            Sets self.pattern and self.parameter_type_registry_like on the instance.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
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
        Handle registered singledispatch for pre-compiled CucumberRegularExpression objects: extract the regex pattern string from the compiled object.

        Responsibility:
            Registered singledispatch handler for pre-compiled CucumberRegularExpression objects: extracts the regex
            pattern string from expression.expression_regexp.pattern and the parameter type registry from
            expression.parameter_type_registry, storing both for lazy rebuilding. This enables step definitions using
            pre-compiled regex expression objects.

        Reason for existence:
            Pre-compiled CucumberRegularExpression objects may come from earlier parsing phases. This handler extracts
            the original regex pattern string (which is stored two levels deep: expression.expression_regexp.pattern)
            and the registry for reconstruction in rebuild_expression_in_test_context with the correct per-test
            registry.

        Delegates:
            - expression.expression_regexp.pattern: The original regex pattern string.
            - expression.parameter_type_registry: The embedded parameter type registry.

        Cohesion:
            Performs one operation: extract pattern (from nested attribute) and registry → store.

        Separation:
            - The string register method: Kept separate because that stores raw inputs while this extracts from existing objects.

        Main consumers:
            - Code using pre-compiled CucumberRegularExpression objects.

        State and side effects:
            Sets self.pattern and self.parameter_type_registry_like. Read-only access to expression object.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        self.pattern = expression.expression_regexp.pattern
        self.parameter_type_registry_like = expression.parameter_type_registry

    @property
    def arguments(self) -> Collection[str]:
        r"""
        Extracts named capture group names from the regex pattern by compiling it with re_compile and reading groupindex.keys().

        Responsibility:
            Extracts named capture group names from the regex pattern by compiling it with re_compile and reading
            groupindex.keys(). Returns the list of group names (e.g., for r"(?P<name>\w+)" returns ["name"]). Unlike
            cucumber_expression which returns an empty list, this property returns meaningful argument names because
            regex patterns have explicit named capture groups that map to step function parameters.

        Reason for existence:
            The step definition manager needs to know which argument names a step parser can extract to validate step
            function signatures. For regex-based patterns, the named capture groups ((?P<name>...)) are the argument
            names. This property extracts them from the compiled regex. The pattern is compiled on each property access
            (no caching) which is acceptable because the property is typically accessed once per step definition during
            collection.

        Delegates:
            - re_compile(self.pattern): Compiles the regex pattern string to a re.Pattern object to access groupindex.

        Cohesion:
            Performs one operation: compile regex → extract group names → return as list.

        Separation:
            - cucumber_expression.arguments: Kept separate because cucumber_expression returns empty (expression-based,
            no regex groups), while cucumber_regular_expression returns actual group names (regex-based, explicit
            capture groups).
            - re.arguments: Kept separate because re uses self.regex.groupindex (already compiled) while this compiles
            fresh each access — different object lifecycles.

        Main consumers:
            - pytest_bdd.steps.manager: Uses arguments to validate step function parameter names.

        State and side effects:
            None. Creates a temporary compiled regex object on each access (no caching).

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        return [*re_compile(self.pattern).groupindex.keys()]


register_parser(
    lambda parserlike: isinstance(parserlike, CucumberRegularExpression),
    cucumber_regular_expression,
)
