"""
Defines the canonical data model for a registered BDD step definition: the `Definition` attrs class that binds a user.

Responsibility:
    Defines the canonical data model for a registered BDD step definition: the `Definition` attrs class that binds a
    user function (StepFunc) to a StepParser, step type (given/when/then), converters, fixture mappings, and metadata
    (liberal, tolerant, not_implemented flags). Also provides the StepFunc Protocol for structural typing of decorated
    step functions, type aliases (StepDecorator, ConverterT, ParamsFixturesMapping), the
    _resolve_callable_source_location helper for extracting file/line from callables, and methods on Definition for
    converting to cucumber_messages StepDefinition (as_message) and resolving step parameters from a PickleStep
    (get_parameters).

Reason for existence:
    This module is the information expert for the Definition entity because it owns all data and behaviour related to a
    single step binding: how the function, parser, type, converters, and fixture mappings are stored (the attrs fields),
    how fixture names are derived from step parameters (fixtures_mapped_from_step_definition), how the definition
    serialises to the Cucumber Messages protocol (as_message using IdGenerator from pytest stash), and how parameter
    values are extracted and converted at execution time (get_parameters). It is kept separate from manager.py (which
    orchestrates definition creation) and matcher.py (which matches definitions to steps) because the Definition is the
    central data object that both consume — changes to the Definition's fields or serialisation affect both, and keeping
    it in its own module prevents circular dependencies between the creation and consumption concerns.

Delegates:
    - _resolve_callable_source_location: Uses inspect.getfile and inspect.getsourcelines to extract the (file_path,
    line_number) of a StepFunc, with fallback to func.__code__.co_firstlineno for edge cases (OSError, TypeError).
    - IdGenerator.from_stash: Used by as_message to obtain a unique ID for the StepDefinition message, reading from
    pytest config stash.
    - StepParser: The Definition.parser field holds a StepParserProtocol-compliant parser; parse_arguments and arguments
    are delegated to it.
    - cucumber_messages types (StepDefinition, StepDefinitionPattern, SourceReference, Location, JavaMethod,
    JavaStackTraceElement): Used by as_message to construct the protocol-compliant message.
    - attrs: The @define decorator with eq=False provides the data class infrastructure for Definition.

Cohesion:
    Every entity in this module revolves around the Definition class and its supporting types. StepFunc, StepDecorator,
    ConverterT, and ParamsFixturesMapping are type aliases used exclusively by Definition's fields and constructor.
    _resolve_callable_source_location is a helper used only by Definition.as_message. The three Definition methods
    (fixtures_mapped_from_step_definition, as_message, get_parameters) each serve one aspect of the Definition
    lifecycle: fixture mapping, serialisation, and parameter resolution.

Separation:
    - manager.py (StepDefinitionManager): Creates Definition instances via decorator_builder; this module defines the
    data model being created but does not own the creation orchestration or namespace injection logic.
    - matcher.py (Matcher): Consumes Definition instances for matching against PickleSteps; this module does not own
    matching logic.
    - registry.py (Registry): Stores OrderedSet[Definition]; this module defines what is stored but not how it is
    organised or discovered.

Main consumers:
    - pytest_bdd.steps.manager.StepDefinitionManager.decorator_builder: Constructs Definition instances with all fields
    populated from decorator parameters.
    - pytest_bdd.steps.matcher.Matcher: Reads Definition.type_, Definition.parser, Definition.liberal for matching;
    calls Definition.get_parameters for parameter extraction.
    - pytest_bdd.steps.registry.Registry: Stores Definition objects in OrderedSet; Registry.registry discovers them from
    namespace objects.
    - pytest_bdd.plugin.pickle_runner: Uses Definition.as_message for reporting and Definition.get_parameters for step
    execution.
    - pytest_bdd.hook: Consumes Definition type for lifecycle hook signatures.

State and side effects:
    Definition stores an __cache dict (field factory=dict) keyed by id(id_generator) for memoising as_message results —
    this is mutable instance state that prevents duplicate StepDefinition messages within a single test run. as_message
    reads from pytest config stash via IdGenerator.from_stash (side effect: reads StashBound). No file/network I/O
    beyond inspect module source reading.

Invariants:
    - Definition.parser must be a StepParserProtocol-compliant object with parse_arguments, is_matching, arguments, and
    type attributes.
    - Definition.id is not set at construction time (init=False); it is lazily assigned by as_message using the IdGenerator.
    - The __cache dict keyed by id(id_generator) ensures that as_message returns the same StepDefinition object for the
    same IdGenerator instance within a test run.
    - get_parameters must be called only after a successful is_matching check on the same step.

Failure semantics:
    - TypeError: Raised by as_message when parser_expression_type (from self.parser.type) cannot be converted to a
    StepDefinitionPatternType enum value. This indicates a parser implementation that provides an unrecognised pattern
    type string. Callers should ensure parser.type returns either a valid StepDefinitionPatternType enum member or a
    string that is a valid enum value name.

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

from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from inspect import getfile, getsourcelines
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, cast

from attrs import define, field
from cucumber_messages import (  # upstream library missing type stubs
    JavaMethod,
    JavaStackTraceElement,
    Location,
    PickleStepType,
    SourceReference,
    StepDefinition,
    StepDefinitionPattern,
)
from cucumber_messages import (
    PickleStep as Step,  # upstream type stubs missing this attribute
)
from typing_extensions import Protocol

from pytest_bdd.compatibility.path import resolvepath
from pytest_bdd.compatibility.pytest import (  # noqa: TC001  -- used in runtime type guards and isinstance checks across the step definition boundary
    Config,
    FixtureRequest,
)
from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers import (
    StepParser,  # noqa: TC001  -- required at runtime for isinstance checks in step registration logic
)
from pytest_bdd.types.protocol import (
    HasPytestStash,  # noqa: TC001  -- used in runtime isinstance checks for stash access validation
)
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.toolz_extra import getitemdefault

if TYPE_CHECKING:
    from types import FunctionType


class StepFunc(Protocol):
    """
    Structural typing Protocol that defines the minimum interface for a callable that can be decorated as a BDD step func.

    Responsibility:
        Structural typing Protocol that defines the minimum interface for a callable that can be decorated as a BDD step
        function. Requires only a `__name__` attribute (str) so the framework can identify and reference the function by
        name. The actual call signature is deliberately unconstrained by this Protocol because step functions can have
        arbitrary pytest fixture parameters — the framework discovers those at decoration time via inspect, not via
        static type checking.

    Reason for existence:
        Exists as a Protocol rather than a concrete type or Callable alias because step functions are ordinary Python
        functions with arbitrary signatures that share only the property of having a __name__. The Protocol enables type
        annotations throughout the step definition subsystem (Definition.func, StepDecorator return type,
        decorator_builder parameter) without imposing constraints on the function's parameter list. Using a Protocol
        with only __name__ allows duck-typing: any object with a __name__ attribute can serve as a step function,
        including functools.partial wrappers and mock objects.

    Delegates:
        - No delegation: pure Protocol definition with a single __name__ attribute.

    Cohesion:
        Defined alongside Definition because StepFunc is the type of Definition.func. It is the input type for the
        entire step decoration pipeline.

    Separation:
        - Definition: Stores a StepFunc instance; StepFunc defines the structural contract for what can be stored.
        - StepDecorator: TypeAlias for Callable[[StepFunc], StepFunc]; StepFunc is the input/output type of the decorator.

    Main consumers:
        - pytest_bdd.steps.manager.StepDefinitionManager.decorator_builder: The inner decorator function accepts a
        StepFunc and returns a StepFunc.
        - pytest_bdd.steps.definition.Definition: The func field is typed as StepFunc.
        - pytest_bdd.steps.decorators: @given, @when, @then, @step all return StepDecorator which wraps StepFunc.

    State and side effects:
        None, pure Protocol definition.

    Invariants:
        - Any object stored as Definition.func must have a truthy __name__ attribute that can be used for identification
        and display.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """

    __name__: str


StepDecorator: TypeAlias = Callable[[StepFunc], StepFunc]
ConverterT: TypeAlias = Callable[[object], object]
ParamsFixturesMapping: TypeAlias = bool | Collection[str] | Mapping[object, str | None]


def _resolve_callable_source_location(func: StepFunc) -> tuple[str, int]:
    """
    Resolve the source file path and starting line number of a callable step function.

    Responsibility:
        Resolves the source file path and starting line number of a callable step function. Uses inspect.getfile and
        inspect.getsourcelines as the primary strategy; falls back to func.__code__.co_firstlineno (or 1 if __code__ is
        absent) when OSError or TypeError occur (e.g., for built-in functions, dynamically generated functions, or
        functions defined in interactive sessions). Returns a (file_path: str, line_number: int) tuple.

    Reason for existence:
        Extracted as a standalone function because source location resolution is needed by Definition.as_message for
        constructing cucumber_messages SourceReference and Location objects, and the fallback logic is non-trivial.
        Keeping it separate from Definition allows testing the edge cases (OSError, TypeError, missing __code__)
        independently. The cast to FunctionType is needed because StepFunc Protocol does not guarantee the inspect
        module's expected attributes.

    Delegates:
        - inspect.getfile: Gets the file path where the function was defined.
        - inspect.getsourcelines: Gets the source lines and starting line number.
        - getattr(func, "__code__", None): Fallback path for functions where getsourcelines fails.
        - cast("FunctionType", func): Narrows the StepFunc Protocol to the types.FunctionType for inspect compatibility.

    Cohesion:
        Single-purpose helper for source location resolution. Used only by Definition.as_message.

    Separation:
        - Definition.as_message: Consumes the (file, line) tuple to construct SourceReference and Location; this
        function handles the extraction logic.
        - pytest_bdd.compatibility.path.resolvepath: Resolves the file path relative to config.rootpath; used by
        as_message, not by this function.

    Main consumers:
        - Definition.as_message: The sole caller; uses the returned tuple to populate SourceReference.uri and Location.line.

    State and side effects:
        Reads the filesystem via inspect.getfile/getsourcelines (reads source files). No mutation, no network I/O.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    typed_func = cast("FunctionType", func)
    source_file = getfile(typed_func)
    try:
        source_line = getsourcelines(typed_func)[1]
    except (OSError, TypeError):
        source_line = getattr(getattr(func, "__code__", None), "co_firstlineno", 1) or 1
    return source_file, int(source_line)


@define(eq=False)
class Definition:
    """
    Attrs-based data class representing a single registered BDD step definition binding.

    Responsibility:
        Attrs-based data class representing a single registered BDD step definition binding. Stores the step function
        (func), step type (type_: given/when/then or PickleStepType), parser (StepParser instance), anonymous group
        names for regex parsers, converter functions for parameter type coercion, fixture mapping configuration
        (params_fixtures_mapping) controlling how step parameters map to pytest fixtures, parameter default values
        (param_defaults), target fixture names (target_fixtures), and behavioural flags (liberal, not_implemented,
        tolerant). Provides methods to compute fixture names from step parameters
        (fixtures_mapped_from_step_definition), serialise to cucumber_messages StepDefinition (as_message), and resolve
        actual parameter values from a PickleStep at execution time (get_parameters).

    Reason for existence:
        This is the central domain object of the step definition layer — it is the "row" in the step registry. It exists
        as a separate class (rather than being a dict or tuple) because it carries both data (the attrs fields) and
        behaviour (the three methods) that are tightly coupled to that data. The id field is lazily assigned
        (init=False) via the IdGenerator to ensure deterministic, unique identification within a test run. The __cache
        dict memoises as_message results per IdGenerator instance, preventing duplicate cucumber_messages protocol
        objects. It is kept in definition.py (rather than in registry.py or manager.py) because it is the shared entity
        that both creation (manager) and consumption (matcher, registry) depend on, and placing it in either would
        create a circular dependency.

    Delegates:
        - self.parser.parse_arguments: Called by get_parameters to extract named parameter values from a step name.
        - self.parser.arguments: Read by fixtures_mapped_from_step_definition to determine expected parameter names.
        - self.parser.type: Read by as_message to determine the StepDefinitionPatternType for the pattern message.
        - _resolve_callable_source_location: Called by as_message to get the source file and line of the step function.
        - IdGenerator.from_stash: Called by as_message to get a unique ID for the StepDefinition message.
        - converters dict: Applied by get_parameters to coerce extracted parameter values to target types.

    Cohesion:
        Every field and method relates to the single concept of "a registered step binding." The fields describe the
        binding's configuration; fixtures_mapped_from_step_definition computes the derived fixture set; as_message
        handles protocol serialisation; get_parameters handles runtime parameter resolution. There are no unrelated
        concerns.

    Separation:
        - StepDefinitionManager.decorator_builder: Creates Definition instances; this class defines what a Definition is
        but not how it is created or registered in namespaces.
        - Matcher: Reads Definition fields (type_, parser, liberal) to match against PickleSteps; this class does not
        own matching logic.
        - Registry: Stores OrderedSet[Definition]; this class defines the stored element but not the container.

    Main consumers:
        - pytest_bdd.steps.manager.StepDefinitionManager.decorator_builder: Constructs Definition(func=..., type_=...,
        parser=..., ...) and attaches it to the step function.
        - pytest_bdd.steps.matcher.Matcher: Reads Definition.type_, Definition.parser, Definition.liberal for matching;
        calls Definition.get_parameters for extraction.
        - pytest_bdd.steps.registry.Registry: Stores Definition objects; Registry.registry discovers them via
        StepProtocol.__pytest_bdd_step_definitions__.
        - pytest_bdd.plugin.pickle_runner: Uses Definition.as_message for reporting and Definition.get_parameters for execution.

    State and side effects:
        Instance-level mutable state: self.id (assigned once by as_message), self.__cache (dict keyed by
        id(id_generator), memoises as_message result). as_message reads from pytest config stash via
        IdGenerator.from_stash. get_parameters calls parser.parse_arguments which may access fixtures via the
        FixtureRequest. No direct file/network I/O.

    Invariants:
        - self.parser must always be a valid StepParserProtocol-compliant object.
        - self.id is not set until as_message is called; after that, it is stable for the lifetime of the Definition.
        - fixtures_mapped_from_step_definition must return a set of fixture name strings that is a superset of the
        actual fixtures needed to execute the step.
        - as_message must return the same StepDefinition object for the same IdGenerator instance (enforced by __cache).

    Failure semantics:
        - TypeError: Raised by as_message when parser_expression_type (from self.parser.type) cannot be converted to a
        valid StepDefinitionPatternType enum value. Indicates a parser that reports an unrecognised pattern type.
        Callers should catch this and either provide a valid parser.type or add the pattern type to the
        StepDefinitionPatternType enum.

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

    func: StepFunc = field()
    type_: str | PickleStepType | None = field()
    parser: StepParser = field()
    anonymous_group_names: Iterable[str] | None = field()
    converters: Mapping[str, ConverterT] = field()
    params_fixtures_mapping: ParamsFixturesMapping = field()
    param_defaults: Mapping[str, object] = field()
    target_fixtures: Sequence[str] = field()
    liberal: bool | None = field()
    not_implemented: bool = field(default=False)
    tolerant: bool = field(default=False)

    id: str = field(init=False)
    __cache: dict[int, StepDefinition] = field(factory=dict)

    @property
    def fixtures_mapped_from_step_definition(self) -> set[str]:
        """
        Computes the complete set of pytest fixture names that this step definition requires.

        Responsibility:
            Computes the complete set of pytest fixture names that this step definition requires. Starts with the
            parser's declared argument names (or anonymous_group_names if set), adds any explicitly named fixtures from
            target_fixtures, then applies the params_fixtures_mapping configuration: if it is a Mapping, extracts
            fixture names from its values and applies wildcard/ellipsis strategy; if it is a Collection, union the
            collection into fixture names; if True (boolean), all non-converted parameters bypass as fixtures; if False,
            no automatic fixture injection. Returns the final set of fixture name strings.

        Reason for existence:
            This is the central fixture resolution algorithm. It exists as a property on Definition because the logic
            depends on the interplay of four Definition fields (parser.arguments, anonymous_group_names,
            target_fixtures, params_fixtures_mapping) and the result is used by the decorator_builder to inject
            placeholder fixtures into the caller's module namespace. Keeping it on Definition ensures the fixture
            resolution logic is co-located with the data it operates on, and the result can be computed on demand
            without storing redundant state.

        Delegates:
            - self.parser.arguments: Provides the set of parameter names expected by the parser.
            - getitemdefault(self.params_fixtures_mapping, ..., default=...): Used to detect the Ellipsis (...) wildcard
            in Mapping-based params_fixtures_mapping.

        Cohesion:
            This method is tightly coupled to Definition's fields — it reads parser, anonymous_group_names,
            target_fixtures, and params_fixtures_mapping and produces a derived value. It serves the fixture injection
            concern within the step definition lifecycle.

        Separation:
            - StepDefinitionManager.decorator_builder: Consumes this property's result to call
            namespace.setdefault(fixture_name, _none_fixture(fixture_name)) for each fixture name.
            - _none_fixture: Creates placeholder pytest fixtures for names returned by this property.

        Main consumers:
            - StepDefinitionManager.decorator_builder: The inner decorator iterates over
            step_definition.fixtures_mapped_from_step_definition to inject placeholder fixtures.

        State and side effects:
            None, pure property. Computes from immutable (after construction) instance fields.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=5
            #arch-eval:locational_stability=5
        """
        known_params = (
            set(self.parser.arguments) if self.anonymous_group_names is None else set(self.anonymous_group_names)
        )

        fixture_names = {*self.target_fixtures}
        converted_params: set[str]
        wildcard_params_strategy: object

        if isinstance(self.params_fixtures_mapping, Mapping):
            converted_params = {param for param in self.params_fixtures_mapping if isinstance(param, str)}
            fixture_names.update(
                fixture_name for fixture_name in self.params_fixtures_mapping.values() if isinstance(fixture_name, str)
            )
            wildcard_params_strategy = getitemdefault(self.params_fixtures_mapping, ..., default=...)
        elif isinstance(self.params_fixtures_mapping, Collection):
            converted_params = set()
            wildcard_params_strategy = None
            fixture_names.update(self.params_fixtures_mapping)
        elif bool(self.params_fixtures_mapping):
            converted_params = set()
            wildcard_params_strategy = ...
        else:
            converted_params = set()
            wildcard_params_strategy = None

        if wildcard_params_strategy is ...:
            bypassed_params = known_params.difference(converted_params)
            fixture_names.update(bypassed_params)
        return fixture_names

    def as_message(self, config: Config | HasPytestStash) -> StepDefinition:
        """
        Serialise this Definition into a cucumber_messages StepDefinition protocol object.

        Responsibility:
            Serialises this Definition into a cucumber_messages StepDefinition protocol object. Lazily assigns self.id
            from an IdGenerator obtained from config.stash, resolves the parser's pattern type to a
            StepDefinitionPatternType enum (raising TypeError for unrecognised types), constructs a
            StepDefinitionPattern with the parser's string representation as source, resolves the step function's source
            location via _resolve_callable_source_location, and builds a full SourceReference with Java interop fields
            (JavaMethod, JavaStackTraceElement). Results are memoised per IdGenerator instance via the __cache dict.

        Reason for existence:
            This method is the bridge between the internal Definition model and the Cucumber Messages protocol used for
            reporting. It exists on Definition (rather than as a standalone function or on a reporter class) because the
            serialisation logic needs access to all Definition fields (func, parser, id, type_) and the memoisation
            cache is instance state. The lazy ID assignment ensures definitions only consume IDs from the IdGenerator
            when they are actually reported, not when they are created.

        Delegates:
            - IdGenerator.from_stash(config.stash): Obtains the unique ID generator for this test run.
            - _resolve_callable_source_location(self.func): Resolves the step function's source file and line.
            - str(self.parser): Used as the StepDefinitionPattern.source.
            - self.parser.type: Used to determine the StepDefinitionPatternType.
            - Path(resolvepath(...)).as_uri(): Converts the source file path to a file:// URI.

        Cohesion:
        Directly serves the serialisation concern for Definition. Every operation in this method builds the
        StepDefinition message from Definition's fields.

        Separation:
            - get_parameters: Handles runtime parameter extraction; this method handles protocol serialisation for reporting.
            - cucumber_messages types: The target format; Definition.as_message constructs them but does not own their schema.

        Main consumers:
            - pytest_bdd.plugin.pickle_runner: Calls definition.as_message(config) to build the StepDefinition message
            for each matched step definition during scenario execution reporting.
            - Reporting plugins (cucumber_json, cucumber_pretty, etc.): Indirect consumers via the StepDefinition messages.

        State and side effects:
            Mutates self.id (set once on first call) and self.__cache (populated with the memoised StepDefinition).
            Reads from config.stash via IdGenerator.from_stash. No file/network I/O beyond source location resolution.

        Failure semantics:
            - TypeError: Raised when self.parser.type returns a value that is neither a StepDefinitionPatternType enum
            member nor a string that is a valid enum value name. The error message includes the unrecognised type for
            debugging. Callers should ensure parser implementations return valid pattern types.

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
        id_generator = IdGenerator.from_stash(config.stash)
        try:
            message = self.__cache[id(id_generator)]
        except KeyError:
            self.id = id_generator.get_next_id()

            parser_expression_type = self.parser.type

            expression_type: StepDefinitionPatternType
            if isinstance(parser_expression_type, StepDefinitionPatternType):
                expression_type = parser_expression_type
            else:
                try:
                    expression_type = StepDefinitionPatternType(str(parser_expression_type))  # type: ignore[call-arg]  # pydantic model __init__ via **kwargs
                except ValueError as exc:
                    msg = f"Unsupported step definition pattern type: {parser_expression_type!r}"
                    raise TypeError(msg) from exc

            pattern = StepDefinitionPattern(source=str(self.parser), type=expression_type)
            source_file, source_line = _resolve_callable_source_location(self.func)
            message = self.__cache[id(id_generator)] = StepDefinition(
                id=self.id,
                pattern=pattern,
                source_reference=SourceReference(
                    uri=Path(resolvepath(source_file, getattr(config, "rootpath", Path.cwd()))).as_uri(),
                    location=Location(line=source_line, column=1),
                    java_method=JavaMethod(
                        class_name="pytest_bdd.steps.StepDefinition",
                        method_name=str(self.func.__name__),
                        method_parameter_types=[],
                    ),
                    java_stack_trace_element=JavaStackTraceElement(
                        class_name="pytest_bdd.steps.StepDefinition",
                        file_name=Path(source_file).name,
                        method_name=str(self.func.__name__),
                    ),
                ),
            )
        return message

    def get_parameters(self, request: FixtureRequest, step: Step) -> dict[str, object]:
        """
        Resolve the actual parameter values for executing this step definition against a given PickleStep.

        Responsibility:
            Resolves the actual parameter values for executing this step definition against a given PickleStep. Calls
            self.parser.parse_arguments to extract named parameter values from the step text, applies default values
            from self.param_defaults for missing parameters, and runs each extracted value through the corresponding
            converter function from self.converters (or an identity lambda if no converter is registered). Returns the
            final dict mapping parameter names to converted values, ready for injection into the step function.

        Reason for existence:
            This is the runtime parameter resolution method called by the pickle_runner during step execution. It exists
            on Definition (rather than in the runner) because it encapsulates the full parameter pipeline that is
            specific to this definition: parser extraction, default application, and type conversion. Keeping it here
            ensures that changes to the parameter resolution logic (e.g., adding new converter types) only affect the
            Definition class.

        Delegates:
            - self.parser.parse_arguments(request, step.text, anonymous_group_names=self.anonymous_group_names):
            Extracts raw parameter values from the step text.
            - self.param_defaults: Provides fallback values for parameters not found in the step text.
            - self.converters: Dict of parameter-name-to-callable mappings applied to coerce extracted values.

        Cohesion:
            Directly serves the runtime parameter resolution concern. Uses the parser, param_defaults, and converters
            fields — all Definition-owned data.

        Separation:
            - as_message: Handles serialisation for reporting; this method handles runtime parameter extraction for execution.
            - StepParser.parse_arguments: Extracts raw values; this method applies defaults and converters on top.

        Main consumers:
            - pytest_bdd.plugin.pickle_runner: Calls definition.get_parameters(request, step) to obtain the parameter
            dict for step function invocation.

        State and side effects:
            Calls parser.parse_arguments which may access pytest fixtures via the FixtureRequest (side effect: fixture
            resolution). No instance state mutation. No file/network I/O.

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
        parsed_arguments = (
            self.parser.parse_arguments(request, step.text, anonymous_group_names=self.anonymous_group_names) or {}
        )
        return {
            **self.param_defaults,
            **{arg: self.converters.get(arg, lambda value: value)(value) for arg, value in parsed_arguments.items()},  # type: ignore[no-untyped-call]  # dynamic converter call
        }
