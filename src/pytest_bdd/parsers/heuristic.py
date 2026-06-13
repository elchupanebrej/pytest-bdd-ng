"""
Implements the heuristic composite step parser — a StepParser subclass that lazily constructs multiple sub-parsers (s.

Responsibility:
    Implements the heuristic composite step parser — a StepParser subclass that lazily constructs multiple sub-parsers
    (string, cucumber_expression, cfparse, re) in priority order and delegates matching and parameter extraction to the
    first sub-parser that succeeds. Provides the _build_parser_result helper for safe parser construction with
    structured error containment (returns Result[StepParser, ParserFailure]), and registers the heuristic class as the
    universal fallback parser via register_fallback_parser(heuristic), ensuring that any parserlike object not handled
    by a specific backend is tried against all available backends in order.

Reason for existence:
    This module exists as a separate parser backend because the heuristic strategy is fundamentally a meta-parser: it
    does not perform its own pattern matching but composes multiple concrete parsers and selects among them. Keeping it
    separate from the concrete parsers (re, parse, cfparse, cucumber_expression, string) avoids coupling the composition
    logic to any individual backend's implementation. It is the only parser that calls register_fallback_parser, making
    it the catch-all safety net that ensures any string or pattern provided by a user can be matched by at least one
    parser backend. The Result-based error handling in _build_parser_result allows individual sub-parser construction
    failures to be gracefully absorbed (returning Failure(ParserFailure.SYNTAX_ERROR)) rather than crashing the entire
    heuristic construction.

Delegates:
    - _build_parser_result(builder): Wraps a parser builder callable in try/except for _EXPECTED_PARSER_BUILD_ERRORS,
    returning Success(parser) or Failure(ParserFailure.SYNTAX_ERROR). Used to safely attempt construction of each sub-
    parser.
    - importlib.import_module: Dynamically imports cucumber_expression, cfparse, re, and string parser classes at
    build_parsers() time rather than at module import time, avoiding circular dependencies.
    - register_fallback_parser(heuristic): Called at module scope to register this class as the global fallback, so
    StepParser.build uses it when no specific predicate matches.
    - Individual sub-parsers: string_parser.string, cucumber_expression.cucumber_expression, parse_parser.cfparse,
    re_parser.re — each constructed and stored as instance attributes on the heuristic instance.

Cohesion:
    Every function and method in this module serves the heuristic composition strategy: _build_parser_result
    encapsulates safe construction, build_parsers orchestrates lazy sub-parser creation, parser_by_priorities defines
    the priority ordering, and is_matching/parse_arguments/arguments/__str__ implement the StepParser contract by
    delegating through the priority chain. There is no unrelated logic.

Separation:
    - Individual parser backends (string_parser.py, cucumber_expression.py, parse_parser.py, re_parser.py): Each
    implements one specific matching strategy; heuristic.py composes them. Changes to an individual backend's API affect
    only build_parsers(), not the heuristic's delegation pattern.
    - pytest_bdd.parsers.base: Defines the StepParser ABC and registration infrastructure that heuristic uses; heuristic
    does not own the registration mechanism, only participates in it.
    - pytest_bdd.parsers.facade: The heuristic factory function in facade.py delegates to this class's constructor; the
    facade is a thin wrapper.

Main consumers:
    - pytest_bdd.parsers.facade.heuristic: Factory function that instantiates the heuristic class; this is the primary
    user-facing entry point.
    - StepParser.build: Uses heuristic as the _FALLBACK_PARSER_BUILDER, calling heuristic(parserlike) when no registered
    predicate matches.
    - pytest_bdd.steps.manager.StepDefinitionManager.decorator_builder: Indirect consumer via StepParser.build, which
    routes unhandled parserlike objects to the heuristic.

State and side effects:
    Instance-level mutable state: self.format (the original pattern), self.parameter_type_registry (RegistryMode or
    ParameterTypeRegistry), self.string_parser, self.cucumber_expression_parser, self.cfparse_parser, self.re_parser
    (each Optional[StepParser], populated lazily by build_parsers), self.parsers_are_built (boolean guard). Module-level
    side effect: calls register_fallback_parser(heuristic) at import time, mutating base._FALLBACK_PARSER_BUILDER. No
    file/network I/O.

Invariants:
    - build_parsers() must be called (via __init__) before any matching methods are used; parsers_are_built guards
    against redundant reconstruction.
    - At least one sub-parser must be successfully constructed; if all fail, build_parsers raises ParserBuildValueError.
    - parser_by_priorities order (string, cucumber_expression, cfparse, re) defines the matching priority: more specific
    parsers are tried first.
    - The heuristic type attribute is StepDefinitionPatternType.pytest_bdd_heuristic_expression, distinguishing it from
    individual backend pattern types.

Failure semantics:
    - ParserBuildValueError: Raised by build_parsers() if all four sub-parsers fail to construct from the given format.
    This propagates up through __init__ to the caller. Since register_fallback_parser(heuristic) is called at module
    scope, this error can surface when a user provides a pattern that no parser backend can handle.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
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
    Safely executes a parser builder callable (a zero-argument lambda that constructs a StepParser subclass), catching al.

    Responsibility:
        Safely executes a parser builder callable (a zero-argument lambda that constructs a StepParser subclass),
        catching all expected parser construction errors (_EXPECTED_PARSER_BUILD_ERRORS: AttributeError, CantEscape,
        KeyError, ParserBuildValueError, regex_error, TypeError, UndefinedParameterTypeError, ValueError) and converting
        them into a returns.result.Result type: Success(parser) on success, Failure(ParserFailure.SYNTAX_ERROR) on
        failure. This enables the heuristic parser to attempt multiple backends without letting one backend's failure
        crash the entire construction process.

    Reason for existence:
        Extracted as a standalone function (rather than inline try/except in build_parsers) because the error-handling
        pattern is repeated for each of the four sub-parsers. Using Result types from the `returns` library provides a
        clean functional composition pattern where build_parsers can attempt all four builders and check which
        succeeded, rather than using nested try/except blocks or sentinel None values with ambiguous failure semantics.
        The function is also re-exported from parsers.__init__ for use by external code that needs safe parser
        construction.

    Delegates:
        - builder(): The callable is invoked with no arguments; its return value is wrapped in Success on success.
        - _EXPECTED_PARSER_BUILD_ERRORS: The tuple of exception types that are caught and converted to Failure.
        - returns.result.Success / returns.result.Failure: Used to construct the Result type.

    Cohesion:
        This function's sole purpose is to convert exceptions into Result types for parser construction. It operates on
        the builder callable boundary between the heuristic class and individual parser backends.

    Separation:
        - heuristic.build_parsers: Calls _build_parser_result four times (once per sub-parser) and uses .value_or(None)
        to extract the parser or None. The function encapsulates the error-handling pattern; build_parsers encapsulates
        the construction orchestration.

    Main consumers:
        - heuristic.build_parsers: The primary (and currently only) caller; wraps each sub-parser construction in
        _build_parser_result.
        - External code via parsers.__init__ re-export: Available for any code that needs safe parser construction with
        structured error handling.

    State and side effects:
        None, pure function. The builder callable may have side effects (importing modules, constructing objects), but
        _build_parser_result itself has none.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    try:
        return Success(builder())
    except _EXPECTED_PARSER_BUILD_ERRORS:
        return Failure(ParserFailure.SYNTAX_ERROR)


class heuristic(StepParser):  # noqa: N801 intentional API
    """
    Composite StepParser that lazily constructs four sub-parsers (string, cucumber_expression, cfparse, re) in priority o.

    Responsibility:
        Composite StepParser that lazily constructs four sub-parsers (string, cucumber_expression, cfparse, re) in
        priority order and delegates all matching operations to the first sub-parser that succeeds. The type attribute
        is set to StepDefinitionPatternType.pytest_bdd_heuristic_expression. On construction, normalises the format_
        string via normalize_to_string, stores the parameter_type_registry mode (defaulting to RegistryMode.FIXTURE for
        cucumber expression parameter resolution), and immediately calls build_parsers() to construct sub-parsers. Acts
        as the universal fallback parser registered via register_fallback_parser.

    Reason for existence:
        This class is the lynchpin of the "it just works" parser philosophy: users can provide any string pattern
        without specifying a parser type, and the heuristic tries all backends in priority order to find one that can
        parse the pattern. It exists as a separate class (rather than being logic in StepParser.build) because it is
        itself a valid StepParser that wraps sub-parsers, maintains its own state (the four sub-parser attributes), and
        needs to participate in the parser protocol as a first-class entity. Registered as the fallback parser so that
        StepParser.build falls through to it when no specific backend claims the parserlike.

    Delegates:
        - normalize_to_string: Normalises the format_ input if it is a StringRepresentable, str, or bytes, storing the
        result as self.format.
        - build_parsers(): Lazily constructs the four sub-parsers using _build_parser_result for safe error handling.
        - parser_by_priorities (property): Returns the ordered list [string_parser, cucumber_expression_parser,
        cfparse_parser, re_parser] for iteration.
        - is_matching: Uses methodcaller("is_matching", request, name) via map/filter over parser_by_priorities,
        returning True if any sub-parser matches.
        - parse_arguments: Iterates parser_by_priorities, calls parser.parse_arguments on the first matching parser.
        - arguments (property): Chains the arguments from all sub-parsers via itertools.chain and getattr.
        - __str__: Returns str(self.format), the original pattern text.

    Cohesion:
        Every method implements one facet of the composite delegation pattern. The class has no logic beyond
        constructing sub-parsers and delegating to them in priority order. All methods operate on the same instance
        state (self.format, self.*_parser, self.parameter_type_registry, self.parsers_are_built).

    Separation:
        - Individual parser classes (string, cucumber_expression, cfparse, re): Each handles one matching strategy;
        heuristic handles the composite selection. Changes to an individual parser's matching logic do not affect the
        heuristic's delegation pattern.
        - StepParser.build: Handles parserlike-to-constructor dispatch; heuristic is the fallback destination when no
        specific backend matches.
        - _build_parser_result: Handles error containment for individual parser construction; heuristic.build_parsers
        orchestrates the construction of all four.

    Main consumers:
        - StepParser.build: The _FALLBACK_PARSER_BUILDER, invoked when no registered predicate matches the parserlike.
        - pytest_bdd.parsers.facade.heuristic: Factory function that instantiates this class directly when users
        explicitly request the heuristic parser.
        - pytest_bdd.steps.matcher.Matcher: Indirect consumer via parser.is_matching and parser.parse_arguments on the
        heuristic instance.

    State and side effects:
        Instance-level mutable state: self.format (str or object), self.parameter_type_registry (RegistryMode or
        ParameterTypeRegistry), self.string_parser, self.cucumber_expression_parser, self.cfparse_parser, self.re_parser
        (each Optional[StepParser]), self.parsers_are_built (bool). The format is normalised at construction time. Sub-
        parsers are constructed at construction time (via build_parsers). No file/network I/O. No pytest stash access.

    Invariants:
        - At least one sub-parser must be non-None after build_parsers(), enforced by the `if not any(...)` check that
        raises ParserBuildValueError.
        - parsers_are_built is set to True immediately after sub-parsers are constructed and before the validity check.
        - The parser_by_priorities order must remain [string, cucumber_expression, cfparse, re] to maintain stable
        matching priority.
        - The type attribute must remain StepDefinitionPatternType.pytest_bdd_heuristic_expression.

    Failure semantics:
        - ParserBuildValueError: Raised by build_parsers() (called from __init__) if all four sub-parsers fail to
        construct. The caller receives this during heuristic() instantiation. Since the heuristic is the fallback
        parser, this represents a complete failure to parse the given pattern and propagates up through StepParser.build
        to the user's @given/@when/@then decorator.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """

    type = StepDefinitionPatternType.pytest_bdd_heuristic_expression  # type:ignore[attr-defined]  # upstream type stubs missing this attribute

    def __init__(
        self,
        format_: object,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | str | None = RegistryMode.FIXTURE,
    ) -> None:
        """
        Construct a heuristic composite parser.

        Responsibility:
            Constructs a heuristic composite parser. Normalises the format_ input to a string (via normalize_to_string
            if it is a StringRepresentable, str, or bytes), stores the parameter_type_registry mode (defaulting to
            RegistryMode.FIXTURE for cucumber expression parameter type resolution), sets parsers_are_built to False,
            and immediately triggers build_parsers() to lazily construct all four sub-parsers. If all sub-parsers fail
            to construct, ParserBuildValueError propagates to the caller.

        Reason for existence:
            This constructor implements the eager-initialisation strategy: sub-parsers are built immediately so that
            construction failures are surfaced at decoration time (when @given/@when/@then is applied) rather than at
            test execution time. The format normalisation via normalize_to_string ensures that pattern objects from
            various sources (raw strings, StringRepresentable subclasses, bytes) are uniformly handled. The
            parameter_type_registry default of RegistryMode.FIXTURE enables cucumber expressions to resolve parameter
            types from pytest fixtures.

        Delegates:
            - normalize_to_string: Normalises the format_ input if it is a StringRepresentable, str, or bytes instance.
            - build_parsers(): Called immediately to construct and store the four sub-parsers.

        Cohesion:
            Pure initialisation logic: store normalised format, store registry mode, trigger parser construction. All
            three steps serve the single purpose of preparing the heuristic instance for use.

        Separation:
            - build_parsers: Handles the actual sub-parser construction and stores results; __init__ only triggers it
            and stores format/registry_mode.

        Main consumers:
            - pytest_bdd.parsers.facade.heuristic: The facade factory function that calls heuristic(format_,
            parameter_type_registry=...).
            - StepParser.build: Calls heuristic(parserlike) as the fallback builder.

        State and side effects:
            Sets instance attributes: self.format, self.parameter_type_registry, self.parsers_are_built. Calls
            normalize_to_string (pure). Calls build_parsers (mutates self.*_parser and self.parsers_are_built).

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
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
        Lazily imports and constructs all four sub-parsers (string, cucumber_expression, cfparse, re) via dynamic importlib.i.

        Responsibility:
            Lazily imports and constructs all four sub-parsers (string, cucumber_expression, cfparse, re) via dynamic
            importlib.import_module calls, wrapping each construction in _build_parser_result for safe error
            containment. Stores each successfully constructed parser or None on its respective instance attribute.
            Guards against redundant reconstruction via the parsers_are_built sentinel. Raises ParserBuildValueError if
            all four sub-parsers fail to construct.

        Reason for existence:
            Centralises the sub-parser construction orchestration into one method, keeping the lazy import and error-
            containment logic out of __init__ and the delegation methods. The dynamic imports (importlib.import_module
            for each parser module) are needed because these modules themselves import from base.py (to call
            register_parser), creating circular import chains that would fail if imported at module top level. The
            idempotency guard (parsers_are_built) ensures that build_parsers can be called multiple times safely, though
            in practice it is only called from __init__.

        Delegates:
            - importlib.import_module: Dynamically imports each of the four parser modules to obtain their parser
            classes (cucumber_expression, cfparse, re, string).
            - _build_parser_result: Wraps each parser construction in try/except, returning Result[StepParser,
            ParserFailure] which is converted to Optional[StepParser] via .value_or(None).
            - cast: Used for type-narrowing the dynamically imported classes to their TYPE_CHECKING aliases.

        Cohesion:
            Every line in this method serves the single purpose of constructing and storing sub-parsers. The import-and-
            construct pattern is repeated four times with different module/class names, all following the same template.

        Separation:
            - __init__: Triggers build_parsers; this method handles the actual construction.
            - _build_parser_result: Handles error containment for each individual construction; this method orchestrates
            the four attempts.

        Main consumers:
            - __init__: The sole caller; invokes build_parsers() immediately after setting format and parameter_type_registry.

        State and side effects:
            Mutates instance attributes: self.string_parser, self.cucumber_expression_parser, self.cfparse_parser,
            self.re_parser (set to parser or None), self.parsers_are_built (set to True). Side effect: imports four
            parser modules via importlib.import_module. No file/network I/O beyond normal Python imports.

        Failure semantics:
            - ParserBuildValueError: Raised if `not any(self.parser_by_priorities)` after all four construction attempts
            — i.e., every sub-parser returned Failure. This error propagates through __init__ to the caller. It is
            marked `# pragma: no cover` because the fallback heuristic() wrapper ensures at least the string parser can
            always be constructed from a string.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
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
        Returns the ordered list of sub-parsers in priority sequence: [string_parser, cucumber_expression_parser, cfparse_par.

        Responsibility:
            Returns the ordered list of sub-parsers in priority sequence: [string_parser, cucumber_expression_parser,
            cfparse_parser, re_parser]. Each element is either a StepParser instance (if successfully constructed) or
            None (if construction failed). This priority order ensures that more specific and deterministic parsers
            (string, cucumber_expression) are tried before more general ones (cfparse, re), minimising ambiguous
            matches.

        Reason for existence:
            Extracted as a property to provide a single canonical source of the parser priority order, used by
            is_matching, parse_arguments, arguments, and the validity check in build_parsers. If the priority order ever
            needs to change, only this property needs updating.

        Delegates:
            - No delegation: simply returns a list literal of the four instance attributes.

        Cohesion:
            Directly serves the composite delegation pattern: every method that iterates sub-parsers uses this property
            to determine the order.

        Separation:
            - Individual matching methods: Each uses this property to iterate; the property itself has no matching logic.

        Main consumers:
            - is_matching: Uses filter(bool, self.parser_by_priorities) to find matching sub-parsers.
            - parse_arguments: Iterates parser_by_priorities to find the first parser that matches and extracts arguments.
            - arguments: Chains getattr(parser, "arguments", None) across parser_by_priorities.
            - build_parsers: Uses any(self.parser_by_priorities) to verify at least one parser was constructed.

        State and side effects:
            None, pure property. Returns a new list each time from existing instance attributes.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        return [
            self.string_parser,
            self.cucumber_expression_parser,
            self.cfparse_parser,
            self.re_parser,
        ]

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """
        Test whether any sub-parser in priority order matches the given step name.

        Responsibility:
            Tests whether any sub-parser in priority order matches the given step name. Uses operator.methodcaller to
            call is_matching(request, name) on each non-None sub-parser from parser_by_priorities. Returns True as soon
            as the first matching sub-parser is found (via any()), short-circuiting further checks.

        Reason for existence:
            Implements the StepParser.is_matching contract for the composite parser. Uses functional composition (map,
            filter, any) rather than an explicit loop to express the short-circuit matching logic concisely. The
            methodcaller approach avoids lambda overhead and is more readable for repeated method calls with the same
            arguments.

        Delegates:
            - operator.methodcaller("is_matching", request, name): Creates a callable that invokes is_matching on each sub-parser.
            - filter(bool, self.parser_by_priorities): Excludes None entries (failed sub-parsers) before attempting matching.
            - Sub-parser.is_matching: The actual pattern matching is performed by whichever sub-parser's is_matching is called.

        Cohesion:
            Directly implements one of the four required StepParser abstract methods for the composite parser. Uses
            parser_by_priorities to maintain consistent ordering.

        Separation:
            - parse_arguments: Extracts parameters after a match is confirmed; this method only tests for matching.
            - Sub-parser matching logic: Each sub-parser has its own is_matching implementation; this method only routes to them.

        Main consumers:
            - pytest_bdd.steps.matcher.Matcher: Calls parser.is_matching(request, step.text) during candidate filtering.

        State and side effects:
            None, pure method. Does not mutate any instance state.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
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
        Iterate sub-parsers in priority order, calling is_matching on each until one returns True, then delegate to that parser's parse_arguments.

        Responsibility:
            Iterates sub-parsers in priority order, calling is_matching on each until one returns True, then delegates
            to that parser's parse_arguments to extract named parameters. If no sub-parser matches, returns None. Uses a
            for/else construct for clarity: the else branch sets arguments = None when the loop completes without
            breaking.

        Reason for existence:
            Implements the StepParser.parse_arguments contract for the composite parser. The two-phase approach
            (is_matching check followed by parse_arguments call) mirrors the framework-level pattern used by Matcher and
            Definition.get_parameters, ensuring consistency. Unlike is_matching which uses functional composition, this
            method uses an explicit loop because it needs to capture the matching parser reference for the subsequent
            parse_arguments call.

        Delegates:
            - Sub-parser.is_matching: Tests whether each sub-parser matches the step name.
            - Sub-parser.parse_arguments: Extracts parameters from the matching sub-parser, passing through anonymous_group_names.

        Cohesion:
            Directly implements one of the four required StepParser abstract methods. Uses parser_by_priorities for
            ordering and delegates to sub-parsers for actual work.

        Separation:
            - is_matching: Tests matching without extracting; this method both tests and extracts.
            - Sub-parser parse_arguments: Each sub-parser has its own extraction logic; this method only routes.

        Main consumers:
            - pytest_bdd.steps.definition.Definition.get_parameters: Calls parser.parse_arguments(request, step.text,
            anonymous_group_names=...) on the matched definition's parser, which may be a heuristic instance.

        State and side effects:
            None, pure method. Does not mutate any instance state.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
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
        Returns the union of all parameter names across all successfully constructed sub-parsers.

        Responsibility:
            Returns the union of all parameter names across all successfully constructed sub-parsers. Uses
            itertools.chain.from_iterable to flatten the arguments from each sub-parser, with a safety check (getattr
            with default None) for sub-parsers that may not have an arguments attribute. Returns a list of parameter
            name strings.

        Reason for existence:
            Implements the StepParser.arguments property for the composite parser. Unlike is_matching and
            parse_arguments which use only the first matching parser, arguments aggregates across all sub-parsers
            because the framework needs to know all possible parameter names for fixture injection, regardless of which
            specific parser ultimately matches at runtime. The from_iterable + getattr pattern handles the case where
            some sub-parsers are None (failed construction) or lack an arguments attribute.

        Delegates:
            - itertools.chain.from_iterable: Flattens the iterator of argument collections into a single sequence.
            - getattr(parser, "arguments", None): Safely retrieves arguments from each sub-parser, returning None if the
            attribute is missing.

        Cohesion:
            Directly implements one of the four required StepParser abstract methods. Consistent with parser_by_priorities ordering.

        Separation:
            - Sub-parser arguments: Each sub-parser reports its own expected parameter names; this property aggregates them.
            - parse_arguments: Extracts actual values for a match; this property returns expected names in the abstract.

        Main consumers:
            - pytest_bdd.steps.definition.Definition.fixtures_mapped_from_step_definition: Reads parser.arguments to
            determine which fixture mappings are needed.

        State and side effects:
            None, pure property. Does not mutate any instance state.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
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
        Return the string representation of the original pattern format.

        Responsibility:
            Returns the string representation of the original pattern format. If self.format is a string, returns it
            directly; if it is a non-string object (e.g., a compiled regex), str() converts it. This is used for display
            and for populating the StepDefinitionPattern.source field in cucumber_messages.

        Reason for existence:
            Implements the StepParser.__str__ contract. The heuristic parser's string representation is simply the
            original format string, since the heuristic itself has no intrinsic pattern — it delegates to sub-parsers.
            Returning str(self.format) ensures consistent display regardless of which sub-parser ultimately handles
            matching.

        Delegates:
            - str(self.format): Converts the format to its string representation.

        Cohesion:
            Directly implements one of the four required StepParser abstract methods.

        Separation:
            - Sub-parser __str__: Each sub-parser returns its own pattern representation; the heuristic returns the
            original input, not any sub-parser's representation.

        Main consumers:
            - pytest_bdd.steps.definition.Definition.as_message: Uses str(parser) as the pattern source for
            cucumber_messages StepDefinition.
            - Error messages and debug output.

        State and side effects:
            None, pure method. Does not mutate any instance state.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        return str(self.format)


register_fallback_parser(heuristic)
