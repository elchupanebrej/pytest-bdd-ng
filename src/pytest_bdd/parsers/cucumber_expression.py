"""
Owns the Cucumber Expressions-based step definition parsers: the abstract `_CucumberExpression` base class that imple.

Responsibility:
    Owns the Cucumber Expressions-based step definition parsers: the abstract `_CucumberExpression` base class that
    implements the StepParser protocol using the cucumber-expressions library with configurable parameter type registry
    resolution (supporting NEW, GLOBAL, NOT_DEFINED, and FIXTURE modes for obtaining ParameterTypeRegistry instances
    from test context), and the concrete `cucumber_expression` subclass that uses the CucumberExpression parser type (vs
    CucumberRegularExpression). Handles UndefinedParameterTypeError by recording the undefined parameter type
    information and returning False (not matching), and CantEscape errors similarly. Registers cucumber_expression as
    the parser wrapper for pre-compiled CucumberExpression objects via register_parser().

Reason for existence:
    Cucumber Expressions provide a Gherkin-native pattern syntax (e.g., "I have {int} cucumbers") that is more readable
    than regex and more standard than parse-format. This module wraps the third-party cucumber-expressions library,
    adding pytest-bdd-specific features: the parameter type registry resolution system that supports global, fixture-
    based, and isolated registries, and the graceful handling of UndefinedParameterTypeError (recording the error for
    later feedback rather than crashing). Without this module, step definitions using Cucumber expression syntax would
    need to be written as regex patterns with manual type conversion.

Delegates:
    - cucumber_expressions.CucumberExpression and RegularExpression: The core parsing and matching classes from the
    third-party library.
    - cucumber_expressions.ParameterTypeRegistry: Manages registered parameter types (e.g., {int}, {string}, {float})
    for type conversion during matching.
    - pytest_bdd.parsers.base.StepParser: Provides the base class and protocol interface.
    - pytest_bdd.parsers.base.register_parser: Registers parser wrapper for pre-compiled CucumberExpression objects.
    - pytest_bdd.model.message_extension.StepDefinitionPatternType: Provides pattern type classification.
    - UNDEFINED_PARAMETER_TYPE_PATTERN (module-level compiled regex): Extracts the undefined parameter type name from
    error messages for diagnostic reporting.

Cohesion:
    All entities in the module serve Cucumber expression matching. _CucumberExpression owns the core matching logic
    (is_matching, parse_arguments, rebuild_expression_in_test_context, _get_parameter_type_registry),
    cucumber_expression specializes it with the CucumberExpression parser type and the singledispatch constructor. The
    UNDEFINED_PARAMETER_TYPE_PATTERN regex exists solely to parse error messages from the cucumber-expressions library.

Separation:
    - pytest_bdd.parsers.cucumber_regex.cucumber_regular_expression: Kept separate because cucumber_regular_expression
    uses CucumberRegularExpression (regex-based Cucumber patterns) while cucumber_expression uses CucumberExpression
    (expression-based Cucumber patterns) — different parser engines, different pattern syntax, shared base class.
    - pytest_bdd.parsers.parse_parser.parse: Kept separate because parse uses the parse library (format strings with
    :type syntax), while cucumber_expression uses cucumber-expressions library (Cucumber standard syntax with {type}
    syntax) — different libraries, different syntaxes.
    - pytest_bdd.parsers.re_parser.re: Kept separate because re uses stdlib regex, a third distinct parsing paradigm.

Main consumers:
    - End-user test code via parsers.cucumber_expression("I have {int} cucumbers").
    - pytest_bdd.steps.manager: Uses the StepParser protocol for matching and argument extraction.
    - register_parser: Registers the parser wrapper for pre-compiled CucumberExpression objects.

State and side effects:
    Instance state: self.last_undefined_parameter_type is set during is_matching() when an UndefinedParameterTypeError
    occurs — this is mutable instance state used for diagnostic reporting. self.parameter_type_registry (class-level
    default) and self.parameter_type_registry_like (instance) control registry resolution.

Invariants:
    - rebuild_expression_in_test_context() must be called (through is_matching or parse_arguments) with a valid
    FixtureRequest when the registry mode is FIXTURE, otherwise getfixturevalue will fail.
    - self.last_undefined_parameter_type must be reset to None at the start of each is_matching() call to avoid stale
    state from previous calls.
    - The expression_type class attribute determines which cucumber-expressions class to instantiate (CucumberExpression
    vs RegularExpression).

Failure semantics:
    Raises NotImplementedError from the base singledispatchmethod __init__ of cucumber_expression — this is the abstract
    hook. UndefinedParameterTypeError is caught and handled (returns False, records error). CantEscape is caught and
    returns False.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=3
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=5
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
    Abstract base class for Cucumber-expression-based step parsers that implements the complete StepParser protocol using.

    Responsibility:
        Abstract base class for Cucumber-expression-based step parsers that implements the complete StepParser protocol
        using the cucumber-expressions library. Owns the parameter type registry resolution system (supporting NEW for
        isolated registries, GLOBAL/NOT_DEFINED for shared registries, and FIXTURE for pytest-fixture-provided
        registries), the expression rebuilding logic (rebuild_expression_in_test_context) that creates fresh expression
        instances per test context to pick up per-test parameter type registries, graceful handling of
        UndefinedParameterTypeError (recording diagnostic info and returning non-match), and the core
        is_matching/parse_arguments pipeline that delegates to the cucumber-expressions library's tree_regexp.match()
        and match() methods. Subclasses provide the expression_type class attribute and the singledispatch constructors.

    Reason for existence:
        The parameter type registry resolution system is the key differentiator from other parsers. Cucumber expressions
        support user-defined parameter types (e.g., {color}, {date}) that must be registered in a ParameterTypeRegistry.
        This class provides four strategies for obtaining the registry: NEW (isolated per-expression), GLOBAL (shared
        module-level default), FIXTURE (pytest fixture named "parameter_type_registry"), and NOT_DEFINED (fallback to
        default). The expression must be rebuilt per test context (via rebuild_expression_in_test_context) because
        different tests may register different parameter types. This pattern avoids the global mutable state problem
        that plagued earlier implementations.

    Delegates:
        - CucumberExpression (cucumber_expressions): The core expression parsing/matching class, instantiated in
        rebuild_expression_in_test_context.
        - RegularExpression (cucumber_expressions): Alternative expression type for regex-based Cucumber patterns,
        instantiated by cucumber_regular_expression subclass.
        - ParameterTypeRegistry: Manages registered parameter types; obtained through one of four strategies in
        _get_parameter_type_registry.
        - UNDEFINED_PARAMETER_TYPE_PATTERN: Compiled regex to extract undefined parameter type names from error messages.
        - StepParser: Provides the base class and protocol interface.

    Cohesion:
        Every method serves the Cucumber expression matching pipeline: _get_parameter_type_registry resolves the
        registry, rebuild_expression_in_test_context creates fresh expression instances, is_matching tests matching
        (with error handling), parse_arguments extracts matched values, __str__ returns the pattern. The class is
        focused solely on adapting cucumber-expressions to pytest-bdd's StepParser protocol.

    Separation:
        - cucumber_expression (subclass): Kept separate because the subclass provides the concrete expression_type
        (CucumberExpression) and the singledispatch constructors, while the base class owns the matching logic —
        construction vs matching.
        - cucumber_regular_expression (from cucumber_regex): Kept separate because it uses RegularExpression (regex-
        based) while cucumber_expression uses CucumberExpression (expression-based) — different parser engines.

    Main consumers:
        - cucumber_expression subclass: Inherits all matching logic.
        - cucumber_regular_expression subclass: Inherits all matching logic, overrides expression_type.
        - pytest_bdd.steps.manager: Uses the StepParser protocol for step matching.

    State and side effects:
        Mutable instance state: self.last_undefined_parameter_type is set to (expression, undefined_name) tuple on
        UndefinedParameterTypeError — this is sticky diagnostic state visible to callers. Reset to None at start of each
        is_matching() call. The class-level self.parameter_type_registry is the default global registry (mutable, shared
        across instances in GLOBAL mode).

    Invariants:
        - last_undefined_parameter_type must be reset to None before each is_matching() call to prevent stale diagnostic
        information.
        - rebuild_expression_in_test_context must create a new expression instance each call — the expression object may
        embed the parameter type registry, which can change between tests.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
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
        Test whether a step name string matches the Cucumber expression pattern by rebuilding the expression in the test context.

        Responsibility:
            Tests whether a step name string matches the Cucumber expression pattern by rebuilding the expression in the
            test context (picking up the correct parameter type registry), then delegating to tree_regexp.match(name)
            for boolean matching. Catches UndefinedParameterTypeError (extracts the undefined type name for diagnostics
            via UNDEFINED_PARAMETER_TYPE_PATTERN regex) and CantEscape errors (eponymous escape character issues), both
            returning False to indicate non-match rather than propagating exceptions. Resets
            last_undefined_parameter_type to None before each attempt.

        Reason for existence:
            The cucumber-expressions library raises UndefinedParameterTypeError when a pattern references a parameter
            type not registered in the current registry (e.g., "{color}" when no "color" type is registered). This
            method catches that error, extracts the undefined type name for diagnostic reporting, sets it on the
            instance for the step manager to report, and returns False. This is user-friendly: it tells the test author
            WHICH type is undefined, rather than crashing with a cryptic error. The tree_regexp.match() call uses the
            internal tree-regex representation which is faster than full match() when only a boolean result is needed.

        Delegates:
            - rebuild_expression_in_test_context: Creates a fresh expression instance with current test context's
            parameter type registry.
            - tree_regexp.match(name): Performs boolean matching (faster than full match with argument extraction).
            - UNDEFINED_PARAMETER_TYPE_PATTERN: Extracts the undefined type name from error message strings.

        Cohesion:
            The method performs one task: boolean matching with graceful error handling. The try/except blocks handle
            two specific error types, both returning False with diagnostic info.

        Separation:
            - parse_arguments: Kept separate because is_matching is a boolean gate while parse_arguments extracts values
            — detection vs extraction.

        Main consumers:
            - pytest_bdd.steps.manager: Called during step lookup to find matching step definitions.

        State and side effects:
            Resets self.last_undefined_parameter_type to None (clearing previous diagnostic state), then sets it to
            (expression, name) if UndefinedParameterTypeError occurs. This is diagnostic state visible to callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
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
        Extract step arguments from a matched step name by rebuilding the expression in test context, calling match(name) to obtain argument values.

        Responsibility:
            Extracts step arguments from a matched step name by rebuilding the expression in test context, calling
            match(name) to get a list of matched Argument objects, extracting their .value attributes via
            operator.attrgetter, and zipping them with the provided anonymous_group_names into a dict. Returns None if
            match() returns None (no match — should not happen if is_matching was checked first). The FixtureRequest is
            required to access the parameter type registry for type conversion.

        Reason for existence:
            The cucumber-expressions library's match() method returns a list of Argument objects, each with a .value
            attribute containing the converted value (using the registered parameter type's transform function). This
            method extracts those values and maps them to names. The anonymous_group_names parameter handles positional
            argument mapping (for non-named groups), although Cucumber expressions primarily use named output parameters
            from the expression syntax.

        Delegates:
            - rebuild_expression_in_test_context: Creates a fresh expression with current test context.
            - expression.match(name): Performs matching and returns Argument objects with converted values.
            - operator.attrgetter("value"): Efficiently extracts the .value from each Argument object.

        Cohesion:
            The method performs one pipeline: rebuild expression → match → extract values → zip with names → return
            dict. Every line serves this purpose.

        Separation:
            - is_matching: Kept separate because is_matching is a boolean pre-check while parse_arguments performs the
            actual extraction — gate vs extraction.
            - parse.parse_arguments: Kept separate because parse uses Result.named/.fixed while cucumber_expression uses
            Argument.value — different result object structures.

        Main consumers:
            - pytest_bdd.steps.manager: Called after successful is_matching() to extract argument values for step
            function parameters.

        State and side effects:
            None. Pure function of inputs (other than registry resolution from FixtureRequest).

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
        Return the original Cucumber expression pattern string (e.g., "I have {int} cucumbers"), providing a human-readable representation.

        Responsibility:
            Returns the original Cucumber expression pattern string (e.g., "I have {int} cucumbers"), providing a human-
            readable representation for debugging and error messages.

        Reason for existence:
            The StepParser protocol requires __str__ for display. The pattern string is the most meaningful
            representation — it shows the exact Cucumber expression syntax the step was matched against.

        Delegates:
            - self.pattern: The stored pattern string.

        Cohesion:
            Returns the stored pattern. No additional logic.

        Separation:
            - Other parser __str__ methods: Each returns the format appropriate for its matching paradigm.

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
        return str(self.pattern)

    def rebuild_expression_in_test_context(
        self,
        request: FixtureRequest,
    ) -> CucumberExpression | CucumberRegularExpression:
        """
        Create a fresh CucumberExpression (or CucumberRegularExpression) instance for the current test context by calling self._recreate_expression.

        Responsibility:
            Creates a fresh CucumberExpression (or CucumberRegularExpression) instance for the current test context by
            calling self.expression_type(self.pattern, self._get_parameter_type_registry(request)). This ensures the
            expression picks up any per-test parameter type registrations (e.g., custom types registered via the
            "parameter_type_registry" fixture) rather than using a stale cached expression. Called before every
            is_matching() and parse_arguments() call.

        Reason for existence:
            Cucumber expressions embed the parameter type registry at construction time. If the registry changes between
            tests (e.g., one test registers a {color} type via fixture, another doesn't), a cached expression would use
            the wrong registry. Rebuilding per call ensures the expression uses the correct registry for the current
            test. The pattern of construction-per-call is also used by the cucumber-expressions library internally and
            is the recommended pattern for registry-isolated usage.

        Delegates:
            - self.expression_type: The concrete expression class to instantiate (CucumberExpression for
            cucumber_expression, RegularExpression for cucumber_regular_expression).
            - _get_parameter_type_registry: Resolves the ParameterTypeRegistry for the current request context.

        Cohesion:
            The method performs exactly one operation: construct expression from pattern + registry. Every line serves this purpose.

        Separation:
            - _get_parameter_type_registry: Kept separate because that method handles the complex registry resolution
            logic (NEW/GLOBAL/FIXTURE/NOT_DEFINED modes), while this method is a thin construction wrapper.

        Main consumers:
            - is_matching: Calls this to get an expression for boolean matching.
            - parse_arguments: Calls this to get an expression for argument extraction.

        State and side effects:
            None. Creates and returns a new expression object. Does not modify any persistent state.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """
        return self.expression_type(self.pattern, self._get_parameter_type_registry(request))

    def _get_parameter_type_registry(self, request: FixtureRequest) -> ParameterTypeRegistry:
        """
        Resolve the ParameterTypeRegistry for the current test context based on the self.parameter_type_registry_like configuration.

        Responsibility:
            Resolves the ParameterTypeRegistry for the current test context based on the
            self.parameter_type_registry_like configuration: NEW creates a fresh isolated registry via
            ParameterTypeRegistry(), GLOBAL and NOT_DEFINED return the class-level default registry (shared across all
            expressions), FIXTURE retrieves the registry from pytest fixture "parameter_type_registry" via
            request.getfixturevalue(). If parameter_type_registry_like is a raw ParameterTypeRegistry instance (not a
            string/enum), returns it directly. This enables four distinct registry-sharing strategies for different
            testing needs.

        Reason for existence:
            Different testing scenarios need different parameter type isolation levels: unit tests may want isolated
            registries (NEW mode) to prevent cross-test contamination, integration tests may want a shared global
            registry (GLOBAL mode) for consistency, and advanced users may want to provide registries via fixtures
            (FIXTURE mode) for dynamic type registration. This method encapsulates all four strategies behind a single
            interface, using a dict dispatch pattern for enum/string cases and direct instance passthrough for object
            cases.

        Delegates:
            - ParameterTypeRegistry(): Creates a new empty registry for NEW mode.
            - self.parameter_type_registry: The class-level default registry for GLOBAL/NOT_DEFINED modes.
            - request.getfixturevalue("parameter_type_registry"): Retrieves the pytest fixture-provided registry for FIXTURE mode.
            - RegistryMode enum: Provides the enum values for the dispatch dict.

        Cohesion:
            The method performs one task: resolve the registry. The if/else dispatch handles all four cases via dict
            lookup for enums and direct passthrough for objects.

        Separation:
            - rebuild_expression_in_test_context: Kept separate because that method constructs the expression from the
            registry, while this method resolves which registry to use — resolution vs construction.

        Main consumers:
            - rebuild_expression_in_test_context: Called to get the registry for expression construction.

        State and side effects:
            Reads from self.parameter_type_registry (class-level mutable state in GLOBAL mode) and request fixture
            system. Does not modify state.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
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
    Concrete Cucumber expression parser class specializing _CucumberExpression with expression_type=CucumberExpression (t.

    Responsibility:
        Concrete Cucumber expression parser class specializing _CucumberExpression with
        expression_type=CucumberExpression (the standard Cucumber expression parser, not the regex-based variant).
        Provides a singledispatchmethod-based dual constructor accepting either a raw expression string with optional
        parameter_type_registry configuration (defaulting to FIXTURE mode for per-test registry isolation) or a pre-
        compiled CucumberExpression object (extracting its expression string and parameter_type_registry). The
        `arguments` property returns an empty collection (Cucumber expressions use output parameters from the expression
        syntax, not regex named groups). Registered as the parser wrapper for pre-compiled CucumberExpression objects.

    Reason for existence:
        This is the standard Cucumber expression parser for pytest-bdd. The singledispatchmethod constructor mirrors the
        pattern used by parse and re parsers, providing both string-based and object-based initialization. The FIXTURE
        default for parameter_type_registry ensures per-test isolation by default, which is the safest default for
        pytest's test isolation model. The empty arguments collection reflects that Cucumber expressions don't use
        Python regex named groups — argument names are determined by the expression syntax output parameters.

    Delegates:
        - _CucumberExpression (parent): Inherits all matching logic (is_matching, parse_arguments,
        rebuild_expression_in_test_context, _get_parameter_type_registry).
        - CucumberExpression (cucumber_expressions): The expression parser type — expression_type class attribute.
        - singledispatchmethod: Enables dual-constructor pattern.
        - register_parser: Registers this class as the parser wrapper for pre-compiled CucumberExpression objects.

    Cohesion:
        The class is a thin specialization of _CucumberExpression: set expression_type to CucumberExpression, implement
        constructors, provide empty arguments collection. All matching logic is inherited.

    Separation:
        - _CucumberExpression: Kept separate because the base class owns matching logic, while this subclass provides
        the concrete expression type and constructors — logic vs specialization.
        - cucumber_regular_expression: Kept separate because that subclass uses RegularExpression (regex-based) while
        this uses CucumberExpression (expression-based) — different parser engines.

    Main consumers:
        - End-user code: parsers.cucumber_expression("I have {int} cucumbers").
        - pytest_bdd.steps.manager: Uses the StepParser protocol for matching.

    State and side effects:
        Inherits mutable state from _CucumberExpression (last_undefined_parameter_type, parameter_type_registry).

    Invariants:
        - expression_type must be CucumberExpression — never RegularExpression (that's cucumber_regular_expression's
        specialization).
        - StepDefinitionPatternType must be cucumber_expression for proper classification in message serialization.

    Failure semantics:
        Raises NotImplementedError from the base singledispatchmethod __init__ — this is the abstract hook, dead code
        guarded by the register methods.

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

    type = StepDefinitionPatternType.cucumber_expression
    expression_type = CucumberExpression

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]  # mypy limitation with singledispatchmethod/dynamic typing
    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Serve as the base singledispatchmethod constructor (abstract hook that raises NotImplementedError).

        Responsibility:
            Base singledispatchmethod constructor — abstract hook that raises NotImplementedError. The two register
            methods handle the actual initialization cases: string expression with optional registry config, and pre-
            compiled CucumberExpression object. This base method never executes in normal usage.

        Reason for existence:
            Pattern requirement of singledispatchmethod — the base method defines the dispatcher interface. Raising
            NotImplementedError clearly signals which types are unsupported.

        Delegates:
            - singledispatchmethod: Dispatches to register methods based on argument types.

        Cohesion:
            Pure guard — ensures unsupported types produce clear errors.

        Separation:
            - The register methods: Handle actual initialization for string and CucumberExpression inputs.

        Main consumers:
            - singledispatchmethod dispatch: Automatically invoked for unmatched types.

        State and side effects:
            None. Raises immediately.

        Failure semantics:
            Raises NotImplementedError for unsupported constructor argument types.

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
        Handle registered singledispatch for string expression inputs: store the expression pattern string and the parameter type registry configuration.

        Responsibility:
            Registered singledispatch handler for string expression inputs: stores the expression pattern string and the
            parameter_type_registry configuration (defaulting to FIXTURE mode). The actual expression compilation
            happens lazily in rebuild_expression_in_test_context when per-test registry info is available. The FIXTURE
            default ensures per-test registry isolation — the safest default for pytest's test isolation model.

        Reason for existence:
            String patterns are the primary way users create Cucumber expression parsers. Unlike regex and parse parsers
            which compile immediately, Cucumber expression compilation is deferred to rebuild_expression_in_test_context
            because the expression must embed the parameter type registry which may change per test. This handler only
            stores the raw inputs for later lazy construction.

        Delegates:
            - None. Simply stores inputs: self.pattern = expression, self.parameter_type_registry_like = parameter_type_registry.

        Cohesion:
            Performs exactly one operation: store pattern and registry config. No compilation, no validation.

        Separation:
            - The CucumberExpression register method: Kept separate because that handles pre-compiled expression
            objects, extracting pattern and registry from the existing object — extraction vs storage.

        Main consumers:
            - User code via parsers.cucumber_expression("I have {int} cucumbers") — the constructor dispatches here.

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
        expression: CucumberExpression,
    ) -> None:
        """
        Handle registered singledispatch for pre-compiled CucumberExpression objects: extract the expression pattern string from the compiled object.

        Responsibility:
            Registered singledispatch handler for pre-compiled CucumberExpression objects: extracts the expression
            pattern string from expression.expression and the parameter type registry from
            expression.parameter_type_registry, storing both for lazy rebuilding in test context. This enables step
            definitions to be registered using expression objects compiled during feature file parsing or from shared
            fixtures.

        Reason for existence:
            Pre-compiled CucumberExpression objects may be passed from earlier parsing stages. This handler extracts the
            raw inputs (pattern string, registry) so that rebuild_expression_in_test_context can reconstruct the
            expression with the correct per-test registry. The extraction pattern mirrors how parse extracts
            format_._format and how re extracts pattern.pattern.

        Delegates:
            - expression.expression: The original pattern string stored in the CucumberExpression object.
            - expression.parameter_type_registry: The registry embedded in the compiled expression.

        Cohesion:
            Performs one operation: extract pattern and registry from pre-compiled expression → store. Every line serves
            this purpose.

        Separation:
            - The string register method: Kept separate because that method stores raw inputs, while this method
            extracts from an existing object.

        Main consumers:
            - Code using pre-compiled CucumberExpression objects for step definition registration.

        State and side effects:
            Sets self.pattern and self.parameter_type_registry_like. Read-only access to expression object attributes.

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
        self.pattern = expression.expression
        self.parameter_type_registry_like = expression.parameter_type_registry

    @property
    def arguments(self) -> Collection[str]:
        """
        Returns an empty collection — Cucumber expressions extract argument names from the expression syntax output parameter.

        Responsibility:
            Returns an empty collection — Cucumber expressions extract argument names from the expression syntax output
            parameters (e.g., {int} produces a typed integer value with no named capture), not from regex named groups.
            The step definition manager uses this property to validate step function signatures, but for Cucumber
            expressions the argument names are determined by the expression's output parameter mapping, not by this
            property.

        Reason for existence:
            The StepParser protocol requires an `arguments` property. For Cucumber expressions, this returns an empty
            list because the argument names are not regex group names — they are determined by the expression's internal
            parameter type definitions. The step manager handles this by using the expression's match() result to
            extract arguments, not by pre-inspecting argument names.

        Delegates:
            - None. Returns literal empty list.

        Cohesion:
            Returns a constant — trivially cohesive.

        Separation:
            - cucumber_regular_expression.arguments: Kept separate because that subclass extracts argument names from
            the regex pattern's groupindex, while cucumber_expression returns empty — regex-based vs expression-based
            argument enumeration.

        Main consumers:
            - pytest_bdd.steps.manager: Uses arguments for signature validation.

        State and side effects:
            None. Returns constant empty list.

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
        return []


register_parser(lambda parserlike: isinstance(parserlike, CucumberExpression), cucumber_expression)
