"""
Defines the core contracts, types, and plugin infrastructure for the step parser subsystem: the StepParserProtocol ru.

Responsibility:
    Defines the core contracts, types, and plugin infrastructure for the step parser subsystem: the StepParserProtocol
    runtime-checkable interface that every parser must satisfy, the StepParser abstract base class with a classmethod
    build() factory for parser dispatch, the parser registry mechanism (register_parser, register_fallback_parser,
    _load_parser_modules) enabling lazy plugin discovery, the RegistryMode enum controlling parameter type registry
    resolution strategy, the ParserBuildValueError for uniform error reporting, and internal protocols
    (_ParseMatchProtocol, _ParserBuilder, _RegexCompiler) for type-safe builder composition. All parser backends
    register themselves here and all consumers obtain parsers through StepParser.build.

Reason for existence:
    This module is the information expert for the parser plugin architecture because it owns the single source of truth
    for parser dispatch: the _PARSER_REGISTRY list of (predicate, builder) pairs, the _FALLBACK_PARSER_BUILDER fallback,
    and the _PARSER_MODULES_LOADED sentinel. It centralises what would otherwise be scattered conditional imports across
    every consumer. The lazy loading strategy in _load_parser_modules (using importlib.import_module for each of the
    five parser backends) ensures that only actually-used parser modules are imported, avoiding circular dependencies
    with the facade module while keeping the dispatch logic in one place. It is kept separate from the concrete parser
    implementations because it defines the abstract contracts they implement—changing the protocol or registry mechanism
    should not require touching individual parser backends.

Delegates:
    - _PARSER_MODULES (tuple): Lists the five parser backend module names (re_parser, parse_parser, cucumber_expression,
    cucumber_regex, heuristic) that self-register via import-time side effects.
    - _load_parser_modules(): Lazily imports all parser backends, ensuring their register_parser calls populate
    _PARSER_REGISTRY before StepParser.build() dispatches. Uses importlib.import_module so imports are deferred until
    first needed.
    - StepParser.build(): Classmethod factory that first checks isinstance(parserlike, StepParserProtocol) for
    passthrough, then iterates _PARSER_REGISTRY predicates, then falls back to _FALLBACK_PARSER_BUILDER, raising
    ParserBuildValueError if nothing matches.
    - _EXPECTED_PARSER_BUILD_ERRORS: Tuple of exception types (AttributeError, CantEscape, KeyError,
    ParserBuildValueError, regex_error, TypeError, UndefinedParameterTypeError, ValueError) that parser builders expect
    and handle during construction.

Cohesion:
    Every entity in this module serves the single purpose of establishing and operating the parser registry
    infrastructure. The protocols (_ParseMatchProtocol, _ParserBuilder, _RegexCompiler) exist only to type-annotate the
    registry callbacks. RegistryMode exists only to parameterise parser construction. ParserBuildValueError exists only
    to signal dispatch failure. The module-level mutable state (_PARSER_REGISTRY, _FALLBACK_PARSER_BUILDER,
    _PARSER_MODULES_LOADED) is exclusively consumed by the registration and build functions.

Separation:
    - facade.py: Contains thin factory functions (parse(), re(), cfparse(), etc.) that are the user-facing API; base.py
    owns the infrastructure those factories depend on but does not re-export them directly.
    - Individual parser modules (re_parser.py, parse_parser.py, cucumber_expression.py, cucumber_regex.py,
    heuristic.py): Each implements one parser backend conforming to StepParserProtocol/StepParser; base.py defines the
    contracts they satisfy and the registry they register with, but does not own their parsing logic.
    - pytest_bdd.steps.definition: Consumes StepParser and StepParserProtocol as the type of Definition.parser, but the
    step definition layer does not own how parsers are built or dispatched.

Main consumers:
    - pytest_bdd.steps.manager.StepDefinitionManager.decorator_builder: Calls StepParser.build(step_parserlike) to
    construct a parser from the user-supplied pattern (string, regex, or parser instance) during @given/@when/@then
    decoration.
    - pytest_bdd.steps.matcher.Matcher: Uses parser.is_matching(request, step.text) at runtime to test each Definition
    against a PickleStep.
    - pytest_bdd.steps.definition.Definition: Stores a StepParser instance and delegates parse_arguments() and arguments
    property calls to it.
    - Individual parser backends: Call register_parser(predicate, builder) at module import time to self-register, and
    register_fallback_parser(heuristic) to set the catch-all.

State and side effects:
    Module-level mutable state: _PARSER_REGISTRY (list, populated by register_parser calls during _load_parser_modules),
    _FALLBACK_PARSER_BUILDER (set once by register_fallback_parser), _PARSER_MODULES_LOADED (boolean sentinel guarding
    idempotent lazy loading). All mutated at import time; no runtime mutation after initialisation. No file/network I/O.
    No pytest stash access.

Invariants:
    - register_parser must only be called during module import (not at runtime), because _load_parser_modules is guarded
    by _PARSER_MODULES_LOADED and never re-executed.
    - The _PARSER_REGISTRY order determines dispatch priority: earlier registrations are checked first in StepParser.build.
    - If _FALLBACK_PARSER_BUILDER remains None and no registered predicate matches, StepParser.build raises
    ParserBuildValueError.
    - Every object returned by a registered builder must satisfy isinstance(obj, StepParserProtocol).

Failure semantics:
    - ParserBuildValueError: Raised by StepParser.build when no registered predicate matches the given parserlike and no
    fallback is set. Callers should treat this as a configuration error indicating an unsupported step pattern format.
    - NotImplementedError: Raised by abstract methods (parse_arguments, arguments, is_matching, __str__) on StepParser
    when a subclass fails to implement them. Indicates an incomplete parser implementation.

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
    Register a (predicate, builder) pair into the module-level _PARSER_REGISTRY list, enabling lazy parser backend discovery.

    Responsibility:
        Registers a (predicate, builder) pair into the module-level _PARSER_REGISTRY list, enabling lazy parser backend
        discovery. Each parser backend calls this at import time with a predicate that tests whether a given parserlike
        object (e.g., a string, compiled regex, or parser instance) should be handled by that backend, and a builder
        callable that constructs the appropriate StepParser subclass from the parserlike.

    Reason for existence:
        This function is the registration entry point for the parser plugin architecture. It exists as a separate
        function (rather than having backends directly append to _PARSER_REGISTRY) to provide a controlled, documented
        API that ensures consistent (predicate, builder) tuple structure and allows future instrumentation (e.g.,
        logging, validation) to be added at the registration boundary without modifying each backend.

    Delegates:
        - No delegation: appends the (predicate, builder) tuple directly to _PARSER_REGISTRY.

    Cohesion:
        The function does exactly one thing: append to the registry. It shares state (_PARSER_REGISTRY) with
        register_fallback_parser and StepParser.build, forming a tightly cohesive trio of registration/dispatch
        operations.

    Separation:
        - register_fallback_parser: Sets the _FALLBACK_PARSER_BUILDER global; this function populates _PARSER_REGISTRY.
        They are separate because fallback registration has different semantics (only one fallback, checked last) vs.
        priority-ordered predicates.

    Main consumers:
        - Individual parser backend modules (re_parser.py, parse_parser.py, cucumber_expression.py, cucumber_regex.py):
        Call register_parser at module scope to self-register during _load_parser_modules.
        - pytest_bdd.parsers.heuristic: Calls register_fallback_parser to set itself as the catch-all parser.

    State and side effects:
        Mutates the module-level _PARSER_REGISTRY list by appending one (predicate, builder) tuple. No other side effects.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """
    _PARSER_REGISTRY.append((predicate, builder))


def register_fallback_parser(builder: Callable[[StepParserLike], object]) -> None:
    """
    Set the module-level _FALLBACK_PARSER_BUILDER to the given builder callable, establishing the catch-all parser that is used when no registered parser claims the format.

    Responsibility:
        Sets the module-level _FALLBACK_PARSER_BUILDER to the given builder callable, establishing the catch-all parser
        that StepParser.build will use when no registered predicate matches the parserlike. Only one fallback is
        permitted; subsequent calls overwrite the previous.

    Reason for existence:
        Exists separately from register_parser because the fallback has fundamentally different dispatch semantics: it
        is checked last (after all registered predicates fail), it is not paired with a predicate, and at most one
        fallback is meaningful. Keeping it as a distinct function makes the contract explicit and prevents accidental
        predicate-less entries in _PARSER_REGISTRY.

    Delegates:
        - No delegation: directly assigns to the _FALLBACK_PARSER_BUILDER global.

    Cohesion:
        Operates on the same module-level state (_FALLBACK_PARSER_BUILDER) that StepParser.build reads. Tightly coupled
        to the build dispatch flow.

    Separation:
        - register_parser: Populates _PARSER_REGISTRY with priority-ordered (predicate, builder) pairs; this function
        sets the unconditional last-resort builder.

    Main consumers:
        - pytest_bdd.parsers.heuristic: Calls register_fallback_parser(heuristic) at module scope to register itself as
        the universal fallback that tries multiple parser backends in priority order.

    State and side effects:
        Mutates the module-level _FALLBACK_PARSER_BUILDER global via the `global` statement. No other side effects.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """
    global _FALLBACK_PARSER_BUILDER
    _FALLBACK_PARSER_BUILDER = builder


def _load_parser_modules() -> None:
    """
    Lazily imports all five parser backend modules (listed in _PARSER_MODULES) exactly once, guarded by the _PARSER_MODUL.

    Responsibility:
        Lazily imports all five parser backend modules (listed in _PARSER_MODULES) exactly once, guarded by the
        _PARSER_MODULES_LOADED boolean sentinel. Each imported module's top-level code calls register_parser to populate
        _PARSER_REGISTRY, making all parser backends available for dispatch in StepParser.build without eagerly
        importing them at package initialisation time.

    Reason for existence:
        This function breaks what would otherwise be a circular import problem: the facade module (__init__.py) imports
        from base.py and from individual parser modules, while individual parser modules import from base.py to call
        register_parser. By using importlib.import_module inside a guarded function rather than top-level imports,
        base.py avoids importing any parser backend until StepParser.build is actually called, and each backend's
        register_parser call executes safely because base.py is fully loaded by then.

    Delegates:
        - importlib.import_module: Performs the actual dynamic import for each module name in _PARSER_MODULES,
        triggering each backend's module-level register_parser call as a side effect.

    Cohesion:
        This function's sole purpose is to populate _PARSER_REGISTRY from the five known backends. It shares the
        _PARSER_MODULES_LOADED guard with no other function and exists only to serve StepParser.build.

    Separation:
        - StepParser.build: Calls _load_parser_modules before iterating _PARSER_REGISTRY; this function handles the
        loading, build handles the dispatch. Separated so build's dispatch logic is not cluttered with import machinery.

    Main consumers:
        - StepParser.build: The only caller; invokes _load_parser_modules() before dispatching to registered predicates.

    State and side effects:
        Mutates _PARSER_MODULES_LOADED to True after first successful load (idempotent guard). Side effect: triggers
        import of five parser modules, each of which calls register_parser, mutating _PARSER_REGISTRY. No file/network
        I/O beyond normal Python import mechanics.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    global _PARSER_MODULES_LOADED
    if _PARSER_MODULES_LOADED:
        return
    for module_name in _PARSER_MODULES:
        importlib.import_module(module_name)
    _PARSER_MODULES_LOADED = True


class _ParseMatchProtocol(Protocol):
    """
    Structural typing protocol describing the result of a successful step parse: a `named` dict mapping parameter names t.

    Responsibility:
        Structural typing protocol describing the result of a successful step parse: a `named` dict mapping parameter
        names to extracted values and a `fixed` sequence of positional match groups. Used internally to type-annotate
        the return value of parser builder callables without coupling to any specific parser library's return type.

    Reason for existence:
        Exists as a Protocol rather than a concrete class because each parser backend (re, parse, cucumber-expression)
        returns different match objects with different APIs. This protocol captures only the two attributes that the
        framework needs (named groups dict and positional groups sequence), allowing type-safe composition of the parser
        registry callbacks without imposing a common base class on otherwise unrelated match result types.

    Delegates:
        - No delegation: pure protocol definition with no implementation.

    Cohesion:
        Defined alongside _ParserBuilder and _RegexCompiler as part of the internal type system for parser registry
        callbacks. All three protocols describe facets of the same parser construction pipeline.

    Separation:
        - _ParserBuilder: Describes the callable that constructs a parser; this protocol describes the match result the
        parser produces.
        - StepParserProtocol: The public, runtime-checkable protocol that all parsers must satisfy; this is an internal
        type for builder return values only.

    Main consumers:
        - Parser builder callables registered via register_parser: Their return type is expected to satisfy this
        protocol so that the framework can extract named and positional parameters.

    State and side effects:
        None, pure protocol definition.

    Invariants:
        - The `named` dict keys must correspond to the parameter names used in the step definition function signature.
        - The `fixed` sequence must contain positional match groups in the order they appear in the pattern.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    named: dict[str, object]
    fixed: Sequence[object]


class _ParserBuilder(Protocol):
    """
    Structural typing protocol describing a callable that constructs a parser object from a format string and optional ar.

    Responsibility:
        Structural typing protocol describing a callable that constructs a parser object from a format string and
        optional arguments. The __call__ signature accepts a `format_` string plus *args/**kwargs and returns an opaque
        object representing the compiled parser. Used to type-annotate builder callables in _PARSER_REGISTRY entries and
        _FALLBACK_PARSER_BUILDER.

    Reason for existence:
        Exists as a Protocol because each parser backend has a different constructor signature (cucumber_expression
        accepts parameter_type_registry, re accepts flags, etc.). This protocol captures the common minimum
        contract—accept a format string and produce a parser object—while allowing extra keyword arguments to be passed
        through via **kwargs, enabling type-safe registration without homogenising diverse constructor APIs.

    Delegates:
        - No delegation: pure protocol definition. The __call__ method is abstract (ellipsis body).

    Cohesion:
        Part of the internal protocol trio (_ParseMatchProtocol, _ParserBuilder, _RegexCompiler) that defines the type
        contracts for the parser registry system. Each describes one role in the parser construction pipeline.

    Separation:
        - _RegexCompiler: Describes a callable that compiles regex patterns specifically; this describes a general
        parser builder.
        - register_parser: Accepts (predicate, builder) where builder must satisfy this protocol.

    Main consumers:
        - register_parser: The `builder` parameter is typed as Callable[[StepParserLike], object] but conceptually
        satisfies this protocol.
        - register_fallback_parser: The `builder` parameter similarly satisfies this protocol.

    State and side effects:
        None, pure protocol definition.

    Invariants:
        - The returned object must support the operations that the framework performs on it (typically .parse() or
        equivalent), though the exact interface is enforced by the concrete parser classes, not this protocol.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    def __call__(self, format_: str, *args: object, **kwargs: object) -> object:
        """
        Construct and return a parser object from the given format string and optional arguments.

        Responsibility:
            Constructs and returns a parser object from the given format string and optional arguments. The returned
            object is opaque to this protocol but is expected to be usable by the concrete StepParser subclass that
            wraps it.

        Reason for existence:
            Defines the callable interface that every registered parser builder must satisfy: accept a format_ string as
            the first positional argument for the step pattern, with *args and **kwargs for backend-specific
            configuration. This uniform signature enables StepParser.build to call any registered builder with a
            consistent invocation pattern.

        Delegates:
            - No delegation: abstract protocol method (ellipsis body).

        Cohesion:
            The single abstract method of the _ParserBuilder protocol; exists solely to define the builder callable contract.

        Separation:
            - _RegexCompiler.__call__: Returns re.Pattern[str] specifically; this returns a generic object.

        Main consumers:
            - StepParser.build: Calls builder(parserlike) where the builder satisfies this protocol.

        State and side effects:
            None, abstract protocol method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...


class _RegexCompiler(Protocol):
    """
    Structural typing protocol describing a callable that compiles a regex pattern string into a compiled re.Pattern[str].

    Responsibility:
        Structural typing protocol describing a callable that compiles a regex pattern string into a compiled
        re.Pattern[str] object. The __call__ signature accepts a `pattern` string plus optional *args/**kwargs (e.g.,
        regex flags) and returns a typed compiled regex. Used internally to type-annotate regex compilation callbacks
        within parser builders.

    Reason for existence:
        Exists as a separate Protocol from _ParserBuilder because regex compilation is a distinct step in the parser
        construction pipeline: some parsers (re, cucumber_regex) compile a regex and then wrap it, while others (parse,
        cucumber_expression) use entirely different matching engines. Separating this protocol allows parser builders
        that do compile regexes to be type-checked for that specific behaviour without forcing all builders to conform
        to a regex-centric interface.

    Delegates:
        - No delegation: pure protocol definition.

    Cohesion:
        Part of the internal protocol trio alongside _ParseMatchProtocol and _ParserBuilder. All three define type
        contracts for the parser registry infrastructure.

    Separation:
        - _ParserBuilder: Builds a parser object from a format string; this protocol specifically compiles regex patterns.
        - re.compile: The standard library function that naturally satisfies this protocol.

    Main consumers:
        - Parser builder internals in re_parser.py and cucumber_regex.py: Accept or use callables satisfying this
        protocol for regex compilation.

    State and side effects:
        None, pure protocol definition.

    Invariants:
        - The returned re.Pattern[str] must be a compiled regex ready for .match() or .search() operations.
        - The `pattern` argument must be a valid regex string; invalid patterns should raise re.error.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    def __call__(self, pattern: str, *args: object, **kwargs: object) -> _RePattern[str]:
        """
        Compiles a regex pattern string into a typed re.Pattern[str] object, accepting optional positional and keyword argume.

        Responsibility:
            Compiles a regex pattern string into a typed re.Pattern[str] object, accepting optional positional and
            keyword arguments (typically regex flags like re.IGNORECASE). Returns the compiled pattern for use in step
            matching operations.

        Reason for existence:
            Defines the callable interface for regex compilation within the parser infrastructure. This is the single
            abstract method of _RegexCompiler, ensuring that any callable used for regex compilation in parser builders
            has a consistent signature accepting a pattern string and returning a compiled Pattern.

        Delegates:
            - No delegation: abstract protocol method (ellipsis body).

        Cohesion:
            The sole method of _RegexCompiler; exists only to define this protocol's contract.

        Separation:
            - _ParserBuilder.__call__: Returns a generic parser object; this returns re.Pattern[str] specifically.

        Main consumers:
            - Regex-based parser builders (re_parser, cucumber_regex) that accept or wrap regex compilation callables.

        State and side effects:
            None, abstract protocol method. Concrete implementations (e.g., re.compile) may cache compiled patterns internally.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...


class ParserBuildValueError(ValueError):
    """
    Signals that StepParser.build() could not construct a parser for the given parserlike object because no registered pr.

    Responsibility:
        Signals that StepParser.build() could not construct a parser for the given parserlike object because no
        registered predicate matched and no fallback parser was configured. Extends ValueError to integrate naturally
        with Python's exception hierarchy while providing a semantically distinct error type that callers can catch
        specifically to handle unsupported parser formats.

    Reason for existence:
        Exists as a distinct exception class (rather than using plain ValueError) so that consumers of StepParser.build
        can catch ParserBuildValueError specifically to distinguish "unsupported parser format" from other ValueError
        conditions that might arise during parser construction (e.g., invalid regex syntax wrapped in
        _EXPECTED_PARSER_BUILD_ERRORS). The __init__ formats a descriptive message including the offending format_
        value, aiding debugging.

    Delegates:
        - super().__init__(): Delegates to ValueError's constructor with a formatted error message.

    Cohesion:
        Tightly coupled to StepParser.build as its primary failure mode. Lives in base.py alongside the build logic it serves.

    Separation:
        - _EXPECTED_PARSER_BUILD_ERRORS: A tuple of exception types that parser builders are expected to catch and
        handle internally; ParserBuildValueError is included in this tuple so that builder failures during heuristic
        fallback are properly contained.

    Main consumers:
        - StepParser.build: Raises ParserBuildValueError when dispatch fails.
        - pytest_bdd.parsers.heuristic._build_parser_result: Catches _EXPECTED_PARSER_BUILD_ERRORS (which includes
        ParserBuildValueError) and converts to Failure(ParserFailure.SYNTAX_ERROR).

    State and side effects:
        None beyond standard exception state (message string). Immutable after construction.

    Invariants:
        - The format_ argument must be the original parserlike object that failed to match, preserved for diagnostic purposes.
        - Must always be raised with a non-None format_ to ensure the error message is informative.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    def __init__(self, format_: object) -> None:
        """
        Construct a ParserBuildValueError with a formatted message indicating that no parser could be built for the given format.

        Responsibility:
            Constructs a ParserBuildValueError with a formatted message indicating that no parser could be built for the
            given format_ object. Delegates to ValueError.__init__ with the message "Unable build parser for format
            {format_}" (note: original source has a grammatical typo "Unable build" — preserved for backward
            compatibility).

        Reason for existence:
            Exists to encapsulate the error message formatting so that all raise sites in StepParser.build produce a
            consistent, informative error message without duplicating the format string. The single-argument constructor
            accepts the raw parserlike object and handles string formatting internally.

        Delegates:
            - super().__init__(): Passes the formatted error message to ValueError's constructor.

        Cohesion:
            The sole constructor of ParserBuildValueError; serves only to format and delegate to the parent class.

        Separation:
            - StepParser.build: The only raise site for this exception; build constructs the error, this class formats the message.

        Main consumers:
            - StepParser.build: Raises ParserBuildValueError(parserlike) when dispatch fails.

        State and side effects:
            None beyond standard exception initialisation.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        super().__init__(f"Unable build parser for format {format_}")


@runtime_checkable
class StepParserProtocol(Protocol):
    """
    Runtime-checkable Protocol defining the interface that every step parser must satisfy: a `type` attribute declaring t.

    Responsibility:
    Runtime-checkable Protocol defining the interface that every step parser must satisfy: a `type` attribute declaring
    the StepDefinitionPatternType (defaulting to pytest_bdd_other_expression), a `parse_arguments` method that extracts
    named parameters from a step name given a FixtureRequest, an `arguments` property returning the collection of
    expected parameter names, an `is_matching` method testing whether a step name matches the parser's pattern, and a
    `__str__` method returning the pattern source text. Decorated with @runtime_checkable so isinstance() checks work at
    runtime for parser passthrough in StepParser.build.

    Reason for existence:
        This is the foundational contract of the entire parser subsystem. It exists as a Protocol rather than an ABC
        because parser implementations come from diverse libraries (re, parse, cucumber-expressions) that cannot share a
        common base class. The Protocol allows structural subtyping: any object with the right attributes satisfies the
        contract without explicit inheritance. It is kept in base.py because base.py is the architectural root of the
        parsers package—everything else depends on this protocol, and it depends only on model types
        (StepDefinitionPatternType) and pytest types (FixtureRequest).

    Delegates:
        - No delegation: pure protocol definition with abstract (ellipsis) method bodies.

    Cohesion:
        All five members (type, parse_arguments, arguments, is_matching, __str__) are the complete set of operations the
        framework performs on any parser. Adding a new parser backend requires implementing exactly these members and
        nothing else.

    Separation:
        - StepParser (ABC): Provides default implementations and the build() classmethod factory. StepParserProtocol
        defines the structural contract; StepParser provides the infrastructure. They are separate because Protocol
        enables isinstance() checks without inheritance, while ABC provides shared behaviour.
        - pytest_bdd.model.message_extension.StepDefinitionPatternType: The enum used for parser.type; defined in the
        model layer (order 3) because pattern types are a domain concept shared across parsing and step_definition
        layers.

    Main consumers:
        - StepParser.build: Checks isinstance(parserlike, StepParserProtocol) as the fast path for already-constructed parsers.
        - pytest_bdd.steps.definition.Definition: Stores a StepParserProtocol-compliant object as its parser attribute.
        - pytest_bdd.steps.matcher.Matcher: Calls parser.is_matching() and parser.parse_arguments() at runtime.
        - Every concrete parser class (in re_parser, parse_parser, cucumber_expression, cucumber_regex, heuristic,
        string_parser): Implements this protocol.

    State and side effects:
        None, pure protocol definition. No mutable state, no I/O.

    Invariants:
        - parser.type must be either a StepDefinitionPatternType enum value or a string convertible to one.
        - parse_arguments must return either a dict[str, object] of extracted parameters or None if the step does not match.
        - is_matching must be consistent with parse_arguments: if is_matching returns True, parse_arguments must return
        a non-None dict.
        - __str__ must return the original pattern source text used to construct the parser.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """

    type: StepDefinitionPatternType | str = StepDefinitionPatternType.pytest_bdd_other_expression  # type:ignore[attr-defined]  # upstream type stubs missing this attribute

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object] | None:
        """
        Extract named parameter values from a Gherkin step name by applying the parser's pattern matching.

        Responsibility:
            Extracts named parameter values from a Gherkin step name by applying the parser's pattern matching. Accepts
            the pytest FixtureRequest for context (e.g., accessing fixtures for parameter type conversion in cucumber
            expressions), the step `name` text to parse, and optional `anonymous_group_names` for regex-based parsers
            that capture unnamed groups. Returns a dict mapping parameter names to extracted values, or None if the step
            does not match the pattern.

        Reason for existence:
            This is the core parameter extraction contract. It exists as a separate method from is_matching because
            matching and extraction are distinct operations: is_matching is a cheaper boolean check used for filtering
            candidate definitions, while parse_arguments performs the full extraction only on confirmed matches. The
            FixtureRequest parameter enables cucumber-expression parsers to resolve parameter types from the pytest
            fixture and configuration context.

        Delegates:
            - No delegation at the protocol level: each concrete parser implements its own extraction logic.
            Implementations typically delegate to underlying library functions (re.match, parse.parse, cucumber-
            expressions match).

        Cohesion:
            One of the five core protocol methods. Together with is_matching, it forms the two-phase match-then-extract
            pattern used by Matcher and Definition.get_parameters.

        Separation:
            - is_matching: Tests whether the step name matches; this method extracts the matched parameters. Separated
            for performance: is_matching is called for every definition in the registry, parse_arguments only for the
            winning match.

        Main consumers:
            - pytest_bdd.steps.definition.Definition.get_parameters: Calls self.parser.parse_arguments(request,
            step.text, anonymous_group_names=self.anonymous_group_names) to obtain the parameter dict for step
            execution.
            - pytest_bdd.parsers.heuristic.heuristic.parse_arguments: Delegates to the first sub-parser whose
            is_matching returns True.

        State and side effects:
            None, abstract protocol method. Concrete implementations are typically pure functions of their inputs.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...  # pragma: no cover -- abstract protocol method

    @property
    def arguments(self) -> Collection[str]:
        """
        Returns the collection of parameter names that this parser expects to extract from a matching step name.

        Responsibility:
            Returns the collection of parameter names that this parser expects to extract from a matching step name.
            These names are used by the step definition framework to determine which pytest fixtures to inject and which
            parameter values to pass to the step function.

        Reason for existence:
            Separated from parse_arguments because parameter names are a static property of the parser (derived from the
            pattern at construction time), not a dynamic property of a particular match. The framework needs to know
            expected parameter names before any step is executed (e.g., for fixture injection during test collection),
            making a property the correct interface.

        Delegates:
            - No delegation at the protocol level. Concrete implementations derive argument names from their compiled
            patterns (e.g., regex named groups, parse format fields, cucumber expression parameter names).

        Cohesion:
            One of the five core protocol members. Together with parse_arguments and is_matching, it enables the full
            step-matching lifecycle.

        Separation:
            - parse_arguments: Returns actual values for a specific match; this property returns the expected parameter
            names in the abstract.

        Main consumers:
            - pytest_bdd.steps.definition.Definition.fixtures_mapped_from_step_definition: Reads self.parser.arguments
            to determine which parameter names need fixture mappings.
            - pytest_bdd.parsers.heuristic.heuristic.arguments: Chains the arguments from all sub-parsers.

        State and side effects:
            None, abstract protocol property. Concrete implementations are typically pure computations from the compiled pattern.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...  # pragma: no cover -- abstract protocol method

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """
        Test whether the given Gherkin step `name` text matches this parser's pattern, using the FixtureRequest for context-dependent matching.

        Responsibility:
            Tests whether the given Gherkin step `name` text matches this parser's pattern, using the FixtureRequest for
            context (e.g., to resolve parameter types that affect matching behaviour). Returns True if the step matches
            and parameters can be extracted, False otherwise. This is the cheaper check called during candidate
            filtering before the full parse_arguments extraction.

        Reason for existence:
            Separated from parse_arguments for performance: the Matcher iterates over all definitions in the registry
            calling is_matching on each, and only calls parse_arguments on the winning match. Having a dedicated boolean
            check avoids the overhead of constructing parameter dicts for non-matching candidates. The FixtureRequest
            parameter is needed because some parser backends (cucumber expressions) use the request's fixture context to
            resolve parameter types that affect whether a match is valid.

        Delegates:
            - No delegation at the protocol level. Concrete implementations delegate to their underlying matching
            engines (regex fullmatch, parse library match, cucumber-expression match).

        Cohesion:
            One of the five core protocol methods. Forms the first phase of the two-phase match-then-extract pattern
            with parse_arguments.

        Separation:
            - parse_arguments: Extracts parameters from a matching step; this method performs the cheaper boolean check.
            - Matcher.strict_matcher / Matcher.unspecified_matcher / Matcher.liberal_matcher: Call parser.is_matching as
            part of their step-type-aware matching strategies.

        Main consumers:
            - pytest_bdd.steps.matcher.Matcher: Calls parser.is_matching(request, step.text) in strict_matcher,
            unspecified_matcher, and liberal_matcher to filter candidate definitions.
            - pytest_bdd.parsers.heuristic.heuristic.is_matching: Delegates to sub-parsers' is_matching until one returns True.

        State and side effects:
            None, abstract protocol method. Concrete implementations should be pure functions of their inputs; no side effects.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...  # pragma: no cover -- abstract protocol method

    def __str__(self) -> str:
        """
        Return the original pattern source text that was used to construct this parser.

        Responsibility:
            Returns the original pattern source text that was used to construct this parser. This string representation
            is used for display purposes (error messages, reports, debug output) and as the source text in
            cucumber_messages StepDefinitionPattern messages.

        Reason for existence:
            Required as part of the protocol because the framework needs a canonical string representation of every
            parser for reporting (Cucumber JSON, pretty printer, error messages) and for the Definition.as_message
            method which uses str(self.parser) as the StepDefinitionPattern.source. Making it part of the protocol
            ensures every parser provides a meaningful string form.

        Delegates:
            - No delegation at the protocol level. Concrete implementations typically return the original format string
            or compiled pattern.pattern.

        Cohesion:
            One of the five core protocol members. Provides the display/identity contract for parsers.

        Separation:
            - Definition.as_message: Uses str(self.parser) as the source for the StepDefinitionPattern message field.

        Main consumers:
            - pytest_bdd.steps.definition.Definition.as_message: Calls str(self.parser) to populate the pattern source
            in cucumber_messages StepDefinition.
            - Error formatting and debug logging throughout the framework.

        State and side effects:
            None, abstract protocol method. Must be pure and idempotent.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        ...  # pragma: no cover -- abstract protocol method


class RegistryMode(Enum):
    """
    Enum controlling how the cucumber-expression ParameterTypeRegistry is resolved during parser construction.

    Responsibility:
        Enum controlling how the cucumber-expression ParameterTypeRegistry is resolved during parser construction. NEW
        creates a fresh ParameterTypeRegistry per parser, GLOBAL uses a shared global registry (stored on pytest config
        stash), FIXTURE resolves the registry from a pytest fixture named `parameter_type_registry`, and NOT_DEFINED
        (None) signals no explicit mode was set. Used as the default value for the parameter_type_registry parameter in
        parser constructors.

    Reason for existence:
        Exists as an enum rather than a plain string to provide type safety and discoverability for the four registry
        resolution strategies. Each value maps to a distinct code path in the cucumber_expression parser's __init__, and
        using an enum ensures that invalid modes are caught at import time rather than at runtime deep inside parser
        construction. Kept in base.py because it is a fundamental configuration concept shared across all parser
        backends that use cucumber expressions.

    Delegates:
        - No delegation: simple enum with four members and no methods.

    Cohesion:
        Directly serves the parser construction flow: every parser constructor that accepts parameter_type_registry uses
        this enum to interpret the argument. It is part of the parser infrastructure alongside StepParserProtocol and
        the registry functions.

    Separation:
        - pytest_bdd.steps.definition.Definition: Does not reference RegistryMode directly; it receives an already-
        constructed parser with the registry mode resolved.
        - cucumber_expression parser: The primary consumer that switches on RegistryMode values.

    Main consumers:
        - pytest_bdd.parsers.cucumber_expression._CucumberExpression.__init__: Switches on the RegistryMode value to
        determine how to obtain the ParameterTypeRegistry.
        - pytest_bdd.parsers.heuristic.heuristic.__init__: Passes RegistryMode.FIXTURE as the default
        parameter_type_registry to the cucumber_expression sub-parser.
        - pytest_bdd.parsers.facade: Passes through registry mode from user-facing factory functions.

    State and side effects:
        None, immutable enum.

    Invariants:
        - NOT_DEFINED must always be None to allow None-as-default semantics in function signatures.
        - The string values ("NEW", "GLOBAL", "FIXTURE") must match the logic in cucumber_expression parser that
        switches on them.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """

    NEW = "NEW"
    GLOBAL = "GLOBAL"
    FIXTURE = "FIXTURE"
    NOT_DEFINED = None


class StepParser(StepParserProtocol, ABC):
    """
    Abstract base class that combines the StepParserProtocol structural contract with default NotImplementedError-raising.

    Responsibility:
        Abstract base class that combines the StepParserProtocol structural contract with default NotImplementedError-
        raising implementations of parse_arguments, arguments (property), is_matching, and __str__, forcing concrete
        subclasses to implement all four. Additionally provides the classmethod build() factory that implements the
        parser registry dispatch: accepts any parserlike object, returns it directly if it already satisfies
        StepParserProtocol, otherwise iterates the registered (predicate, builder) pairs and falls back to the
        registered fallback parser, raising ParserBuildValueError if nothing matches.

    Reason for existence:
        Exists as an ABC separate from the Protocol because it provides two things the Protocol cannot: (1) default
        abstractmethod implementations that produce clear NotImplementedError messages when a subclass fails to
        implement them, serving as documentation and safe failure, and (2) the build() classmethod that is the single
        entry point for constructing parsers from arbitrary user input. The Protocol enables isinstance() structural
        checks; the ABC provides infrastructure. Both are needed because Python's Protocol and ABC serve complementary
        roles.

    Delegates:
        - StepParserProtocol: Inherited Protocol interface with default type attribute.
        - _load_parser_modules(): Called by build() to ensure all parser backends have registered before dispatch.
        - _PARSER_REGISTRY: Iterated by build() to find a matching (predicate, builder) pair.
        - _FALLBACK_PARSER_BUILDER: Used by build() as last-resort builder when no predicate matches.
        - ParserBuildValueError: Raised by build() when dispatch completely fails.

    Cohesion:
        Every abstract method directly serves the StepParserProtocol contract. The build() classmethod directly serves
        the parser construction concern. No unrelated logic.

    Separation:
        - StepParserProtocol: The runtime-checkable Protocol that enables isinstance() passthrough. StepParser inherits
        from it to unify the two type hierarchies.
        - Individual parser classes (heuristic, re, parse, cfparse, cucumber_expression, cucumber_regex, string):
        Concrete subclasses that implement the abstract methods.

    Main consumers:
        - pytest_bdd.parsers.facade.StepParser: The public re-export of this class.
        - pytest_bdd.steps.manager.StepDefinitionManager.decorator_builder: Calls StepParser.build(step_parserlike) to
        construct the parser for a new Definition.
        - pytest_bdd.steps.definition.Definition: Stores a StepParser instance in its parser field.
        - Concrete parser subclasses: Inherit from StepParser to get the build() factory and abstract method stubs.

    State and side effects:
        None at the instance level (abstract, no __init__). The build() classmethod triggers _load_parser_modules()
        which has import side effects (populates _PARSER_REGISTRY).

    Invariants:
        - Every concrete subclass MUST implement parse_arguments, arguments, is_matching, and __str__.
        - build() must be called rather than directly instantiating parser subclasses, to ensure parserlike objects that
        already satisfy the protocol are passed through without re-wrapping.

    Failure semantics:
        - NotImplementedError: Raised by abstract methods when a subclass fails to implement them. Indicates an
        incomplete parser implementation.
        - ParserBuildValueError: Raised by build() when no registered predicate matches the parserlike and no fallback
        is set. Callers should treat this as a configuration error.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5
    """

    @abstractmethod
    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object] | None:
        """
        Abstract method that concrete parser subclasses must override to extract named parameter values from a Gherkin step n.

        Responsibility:
            Abstract method that concrete parser subclasses must override to extract named parameter values from a
            Gherkin step name. Raises NotImplementedError if not overridden. Accepts the pytest FixtureRequest for
            context (parameter type resolution), the step `name` text, and optional anonymous_group_names for regex-
            based parsers with unnamed capture groups.

        Reason for existence:
            Defined as abstractmethod here (rather than relying solely on the Protocol's ellipsis) to ensure that any
            concrete StepParser subclass that forgets to implement parse_arguments gets a clear NotImplementedError at
            call time rather than a silent AttributeError or unexpected Protocol behaviour. The ABC enforcement provides
            a safety net for internal parser development.

        Delegates:
            - No delegation: raises NotImplementedError. Concrete subclasses delegate to their respective parsing libraries.

        Cohesion:
            One of the four abstract methods that every StepParser subclass must implement. Forms the core extraction contract.

        Separation:
            - StepParserProtocol.parse_arguments: The Protocol-level declaration with ellipsis body; this is the ABC-
            level enforcement with NotImplementedError.

        Main consumers:
            - pytest_bdd.steps.definition.Definition.get_parameters: Calls parser.parse_arguments() on the matched definition.
            - pytest_bdd.parsers.heuristic.heuristic.parse_arguments: Delegates to sub-parser parse_arguments.

        State and side effects:
            None in the abstract implementation. Concrete implementations should be pure functions.

        Failure semantics:
            - NotImplementedError: Raised if a concrete subclass fails to override this method. Callers should never
            encounter this in production; it indicates a bug in parser implementation.

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
        raise NotImplementedError  # pragma: no cover -- abstract subclass hook

    @property
    @abstractmethod
    def arguments(self) -> Collection[str]:
        """
        Abstract property that concrete parser subclasses must override to return the collection of parameter names this pars.

        Responsibility:
            Abstract property that concrete parser subclasses must override to return the collection of parameter names
            this parser expects to extract. Raises NotImplementedError if not overridden. Used by the step definition
            framework to determine fixture injection needs.

        Reason for existence:
            Defined as abstractmethod here for the same reason as parse_arguments: to provide a clear
            NotImplementedError safety net for incomplete parser implementations, complementing the Protocol-level
            declaration with ABC enforcement.

        Delegates:
            - No delegation: raises NotImplementedError. Concrete subclasses derive argument names from their compiled patterns.

        Cohesion:
            One of the four abstract methods that every StepParser subclass must implement.

        Separation:
            - StepParserProtocol.arguments: The Protocol-level property with ellipsis body; this is the ABC-level enforcement.

        Main consumers:
            - pytest_bdd.steps.definition.Definition.fixtures_mapped_from_step_definition: Reads parser.arguments to
            determine fixture mappings.

        State and side effects:
            None in the abstract implementation.

        Failure semantics:
            - NotImplementedError: Raised if a concrete subclass fails to override this property. Indicates an
            incomplete parser implementation.

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
        raise NotImplementedError  # pragma: no cover -- abstract subclass hook

    @abstractmethod
    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """
        Abstract method that concrete parser subclasses must override to test whether a Gherkin step name matches this parser.

        Responsibility:
            Abstract method that concrete parser subclasses must override to test whether a Gherkin step name matches
            this parser's pattern. Raises NotImplementedError if not overridden. Called by Matcher during candidate
            filtering; should be cheaper than parse_arguments.

        Reason for existence:
            ABC-level enforcement of the is_matching contract, providing NotImplementedError for incomplete
            implementations. The separation from parse_arguments at the ABC level reinforces the two-phase match-then-
            extract pattern that all subclasses must follow.

        Delegates:
            - No delegation: raises NotImplementedError. Concrete subclasses delegate to their parsing libraries.

        Cohesion:
            One of the four abstract methods. Forms the first phase of the match-then-extract pattern.

        Separation:
            - StepParserProtocol.is_matching: Protocol declaration; this is ABC enforcement.
            - parse_arguments: The extraction phase; this is the cheaper matching phase.

        Main consumers:
            - pytest_bdd.steps.matcher.Matcher.strict_matcher / unspecified_matcher / liberal_matcher: Call parser.is_matching().

        State and side effects:
            None in the abstract implementation.

        Failure semantics:
            - NotImplementedError: Raised if a concrete subclass fails to override. Indicates a bug in parser implementation.

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
        raise NotImplementedError  # pragma: no cover -- abstract subclass hook

    @abstractmethod
    def __str__(self) -> str:
        """
        Abstract method that concrete parser subclasses must override to return the original pattern source text.

        Responsibility:
            Abstract method that concrete parser subclasses must override to return the original pattern source text.
            Raises NotImplementedError if not overridden. Used for display and for populating cucumber_messages
            StepDefinitionPattern.source.

        Reason for existence:
            ABC-level enforcement ensuring every parser provides a meaningful string representation. Required because
            the framework uses str(parser) in reporting and message generation, and a missing implementation would
            produce unhelpful default output.

        Delegates:
            - No delegation: raises NotImplementedError. Concrete subclasses return self.format or self.pattern.pattern.

        Cohesion:
            One of the four abstract methods. Provides the display contract.

        Separation:
            - StepParserProtocol.__str__: Protocol declaration; this is ABC enforcement.

        Main consumers:
            - pytest_bdd.steps.definition.Definition.as_message: Uses str(self.parser) as StepDefinitionPattern.source.
            - Error messages and debug logging throughout the framework.

        State and side effects:
            None in the abstract implementation.

        Failure semantics:
            - NotImplementedError: Raised if a concrete subclass fails to override. Indicates a bug in parser implementation.

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
        raise NotImplementedError  # pragma: no cover -- abstract subclass hook

    @classmethod
    def build(cls, parserlike: StepParserLike) -> StepParser:
        """
        Classmethod factory that is the single entry point for constructing a StepParser from arbitrary user input.

        Responsibility:
            Classmethod factory that is the single entry point for constructing a StepParser from arbitrary user input.
            First checks if parserlike already satisfies StepParserProtocol (passthrough for pre-constructed parsers),
            then lazily loads all parser backends via _load_parser_modules(), iterates _PARSER_REGISTRY checking each
            predicate against parserlike and calling the matching builder, and finally falls back to
            _FALLBACK_PARSER_BUILDER. Raises ParserBuildValueError if no match is found and no fallback exists.

        Reason for existence:
            Centralises all parser dispatch logic in one method, eliminating the need for consumers to know which parser
            backend handles which input type. Users pass a string, compiled regex, or parser instance, and build()
            returns the correct StepParser. This is the lynchpin of the parser plugin architecture: adding a new parser
            backend requires only calling register_parser with a predicate and builder; build() discovers it
            automatically via _load_parser_modules.

        Delegates:
            - _load_parser_modules(): Ensures all parser backends are imported and self-registered before dispatch.
            - _PARSER_REGISTRY: Each (predicate, builder) pair is checked in order; first matching predicate's builder is called.
            - _FALLBACK_PARSER_BUILDER: Called as last resort when no predicate matches.
            - isinstance(parserlike, StepParserProtocol): Fast path for already-constructed parsers.

        Cohesion:
            The core dispatch method of the parser infrastructure. Every line of logic in this method serves the single
            purpose of mapping a parserlike object to a StepParser instance.

        Separation:
            - register_parser / register_fallback_parser: Populate the registries; build() consumes them. Separated so
            registration can happen at import time while dispatch happens at decoration time.

        Main consumers:
            - pytest_bdd.steps.manager.StepDefinitionManager.decorator_builder: The primary caller; calls
            StepParser.build(step_parserlike) during @given/@when/@then decoration.
            - Any code constructing a Definition programmatically.

        State and side effects:
            Triggers _load_parser_modules() on first call, which imports five parser modules and populates
            _PARSER_REGISTRY (module-level mutation). No other side effects. Idempotent after first call.

        Failure semantics:
            - ParserBuildValueError: Raised when no registered predicate matches and _FALLBACK_PARSER_BUILDER is None.
            Indicates an unsupported parser format. Callers should either handle this error or ensure a fallback parser
            is always registered.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
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
