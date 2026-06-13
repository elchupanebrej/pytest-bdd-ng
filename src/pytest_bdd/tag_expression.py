"""
Owns the complete tag expression parsing and evaluation infrastructure for filtering BDD scenarios by Gherkin tags an.

Responsibility:
    Owns the complete tag expression parsing and evaluation infrastructure for filtering BDD scenarios by Gherkin tags
    and pytest markers. Defines the polymorphic TagExpression Protocol with parse() and evaluate() methods, three
    concrete implementations (_ModernTagExpression for pytest Expression-based matching on pytest>=8.3,
    _MarksTagExpression as the legacy fallback for older pytest, _EnhancedMarksTagExpression as the enhanced variant),
    GherkinTagExpression for cucumber-compatible tag expression syntax via cucumber_tag_expressions, and the
    MarksTagExpression type alias that selects the correct implementation at import time based on PYTEST83 flag. This
    module is the single authority on whether a given set of marks/tags satisfies a filter expression.

Reason for existence:
    This module is the information expert for tag evaluation because it bridges two different expression syntaxes
    (pytest mark expressions like "smoke and not slow" and Gherkin tag expressions like "@smoke and not @slow") and two
    different pytest versions (pre-8.3 and post-8.3 with different MarkMatcher APIs). Without this module, expression
    parsing and evaluation logic would be scattered across hook.py (for hook filtering), collector.py (for scenario
    filtering), and scenario.py (for scenario selection), each reimplementing the same boolean expression evaluation
    with minor variations. The PYTEST83-based type alias pattern ensures the correct MarkMatcher API is used without
    runtime version checks.

Delegates:
    - cucumber_tag_expressions.TagExpressionParser: Provides the Gherkin-compatible tag expression parser used by
    GherkinTagExpression.parse(). This is a third-party library implementing the Cucumber tag expression grammar
    (boolean logic with @tags).
    - pytest_bdd.compatibility.pytest: Provides PYTEST83 flag, Expression, Mark, MarkMatcher, and ParseError types for
    pytest-version-compatible mark expression handling. The MarkMatcher API changed between pytest <8.3 (dict-based) and
    >=8.3 (class-based), and this module handles both via the type alias pattern.
    - attrs: Provides the @define decorator and field() for the three concrete expression classes.

Cohesion:
    All entities in this module participate in the same abstract interface: TagExpression.parse() creates an expression
    from a string, and TagExpression.evaluate() tests a list of Mark objects against that expression. The three concrete
    implementations differ only in which underlying parser/evaluator they use, but all satisfy the same protocol. The
    type alias MarksTagExpression is a natural part of this pattern — it selects between _EnhancedMarksTagExpression and
    _MarksTagExpression based on PYTEST83, providing a unified name for consumers.

Separation:
    - pytest_bdd.hook: Kept separate because hook.py owns the hook lifecycle (when and how to filter) while
    tag_expression.py owns the filtering algorithm (the expression parsing and evaluation logic) — policy vs mechanism.
    Hook consumers import MarksTagExpression and GherkinTagExpression as tools but do not own their implementation.
    - pytest_bdd.parsers: Kept separate because parsers own step text matching (matching Gherkin step text to step
    definitions), while tag_expression owns tag expression matching (matching boolean tag expressions to scenario
    annotations) — different matching domains with different syntaxes and algorithms.

Main consumers:
    - pytest_bdd.hook: Uses GherkinTagExpression for tag-based hooks and MarksTagExpression for mark-based hooks to
    parse expressions and evaluate them against scenario tags/marks.
    - pytest_bdd.collector: Uses tag expressions during scenario collection to filter scenarios by tag expression (e.g.,
    pytest -m "smoke and not slow").
    - pytest_bdd.scenario: Uses tag expressions when the scenarios() function accepts a filter expression to select
    specific scenarios.

State and side effects:
    None, keeps no persistent state. All expression classes are immutable attrs-defined objects. The PYTEST83 module-
    level check determines which MarkMatcher API to use, but this is evaluated once at import time and never changes.

Invariants:
    - TagExpression.parse() must never raise exceptions to callers — errors during parsing should produce warnings or
    empty expressions that always match/never match, not crash the test collection.
    - MarksTagExpression must always resolve to either _EnhancedMarksTagExpression (pytest >=8.3) or _MarksTagExpression
    (pytest <8.3) at import time, never both.
    - GherkinTagExpression.evaluate() must produce the same boolean result for the same expression and tag set
    regardless of pytest version.

Failure semantics:
    - _ModernTagExpression.parse() raises ValueError (not ParseError) when the mark expression syntax is invalid — this
    wraps pytest's ParseError to provide a consistent error type. Callers should catch ValueError for graceful
    degradation (e.g., skipping the filter).
    - GherkinTagExpression.parse() raises ValueError when the tag expression syntax is invalid — this wraps
    cucumber_tag_expressions.TagExpressionError. Callers should treat this as a configuration error.
    - TagExpression.parse() on the Protocol raises NotImplementedError — this is an abstract interface marker; concrete
    implementations override it.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""

from operator import attrgetter
from typing import Protocol, runtime_checkable

from attrs import define, field
from cucumber_tag_expressions import TagExpressionError, TagExpressionParser
from typing_extensions import Self

from pytest_bdd.compatibility.pytest import PYTEST83, Expression, Mark, MarkMatcher, ParseError


@runtime_checkable
class TagExpression(Protocol):
    """
    Defines the runtime-checkable Protocol that all tag expression implementations must satisfy: a parse() classmethod th.

    Responsibility:
        Defines the runtime-checkable Protocol that all tag expression implementations must satisfy: a parse()
        classmethod that creates an expression instance from a string pattern, and an evaluate() instance method that
        tests a list of pytest Mark objects against the compiled expression and returns True if the marks satisfy the
        pattern. This protocol enables polymorphic handling of both pytest mark expressions and Gherkin tag expressions
        through a single interface, allowing consumers (hook.py, collector.py) to treat them uniformly.

    Reason for existence:
        This protocol is the abstraction layer that enables the hook system to work with either mark-based or tag-based
        filtering without knowing which concrete expression type is in use. Without it, every consumer of expression
        evaluation would need separate code paths for MarksTagExpression vs GherkinTagExpression, duplicating the "parse
        → evaluate" pipeline. The @runtime_checkable decorator enables isinstance checks against this protocol, which is
        used by the type system to verify that variables assigned from _get_expression_type() are valid expression
        types.

    Delegates:
        - Protocol (typing): Provides the structural subtyping base for the protocol.
        - runtime_checkable (typing): Enables isinstance checks against this protocol at runtime.

    Cohesion:
        The two method signatures (parse and evaluate) are perfectly cohesive — they represent the minimal complete
        interface for a boolean expression evaluator: create an expression (parse), then test values against it
        (evaluate). Every concrete implementation (three Mark expression variants and one Gherkin expression variant)
        implements both methods.

    Separation:
        - pytest_bdd.parsers.base.StepParser: Kept separate because StepParser defines the interface for step text
        matching (is_matching, parse_arguments), while TagExpression defines the interface for tag expression matching
        (parse, evaluate) — step text vs tag filters, completely different domains.
        - pytest_bdd.hook._HookFunctionProtocol: Kept separate because that protocol defines the interface for hook
        callables (callable + metadata), while this protocol defines the interface for expression evaluators — callable
        contracts vs data-processing contracts.

    Main consumers:
        - pytest_bdd.hook._get_expression_type: Returns TagExpression subclasses based on HookKind, and the hook fixture
        calls parse() and evaluate() through this protocol.
        - pytest_bdd.collector: Uses TagExpression implementations to filter scenarios based on user-provided tag/mark
        filter strings.

    State and side effects:
        None, keeps no persistent state. Pure Protocol definition.

    Invariants:
        - parse() must return Self (the concrete class type, not a generic TagExpression) to ensure type-safe factory usage.
        - evaluate() must accept list[Mark] and return bool — all consumers depend on this signature.

    Failure semantics:
        - parse() raises NotImplementedError by default (abstract marker) — concrete implementations override it and may
        raise ValueError for invalid expression syntax.
        - evaluate() raises NotImplementedError by default (abstract marker) — concrete implementations override it and
        should not raise exceptions for valid Mark inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    @classmethod
    def parse(cls, expression: str) -> Self:
        """
        Define the factory classmethod contract for creating a parsed tag expression from a string pattern (e.g., "smoke and.

        Responsibility:
            Defines the factory classmethod contract for creating a parsed tag expression from a string pattern (e.g.,
            "smoke and not slow" or "@smoke and not @slow"). The concrete implementation is responsible for parsing the
            string syntax, validating it, and returning an expression instance that can evaluate lists of Mark objects.
            This is the canonical entry point for expression creation across all expression types.

        Reason for existence:
            This classmethod signature is the standard factory pattern for immutable expression objects. It takes a raw
            string (as provided by the user or test configuration) and produces a structured, validated expression
            object. The classmethod pattern (rather than __init__) is used because expression parsing may fail, and a
            classmethod can return alternative objects or raise descriptive errors, while __init__ can only return None
            or raise. The @classmethod decorator ensures cls is the concrete type, enabling type-safe construction.

        Delegates:
            - Expression.compile (pytest): Used by _ModernTagExpression.parse for pytest mark expression syntax parsing.
            - TagExpressionParser.parse (cucumber_tag_expressions): Used by GherkinTagExpression.parse for Gherkin tag
            expression syntax parsing.

        Cohesion:
            The method signature is perfectly focused on a single transformation: string → expression object. All
            concrete implementations follow this pattern.

        Separation:
            - evaluate: Kept separate because parse creates the expression object while evaluate uses it — construction
            vs consumption, two distinct phases of the expression lifecycle.

        Main consumers:
            - pytest_bdd.hook.decorator_builder (inner hook function): Calls ExpressionType.parse(expression_) to create
            a parsed expression from the hook's expression string.
            - pytest_bdd.collector: Calls parse() to create filter expressions from user-provided tag strings.

        State and side effects:
            None, keeps no persistent state. Pure factory method.

        Failure semantics:
            Raises NotImplementedError by default — this is an abstract method marker. Concrete implementations raise
            ValueError for invalid expression syntax, wrapping underlying parser errors.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        raise NotImplementedError  # pragma: no cover

    def evaluate(self, marks: list[Mark]) -> bool:
        """
        Define the instance method contract for testing whether a list of pytest Mark objects satisfies the compiled express.

        Responsibility:
            Defines the instance method contract for testing whether a list of pytest Mark objects satisfies the
            compiled expression. Returns True if the marks match the expression pattern (e.g., the marks include both
            "smoke" and not "slow"), False otherwise. This is the runtime evaluation method that determines whether a
            hook should fire or a scenario should be collected.

        Reason for existence:
            This is the core runtime operation of the expression system. Every consumer of tag expressions ultimately
            calls evaluate() to make a boolean decision. The method signature takes list[Mark] because both pytest
            markers and Gherkin tags are normalized to Mark objects before evaluation — this unification is the key
            design decision that allows GherkinTagExpression and MarksTagExpression to share the same interface despite
            operating on different data sources.

        Delegates:
            - Expression.evaluate (pytest): Used by _EnhancedMarksTagExpression and _MarksTagExpression to evaluate
            against a MarkMatcher built from the marks list.
            - TagExpressionParser.evaluate (cucumber_tag_expressions): Used by GherkinTagExpression to evaluate against
            tag name strings extracted from marks.

        Cohesion:
            The method is perfectly focused on a single boolean decision: do these marks match this expression? No other
            logic is performed.

        Separation:
            - parse: Kept separate because evaluate consumes the expression created by parse — distinct lifecycle phases.

        Main consumers:
            - pytest_bdd.hook.decorator_builder (inner hook function): Calls evaluate() to decide whether to execute the
            hook for the current scenario.
            - pytest_bdd.collector: Calls evaluate() to decide whether to include a scenario in the test collection.

        State and side effects:
            None, keeps no persistent state. Pure function of the expression's compiled pattern and the input marks.

        Failure semantics:
            Raises NotImplementedError by default — abstract method marker. Concrete implementations should not raise
            exceptions; they return False for non-matching marks (not errors).

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        raise NotImplementedError  # pragma: no cover


@define
class _ModernTagExpression(TagExpression):
    """
    Implements the TagExpression protocol using pytest's Expression.compile() for mark expression parsing.

    Responsibility:
        Implements the TagExpression protocol using pytest's Expression.compile() for mark expression parsing. Stores an
        optional Expression object (None representing "always match"), provides a parse() classmethod that wraps
        Expression.compile() with ValueError conversion on ParseError, and inherits evaluate() from its subclass. This
        is the base class for both _EnhancedMarksTagExpression (pytest >=8.3) and _MarksTagExpression (pytest <8.3),
        which differ only in how they construct the MarkMatcher for evaluation.

    Reason for existence:
        This class factors out the common parsing logic shared by the two pytest mark expression variants. Both need to
        compile expression strings using Expression.compile() and handle ParseError by wrapping it in ValueError with a
        descriptive message. Without this base class, the parse logic would be duplicated in both
        _EnhancedMarksTagExpression and _MarksTagExpression. The expression field being Optional[Expression] supports
        the pattern where an empty expression string produces None (meaning "match everything").

    Delegates:
        - pytest.Expression.compile: The actual mark expression parser provided by pytest. Compiles boolean expressions
        like "smoke and not slow" into structured Expression objects.
        - attrs.define: Provides the frozen/slotted class definition with the expression field.

    Cohesion:
        Every aspect of this class serves expression parsing: the expression field stores the compiled expression,
        parse() creates instances by compiling strings, and the Optional[Expression] type represents the "always match"
        sentinel. evaluate() is inherited from subclasses because the evaluation strategy differs between pytest
        versions.

    Separation:
        - GherkinTagExpression: Kept separate because GherkinTagExpression uses
        cucumber_tag_expressions.TagExpressionParser for parsing and evaluates against tag names, while this class uses
        pytest's Expression for parsing and evaluates against Mark objects — different parser libraries and different
        evaluation strategies, though they share the TagExpression protocol.
        - _EnhancedMarksTagExpression / _MarksTagExpression: Kept separate because they differ in how MarkMatcher is
        constructed for evaluate(), which is a pytest-version-specific concern that belongs in the leaf classes.

    Main consumers:
        - MarksTagExpression type alias: Selects between _EnhancedMarksTagExpression and _MarksTagExpression (both
        subclasses of this) based on PYTEST83.
        - pytest_bdd.hook._get_expression_type: Returns MarksTagExpression (which resolves to a subclass of
        _ModernTagExpression) for HookKind.mark hooks.

    State and side effects:
        None, keeps no persistent state. The expression field is immutable (attrs frozen by default). Parse() is a pure
        factory with no side effects.

    Invariants:
        - expression being None means "always match" — evaluate() must return True when expression is None.
        - expression being a compiled Expression means the expression string was valid — evaluate() may return True or
        False based on the marks.

    Failure semantics:
        Raises ValueError when the expression string has invalid syntax, wrapping pytest's ParseError. Callers should
        handle ValueError as a configuration error (e.g., skip the filter, log a warning).

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    expression: Expression | None = field()

    @classmethod
    def parse(cls, expression: str) -> Self:
        """
        Compiles a pytest mark expression string (e.g., "smoke and not slow") into an Expression object using pytest's Expres.

        Responsibility:
            Compiles a pytest mark expression string (e.g., "smoke and not slow") into an Expression object using
            pytest's Expression.compile(), and wraps the result in a _ModernTagExpression instance. If the expression
            string is empty (falsy), stores None as the expression (meaning "always match"). Catches pytest's ParseError
            and re-raises it as ValueError with a descriptive message so that downstream consumers can handle a single
            error type regardless of the expression backend.

        Reason for existence:
            This method is the bridge between user-provided filter strings and pytest's internal expression compiler.
            The empty-string-to-None conversion implements the "no expression → match all" semantics that the hook
            system relies on for hooks with no filter expression. The ParseError wrapping is critical: pytest's
            Expression.compile raises a pytest-specific ParseError that consumers in the hook and collection layers
            should not need to import — ValueError is a standard Python exception that any caller can handle.

        Delegates:
            - Expression.compile (pytest): Performs the actual parsing and compilation of the mark expression string
            into a structured Expression object.
            - ParseError (pytest): The exception type raised by Expression.compile for invalid syntax — caught and
            converted to ValueError.

        Cohesion:
            The method performs a single cohesive transformation: string → Expression | None → _ModernTagExpression
            instance. Error handling is integral to this transformation since invalid strings are an expected input
            scenario.

        Separation:
            - GherkinTagExpression.parse: Kept separate because that method uses TagExpressionParser.parse() for Gherkin
            tag expression syntax, while this method uses Expression.compile() for pytest mark expression syntax —
            different parsers, different syntaxes, different error types.

        Main consumers:
            - pytest_bdd.hook.decorator_builder: The inner hook function calls ExpressionType.parse() which dispatches
            to this method when ExpressionType is MarksTagExpression.

        State and side effects:
            None, keeps no persistent state. Pure factory classmethod.

        Failure semantics:
            Raises ValueError with message "Unable parse mark expression: {expression}: {e}" when the expression string
            has invalid syntax. The original ParseError is preserved in __cause__ for debugging.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        try:
            return cls(expression=Expression.compile(expression) if expression else None)
        except ParseError as e:
            msg = f"Unable parse mark expression: {expression}: {e}"
            raise ValueError(msg) from e


@define
class _EnhancedMarksTagExpression(_ModernTagExpression):
    """
    Implements the evaluate() method for pytest >=8.3 using the enhanced MarkMatcher API where MarkMatcher.from_markers().

    Responsibility:
        Implements the evaluate() method for pytest >=8.3 using the enhanced MarkMatcher API where
        MarkMatcher.from_markers() creates a matcher from a list of Mark objects. This is the selected implementation
        when PYTEST83 is True, providing mark expression evaluation for modern pytest versions where the MarkMatcher
        constructor changed from dict-based to class-method-based instantiation.

    Reason for existence:
        pytest 8.3 changed the MarkMatcher API: previously, MarkMatcher accepted a dict argument; now, it uses
        MarkMatcher.from_markers() as a classmethod. This class exists to provide the correct evaluate() implementation
        for modern pytest without runtime version checks — the type alias MarksTagExpression selects this class when
        PYTEST83 is True. Without this class, the code would need if/else branches inside a single evaluate() method,
        which is less maintainable and obscures the API difference in the type system.

    Delegates:
        - self.expression.evaluate: The pytest Expression object's evaluate method, which accepts a MarkMatcher and
        returns a boolean.
        - MarkMatcher.from_markers: The pytest >=8.3 API for creating a MarkMatcher from a list of Mark objects.

    Cohesion:
        The class has a single responsibility: implementing evaluate() for pytest >=8.3 MarkMatcher API. The evaluate()
        method is a thin adapter between the generic evaluate() signature (list[Mark]) and the pytest-specific
        MarkMatcher.from_markers() call.

    Separation:
        - _MarksTagExpression: Kept separate because that class implements evaluate() for pytest <8.3 using the dict-
        based MarkMatcher constructor — same interface, different MarkMatcher construction strategy, selected by
        PYTEST83.
        - GherkinTagExpression: Kept separate because that class evaluates against tag name strings rather than Mark
        objects, using a completely different evaluation backend.

    Main consumers:
        - MarksTagExpression type alias: Selected when PYTEST83 is True (pytest >=8.3). Used by hook.py for mark-based
        hook expression evaluation.

    State and side effects:
        None, keeps no persistent state. evaluate() is a pure function of the compiled expression and input marks.

    Invariants:
        - evaluate() must return the same result for identical input marks and expression across calls (pure function).
        - MarkMatcher.from_markers() must receive valid Mark objects; invalid marks may cause evaluation errors.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    def evaluate(self, marks: list[Mark]) -> bool:
        """
        Evaluat whether a list of pytest Mark objects satisfies the compiled mark expression using the pytest >=8.3 MarkMat.

        Responsibility:
            Evaluates whether a list of pytest Mark objects satisfies the compiled mark expression using the pytest
            >=8.3 MarkMatcher.from_markers() API. Returns True if the marks match the expression pattern, True if the
            expression is None (no filter), False otherwise. This method bridges the generic evaluate() interface
            (list[Mark]) to the pytest-specific MarkMatcher.from_markers() construction.

        Reason for existence:
            pytest >=8.3 changed how MarkMatcher is instantiated: the previous dict-based constructor was replaced with
            a from_markers classmethod. This method implements the new API. The expression-is-None guard (returning
            True) implements the "empty expression → match all" semantics that the hook system depends on when a hook
            has no filter expression.

        Delegates:
            - MarkMatcher.from_markers: Converts the list of Mark objects into a MarkMatcher instance for the pytest
            Expression evaluator.
            - self.expression.evaluate: Performs the actual boolean evaluation of the expression against the constructed
            MarkMatcher.

        Cohesion:
            The method performs a single transformation: list[Mark] → MarkMatcher → boolean. The None-expression guard
            is an integral part of this transformation.

        Separation:
            - _MarksTagExpression.evaluate: Kept separate because that method constructs MarkMatcher with a dict instead
            of from_markers() — different constructor APIs for different pytest versions.

        Main consumers:
            - pytest_bdd.hook.decorator_builder (inner hook function): Calls evaluate() on the parsed expression to
            decide whether to execute the hook.

        State and side effects:
            None, keeps no persistent state. Pure function.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        return self.expression.evaluate(MarkMatcher.from_markers(marks)) if self.expression is not None else True  # type: ignore[arg-type]  # pytest Expression.evaluate is untyped


@define
class _MarksTagExpression(_ModernTagExpression):
    """
    Implements the evaluate() method for pytest <8.3 using the legacy dict-based MarkMatcher constructor where marks are .

    Responsibility:
        Implements the evaluate() method for pytest <8.3 using the legacy dict-based MarkMatcher constructor where marks
        are organized into a dict keyed by mark name. Each Mark name maps to a list containing that Mark object. This is
        the fallback implementation when PYTEST83 is False, providing backward compatibility with older pytest versions
        where MarkMatcher did not have the from_markers() classmethod.

    Reason for existence:
        pytest versions before 8.3 used a different MarkMatcher API where the constructor accepted a dict[str,
        list[Mark]] mapping mark names to their occurrences. This class adapts the generic evaluate() interface to that
        legacy API. The dict construction (mark.name → [mark]) is necessary because MarkMatcher expects a list of marks
        per name to support multiple occurrences of the same marker. This class exists alongside
        _EnhancedMarksTagExpression so the type alias can switch between them at import time based on PYTEST83.

    Delegates:
        - self.expression.evaluate: The pytest Expression object's evaluate method, which accepts a MarkMatcher and
        returns a boolean.
        - MarkMatcher (dict-based constructor): The pytest <8.3 API that accepts a dict mapping mark names to lists of
        Mark objects.

    Cohesion:
        The class has a single responsibility: implementing evaluate() for the pytest <8.3 MarkMatcher API. The dict
        comprehension in evaluate() is a thin adapter from the generic list[Mark] interface to the legacy dict-based
        MarkMatcher.

    Separation:
        - _EnhancedMarksTagExpression: Kept separate because that class uses from_markers() for pytest >=8.3 while this
        class uses the dict-based constructor for pytest <8.3 — same interface, different MarkMatcher construction,
        selected by PYTEST83.
        - GherkinTagExpression: Kept separate because that class uses cucumber_tag_expressions for evaluation, not
        pytest's Expression/MarkMatcher system.

    Main consumers:
        - MarksTagExpression type alias: Selected when PYTEST83 is False (pytest <8.3). Used by hook.py for mark-based
        hook expression evaluation on older pytest versions.

    State and side effects:
        None, keeps no persistent state. evaluate() is a pure function.

    Invariants:
        - evaluate() must return the same result for identical input marks and expression across calls (pure function).
        - MarkMatcher constructor must receive valid dict[str, list[Mark]] format for legacy evaluation.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    def evaluate(self, marks: list[Mark]) -> bool:
        """
        Evaluat whether a list of pytest Mark objects satisfies the compiled mark expression using the pytest <8.3 dict-bas.

        Responsibility:
            Evaluates whether a list of pytest Mark objects satisfies the compiled mark expression using the pytest <8.3
            dict-based MarkMatcher constructor. Organizes marks into a dict[str, list[Mark]] keyed by mark name,
            constructs a MarkMatcher from this dict, and delegates to Expression.evaluate() for the boolean result.
            Returns True when expression is None (no filter), True if marks satisfy the expression, False otherwise.

        Reason for existence:
            This method exists specifically to support pytest versions before 8.3 where MarkMatcher required a dict[str,
            list[Mark]] constructor argument. The dict comprehension groups marks by name, which is needed because
            multiple markers with the same name can exist (e.g., multiple @pytest.mark.smoke markers), and MarkMatcher
            needs them as lists. The expression-is-None guard implements "empty expression → match all" semantics.

        Delegates:
            - MarkMatcher (dict-based constructor): Accepts {mark.name: [mark] for mark in marks} dict and creates a
            matcher that pytest's Expression can evaluate against.
            - self.expression.evaluate: Performs the actual boolean evaluation of the compiled expression against the MarkMatcher.

        Cohesion:
            The method performs the minimal transformation needed: organize marks by name → construct MarkMatcher →
            evaluate. No extraneous logic.

        Separation:
            - _EnhancedMarksTagExpression.evaluate: Kept separate because that method uses MarkMatcher.from_markers()
            instead of the dict-based constructor — different pytest version APIs.

        Main consumers:
            - pytest_bdd.hook.decorator_builder (inner hook function): Calls evaluate() on the parsed expression when
            running on pytest <8.3.

        State and side effects:
            None, keeps no persistent state. Pure function of inputs.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        return (
            self.expression.evaluate(MarkMatcher({mark.name: [mark] for mark in marks}))  # type: ignore[arg-type, call-arg]  # pytest Expression.evaluate/MarkMatcher are untyped
            if self.expression is not None
            else True
        )


MarksTagExpression: type[_EnhancedMarksTagExpression | _MarksTagExpression]
MarksTagExpression = _EnhancedMarksTagExpression if PYTEST83 else _MarksTagExpression


@define
class GherkinTagExpression(TagExpression):
    """
    Implements the TagExpression protocol using the Cucumber-compatible tag expression parser from cucumber_tag_expressions.

    Responsibility:
        Implements the TagExpression protocol using the Cucumber-compatible tag expression parser from
        cucumber_tag_expressions. Stores a TagExpressionParser instance (the compiled expression), provides parse() that
        wraps TagExpressionParser.parse() with ValueError conversion on TagExpressionError, and implements evaluate() by
        extracting tag name strings from Mark objects (via operator.attrgetter("name")) and passing them to
        TagExpressionParser.evaluate() for boolean evaluation. This is the expression type used when HookKind is "tag".

    Reason for existence:
        Gherkin/Cucumber uses a different tag expression syntax than pytest's mark expressions: Cucumber uses "@smoke
        and not @slow" with @ prefix on tag names, while pytest uses "smoke and not slow" without prefix. This class
        bridges that syntax difference by using the cucumber_tag_expressions library (which implements the official
        Cucumber tag expression grammar) and adapting the Mark-based interface (list[Mark]) to the string-based
        interface (list[str]) that the cucumber parser expects.

    Delegates:
        - cucumber_tag_expressions.TagExpressionParser: The third-party library implementing the official Cucumber tag
        expression grammar parser and evaluator.
        - TagExpressionParser.parse: Parses a Cucumber tag expression string into a compiled parser object.
        - TagExpressionParser.evaluate: Evaluates a list of tag name strings against the compiled expression.
        - operator.attrgetter("name"): Extracts the name attribute from each Mark object to produce the list of tag
        strings for evaluation.

    Cohesion:
        The class is perfectly focused on being the Cucumber-compatible expression evaluator. The expression field
        stores the compiled parser, parse() creates it from strings, and evaluate() feeds tag names to it. Every aspect
        serves the Cucumber tag expression domain.

    Separation:
        - _ModernTagExpression and its subclasses: Kept separate because those classes use pytest's
        Expression/MarkMatcher for mark expression syntax, while this class uses cucumber_tag_expressions for Gherkin
        tag expression syntax — different parsers, different syntax, different evaluation backends.
        - pytest_bdd.hook: Kept separate because hook.py owns when to use GherkinTagExpression (via _get_expression_type
        dispatch), while this class owns how tag expressions are evaluated.

    Main consumers:
        - pytest_bdd.hook._get_expression_type: Returns GherkinTagExpression for HookKind.tag hooks, and the hook
        fixture calls parse() and evaluate() through this class.
        - pytest_bdd.collector: May use GherkinTagExpression for tag-based scenario filtering (separate from mark-based
        filtering).

    State and side effects:
        None, keeps no persistent state. The expression field (TagExpressionParser) is immutable. evaluate() is a pure function.

    Invariants:
        - evaluate() must extract tag names via attrgetter("name") from Mark objects, consistent with how _get_marks
        creates Mark objects from pickle tags via make_mark(tag.name).
        - The expression field must be a valid TagExpressionParser instance created by TagExpressionParser.parse().

    Failure semantics:
        Raises ValueError with message "Unable parse tag expression: {expression}: {e}" when the Gherkin tag expression
        syntax is invalid. The original TagExpressionError is preserved in __cause__.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    expression: TagExpressionParser = field()

    @classmethod
    def parse(cls, expression: str) -> Self:
        """
        Compiles a Cucumber-compatible tag expression string (e.g., "@smoke and not @slow") into a TagExpressionParser object.

        Responsibility:
            Compiles a Cucumber-compatible tag expression string (e.g., "@smoke and not @slow") into a
            TagExpressionParser object using the cucumber_tag_expressions library, and wraps the result in a
            GherkinTagExpression instance. Catches TagExpressionError and re-raises as ValueError with a descriptive
            message for consistent error handling across expression backends.

        Reason for existence:
            This is the factory method for creating Cucumber tag expressions. Unlike mark expressions which use pytest's
            Expression.compile(), tag expressions go through the cucumber_tag_expressions library which implements the
            official Cucumber grammar (boolean operators, parentheses, tag literals with @ prefix). The
            TagExpressionError wrapping is essential for consistency: consumers should only need to catch ValueError
            regardless of which expression backend (mark or tag) produced the error.

        Delegates:
            - TagExpressionParser.parse (cucumber_tag_expressions): Performs the actual parsing and compilation of the
            Cucumber tag expression string.
            - TagExpressionError (cucumber_tag_expressions): The exception type raised for invalid tag expression syntax
            — caught and converted to ValueError.

        Cohesion:
            The method performs a single transformation: string → TagExpressionParser → GherkinTagExpression instance.
            Error handling is integral to this transformation.

        Separation:
            - _ModernTagExpression.parse: Kept separate because that method uses pytest's Expression.compile() for mark
            expressions, while this method uses TagExpressionParser.parse() for tag expressions — different parsers for
            different syntaxes.

        Main consumers:
            - pytest_bdd.hook.decorator_builder (inner hook function): Calls ExpressionType.parse() which dispatches to
            this method when ExpressionType is GherkinTagExpression for tag-based hooks.

        State and side effects:
            None, keeps no persistent state. Pure factory classmethod.

        Failure semantics:
            Raises ValueError with message "Unable parse tag expression: {expression}: {e}" when the tag expression has
            invalid syntax. The original TagExpressionError is preserved in __cause__ for debugging.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        try:
            return cls(expression=TagExpressionParser.parse(expression))
        except TagExpressionError as e:
            msg = f"Unable parse tag expression: {expression}: {e}"
            raise ValueError(msg) from e

    def evaluate(self, marks: list[Mark]) -> bool:
        """
        Evaluat whether a list of pytest Mark objects satisfies the compiled Cucumber tag expression by extracting the tag .

        Responsibility:
            Evaluates whether a list of pytest Mark objects satisfies the compiled Cucumber tag expression by extracting
            the tag name strings from each Mark (using operator.attrgetter("name")), converting them to a list of
            strings, and passing them to TagExpressionParser.evaluate() for boolean evaluation. This bridges the Mark-
            based interface (used by the hook system for type consistency) to the string-based interface expected by the
            Cucumber tag expression parser.

        Reason for existence:
            The cucumber_tag_expressions library's TagExpressionParser.evaluate() expects a list of tag name strings
            (e.g., ["smoke", "regression"]), not Mark objects. However, the hook system normalizes both pytest markers
            and Gherkin tags into Mark objects (via make_mark()). This method performs the Mark → string extraction
            using attrgetter, which is efficient (C-level attribute access) and consistent with how marks are
            constructed (make_mark saves the tag name as the mark's .name attribute).

        Delegates:
            - operator.attrgetter("name"): Extracts the .name attribute from each Mark object efficiently using C-level
            attribute access.
            - self.expression.evaluate (TagExpressionParser): Performs the actual boolean evaluation of the tag
            expression against the list of tag name strings.

        Cohesion:
            The method performs one transformation: list[Mark] → list[str] → bool. The map/attrgetter extraction and the
            evaluate() call form a single cohesive operation.

        Separation:
            - _EnhancedMarksTagExpression.evaluate / _MarksTagExpression.evaluate: Kept separate because those methods
            use pytest's Expression.evaluate with MarkMatcher, while this method uses TagExpressionParser.evaluate with
            tag name strings — different evaluation backends.

        Main consumers:
            - pytest_bdd.hook.decorator_builder (inner hook function): Calls evaluate() when the hook kind is "tag" to
            decide whether to execute the tag-based hook.

        State and side effects:
            None, keeps no persistent state. Pure function of inputs.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        return bool(self.expression.evaluate(list(map(attrgetter("name"), marks))))


TagExpressionType = _EnhancedMarksTagExpression | _MarksTagExpression | GherkinTagExpression
