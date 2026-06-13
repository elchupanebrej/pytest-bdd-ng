"""
Owns the simplest step definition parser: the `string` class that implements the StepParser protocol using exact stri.

Responsibility:
    Owns the simplest step definition parser: the `string` class that implements the StepParser protocol using exact
    string equality matching. The constructor takes a step name string (normalized via normalize_to_string),
    is_matching() returns True only when the input name exactly equals the stored step name (no pattern matching, no
    regex, no format parsing), parse_arguments() always returns an empty dict (no arguments to extract), and the
    `arguments` property returns an empty collection. This parser is used for step definitions that require exact
    keyword matching without any parameter extraction.

Reason for existence:
    Not all BDD steps have parameters. Simple steps like "Given the system is initialized" match exactly one string and
    extract no arguments. Without the `string` parser, users would need to use a regex like r"^the system is
    initialized$" which is needlessly verbose for exact matches. The `string` parser provides the most efficient
    matching strategy (Python string equality, O(n) comparison) and clearly signals intent: "this step definition
    matches exactly this text, with no arguments."

Delegates:
    - pytest_bdd.parsers.base.StepParser: Provides the base class with the protocol interface.
    - pytest_bdd.util.other.normalize_to_string: Converts StringRepresentable/bytes inputs to canonical string form.
    - pytest_bdd.model.message_extension.StepDefinitionPatternType: Provides pattern type classification.

Cohesion:
    Every method in this class serves exact string matching. The constructor stores the canonical name, is_matching
    compares with ==, parse_arguments returns empty dict, arguments returns empty list, and __str__ returns the stored
    name. There is no pattern compilation, no regex, and no argument parsing — the class is perfectly minimal.

Separation:
    - pytest_bdd.parsers.re_parser.re: Kept separate because re uses regex pattern matching (powerful but complex) while
    string uses exact equality (simple but limited) — opposite ends of the matching complexity spectrum.
    - pytest_bdd.parsers.parse_parser.parse: Kept separate because parse uses format-string matching with argument
    extraction, while string matches exactly with no arguments — parameterized vs literal matching.
    - pytest_bdd.parsers.cucumber_expression: Kept separate because cucumber_expression uses the cucumber-expressions
    library (Gherkin syntax), while string uses pure Python string comparison.

Main consumers:
    - End-user test code via parsers.string("exact step text").
    - pytest_bdd.steps.manager: Uses the StepParser protocol for step matching — string parsers are the first to be
    checked during step lookup due to their simplicity.

State and side effects:
    None, keeps no persistent state. self.name (str) is immutable after construction.

Invariants:
    - is_matching() must use exact equality (==), not substring matching or case-insensitive comparison — the step text
    must be identical.
    - parse_arguments() must always return an empty dict — the string parser never extracts arguments.
    - arguments property must always return an empty collection.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=2
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.util.other import StringRepresentable, normalize_to_string

from .base import StepParser

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from pytest_bdd.compatibility.pytest import FixtureRequest


class string(StepParser):  # noqa: N801 intentional API
    """
    Implements the simplest StepParser protocol variant: exact string equality matching with no argument extraction.

    Responsibility:
        Implements the simplest StepParser protocol variant: exact string equality matching with no argument extraction.
        Stores a canonical step name string, is_matching() returns True only for exact match (self.name == name),
        parse_arguments() unconditionally returns an empty dict, and the `arguments` property returns an empty
        collection. This parser is the fallback/default for step definitions that match literal text with no
        parameterized fields.

    Reason for existence:
        Provides the most efficient and intent-clarifying parser for literal step definitions. When a step has no
        parameters, using string is clearer than a regex (no need to escape special characters, no risk of accidental
        partial matches) and more efficient than the parse library (no compilation overhead). It also serves as the
        canonical example of the minimal StepParser implementation — all required methods are trivially implemented.

    Delegates:
        - normalize_to_string: Converts StringRepresentable/bytes inputs to canonical string form at construction time.
        - StepParser: Provides the protocol interface with default implementations where applicable.

    Cohesion:
        Perfectly cohesive: every method serves exact string matching. There is zero complexity — the class is the
        simplest valid StepParser implementation.

    Separation:
        - re: Kept separate because re does regex matching (complex, powerful) while string does equality matching
        (simple, limited) — opposite complexity levels.
        - parse: Kept separate because parse does format-string matching with argument extraction, while string does
        exact matching with no arguments — parameterized vs literal.
        - cucumber_expression: Kept separate because cucumber_expression uses a third-party library for Gherkin
        expression matching.

    Main consumers:
        - End-user code: parsers.string("exact step text").
        - pytest_bdd.steps.manager: First checked during step lookup due to its simple matching semantics.

    State and side effects:
        None. self.name is immutable after construction.

    Invariants:
        - is_matching must use exact equality (==), case-sensitive, no substring matching.
        - parse_arguments must always return {} regardless of inputs — no exceptions, no special cases.
        - arguments must always return an empty collection.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    type = StepDefinitionPatternType.pytest_bdd_string_expression  # type:ignore[attr-defined]  # upstream type stubs missing this attribute

    def __init__(self, name: StringRepresentable | str | bytes) -> None:
        """
        Initialize a string parser with the exact step name to match.

        Responsibility:
            Initializes a string parser with the exact step name to match. Accepts string-like inputs (str, bytes,
            StringRepresentable) and normalizes them to a canonical str via normalize_to_string. The stored name is used
            for exact equality comparison in is_matching() and for string representation in __str__().

        Reason for existence:
            The simplest possible parser constructor: accept a name, normalize it to a string, store it. The
            StringRepresentable protocol allows custom objects with __str__ methods to be used as step names, while
            bytes inputs are converted to str (assuming UTF-8 or similar encoding). No compilation, no validation beyond
            normalization, no configuration options — this is deliberately minimal.

        Delegates:
            - normalize_to_string: Converts the input name to a canonical str, handling str, bytes, and StringRepresentable.

        Cohesion:
            Performs exactly one operation: normalize input → store. Every line serves this single purpose.

        Separation:
            - Other parser constructors: Those constructors perform compilation (re.compile, parse.compile,
            CucumberExpression construction) while this constructor only normalizes and stores — zero compilation
            overhead.

        Main consumers:
            - User code: parsers.string("step name") — the constructor is the only public API for creating string parsers.

        State and side effects:
            Sets self.name (str). No external side effects.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        self.name = normalize_to_string(name)

    def parse_arguments(  # noqa: PLR6301  -- interface method required by StepParser protocol; must remain an instance method for polymorphism
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,  # noqa: ARG002 overload
        anonymous_group_names: Iterable[str] | None = None,  # noqa: ARG002 overload
    ) -> dict[str, object]:
        """
        Return an empty dict unconditionally; the string parser extracts no arguments from step text because there are no capture groups.

        Responsibility:
            Returns an empty dict unconditionally — the string parser extracts no arguments from step text because there
            are no capture groups or parameterized fields in an exact string match. All parameters (request, name,
            anonymous_group_names) are accepted but unused, conforming to the StepParser protocol signature for
            polymorphism across all parser types. This method exists solely to satisfy the protocol interface.

        Reason for existence:
            The StepParser protocol requires parse_arguments(), and the step definition manager calls it uniformly for
            all parser types after a successful is_matching() check. For the string parser, there are never arguments to
            extract, so this method returns an empty dict. It cannot be omitted because the manager expects the method
            to exist — raising NotImplementedError would break step execution for string-matched steps.

        Delegates:
            - None. Returns a literal empty dict.

        Cohesion:
            Perfectly minimal — returns the only valid result (empty dict) with no branching, no processing, no conditions.

        Separation:
            - Other parser parse_arguments methods: Those methods extract actual values from match objects, while this
            method is a trivial no-op — extraction vs no-op.

        Main consumers:
            - pytest_bdd.steps.manager: Called after is_matching() returns True to extract step arguments for function
            parameter injection.

        State and side effects:
            None. Returns a constant empty dict.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return {}

    @property
    def arguments(self) -> Collection[str]:
        """
        Returns an empty collection — the string parser has no named arguments because it matches exact text with no capture .

        Responsibility:
            Returns an empty collection — the string parser has no named arguments because it matches exact text with no
            capture groups or parameterized fields. The step definition manager uses this property to validate step
            function signatures: an empty collection means the step function should not expect any step-derived
            arguments.

        Reason for existence:
            The StepParser protocol requires an `arguments` property. For the string parser, this is always empty
            because exact string matching has no concept of parameterized fields. Returning an empty list ([] ) is the
            simplest and most efficient implementation — no computation, no state access, just a constant.

        Delegates:
            - None. Returns a literal empty list.

        Cohesion:
            Trivially cohesive — returns the only valid result for a parser that extracts no arguments.

        Separation:
            - Other parser arguments properties: Those properties extract group names from compiled patterns, while this
            property is constant — compiled extraction vs constant.

        Main consumers:
            - pytest_bdd.steps.manager: Uses arguments to validate step function signatures against parser capabilities.

        State and side effects:
            None. Returns a constant empty list.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return []

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
    ) -> bool:
        """
        Test whether a step name string exactly matches the stored step name using Python's equality operator (==).

        Responsibility:
            Tests whether a step name string exactly matches the stored step name using Python's equality operator (==).
            This is case-sensitive, requires the full strings to be identical, and performs no substring matching.
            FixtureRequest accepted but unused — protocol compatibility with other parsers that need request context.

        Reason for existence:
            This is the simplest possible matching algorithm: string equality. It's O(n) in the length of the shorter
            string, requires no compilation, catches no exceptions, and returns immediately. For steps with exact
            keyword matches (no parameters), this is the most efficient matching strategy available. The == operator is
            used deliberately (not `is`) because string identity is not guaranteed — the step name comes from Gherkin
            parsing, and the stored name comes from the user's decorator.

        Delegates:
            - str.__eq__: Python's built-in string equality comparison.

        Cohesion:
            Performs exactly one comparison: does the input name equal the stored name? No branching, no conditions, no
            preprocessing.

        Separation:
            - Other parser is_matching methods: Those methods invoke pattern matching engines (regex.fullmatch,
            parse.Parser.parse, CucumberExpression.match), while string uses simple == — pattern matching vs literal
            comparison.

        Main consumers:
            - pytest_bdd.steps.manager: Called during step definition lookup to find which step definition matches the
            current scenario step text.

        State and side effects:
            None. Pure function of the input name and stored name.

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
        return bool(self.name == name)

    def __str__(self) -> str:
        """
        Return the stored step name string, providing a human-readable representation for debugging, error messages, and logging.

        Responsibility:
            Returns the stored step name string, providing a human-readable representation for debugging, error
            messages, and logging. Since the string parser matches exact text, the stored name is both the parser's
            identity and its matching pattern — there is no distinction between "pattern" and "name" as there is with
            regex or parse-format parsers.

        Reason for existence:
            The StepParser protocol requires __str__ for display purposes. For the string parser, the most meaningful
            representation is simply the exact step name — there is no pattern to display separately. This is simpler
            than other parsers which must return format strings or pattern strings.

        Delegates:
            - self.name: The stored canonical step name string.

        Cohesion:
            Trivially cohesive — returns the stored name.

        Separation:
            - Other parser __str__ methods: Those return format strings or pattern strings, while string returns the
            exact match name — identity vs pattern representation.

        Main consumers:
            - Error messages in pytest_bdd.steps.manager when reporting which step definition matched or failed to match.

        State and side effects:
            None. Read-only property.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return self.name
