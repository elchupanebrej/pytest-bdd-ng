"""
Primary public API surface for BDD test generation.

Responsibility:
    Primary public API surface for BDD test generation. Defines the two core entry-point functions — scenario() and
    scenarios() — that end users call to register Gherkin feature files as pytest tests. scenario() generates a
    decorator or test function for a single named scenario within a feature file; scenarios() generates a decorator or
    test function for all (or filtered) scenarios across multiple feature files. Also defines supporting types:
    ScenarioFunction (Protocol for decorated test callables), Args (NamedTuple for parser arguments), FeaturePathType
    (enum for PATH/URL/UNDEFINED), get_python_name_generator (iterator for unique test function names), and type aliases
    ScenarioDecorator, ScenarioTest, and ScenarioFilterT.

Reason for existence:
    This module is the user-facing entry point to the entire pytest-bdd-ng library. Every end-user test file imports
    scenario() or scenarios() from here (via the top-level pytest_bdd re-export). It is the information expert for "how
    does a user declare that Gherkin scenarios should become pytest tests?" The functions compose pytest marks
    (pytest.mark.pytest_bdd, pytest.mark.pytest_bdd_scenarios, pytest.mark.usefixtures) into decorators that the
    collection/runtime plugins later interpret. It is kept as a top-level module (layer: collection, order 5) because it
    bridges user code to the collection infrastructure — the functions here don't collect tests themselves, they create
    the markers that the plugins consume.

Delegates:
    - get_python_name_generator: Produces unique, sanitized Python function names from scenario names, ensuring test_
    prefix compliance.
    - format_as_simplified_python_identifier (from util.other): Sanitizes scenario names into valid Python identifiers.
    - pytest.mark decorators: The functions compose pytest.mark.pytest_bdd, pytest.mark.usefixtures, and
    pytest.mark.pytest_bdd_scenarios into a decorator pipeline.
    - pytest_bdd.util.toolz_extra.compose: Chains the mark decorators into a single composite decorator.
    - pytest_bdd.model.scenario_collection: Defines the mark name constants (PYTEST_BDD_MARK, PYTEST_BDD_SCENARIOS_MARK).

Cohesion:
    All entities in this module serve the single concern of "declare scenarios as pytest tests." scenario() and
    scenarios() are the two entry points. FeaturePathType enumerates the path types they accept. Args wraps extra parser
    arguments. ScenarioFunction defines the callable contract. get_python_name_generator solves the test-naming problem.
    There are no unrelated utilities or cross-cutting concerns.

Separation:
    - pytest_bdd.feature_locator.ScenarioLocatorBuilder: Consumes the pytest marks created by scenarios() to build
    actual ScenarioLocator instances. scenarios() creates the marks; the builder interprets them. The separation
    prevents circular dependencies between declaration and interpretation.
    - pytest_bdd.steps: Defines step decorators (@given, @when, @then). scenario() does not import or depend on step
    definitions — it only declares which scenarios to run.
    - pytest_bdd.collector: Collects test functions from virtual modules. scenarios() generates the marks that the
    collector discovers.

Main consumers:
    - End-user test files: import pytest_bdd and call @scenario("features/my.feature", "My Scenario") or
    @scenarios("features/") to register BDD tests.
    - pytest_bdd.collector.FeatureFileModule._build_test_module: Calls scenarios() with return_test_decorator=False to
    create a test_scenarios attribute on synthetic modules.
    - pytest_bdd.__init__: Re-exports scenario, scenarios, and FeaturePathType as the public API.

State and side effects:
    scenario() and scenarios() create pytest mark decorators (via pytest.mark) and attach them to functions. They do not
    perform file I/O or parsing — that happens later during collection. get_python_name_generator maintains a closure-
    based counter (index) to generate unique names. The test() inner function in scenarios() calls
    Nothing.value_or(None) which returns None (a no-op test body).

Invariants:
    - scenario() must delegate all logic to scenarios() — it is a thin wrapper that translates scenario_name to the
    filter_ parameter.
    - scenarios() must raise ValueError if both features_base_dir and features_base_url are specified simultaneously.
    - Setting features_base_dir forces features_path_type to PATH; setting features_base_url forces it to URL.
    - When return_test_decorator=False, the generated test function must have a name starting with "test_" for pytest to
    collect it.
    - The composite decorator must apply marks in order: pytest_bdd → usefixtures → pytest_bdd_scenarios.

Failure semantics:
    scenarios() raises ValueError with message 'Both "features_base_dir" and "features_base_url" were specified' if both
    parameters are provided. No other exceptions are raised directly; failures in downstream collection or parsing
    propagate from the plugin layer.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=5
"""

from collections.abc import Callable, Iterable, Iterator
from enum import Enum
from pathlib import Path
from typing import Any, Literal, NamedTuple, Protocol, TypeAlias, cast, overload

import pytest
from returns.maybe import Nothing

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model.scenario_collection import PYTEST_BDD_MARK, PYTEST_BDD_SCENARIOS_MARK
from pytest_bdd.util.other import format_as_simplified_python_identifier
from pytest_bdd.util.toolz_extra import compose


class ScenarioFunction(Protocol):
    """
    Structural typing Protocol defining the contract for BDD test functions produced by the scenario() and scenarios() de.

    Responsibility:
        Structural typing Protocol defining the contract for BDD test functions produced by the scenario() and
        scenarios() decorators. Specifies that a ScenarioFunction must have a __name__ attribute (str) and be callable
        with no arguments (returning object). This Protocol allows type checkers to validate that decorated functions
        satisfy the pytest test function interface without requiring a concrete base class.

    Reason for existence:
        pytest discovers test functions by inspecting callable objects with __name__ attributes. This Protocol
        formalizes that contract for pytest-bdd-generated tests, enabling mypy/pyright to catch type errors when user
        code violates the test function interface. It is a Protocol rather than an ABC because test functions can be
        plain functions or objects with __call__ — structural typing accommodates both. It lives in scenario.py because
        that module owns the concept of "a BDD scenario as a pytest test."

    Delegates:
        - None. This is a pure type contract with no implementation.

    Cohesion:
        The Protocol defines exactly the attributes needed by pytest: a name (for collection) and callability (for
        execution). No extraneous members.

    Separation:
        - ScenarioDecorator / ScenarioTest: Type aliases for the decorator and test function types that use
        ScenarioFunction as the decorated target.
        - pytest.Item / pytest.Function: Pytest's own test function types. ScenarioFunction is compatible with them but
        defined independently.

    Main consumers:
        - scenario() / scenarios() overload signatures: Use ScenarioFunction in the return type of ScenarioDecorator and
        ScenarioTest type aliases.
        - Type checkers: mypy/pyright validate that decorated functions conform to this Protocol.

    State and side effects:
        None. Protocol is a static type construct.

    Invariants:
        - Any ScenarioFunction must have __name__: str.
        - Any ScenarioFunction must be callable with zero arguments.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    __name__: str

    def __call__(self) -> object:
        """
        Protocol method declaring that a ScenarioFunction must be callable with no arguments (self only) and return an object.

        Responsibility:
            Protocol method declaring that a ScenarioFunction must be callable with no arguments (self only) and return
            an object. This ensures that pytest can invoke BDD test functions without needing to supply fixtures or
            arguments — all fixture injection is handled by pytest's dependency injection machinery, not by the call
            site.

        Reason for existence:
            The __call__ signature in this Protocol establishes the interface contract for test execution. Pytest calls
            test functions with no arguments (fixtures are auto-injected), so the Protocol enforces this. It is separate
            from the __name__ attribute to follow Protocol best practices where each interface member is explicitly
            declared.

        Delegates:
            - None. Abstract protocol member.

        Cohesion:
            Single-purpose: declare the callable interface. No implementation.

        Separation:
            - pytest.Item.runtest(): Pytest's own test execution method. ScenarioFunction.__call__ is the user-facing equivalent.

        Main consumers:
            - pytest: Invokes __call__() on collected test functions during test execution.
            - Type checkers: Validate that decorated functions have the correct call signature.

        State and side effects:
            None. Abstract protocol.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=1
            #arch-eval:locational_stability=5
        """
        ...


class Args(NamedTuple):
    """
    NamedTuple wrapping extra positional and keyword arguments passed through to the Gherkin parser.

    Responsibility:
        NamedTuple wrapping extra positional and keyword arguments passed through to the Gherkin parser. The args field
        holds a tuple of positional objects; the kwargs field holds a dict of keyword objects. Used as the parse_args
        parameter in scenario() and scenarios() to forward implementation-specific options to parser backends without
        polluting the main function signatures.

    Reason for existence:
        Different Gherkin parser backends may accept different configuration options. Rather than adding parser-specific
        parameters to scenario()/scenarios() (which would couple the public API to parser implementations), this opaque
        container allows any parser to receive its specific arguments. It is a NamedTuple for immutability and
        convenience (attribute access instead of dict key access).

    Delegates:
        - None. Pure data container.

    Cohesion:
        Two fields that together hold "extra arguments for the parser." No behavior, no validation.

    Separation:
        - FeatureLocatorArgs: A broader TypedDict for all scenario locator arguments. Args is specifically for
        parse_args within that schema.
        - ParserProtocol: The parser interface that consumes Args instances.

    Main consumers:
        - scenario() / scenarios(): Accept parse_args as an optional parameter and pass it through to the pytest marks.
        - Parser backends: Receive Args instances and extract backend-specific options.

    State and side effects:
        None.

    Invariants:
        - args must be a tuple of objects (not a list — NamedTuple enforces immutability).
        - kwargs must be a dict with string keys mapping to objects.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    args: tuple[object, ...]
    kwargs: dict[str, object]


ScenarioDecorator: TypeAlias = Callable[[ScenarioFunction], ScenarioFunction]
ScenarioTest: TypeAlias = Callable[[], object]
ScenarioFilterT: TypeAlias = str | Callable[[Config, object, object], bool] | None


def get_python_name_generator(name: str) -> Iterator[str]:
    """
    Generate unique, pytest-compatible function names from a scenario name.

    Responsibility:
        Generates unique, pytest-compatible function names from a scenario name. Sanitizes the input name via
        format_as_simplified_python_identifier, then yields names in the format "test_{python_name}" (or
        "test_{python_name}_{n}" for subsequent calls to avoid collisions). The first yielded name uses no numeric
        suffix; subsequent names append an incrementing index (1, 2, 3, ...). A bare "test" result is corrected to
        "test_" to ensure pytest collection matches.

    Reason for existence:
        pytest collects test functions by matching names against the "test_*" pattern. When scenarios() generates test
        functions from Gherkin scenarios, each function needs a unique, valid Python identifier that starts with
        "test_". This generator produces those names, handling edge cases like empty names (yields "test_"), name
        collisions (adds numeric suffixes), and non-identifier characters (sanitized by
        format_as_simplified_python_identifier).

    Delegates:
        - format_as_simplified_python_identifier: Sanitizes the raw scenario name into a valid Python identifier.
        - get_name (inner function): Produces a single name by joining "test", the sanitized name, and the current suffix.

    Cohesion:
        The function has a single purpose: produce an infinite sequence of unique test function names. The closure-based
        generator pattern keeps the counter (index) and suffix state encapsulated.

    Separation:
        - format_as_simplified_python_identifier: Owns the name sanitization logic. This function only handles the
        "test_" prefix and collision-avoidance suffix.

    Main consumers:
        - scenarios(): Calls next(get_python_name_generator("")) to name the generated test() function when
        return_test_decorator=False.
        - Any code that needs to generate unique pytest test names from scenario names.

    State and side effects:
        Maintains mutable closure state: suffix (str) and index (int) that increment with each yield. This is local
        generator state, not module-level or global.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    python_name = format_as_simplified_python_identifier(name)
    suffix = ""
    index = 0

    def get_name() -> str:
        """
        Produce a single pytest-compatible test function name by joining "test", the sanitized scenario python_name, and the.

        Responsibility:
            Produces a single pytest-compatible test function name by joining "test", the sanitized scenario
            python_name, and the current suffix (empty string for first call, numeric string for subsequent calls).
            Filters out empty components and joins with underscores. Corrects a bare "test" result to "test_" to match
            pytest's collection pattern matching.

        Reason for existence:
            The name-generation logic is extracted into an inner function so the generator can call it repeatedly while
            the outer function manages the suffix/index state. The empty-component filtering handles edge cases like
            empty scenario names (produces "test_") and double underscores (produces single underscore). The "test" →
            "test_" correction exists because pytest's collection pattern "test_*" would not match a function literally
            named "test".

        Delegates:
            - str.join and filter: Compose the name from non-empty components.
            - Conditional expression: Corrects bare "test" to "test_".

        Cohesion:
            Single-purpose: produce one name from current state. Pure function of its closure variables.

        Separation:
            - The outer get_python_name_generator: Manages state and looping. get_name() is the pure name-composition step.

        Main consumers:
            - get_python_name_generator: Called in each iteration of the while loop.

        State and side effects:
            None. Reads but does not mutate closure variables (suffix, python_name).

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        result = "_".join(filter(bool, ["test", python_name, suffix]))
        return result if result != "test" else "test_"

    while True:
        yield get_name()
        index += 1
        suffix = f"{index}"


class FeaturePathType(Enum):
    """
    Enumeration defining the three valid feature path classification types: PATH (local filesystem), URL (remote resource.

    Responsibility:
        Enumeration defining the three valid feature path classification types: PATH (local filesystem), URL (remote
        resource), and UNDEFINED (automatic detection based on path format). Controls whether scenario feature paths are
        interpreted as filesystem paths (resolved against features_base_dir), URLs (resolved against features_base_url),
        or auto-detected by the locator infrastructure.

    Reason for existence:
        The distinction between file and URL feature paths is fundamental to how scenarios are located and parsed. This
        enum provides a type-safe way to express that distinction, replacing magic strings like "path", "url", and
        "undefined". It is defined in scenario.py (not in types.py or const.py) because it is a parameter of the
        scenario()/scenarios() public API — it belongs with the functions that accept it.

    Delegates:
        - None. Pure enum with no behavior.

    Args:
        None — Enum members are accessed as class attributes (FeaturePathType.PATH, etc.).

    Cohesion:
        Three members representing the three possible path classification strategies. No unrelated values.

    Separation:
        - pytest_bdd.feature_locator.ScenarioLocatorBuilder.resolve_features_path_type: Normalizes string/None inputs to
        this enum.
        - pytest_bdd.collector.FeatureFileModule: Uses PathType (an alias for FeaturePathType) when resolving feature
        paths from shortcut files.

    Main consumers:
        - scenario() / scenarios(): Accept features_path_type as a parameter.
        - pytest_bdd.feature_locator.ScenarioLocatorBuilder: Resolves and normalizes path type values.
        - pytest_bdd.collector.FeatureFileModule: Uses PathType alias.

    Returns:
        The enum member itself when accessed (e.g., FeaturePathType.PATH returns FeaturePathType.PATH).

    State and side effects:
        None.

    Invariants:
        - Exactly three members: PATH, URL, UNDEFINED.
        - String values match the member names in lowercase ("path", "url", "undefined").

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5

    """

    PATH = "path"
    URL = "url"
    UNDEFINED = "undefined"


@overload
def scenario(
    feature_name: Path | str | None = None,
    scenario_name: str | None = None,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
    *,
    return_test_decorator: Literal[True] = True,
) -> ScenarioDecorator: ...


@overload
def scenario(
    feature_name: Path | str | None = None,
    scenario_name: str | None = None,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
    *,
    return_test_decorator: Literal[False],
) -> ScenarioTest: ...


def scenario(  # noqa: PLR0913, PLR0917  -- suppressed warning
    feature_name: Path | str | None = None,
    scenario_name: str | None = None,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
    *,
    return_test_decorator: bool = True,
) -> ScenarioDecorator | ScenarioTest:
    """
    Register a single named Gherkin scenario as a pytest test.

    Responsibility:
        Registers a single named Gherkin scenario as a pytest test. Translates the scenario_name parameter into the
        filter_ argument for scenarios(), wraps the feature_name in a single-element list (or empty list if None), and
        delegates entirely to scenarios() for mark composition and test generation. The overloaded return_test_decorator
        parameter controls whether the function returns a decorator (for use as @scenario(...)) or a ready-to-run test
        function. All other parameters (encoding, features_base_dir, features_base_url, features_path_type,
        features_mimetype, parser_type, parse_args, locators) are forwarded unchanged to scenarios().

    Reason for existence:
        This is the most commonly used user-facing function in the library. It provides a simplified API for the common
        case of "one scenario from one feature file," while scenario() handles the general case of "filtered scenarios
        from multiple feature files." The thin-wrapper design ensures that all logic lives in scenarios() and scenario()
        is purely a convenience adapter. The two overloads provide type-narrowing: return_test_decorator=True returns
        ScenarioDecorator, return_test_decorator=False returns ScenarioTest.

    Delegates:
        - scenarios(): Performs all actual work: argument validation, mark composition, test function generation.

    Args:
        feature_name: Path or name of the feature file containing the scenario.
        scenario_name: Name of the scenario within the feature file to register.
        encoding: Character encoding for reading feature files.
        features_base_dir: Base directory for resolving relative feature paths.
        features_base_url: Base URL for resolving remote feature paths.
        features_path_type: Classification of how feature paths should be interpreted (path, url, or auto-detect).
        features_mimetype: MIME type hint for feature file format detection.
        parser_type: Custom parser class to use for parsing feature files.
        parse_args: Additional arguments to pass to the parser.
        locators: Custom scenario locators for resolving scenarios.
        return_test_decorator: If True, returns a decorator; if False, returns a ready-to-run test function.

    Returns:
        A scenario decorator (when return_test_decorator=True) or a ready-to-run test function.

    Cohesion:
        The function body is a single if/else that delegates to scenarios() with either return_test_decorator=True or
        False. The feature_name → feature_paths translation is trivial. No other logic.

    Separation:
        - scenarios(): The general-purpose function. scenario() is a convenience wrapper that should never contain logic
        beyond parameter translation.

    Main consumers:
        - End-user test files: @scenario("features/login.feature", "Successful login") is the standard way to declare a
        single BDD test.
        - pytest_bdd.__init__: Re-exports scenario as a top-level public API symbol.

    State and side effects:
        None directly. All side effects are in scenarios() which creates pytest marks.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5

    """
    feature_paths = [feature_name] if feature_name is not None else []
    if return_test_decorator:
        return scenarios(
            *feature_paths,
            filter_=scenario_name,
            encoding=encoding,
            features_base_dir=features_base_dir,
            features_base_url=features_base_url,
            features_path_type=features_path_type,
            features_mimetype=features_mimetype,
            return_test_decorator=True,
            locators=locators,
            parser_type=parser_type,
            parse_args=parse_args,
        )
    return scenarios(
        *feature_paths,
        filter_=scenario_name,
        encoding=encoding,
        features_base_dir=features_base_dir,
        features_base_url=features_base_url,
        features_path_type=features_path_type,
        features_mimetype=features_mimetype,
        return_test_decorator=False,
        locators=locators,
        parser_type=parser_type,
        parse_args=parse_args,
    )


@overload
def scenarios(
    *feature_paths: Path | str,
    filter_: ScenarioFilterT = None,
    return_test_decorator: Literal[True],
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
) -> ScenarioDecorator: ...


@overload
def scenarios(
    *feature_paths: Path | str,
    filter_: ScenarioFilterT = None,
    return_test_decorator: Literal[False] = False,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
) -> ScenarioTest: ...


def scenarios(  # noqa: PLR0913  -- suppressed warning
    *feature_paths: Path | str,
    filter_: ScenarioFilterT = None,
    return_test_decorator: bool = False,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = FeaturePathType.PATH,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args: Args | None = None,
    locators: Iterable[object] = (),
) -> ScenarioDecorator | ScenarioTest:
    """
    Core BDD test registration function that composes three pytest marks (pytest_bdd, usefixtures with gherkin_document/p.

    Responsibility:
        Core BDD test registration function that composes three pytest marks (pytest_bdd, usefixtures with
        gherkin_document/pickle/feature_source fixtures, and pytest_bdd_scenarios with all feature path and filter
        arguments) into a composite decorator. Validates that features_base_dir and features_base_url are not both
        specified (raises ValueError). Forces features_path_type to PATH when features_base_dir is set, and to URL when
        features_base_url is set. When return_test_decorator=True, returns the composite decorator for use as
        @scenarios(...). When False, applies the decorator to a generated no-op test() function, assigns it a unique
        test_* name via get_python_name_generator, and returns the decorated function.

    Reason for existence:
        This is the implementation behind both scenario() and scenarios(). It is the single point where pytest marks are
        composed for BDD test registration. The three-mark composition (pytest_bdd → usefixtures → pytest_bdd_scenarios)
        establishes the contract that downstream plugins (scenario_test_collector, pickle_runner) rely on: the
        pytest_bdd_scenarios mark carries the feature paths and configuration; the usefixtures mark ensures the required
        fixtures are available; the pytest_bdd mark identifies this as a BDD test. The mutual exclusion of
        features_base_dir and features_base_url prevents ambiguous feature resolution.

    Delegates:
        - pytest.mark decorators: pytest.mark.pytest_bdd, pytest.mark.usefixtures, pytest.mark.pytest_bdd_scenarios.
        - pytest_bdd.util.toolz_extra.compose: Chains the three mark decorators into a single callable.
        - get_python_name_generator: Generates a unique test_* name for the no-op test function.
        - Args constructor: Wraps empty parse_args when None is provided.

    Args:
        *feature_paths: One or more paths to feature files to register scenarios from.
        filter_: Optional callable to filter which scenarios are registered.
        return_test_decorator: If True, returns a decorator; if False, applies decorator to a generated test function.
        encoding: Character encoding for reading feature files.
        features_base_dir: Base directory for resolving relative feature paths.
        features_base_url: Base URL for resolving remote feature paths.
        features_path_type: Classification of how feature paths should be interpreted (path, url, or auto-detect).
        features_mimetype: MIME type hint for feature file format detection.
        parser_type: Custom parser class to use for parsing feature files.
        parse_args: Additional arguments to pass to the parser.
        locators: Custom scenario locators for resolving scenarios.

    Returns:
        A scenario decorator (when return_test_decorator=True) or a decorated test function.

    Cohesion:
        The function body has two phases: validation/normalization (check mutual exclusion, normalize path type, default
        parse_args) and decorator composition (build the mark pipeline, conditionally apply it). Both phases serve the
        single goal of "produce a pytest-compatible test registration from feature paths."

    Separation:
        - scenario(): A convenience wrapper that delegates to scenarios() with a single feature_name and scenario_name-
        as-filter.
        - pytest_bdd.feature_locator.ScenarioLocatorBuilder: Consumes the marks created here to build actual locators.
        scenarios() doesn't know how locators work — it only creates marks.

    Main consumers:
        - End-user test files: @scenarios("features/") or @scenarios("features/", filter_="login") for bulk BDD test
        registration.
        - pytest_bdd.collector.FeatureFileModule._build_test_module: Calls scenarios() with return_test_decorator=False.
        - scenario(): Delegates entirely to this function.

    State and side effects:
        Creates pytest mark objects (via getattr and function calls). The pytest.mark module's internal state tracks
        registered marks. When return_test_decorator=False, defines and decorates an inner test() function, assigning it
        a generated name. No file I/O or parsing.

    Failure semantics:
        Raises ValueError with message 'Both "features_base_dir" and "features_base_url" were specified' if both
        parameters are truthy. This prevents ambiguous feature resolution configurations. No other exceptions are raised
        directly.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5

    """
    if parse_args is None:
        parse_args = Args((), {})

    if features_base_dir and features_base_url:
        msg = 'Both "features_base_dir" and "features_base_url" were specified'
        raise ValueError(msg)
    if features_base_dir:
        features_path_type = FeaturePathType.PATH
    elif features_base_url:
        features_path_type = FeaturePathType.URL

    decorator = cast(
        "ScenarioDecorator",
        compose(
            cast("Callable[..., Any]", getattr(pytest.mark, PYTEST_BDD_MARK)),
            pytest.mark.usefixtures("gherkin_document", "pickle", "feature_source"),  # type: ignore[attr-defined]  # pytest.mark module attribute, not the function
            cast("Callable[..., Any]", getattr(pytest.mark, PYTEST_BDD_SCENARIOS_MARK))(
                *feature_paths,
                filter_=filter_,
                encoding=encoding,
                features_base_dir=features_base_dir,
                features_base_url=features_base_url,
                features_path_type=features_path_type,
                features_mimetype=features_mimetype,
                parser_type=parser_type,
                parse_args=parse_args,
                locators=locators,
            ),
        ),
    )

    if return_test_decorator:
        return decorator

    @decorator
    def test() -> None:
        """
        No-op test function body that serves as the decorated target when scenarios() is called with return_test_decorator=Fa.

        Responsibility:
            No-op test function body that serves as the decorated target when scenarios() is called with
            return_test_decorator=False. Returns Nothing.value_or(None) (effectively None) — the test passes trivially
            because the actual BDD scenario execution is handled by the pickle_runner plugin, not by this function body.
            The function exists solely to be discovered by pytest collection and to carry the BDD marks that trigger
            scenario execution.

        Reason for existence:
            pytest collects test functions, not marks alone. When return_test_decorator=False, scenarios() needs to
            return a concrete test function (not a decorator), and pytest requires that the function has a body. This
            inner function provides that body. The actual BDD test logic runs in the pickle_runner plugin which
            intercepts test execution via pytest hooks — the function body itself is intentionally empty.
            Nothing.value_or(None) is used instead of a bare return to satisfy the non-None return convention.

        Delegates:
            - returns.maybe.Nothing.value_or: Returns None, which is the function's actual return value.

        Cohesion:
            Single-purpose: provide a body for the auto-generated test function. No logic, no assertions, no fixtures.

        Separation:
            - pytest_bdd.plugin.pickle_runner: The plugin that intercepts pytest_runtest_call and executes the actual
            BDD scenario steps. This function is not aware of the plugin.

        Main consumers:
            - pytest: Collects and executes this function as a test item.
            - scenarios(): Creates, decorates, and names this function.

        State and side effects:
            None. Returns None.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=5
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=1
            #arch-eval:locational_stability=5
        """
        return Nothing.value_or(None)

    test.__name__ = next(get_python_name_generator(""))

    return test
