"""
Owns the python-parse-based step definition parsers: the `parse` class (using base_parse.compile from the `parse` lib.

Responsibility:
    Owns the python-parse-based step definition parsers: the `parse` class (using base_parse.compile from the `parse`
    library) and the `cfparse` subclass (using parse_type.cfparse.Parser for case-insensitive field type parsing). Both
    classes satisfy the StepParser protocol with singledispatchmethod-based constructor accepting either a format string
    or a pre-compiled Parser object, and implement is_matching() (via self.parser.parse(), catching ValueError),
    parse_arguments() (extracting named and fixed/anonymous groups), and the `arguments` property (exposing regex group
    names from the compiled parser's internal regex). The module also registers `parse` as the parser wrapper for pre-
    compiled parse.Parser objects via register_parser().

Reason for existence:
    The `parse` library is the legacy/default step parser in pytest-bdd, providing a format-string-based pattern
    matching with named fields (e.g., "I have {n:d} cucumbers"). This module wraps the third-party `parse` library to
    conform to pytest-bdd's StepParser protocol, adding FixtureRequest context (unused by the parse parser itself but
    required by the protocol for other parsers like cucumber_expression). The cfparse variant extends parse with case-
    insensitive field type matching (e.g., allowing {name:Name} type casts). Without this module, step definition
    authors would lose the familiar parse-format syntax ("{}" placeholders) that they've used for years.

Delegates:
    - parse (third-party library, aliased as base_parse): Provides the Parser.compile() builder and the Parser.parse()
    matching method. The `parse` class wraps this library.
    - parse_type.cfparse (aliased as base_cfparse): Provides the cfparse.Parser class that extends base_parse with case-
    insensitive field type casting. The `cfparse` class wraps this.
    - pytest_bdd.parsers.base.StepParser: Provides the base class with protocol methods (is_matching, parse_arguments,
    arguments) that the `parse` class implements.
    - pytest_bdd.parsers.base.ParserBuildValueError: Raised when the constructor receives an unsupported format_ type.
    - pytest_bdd.parsers.base.register_parser: Registers the `parse` class as the wrapper for pre-compiled
    base_parse.Parser objects.
    - pytest_bdd.util.other.normalize_to_string: Converts StringRepresentable/bytes format values to strings for storage.
    - pytest_bdd.model.message_extension.StepDefinitionPatternType: Provides the pattern type enum value for classification.

Cohesion:
    All entities in this module support the parse-format-based step matching. The `parse` class owns the core matching
    logic, _init_stringable encapsulates the common string-format initialization shared by both constructor overloads
    and cfparse, and the `cfparse` subclass specializes the builder default. The singledispatchmethod on __init__
    enables the dual-constructor pattern (string or pre-compiled Parser). Everything serves the same pattern matching
    domain.

Separation:
    - pytest_bdd.parsers.re_parser.re: Kept separate because `re` uses stdlib re.Pattern for regex-based matching, while
    `parse` uses the third-party parse library for format-string-based matching — different matching engines, different
    pattern syntaxes.
    - pytest_bdd.parsers.cucumber_expression: Kept separate because cucumber_expression uses the cucumber-expressions
    library for Gherkin-compatible expression matching, a third distinct matching paradigm.
    - pytest_bdd.parsers.string_parser.string: Kept separate because string does exact string equality matching (no
    pattern parsing), the simplest matching strategy.

Main consumers:
    - End-user test code: `from pytest_bdd import parsers; parsers.parse("I have {n:d} cucumbers")` or
    `parsers.cfparse("...")`.
    - pytest_bdd.steps.manager.StepDefinitionManager: The step registration system uses the StepParser protocol that
    `parse` implements for matching steps at collection time.

State and side effects:
    None, keeps no persistent state. The `parse` instance stores self.format (string) and self.parser (compiled Parser),
    both immutable after construction.

Invariants:
    - self.format must be a string representation of the original pattern (normalized via normalize_to_string).
    - self.parser must be a compiled parse.Parser instance capable of matching against step text.
    - The `arguments` property must return the named capture group keys from the compiled parser's internal regex.
    - is_matching() must catch ValueError from parser.parse() — the parse library raises ValueError (not a custom
    exception) for non-matching input when using type casts.

Failure semantics:
    Raises ParserBuildValueError when __init__ receives a format_ that is not a string, bytes, StringRepresentable, or
    pre-compiled parse.Parser — the singledispatch catches all other types and raises this error. Callers should handle
    this as a coding error (wrong argument type passed to the parser constructor).

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from functools import singledispatchmethod
from typing import TYPE_CHECKING, cast

import parse as base_parse
import parse_type.cfparse as base_cfparse

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.util.other import StringRepresentable, normalize_to_string

from .base import ParserBuildValueError, StepParser, _ParseMatchProtocol, _ParserBuilder, register_parser

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from pytest_bdd.compatibility.pytest import FixtureRequest


class parse(StepParser):  # noqa:N801 intentional API
    """
    Implements the StepParser protocol using the third-party `parse` library for format-string-based step pattern matchin.

    Responsibility:
        Implements the StepParser protocol using the third-party `parse` library for format-string-based step pattern
        matching (e.g., "I have {n:d} cucumbers"). Stores a format string and a compiled parse.Parser instance, provides
        dual constructors (singledispatchmethod) accepting either a raw format string (compiles using
        base_parse.compile) or a pre-compiled parse.Parser, implements is_matching() by calling parser.parse() and
        catching ValueError for non-matches, parse_arguments() extracting both named groups and anonymous (positional)
        groups into a dict, and exposes the `arguments` property listing named capture group names from the compiled
        parser's internal regex. Also provides a cfparse() classmethod factory for case-insensitive field type parsing.

    Reason for existence:
        This is the legacy/default step parser that pytest-bdd users are most familiar with. The parse library's format-
        string syntax (with :type casts like {n:d}, {name:w}) provides a concise, readable way to match step patterns
        while extracting typed arguments. This class wraps the third-party library to conform to pytest-bdd's StepParser
        protocol (adding FixtureRequest parameter for protocol compatibility even though the parse parser doesn't use
        it), and handles the dual-constructor pattern needed because step definitions can be registered with either raw
        strings or pre-compiled parse.Parser objects from earlier parsing phases.

    Delegates:
        - base_parse.compile: Compiles format strings into parse.Parser instances. Used by _init_stringable when the
        constructor receives a string format.
        - base_parse.Parser: The compiled parser object that performs actual step text matching and argument extraction.
        - _init_stringable: Shared initialization for string-based constructors, setting self.format and self.parser.
        - normalize_to_string: Converts various string-like inputs to canonical string form.
        - singledispatchmethod: Enables the dual-constructor pattern (string vs pre-compiled Parser) without if/else chains.

    Cohesion:
        Every method serves the parse-based step matching: __init__ creates the compiled parser from the format,
        is_matching and parse_arguments delegate to the compiled parser, arguments exposes the parser's capture groups,
        __str__ returns the format string. The cfparse classmethod is a factory that injects a different builder. All
        logic is about parse-format matching.

    Separation:
        - cfparse (subclass): Kept separate because cfparse specializes with a different builder (base_cfparse.Parser
        for case-insensitive types) and a different StepDefinitionPatternType, while inheriting all matching logic —
        builder specialization.
        - re (from re_parser): Kept separate because re uses stdlib regex patterns, not parse format patterns —
        different syntax, different library, different matching algorithm.

    Main consumers:
        - End-user test code via parsers.parse("pattern").
        - pytest_bdd.steps.manager: Uses the StepParser protocol to match and parse step definitions.
        - register_parser: Registers parse as the wrapper for pre-compiled base_parse.Parser objects via the lambda
        isinstance check.

    State and side effects:
        None, keeps no persistent state. self.format (str) and self.parser (parse.Parser) are both immutable after construction.

    Invariants:
        - self.format must be a string normalized from the original input (via normalize_to_string).
        - self.parser must be a compiled parse.Parser that matches the format pattern.
        - is_matching() must not raise exceptions — ValueError from non-matching type casts is caught and returns False.

    Failure semantics:
        Raises ParserBuildValueError when __init__ receives a format_ that is not a
        string/bytes/StringRepresentable/parse.Parser — this is a defensive catch-all for unsupported types. Callers
        should ensure they pass valid format values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    type = StepDefinitionPatternType.pytest_bdd_parse_expression  # type:ignore[attr-defined]  # upstream type stubs missing this attribute

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]  # mypy limitation with singledispatchmethod/dynamic typing
    def __init__(self, format_: object, *args: object, **kwargs: object) -> None:
        """
        Implement the singledispatchmethod-based dual constructor that handles two input types: string-format inputs (str, bytes) and pre-compiled parse.Parser objects.

        Responsibility:
            Implements the singledispatchmethod-based dual constructor that handles two input types: string-format
            inputs (str, bytes, StringRepresentable) are routed to _init_stringable with a configurable builder
            (defaulting to base_parse.compile but overridable for cfparse), while all other types raise
            ParserBuildValueError (a defensive catch-all since the singledispatch register methods handle the expected
            types). Accepts *args and **kwargs that are passed through to the builder function (base_parse.compile or
            base_cfparse.Parser).

        Reason for existence:
            The singledispatchmethod pattern enables type-based constructor dispatch without if/elif chains. String
            inputs need compilation via a builder function, pre-compiled Parser objects need their internal format
            extracted, and unsupported types should produce clear errors. The format_ parameter name uses a trailing
            underscore to avoid shadowing the built-in format() function. The *args/**kwargs passthrough allows each
            parser implementation to customize its compilation with additional parameters (e.g., case_sensitive for
            cfparse).

        Delegates:
            - _init_stringable: Handles string-format initialization (self.format and self.parser setup).
            - singledispatchmethod: Dispatches to the correct registered method based on format_ type.

        Cohesion:
            The method is a pure dispatch mechanism — it routes to the appropriate initializer based on input type, with
            a default error case for unsupported types.

        Separation:
            - _init_stringable: Kept separate because this method handles dispatch and the error case, while
            _init_stringable handles the actual string-format initialization — routing vs implementation.

        Main consumers:
            - User code indirectly via parsers.parse("pattern") or parsers.parse(pre_compiled_parser) — the constructor
            is the entry point for creating parse parser instances.
            - cfparse.__init__: Calls super().__init__() which triggers this dispatch method.

        State and side effects:
            Sets self.format and self.parser through _init_stringable. No external side effects.

        Failure semantics:
            Raises ParserBuildValueError for unsupported format_ types — this is a coding error indicating the caller
            passed a wrong argument type.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        if isinstance(format_, (StringRepresentable, str, bytes)):
            builder = cast("_ParserBuilder", kwargs.pop("builder", base_parse.compile))
            self._init_stringable(format_, *args, builder=builder, **kwargs)
        else:
            raise ParserBuildValueError(
                format_,
            )  # pragma: no cover -- unreachable; guarded by isinstance checks above

    def _init_stringable(
        self,
        format_: StringRepresentable | str | bytes,
        *args: object,
        builder: _ParserBuilder = base_parse.compile,  # type: ignore[assignment]  # dynamic parser builder dispatch
        **kwargs: object,
    ) -> None:
        """
        Shared initialization for string-format-based parser construction: normalizes the format_ input to a canonical string.

        Responsibility:
            Shared initialization for string-format-based parser construction: normalizes the format_ input to a
            canonical string via normalize_to_string (handling StringRepresentable, bytes, and str), compiles the format
            string into a parse.Parser using the provided builder callable (base_parse.compile for parse,
            base_cfparse.Parser for cfparse), and stores both the format string and compiled parser in instance
            attributes. Accepts *args and **kwargs that are forwarded to the builder function for customization.

        Reason for existence:
            Both the parse string constructor and cfparse need the same initialization logic (normalize format → compile
            → store), differing only in the builder callable. This method factors out the common logic, avoiding
            duplication between the two singledispatch register methods for string inputs. The builder parameter enables
            cfparse to inject base_cfparse.Parser without overriding the entire initialization.

        Delegates:
            - normalize_to_string: Converts various string-like inputs (StringRepresentable, bytes, str) to a canonical str.
            - builder (base_parse.compile or base_cfparse.Parser): Compiles the normalized format string into a compiled
            parser object.

        Cohesion:
            The method performs a single initialization pipeline: normalize → compile → store. Every line serves this purpose.

        Separation:
            - parse.__init__: Kept separate because __init__ handles dispatch, while _init_stringable handles the actual
            initialization logic for string inputs.

        Main consumers:
            - parse.__init__: Called when the singledispatch detects a string-like format_ input.
            - cfparse.__init__ (indirectly through super().__init__): Cfparse overrides the default builder to base_cfparse.Parser.

        State and side effects:
            Sets self.format and self.parser on the instance. No external side effects.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        self.format = normalize_to_string(format_)
        self.parser = cast("base_parse.Parser", builder(self.format, *args, **kwargs))

    @__init__.register
    def _(self, format_: base_parse.Parser) -> None:
        """
        Handle the singledispatchmethod registered case for pre-compiled parse.Parser objects: extract the original format string and create a new CFParser wrapping it.

        Responsibility:
            Handles the singledispatchmethod registered case for pre-compiled parse.Parser objects: extracts the
            original format string from the parser's internal _format attribute and stores both the extracted format and
            the pre-compiled parser instance. This enables users to register step definitions using parser objects that
            were compiled elsewhere (e.g., during a previous collection phase).

        Reason for existence:
        Step parsers may be pre-compiled during feature file parsing or in shared conftest fixtures, and step definition
        registration needs to accept these pre-compiled objects without re-compiling. This overload extracts the
        original format string (needed for string representation and debugging) while reusing the existing compiled
        parser. The _format attribute access (with SLF001 suppression) is required because the parse library doesn't
        expose the original format string through a public API.

        Delegates:
            - format_._format: Accesses the parse library's internal _format attribute to retrieve the original format string.

        Cohesion:
            The method performs a single task: accept pre-compiled Parser → extract format → store both. No other logic.

        Separation:
            - _init_stringable: Kept separate because that method handles string-format compilation, while this method
            handles pre-compiled parser acceptance — different initialization paths for different input types.

        Main consumers:
            - parse.__init__ singledispatch: This is the registered handler for base_parse.Parser inputs, dispatched
            automatically when a pre-compiled parser is passed to the constructor.

        State and side effects:
            Sets self.format and self.parser on the instance. The format_._format access is read-only.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        self.format = format_._format  # noqa: SLF001  -- access to parse library's internal _format attribute required by the step parser protocol
        self.parser = format_

    @classmethod
    def cfparse(cls, *args: object, **kwargs: object) -> parse:
        """
        Classmethod factory that creates a `parse` instance configured for case-insensitive field type parsing by setting the.

        Responsibility:
            Classmethod factory that creates a `parse` instance configured for case-insensitive field type parsing by
            setting the builder keyword argument to base_cfparse.Parser. This is the programmatic entry point for
            creating a cfparse-style parser without using the cfparse subclass directly. Returns a `parse` instance (not
            a `cfparse` instance) with the cfparse builder injected.

        Reason for existence:
            Provides a composable way to create case-insensitive parse parsers. While the `cfparse` subclass exists for
            direct use, this classmethod allows code that already has a reference to the `parse` class to create a
            cfparse-configured instance without importing cfparse separately. The builder default injection pattern
            means callers pass the format string and any other args, and the cfparse builder is automatically used.

        Delegates:
            - base_cfparse.Parser: The builder class that handles case-insensitive field type matching.
            - cls(*args, **kwargs): Delegates to the standard constructor with builder injected.

        Cohesion:
            The method performs one operation: set builder default → call constructor. The kwargs.setdefault pattern
            ensures the caller can still override the builder if needed.

        Separation:
            - cfparse.__init__: Kept separate because cfparse.__init__ explicitly sets builder=base_cfparse.Parser for
            the subclass constructor, while this classmethod injects it through kwargs — subclass constructor vs factory
            method, achieving the same result through different patterns.

        Main consumers:
            - Programmatic parser creation: code that builds parsers dynamically and wants case-insensitive behavior
            without instantiating cfparse directly.

        State and side effects:
            None, keeps no persistent state. Factory method that returns a new instance.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        kwargs.setdefault("builder", base_cfparse.Parser)
        return cast("parse", cls(*args, **kwargs))

    def parse_arguments(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object]:
        """
        Extract step arguments from a matched step name string using the compiled parse.Parser: call parser.parse(name) to obtain named and fixed arguments.

        Responsibility:
            Extracts step arguments from a matched step name string using the compiled parse.Parser: calls
            parser.parse(name) to get a Result object, extracts named groups via result.named (a dict), and if
            anonymous_group_names are provided, supplements with positional fixed groups via result.fixed, zipping them
            with the provided names. The FixtureRequest parameter is accepted but unused — it exists for StepParser
            protocol compatibility with parsers that need request context.

        Reason for existence:
            The parse.Parser.parse() method returns a Result object with two key attributes: .named (dict of named
            fields) and .fixed (tuple of positional matches). This method bridges the parse library's result format to
            pytest-bdd's step argument dict format. The anonymous_group_names parameter enables mapping of positional
            regex groups (from other parser types like re) to named arguments, though for parse parsers the named groups
            are the primary extraction method.

        Delegates:
            - self.parser.parse(name): Performs the actual step text matching and returns a Result with .named and
            .fixed attributes.
            - cast("_ParseMatchProtocol", ...): Type assertion that the result conforms to the expected match protocol.
            - dict(match.named): Converts the named groups to a standard dict.

        Cohesion:
            The method performs one operation: extract arguments from matched text → return as dict. The
            anonymous_group_names zip is a cross-parser compatibility feature.

        Separation:
            - is_matching: Kept separate because is_matching checks whether a match exists (boolean), while
            parse_arguments extracts the matched values (dict) — boolean check vs data extraction, two phases of the
            matching pipeline.

        Main consumers:
            - pytest_bdd.steps.manager: Called during step execution to extract argument values for injection into step
            function parameters.

        State and side effects:
            None, keeps no persistent state. Pure function of inputs.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        match = cast("_ParseMatchProtocol", self.parser.parse(name))
        group_dict = dict(match.named)
        if anonymous_group_names is not None:
            group_dict.update(dict(zip(anonymous_group_names, match.fixed, strict=False)))
        return group_dict

    @property
    def arguments(self) -> Collection[str]:
        """
        Returns the named capture group keys from the compiled parser's internal regex pattern via self.parser._match_re.grou.

        Responsibility:
            Returns the named capture group keys from the compiled parser's internal regex pattern via
            self.parser._match_re.groupindex.keys(). These are the argument names that the parse format string defines
            (e.g., for "I have {n:d} cucumbers", returns ["n"]). The collection is used by the step definition manager
            to determine which fixture names correspond to step arguments.

        Reason for existence:
            The StepParser protocol requires an `arguments` property that exposes the named arguments a step parser can
            extract, enabling the step definition system to validate that step function parameters match the parser's
            expected arguments. The parse library stores the compiled regex pattern in _match_re (a private attribute),
            and this property accesses it via SLF001-suppressed private attribute access — this is a necessary evil
            because the parse library's public API doesn't expose the group names directly.

        Delegates:
            - self.parser._match_re.groupindex.keys(): Accesses the compiled regex's named group index to enumerate argument names.

        Cohesion:
            The property performs exactly one operation: extract argument names from the compiled parser. The list
            conversion from dict_keys ensures the result is iterable and indexable.

        Separation:
            - re.arguments (from re_parser): Kept separate because re.arguments uses stdlib re.Pattern.groupindex, while
            parse.arguments uses parse.Parser._match_re.groupindex — different compiled parser types, different internal
            regex storage, but same conceptual operation.

        Main consumers:
            - pytest_bdd.steps.manager: Uses arguments to validate step function signatures and map fixture names.

        State and side effects:
            None, keeps no persistent state. Read-only property.

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
        return [*self.parser._match_re.groupindex.keys()]  # noqa: SLF001  -- access to parse library's internal _match_re required to enumerate named capture groups

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
    ) -> bool:
        """
        Test whether a step name string matches the compiled parse format pattern by calling parser.parse(name) and converting the result to a boolean.

        Responsibility:
            Tests whether a step name string matches the compiled parse format pattern by calling parser.parse(name) and
            converting the result to bool. Catches ValueError (raised by the parse library when type-cast fields receive
            non-matching input, e.g., {n:d} receiving "abc") and returns False, treating type-cast failures as non-
            matches. The FixtureRequest parameter is accepted but unused — present for protocol compatibility.

        Reason for existence:
            The parse library raises ValueError (not a custom ParseError) when type-cast fields cannot parse their input
            — this is a quirk of the parse library's error handling. This method catches these ValueErrors and returns
            False instead of letting the exception propagate, treating type-cast mismatch as "doesn't match" rather than
            "error." Without this catch, a step like "I have {n:d} cucumbers" would raise ValueError when matched
            against "I have many cucumbers" instead of simply not matching.

        Delegates:
            - self.parser.parse(name): Performs the actual pattern matching and returns a Result on match, or raises
            ValueError on type-cast failure.

        Cohesion:
            The method performs exactly one check: does the step text match the pattern? The ValueError catch is
            integral to this check for parse-format patterns.

        Separation:
            - parse_arguments: Kept separate because is_matching is a boolean gate (should we proceed?), while
            parse_arguments extracts values after matching (what values were matched?) — gate vs extraction.
            - re.is_matching (from re_parser): Kept separate because re uses regex.fullmatch while parse uses
            parse.Parser.parse — different matching algorithms, different error handling.

        Main consumers:
            - pytest_bdd.steps.manager: Called during step definition lookup to find which step definition matches the
            current scenario step text.

        State and side effects:
            None, keeps no persistent state. Pure function of inputs.

        Failure semantics:
            Returns False on ValueError from type-cast failures — silently treats non-matching type casts as "doesn't
            match". Does not raise exceptions.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        try:
            return bool(self.parser.parse(name))
        except ValueError:
            return False

    def __str__(self) -> str:
        """
        Return the original format string used to create the parser, providing a human-readable representation for debugging.

        Responsibility:
            Returns the original format string used to create the parser, providing a human-readable representation for
            debugging, error messages, and logging. This is the string that the user originally passed to the parser
            constructor (e.g., "I have {n:d} cucumbers").

        Reason for existence:
            The StepParser protocol requires __str__ for display purposes (error messages showing which parser
            matched/mismatched, debug logging of step definitions). The format string is the most meaningful
            representation — it shows the pattern the step was matched against. This is simpler than showing the
            compiled parser object which would be unreadable.

        Delegates:
            - self.format: The format string stored during construction, normalized via normalize_to_string.

        Cohesion:
            Trivially cohesive — returns the stored format string.

        Separation:
            - Other parser __str__ methods: Each parser returns the format that makes sense for its matching paradigm
            (re.pattern for regex, cucumber_expression.pattern for Cucumber expressions, parse.format for parse
            parsers).

        Main consumers:
            - Error messages in pytest_bdd.steps.manager: Used when reporting step definition mismatches or undefined steps.
            - Logging and debugging: Provides human-readable parser identification.

        State and side effects:
            None, keeps no persistent state. Read-only.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return str(self.format)


class cfparse(parse):  # noqa:N801 intentional API
    """
    A subclass of `parse` that specializes the parser builder to base_cfparse.Parser (from the parse_type library) for ca.

    Responsibility:
        A subclass of `parse` that specializes the parser builder to base_cfparse.Parser (from the parse_type library)
        for case-insensitive field type matching. This parser treats field type names as case-insensitive (e.g.,
        {name:Name} and {name:name} match the same type) and handles custom type conversions defined by the parse_type
        library. Otherwise inherits all matching and argument extraction logic from the parent `parse` class. Has its
        own StepDefinitionPatternType (pytest_bdd_cfparse_expression) for classification.

    Reason for existence:
        The parse_type library extends the standard parse library with case-insensitive type resolution and additional
        built-in types (e.g., Name, Color, etc.). This class provides pytest-bdd users access to those extended features
        without modifying the base `parse` parser. The subclass pattern is used rather than a configuration flag because
        the compiled parser object is fundamentally different (base_cfparse.Parser vs base_parse.Parser), and the
        pattern type classification needs to distinguish them for message serialization purposes.

    Delegates:
        - base_cfparse.Parser: The extended parser class from parse_type that handles case-insensitive type casting.
        - parse (parent class): Inherits all matching (is_matching, parse_arguments), argument extraction (arguments
        property), and string representation (__str__) logic.

    Cohesion:
        The class has a single specialization: using the cfparse builder instead of the parse builder. All other
        behavior is inherited unchanged, making this a clean, focused subclass.

    Separation:
        - parse (parent): Kept separate because parse uses base_parse.compile/basic Parser while cfparse uses
        base_cfparse.Parser — different parser backends, different feature sets, different pattern type classification.
        - cucumber_expression: Kept separate because cucumber_expression uses the cucumber-expressions library (a
        completely different parsing paradigm), while cfparse uses the parse-type-extended parse library — different
        libraries, different syntax.

    Main consumers:
        - End-user test code via parsers.cfparse("pattern").
        - pytest_bdd.steps.manager: Uses the StepParser protocol inherited from parse for matching.

    State and side effects:
        None, keeps no persistent state beyond what the parent class stores. The builder default is set during __init__.

    Invariants:
        - The builder must be base_cfparse.Parser or a compatible subclass for case-insensitive type matching.
        - Inherits all matching and argument extraction contracts from the parent parse class.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    type = StepDefinitionPatternType.pytest_bdd_cfparse_expression  # type:ignore[attr-defined]  # upstream type stubs missing this attribute

    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Override the parent constructor to inject base_cfparse.Parser as the default builder, then delegate to the parent __init__.

        Responsibility:
            Overrides the parent constructor to inject base_cfparse.Parser as the default builder, then delegates to the
            parent __init__ for the actual initialization (which will detect the string format and call _init_stringable
            with the overridden builder). This ensures that cfparse instances always use the case-insensitive field type
            parser from parse_type without requiring the user to explicitly specify the builder.

        Reason for existence:
            The only difference between parse and cfparse is the builder (base_cfparse.Parser vs base_parse.compile).
            This __init__ override injects that difference cleanly: set the builder default on kwargs, then let the
            parent class handle the rest. Without this override, users would need to explicitly pass
            builder=base_cfparse.Parser to the parse constructor, which is less discoverable and more error-prone.

        Delegates:
            - super().__init__: Passes control to the parent class's singledispatchmethod-based constructor with the
            builder already injected.
            - base_cfparse.Parser: The builder that will be used by _init_stringable to compile the format string.

        Cohesion:
        The method performs a single injection: set builder default → delegate to parent. No other logic.

        Separation:
            - parse.__init__: Kept separate because parse.__init__ uses base_parse.compile as the default builder, while
            cfparse.__init__ overrides it — default builder injection is the sole specialization.

        Main consumers:
            - User code via parsers.cfparse("pattern") — the constructor is the entry point for creating cfparse parsers.

        State and side effects:
            Modifies kwargs in place (sets "builder" key), then delegates. No external side effects.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        kwargs.setdefault("builder", base_cfparse.Parser)
        super().__init__(*args, **kwargs)


register_parser(lambda parserlike: isinstance(parserlike, base_parse.Parser), parse)
