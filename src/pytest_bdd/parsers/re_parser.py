"""
Owns the stdlib regex-based step definition parser class `re` that implements the StepParser protocol using Python's .

Responsibility:
    Owns the stdlib regex-based step definition parser class `re` that implements the StepParser protocol using Python's
    re.Pattern for pattern matching. Provides a singledispatchmethod-based dual constructor accepting either a raw regex
    pattern string (compiled via re.compile with forwarded *args/**kwargs) or a pre-compiled re.Pattern object.
    Implements is_matching() via regex.fullmatch(), parse_arguments() extracting named groups (via match.groupdict())
    and anonymous positional groups (filtering out already-named spans and mapping them to provided
    anonymous_group_names), and the `arguments` property exposing capture group names via regex.groupindex. Also
    registers `re` as the parser wrapper for pre-compiled re.Pattern objects via register_parser().

Reason for existence:
    Python's stdlib regular expressions are the most powerful and flexible matching engine available, supporting
    features that format-string parsers cannot express (lookahead, alternation with named groups, complex quantifiers).
    This module provides first-class regex support as a parser option for step definition authors who need this
    expressiveness. Without this module, step definitions requiring complex regex patterns would need to use workarounds
    or fall back to the less powerful parse-format syntax.

Delegates:
    - re.compile (stdlib): Compiles regex pattern strings into re.Pattern objects with forwarded compilation flags.
    - re.Pattern (stdlib): The compiled regex object that performs matching (fullmatch) and provides group information
    (groupindex).
    - pytest_bdd.parsers.base.StepParser: Provides the base class with the protocol interface.
    - pytest_bdd.parsers.base.register_parser: Registers `re` as the wrapper for pre-compiled re.Pattern objects.
    - pytest_bdd.util.other.normalize_to_string: Converts the pattern to a canonical string for __str__.
    - pytest_bdd.model.message_extension.StepDefinitionPatternType: Provides pattern type classification.

Cohesion:
    All logic in this module supports regex-based step matching. The `re` class owns the matching, argument extraction,
    and argument enumeration logic. Every method delegates to the compiled regex object (self.regex) — is_matching calls
    fullmatch, parse_arguments calls fullmatch and uses match.groupdict/match.span, arguments reads groupindex. This is
    a clean single-responsibility class.

Separation:
    - pytest_bdd.parsers.parse_parser.parse: Kept separate because parse uses format-string matching (parse library)
    while re uses regex matching (stdlib) — completely different matching engines with different syntax and
    capabilities.
    - pytest_bdd.parsers.cucumber_expression: Kept separate because cucumber_expression uses the cucumber-expressions
    library for Gherkin-compatible expression matching — yet another distinct matching paradigm.
    - pytest_bdd.parsers.string_parser.string: Kept separate because string does exact equality matching (no pattern),
    the simplest matching strategy.

Main consumers:
    - End-user test code via parsers.re(r"pattern").
    - pytest_bdd.steps.manager: Uses the StepParser protocol for step definition matching.

State and side effects:
    None, keeps no persistent state. self.pattern (str) and self.regex (re.Pattern) are both immutable after construction.

Invariants:
    - self.pattern must be the original regex pattern string (extracted from re.Pattern.pattern for pre-compiled inputs).
    - self.regex must be a compiled re.Pattern object capable of fullmatch() against step text.
    - is_matching() must use fullmatch(), not match() or search() — the step text must match the entire pattern, not
    just a prefix or substring.

Failure semantics:
    Raises NotImplementedError from the base singledispatchmethod __init__ — this is the abstract hook that should never
    be called because the two register methods handle string and re.Pattern inputs. If reached, it indicates a
    programming error (unsupported input type).

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from functools import partial, singledispatchmethod
from itertools import filterfalse
from operator import contains
from re import Match
from re import Pattern as _RePattern
from re import compile as re_compile
from typing import TYPE_CHECKING, cast

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.util.other import normalize_to_string

from .base import StepParser, _RegexCompiler, register_parser

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from pytest_bdd.compatibility.pytest import FixtureRequest


class re(StepParser):  # noqa:N801 intentional API
    r"""
    Implements the StepParser protocol using Python's stdlib re.Pattern for regex-based step matching.

    Responsibility:
        Implements the StepParser protocol using Python's stdlib re.Pattern for regex-based step matching. Supports both
        raw pattern strings (compiled via re.compile with configurable flags) and pre-compiled re.Pattern objects via
        singledispatchmethod constructor dispatch. is_matching() uses fullmatch() for complete string matching,
        parse_arguments() extracts named (groupdict) and anonymous positional groups (determined by excluding named
        group spans and mapping remaining to anonymous_group_names), and the `arguments` property exposes named capture
        groups via groupindex. Registered as the parser wrapper for pre-compiled re.Pattern objects.

    Reason for existence:
        Regex is the most expressive pattern matching option in pytest-bdd, supporting features like alternation
        ((a|b)), lookahead ((?=...)), named groups ((?P<name>...)), and non-capturing groups ((?:...)) that are
        impossible in format-string parsers. This class provides full regex support while maintaining the StepParser
        protocol interface, including the sophisticated parse_arguments logic that correctly separates named groups from
        anonymous groups by comparing span positions — ensuring that unnamed capture groups are properly mapped to
        anonymous_group_names without double-counting named groups.

    Delegates:
        - re_compile (stdlib re.compile): Compiles pattern strings into re.Pattern objects.
        - re.Pattern.fullmatch: Performs the actual pattern matching, requiring the entire string to match.
        - re.Pattern.groupindex: Provides the mapping of named group names to group numbers.
        - singledispatchmethod: Enables dual-constructor pattern for strings vs pre-compiled patterns.
        - normalize_to_string: Converts the pattern to a canonical string for __str__.

    Cohesion:
        Every method in this class serves regex-based matching: the constructors create compiled regex objects,
        is_matching tests with fullmatch, parse_arguments extracts groups from match objects, arguments lists named
        groups, and __str__ returns the pattern string. All logic revolves around a single re.Pattern instance.

    Separation:
        - parse (from parse_parser): Kept separate because parse uses format-string matching while re uses regex
        matching — different engines with completely different syntax.
        - cucumber_expression: Kept separate because cucumber_expression uses the cucumber-expressions library — a third
        distinct paradigm.

    Main consumers:
        - End-user test code: parsers.re(r"^I have (\d+) cucumbers$").
        - pytest_bdd.steps.manager: Uses the StepParser protocol for matching.

    State and side effects:
        None. self.pattern (str) and self.regex (re.Pattern) are immutable after construction.

    Invariants:
        - is_matching must use fullmatch() — step text must match the entire pattern, not a prefix.
        - parse_arguments must correctly distinguish named from anonymous groups by comparing span positions against
        named group spans.

    Failure semantics:
        Raises NotImplementedError from the base __init__ dispatch — this is a dead code path guarded by the two
        register methods handling all valid input types.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    type = StepDefinitionPatternType.pytest_bdd_regular_expression  # type:ignore[attr-defined]  # upstream type stubs

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]  # mypy limitation with singledispatchmethod/dynamic typing
    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Serve as the base singledispatchmethod constructor for the abstract/default case — raise NotImplementedError to indica.

        Responsibility:
            Serve as the base singledispatchmethod constructor for the abstract/default case — raise NotImplementedError
            to indicate that subclasses or registered dispatch methods should handle specific input types. The two
            registered methods handle str patterns and re.Pattern objects. This never executes in normal usage because
            the register methods cover all expected types.

        Reason for existence:
            singledispatchmethod requires a base implementation that serves as the fallback. Rather than implementing
            logic in the base (which would handle unknown types incorrectly), raising NotImplementedError makes it clear
            that unregistered types are programmer errors. This follows the pattern used by cucumber_expression and
            cucumber_regular_expression.

        Delegates:
            - singledispatchmethod: Dispatches to register methods based on argument type.

        Cohesion:
            The method is a pure guard — it ensures unsupported types produce clear errors rather than silent misbehavior.

        Separation:
            - The register methods: Kept separate because each handles a specific input type (str → compile, re.Pattern
            → extract pattern).

        Main consumers:
            - singledispatchmethod dispatch: Automatically called when args don't match any registered overload.

        State and side effects:
            None.

        Failure semantics:
            Raises NotImplementedError — indicates the caller passed an unsupported type. This is a programming error,
            not a recoverable condition.

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
    def _(self, pattern: str, *args: object, **kwargs: object) -> None:
        """
        Register the singledispatch handler for string pattern inputs: store the original pattern string and compile it into .

        Responsibility:
            Registered singledispatch handler for string pattern inputs: stores the original pattern string and compiles
            it into a re.Pattern using re_compile() with forwarded *args (e.g., re.IGNORECASE flag) and **kwargs. This
            enables users to create regex parsers with custom compilation flags like parsers.re(r"pattern",
            re.IGNORECASE).

        Reason for existence:
            String patterns are the primary way users create regex step parsers. This handler compiles the string into a
            re.Pattern object that the rest of the class uses for matching. The *args/**kwargs passthrough enables regex
            flags (re.IGNORECASE, re.DOTALL, etc.) to be passed through to re.compile without requiring a separate flags
            parameter.

        Delegates:
            - re_compile (stdlib): Compiles the pattern string with forwarded args/kwargs into a re.Pattern.

        Cohesion:
            The method performs a single operation: store pattern → compile → store regex. Every line serves this purpose.

        Separation:
            - The re.Pattern register method: Kept separate because that method handles pre-compiled patterns
            (extracting pattern string from pattern.pattern) while this method handles raw strings (compiling them).

        Main consumers:
            - User code via parsers.re(r"pattern", re.IGNORECASE) — the constructor dispatches here for string inputs.

        State and side effects:
            Sets self.pattern and self.regex on the instance.

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
        self.pattern = pattern
        self.regex = cast("_RegexCompiler", re_compile)(self.pattern, *args, **kwargs)

    @__init__.register
    def _(self, pattern: _RePattern) -> None:  # type: ignore[type-arg]  # re.Pattern[str] not a class at runtime
        """
        Register the singledispatch handler for pre-compiled re.Pattern inputs: extract the original pattern string from patte.

        Responsibility:
            Registered singledispatch handler for pre-compiled re.Pattern inputs: extracts the original pattern string
            from pattern.pattern and stores both the extracted string and the pre-compiled pattern. Enables registration
            of step definitions using regex objects compiled elsewhere (e.g., during a previous parsing phase or from
            shared constants).

        Reason for existence:
            Pre-compiled regex objects may be passed from earlier parsing stages or shared conftest fixtures. This
            handler avoids re-compilation by extracting the pattern string for display/debugging purposes while keeping
            the existing compiled pattern for matching. The pattern.pattern attribute is a standard re.Pattern property
            that stores the original pattern string.

        Delegates:
            - pattern.pattern: Standard re.Pattern attribute that stores the original pattern string.

        Cohesion:
            The method performs one operation: extract pattern string → store both string and compiled pattern.

        Separation:
            - The string register method: Kept separate because that method compiles strings while this method extracts
            from pre-compiled objects — compilation vs extraction.

        Main consumers:
            - Code that needs to register step definitions using pre-compiled regex objects: parsers.re(pre_compiled_pattern).

        State and side effects:
            Sets self.pattern and self.regex on the instance. Read-only access to pattern.pattern.

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
        self.pattern = pattern.pattern
        self.regex = pattern

    def parse_arguments(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object]:
        """
        Extract step arguments from a matched step name using regex fullmatch: create a match object, extract named groups.

        Responsibility:
            Extracts step arguments from a matched step name using regex fullmatch: creates a match object, extracts
            named groups via match.groupdict(), and if anonymous_group_names are provided, identifies
            anonymous/positional groups by filtering out spans that overlap with named group spans (using filterfalse
            with partial(contains, named_spans)), then maps the remaining group spans to the provided anonymous names
            and to their corresponding string slices from the step name. Returns a dict excluding None values.
            FixtureRequest parameter accepted but unused — present for protocol compatibility.

        Reason for existence:
            Regex patterns can have both named groups ((?P<name>...)) and anonymous groups ((...)). The step definition
            system needs to extract both types. Named groups are straightforward (match.groupdict()), but anonymous
            groups require identifying which group numbers correspond to anonymous vs named captures. This method uses a
            clever algorithm: collect all named group spans, then for each group number, check if its span overlaps with
            any named span — if not, it's an anonymous group and gets mapped to the corresponding anonymous_group_name.

        Delegates:
            - self.regex.fullmatch(name): Performs the pattern matching and returns a Match object.
            - match.groupdict(): Extracts named groups as a dict.
            - match.span(group_num): Gets the span (start, end) for each group by number.
            - filterfalse with partial(contains, named_spans): Filters out group spans that overlap with named group spans.

        Cohesion:
            The method performs one task: extract arguments from regex match result. Every line (match creation, named
            group extraction, anonymous group identification, None filtering) serves this purpose.

        Separation:
            - is_matching: Kept separate because is_matching is a boolean gate while parse_arguments extracts values —
            detection vs extraction phases.
            - parse.parse_arguments: Kept separate because parse uses the parse library's Result object while re uses
            re.Match — different match object types with different APIs.

        Main consumers:
            - pytest_bdd.steps.manager: Called during step execution to extract argument values for step function
            parameter injection.

        State and side effects:
            None. Pure function of the step name and pattern.

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
        match = cast("Match[str]", self.regex.fullmatch(name))
        group_dict = match.groupdict()
        if anonymous_group_names is not None:
            group_dict.update(
                zip(
                    anonymous_group_names,
                    (
                        name[slice(*span)]
                        for span in filterfalse(
                            partial(contains, [*map(match.span, group_dict.keys())]),
                            map(match.span, range(1, len(match.groups()) + 1)),
                        )
                    ),
                    strict=False,
                ),
            )

        return {k: v for k, v in group_dict.items() if v is not None}

    @property
    def arguments(self) -> Collection[str]:
        """
        Returns the named capture group keys from the compiled regex pattern via self.regex.groupindex.keys().

        Responsibility:
            Returns the named capture group keys from the compiled regex pattern via self.regex.groupindex.keys(). These
            are the argument names defined by (?P<name>...) syntax in the pattern. The collection is used by the step
            definition manager to validate step function parameter names against the regex pattern's named groups.

        Reason for existence:
            The StepParser protocol requires exposing named arguments so the step definition system can validate
            function signatures and map fixture names. regex.groupindex provides a direct mapping of group names to
            group numbers — the keys are the argument names. This is a clean public API compared to the parse parser
            which requires SLF001-suppressed private attribute access.

        Delegates:
            - self.regex.groupindex.keys(): Standard re.Pattern attribute providing named group → group number mapping.

        Cohesion:
            The property performs one operation: extract named group names from the compiled regex. The list conversion
            from dict_keys ensures iterable output.

        Separation:
            - parse.arguments (from parse_parser): Kept separate because parse uses parse.Parser._match_re.groupindex
            while re uses re.Pattern.groupindex — different compiled pattern types, different APIs.

        Main consumers:
            - pytest_bdd.steps.manager: Uses arguments to validate step function signatures.

        State and side effects:
            None. Read-only property.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        return [*self.regex.groupindex.keys()]

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
    ) -> bool:
        r"""
        Test whether a step name string matches the compiled regex pattern using re.Pattern.fullmatch(), which requires the .

        Responsibility:
            Tests whether a step name string matches the compiled regex pattern using re.Pattern.fullmatch(), which requires the entire string to match (unlike match() which only requires a prefix match, or search() which finds a match anywhere). Returns the boolean result directly. FixtureRequest accepted but unused — protocol compatibility.

        Reason for existence:
            fullmatch() is used specifically (not match() or search()) because step definitions should match the complete step text, not just a prefix or substring. For example, r"I have (\d+)" with fullmatch would not match "I have 5 cucumbers" because " cucumbers" remains unmatched — this is the correct behavior for step definitions. The FixtureRequest parameter is accepted but unused because the regex parser has no FixtureRequest-dependent behavior (unlike cucumber_expression which uses it for parameter type registry access).

        Delegates:
            - self.regex.fullmatch(name): Performs the pattern matching operation.

        Cohesion:
            The method performs exactly one check: does the full step text match the regex? The bool conversion is standard.

        Separation:
            - parse_arguments: Kept separate because is_matching is a boolean gate while parse_arguments extracts matched values — gate vs extraction.

        Main consumers:
            - pytest_bdd.steps.manager: Called during step definition lookup to find matching step definitions.

        State and side effects:
            None. Pure function of the step name and pattern.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        return bool(self.regex.fullmatch(name))

    def __str__(self) -> str:
        """
        Return the original regex pattern string (normalized via normalize_to_string) used to create this parser, providing .

        Responsibility:
            Returns the original regex pattern string (normalized via normalize_to_string) used to create this parser, providing a human-readable representation for debugging, error messages, and logging. This is the pattern string the user originally passed to the constructor or extracted from the pre-compiled re.Pattern.

        Reason for existence:
            The StepParser protocol requires __str__ for display purposes. The pattern string is the most meaningful representation of a regex parser — it shows exactly what pattern steps are being matched against. The normalize_to_string call ensures consistency for edge cases like StringRepresentable inputs.

        Delegates:
            - normalize_to_string: Converts string-like inputs to canonical form.

        Cohesion:
            Trivially cohesive — returns the stored pattern string.

        Separation:
            - Other parser __str__ methods: Each parser returns its own meaningful representation (parse.format, cucumber_expression.pattern, re.pattern).

        Main consumers:
            - Error messages and logging in pytest_bdd.steps.manager.

        State and side effects:
            None. Read-only.

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
        return normalize_to_string(self.pattern)


register_parser(lambda parserlike: isinstance(parserlike, _RePattern), re)
