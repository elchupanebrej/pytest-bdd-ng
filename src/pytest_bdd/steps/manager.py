"""
Implements StepDefinitionManager, the central orchestrator for step definition registration.

Responsibility:
    Implements StepDefinitionManager, the central orchestrator for step definition registration. Its static method
    `decorator_builder` is a factory that produces @given/@when/@then/@step decorators: when applied to a function, the
    inner decorator constructs a Definition object via the parser subsystem (StepParser.build), attaches the Definition
    to the function via `__pytest_bdd_step_definitions__`, injects placeholder pytest fixtures for mapped parameters
    into the caller's module namespace, and registers the function under a generated unique name in that namespace. Also
    provides the _none_fixture helper that creates pytest fixtures returning None for step parameters not yet bound to
    real fixtures.

Reason for existence:
    This module is the information expert for the step registration process because it owns the complete decorator
    construction pipeline: resolving target fixtures from overlapping target_fixture/target_fixtures parameters,
    constructing the Definition with all its fields, attaching the definition to the decorated function, generating
    unique namespace names, injecting placeholder fixtures, and discovering the caller's module namespace via
    get_caller_module_locals. It is kept separate from definition.py (which defines the Definition data model) because
    the Definition is a passive data object, while this module owns the active orchestration that creates, attaches, and
    namespace-registers definitions. Separating them prevents definition.py from depending on pytest fixture internals
    and namespace manipulation utilities.

Delegates:
    - StepParser.build(step_parserlike): Constructs the appropriate StepParser from the user-provided pattern (string,
    regex, or parser instance).
    - Definition(...): The attrs constructor called with all resolved parameters to create the step binding object.
    - setdefaultattr(step_func, "__pytest_bdd_step_definitions__", value_factory=set): Ensures the decorated function
    has a set of Definition objects for registry discovery.
    - format_as_python_identifier(f"step_{step_type or ''}_{step_parserlike}_{uuid4()}"): Generates a unique, valid
    Python identifier for the step function in the caller's namespace.
    - get_caller_module_locals(stacklevel=stacklevel): Introspects the caller's stack frame to obtain the module-level
    namespace dict for fixture injection.
    - _none_fixture(fixture_name): Creates a pytest fixture that returns None, serving as a placeholder for step
    parameters not yet mapped to real fixtures.
    - OrderedSet: Used to deduplicate target fixture names when both target_fixture and target_fixtures are specified.

Cohesion:
    Every entity in this module serves the step registration orchestration pipeline.
    StepDefinitionManager.decorator_builder constructs decorators; its inner decorator function creates and attaches
    Definitions; _none_fixture creates placeholder fixtures needed by that process; _none_fixture.placeholder is the
    actual pytest fixture function. All operate on the same step-definition-creation lifecycle.

Separation:
    - definition.py (Definition): Defines the data object being created; this module orchestrates its creation and
    registration. Definition does not import manager.
    - registry.py (Registry): Discovers step definitions from namespace objects at collection time; this module plants
    the definitions and fixtures that registry later discovers. Manager writes, Registry reads.
    - matcher.py (Matcher): Matches definitions to steps at runtime; this module has no matching logic.
    - decorators.py (@given, @when, @then, @step): Thin wrappers that call StepDefinitionManager.decorator_builder with
    the appropriate step_type; manager provides the builder, decorators provide the user-facing API.

Main consumers:
    - pytest_bdd.steps.decorators.given / when / then / step / tolerant / not_implemented: Each calls
    StepDefinitionManager.decorator_builder(step_type=..., ...) and returns the resulting decorator.
    - End-user test files: Import and use @given, @when, @then, @step which indirectly invoke decorator_builder.

State and side effects:
    decorator_builder mutates the caller's module namespace: injects placeholder fixtures via
    namespace.setdefault(fixture_name, _none_fixture(fixture_name)) and registers the step function via
    namespace[converted_name] = step_func. It also mutates the decorated function by setting
    __pytest_bdd_step_definitions__ to a set of Definition objects. No file/network I/O. Reads the call stack via
    get_caller_module_locals.

Invariants:
    - Every call to decorator_builder must produce a decorator that, when applied, creates exactly one Definition and
    adds it to the function's __pytest_bdd_step_definitions__ set.
    - Placeholder fixtures injected into the namespace must not overwrite existing fixtures (namespace.setdefault
    ensures this).
    - Fixture names starting with "pytest_" are skipped during injection to avoid conflicting with pytest's internal
    fixtures.
    - The generated unique name for each step function ensures that multiple steps with the same pattern can coexist in
    the same module namespace.

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

import warnings
from collections.abc import (  # noqa: TC003  -- needed at runtime for attrs validators and generic type checks
    Iterable,
    Mapping,
    Sequence,
)
from typing import cast
from uuid import uuid4

import pytest
from cucumber_messages import (
    PickleStepType,  # noqa: TC002  -- used in runtime isinstance checks inside attrs validators
)
from ordered_set import OrderedSet

from pytest_bdd.steps.definition import (
    ConverterT,
    Definition,
    ParamsFixturesMapping,
    StepDecorator,
    StepFunc,
)
from pytest_bdd.steps.matcher import Matcher
from pytest_bdd.steps.registry import Registry, StepProtocol, StepRegistryProtocol
from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning
from pytest_bdd.util.inspect_extra import get_caller_module_locals
from pytest_bdd.util.other import format_as_python_identifier
from pytest_bdd.util.toolz_extra import setdefaultattr


class StepDefinitionManager:
    """
    Central orchestrator for step definition registration.

    Responsibility:
        Central orchestrator for step definition registration. Exposes class-level references to Registry, Matcher,
        Definition, StepProtocol, and StepRegistryProtocol for convenient single-import access. Its sole behavioural
        method is the static decorator_builder, a factory that constructs @given/@when/@then/@step decorators. The
        builder resolves overlapping target_fixture and target_fixtures parameters (emitting a warning if both are
        specified), constructs a Definition via the parser subsystem, attaches it to the decorated function, generates a
        unique namespace identifier for the function, injects placeholder pytest fixtures for all fixture names derived
        from the Definition, and registers the function in the caller's module namespace.

    Reason for existence:
        This class exists as a namespace container and orchestrator rather than a set of module-level functions because
        the step registration pipeline involves multiple tightly coupled steps (parameter resolution, Definition
        construction, attribute attachment, namespace injection, fixture placeholder creation) that share the same
        configuration parameters. The class provides a single, discoverable entry point (decorator_builder) and exposes
        the key types (Registry, Matcher, Definition) as class attributes for convenient access without additional
        imports. It is kept separate from the Definition class because Definition is a data object, while this class
        owns the active orchestration logic.

    Delegates:
        - StepParser.build(step_parserlike): Constructs the appropriate StepParser from the user's pattern argument.
        - Definition(...): Attrs constructor creating the step binding with all resolved parameters.
        - setdefaultattr(step_func, "__pytest_bdd_step_definitions__", value_factory=set): Attaches a definitions set to
        the decorated function for Registry discovery.
        - format_as_python_identifier(...): Generates unique, valid Python identifiers for step functions.
        - get_caller_module_locals(stacklevel=stacklevel): Obtains the caller's module namespace dict for injection.
        - _none_fixture(fixture_name): Creates a pytest fixture placeholder for parameters not yet bound to real fixtures.
        - OrderedSet: Deduplicates fixture name lists.
        - warnings.warn: Emits PytestBDDStepDefinitionWarning when both target_fixture and target_fixtures are specified.

    Cohesion:
        Every class attribute and the single static method serve the step registration concern. The class aliases
        (Registry, Matcher, Definition, StepProtocol, NamespaceStepRegistryProtocol) provide convenience access;
        decorator_builder provides the behaviour.

    Separation:
        - definition.py (Definition): The data object being created and attached. This class orchestrates creation;
        Definition stores the result.
        - registry.py (Registry): Discovers definitions at collection time. This class plants them; Registry harvests them.
        - decorators.py: Thin wrappers that call decorator_builder with specific step_type values. This class provides
        the builder; decorators provide the user-facing @given/@when/@then API.

    Main consumers:
        - pytest_bdd.steps.decorators.given / when / then / step / tolerant / not_implemented: Each calls
        StepDefinitionManager.decorator_builder(step_type=..., ...).
        - Downstream code that references StepDefinitionManager.Registry, StepDefinitionManager.Matcher,
        StepDefinitionManager.Definition for convenience.

    State and side effects:
        No instance state (all methods are static, class is never instantiated). decorator_builder mutates: (1) the
        decorated function's __pytest_bdd_step_definitions__ attribute, (2) the caller's module namespace (injects
        fixtures and registers function names), (3) the caller's module via setdefaultattr. Reads the call stack via
        get_caller_module_locals.

    Invariants:
        - decorator_builder must always return a callable decorator that accepts and returns a StepFunc.
        - The inner decorator must create exactly one Definition per application.
        - Placeholder fixtures must use namespace.setdefault to avoid overwriting user-defined fixtures.
        - Fixture names starting with "pytest_" must be skipped during injection.

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

    Registry = Registry
    Matcher = Matcher
    Definition = Definition
    StepProtocol = StepProtocol
    NamespaceStepRegistryProtocol = StepRegistryProtocol

    @staticmethod
    def decorator_builder(  # noqa: PLR0913, PLR0917  -- step decorator builder requires all config params in one call site
        step_type: str | PickleStepType | None,
        step_parserlike: object,
        anonymous_group_names: Iterable[str] | None = None,
        converters: Mapping[str, ConverterT] | None = None,
        target_fixture: str | None = None,
        target_fixtures: Sequence[str] | None = None,
        params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002  -- boolean default is the documented public API default for this parameter
        param_defaults: Mapping[str, object] | None = None,
        *,
        liberal: bool | None = None,
        stacklevel: int = 2,
    ) -> StepDecorator:
        """
        Produce a step decorator function.

        Responsibility:
            Factory method that produces a step decorator function. Accepts all configuration parameters for a step
            definition: step_type (given/when/then), the parserlike pattern, anonymous group names for regex parsers,
            converter mappings for parameter type coercion, target fixture names (with deduplication and overlap warning
            via OrderedSet), params_fixtures_mapping configuration, parameter defaults, liberal mode flag, and
            stacklevel for caller namespace discovery. Returns a callable decorator that, when applied to a function,
            constructs a Definition, attaches it to the function, injects placeholder fixtures, and registers the
            function in the caller's namespace.

        Reason for existence:
            This is the single entry point for all step decorator construction, used by @given, @when, @then, @step,
            @tolerant, and @not_implemented. It exists as a static method on StepDefinitionManager rather than as a
            module-level function because it is the primary behaviour of the manager and benefits from the class's
            namespace context. The extensive parameter list is necessary because step definitions support a rich
            configuration surface; using a builder method with keyword arguments is more usable than requiring users to
            construct Definition objects directly.

        Delegates:
            - OrderedSet: Deduplicates the combined target_fixture + target_fixtures list.
            - warnings.warn: Emits PytestBDDStepDefinitionWarning when both target_fixture and target_fixtures are specified.
            - Inner decorator function: The returned closure that performs the actual decoration when applied to a StepFunc.

        Cohesion:
            This method exists solely to produce step decorators. All its logic (parameter resolution, warning emission,
            decorator construction) serves that purpose.

        Separation:
            - Inner decorator: The returned closure that performs Definition construction and namespace injection; this
            method sets up the closure's captured state.
            - @given/@when/@then in decorators.py: Thin callers that pass only the step_type to this method.

        Main consumers:
            - pytest_bdd.steps.decorators.given / when / then / step / tolerant / not_implemented: Each calls this
            method with the appropriate step_type.

        State and side effects:
            None at call time (only returns a decorator). The side effects happen when the returned decorator is applied
            to a function (see inner decorator documentation).

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
        converters = dict(converters or {})
        param_defaults = dict(param_defaults or {})
        if target_fixture is not None and target_fixtures is not None:
            warnings.warn(
                PytestBDDStepDefinitionWarning("Both target_fixture and target_fixtures are specified"),
                stacklevel=2,
            )
        resolved_target_fixtures: list[str] = list(
            OrderedSet(
                [
                    *([target_fixture] if target_fixture is not None else []),
                    *(target_fixtures if target_fixtures is not None else []),
                ],
            ),
        )

        def decorator(step_func: StepFunc) -> StepFunc:
            """
            Act as the inner decorator closure returned by decorator_builder.

            Responsibility:
                The inner decorator closure returned by decorator_builder. When applied to a step function, it: (1)
                imports StepParser via deferred import to avoid circular dependencies, (2) constructs a Definition with
                all resolved parameters (func, type_, parser from StepParser.build, converters, fixture mappings, flags
                for not_implemented and tolerant), (3) attaches the Definition to the function's
                __pytest_bdd_step_definitions__ set (creating it if needed via setdefaultattr), (4) generates a unique
                Python identifier for the function and registers it in the caller's module namespace, and (5) injects
                placeholder pytest fixtures for all fixture names derived from the Definition's
                fixtures_mapped_from_step_definition, skipping names starting with "pytest_". Returns the original
                step_func unchanged.

            Reason for existence:
                This closure is the actual decorator that executes when @given/@when/@then is applied. It exists as a
                nested function to capture the configuration parameters from decorator_builder's scope (step_type,
                step_parserlike, converters, etc.) without requiring them to be passed explicitly. The deferred import
                of StepParser inside the closure avoids a circular import between parsers and steps.

            Delegates:
                - StepParser.build(step_parserlike): Constructs the parser from the user's pattern.
                - Definition(...): Creates the step binding data object.
                - setdefaultattr(step_func, "__pytest_bdd_step_definitions__", value_factory=set): Creates or retrieves
                the definition set on the decorated function.
                - format_as_python_identifier(f"step_{step_type or ''}_{step_parserlike}_{uuid4()}"): Generates a unique
                namespace-safe name.
                - get_caller_module_locals(stacklevel=stacklevel): Obtains the caller's module namespace.
                - step_definition.fixtures_mapped_from_step_definition: Computes the set of fixture names to inject.
                - _none_fixture(fixture_name): Creates a placeholder pytest fixture for each unmapped parameter.
                - namespace.setdefault(fixture_name, _none_fixture(fixture_name)): Injects fixtures without overwriting existing ones.

            Cohesion:
                Every operation in this closure serves the single purpose of registering a step function with the
                framework. The sequence is: construct Definition, attach to function, register in namespace, inject
                fixtures.

            Separation:
                - decorator_builder: Sets up the captured configuration; this closure applies it to a specific function.
                - Definition: The data object being constructed; this closure owns the construction orchestration.

            Main consumers:
                - End-user test code: When @given('pattern'), @when('pattern'), @then('pattern'), or @step('pattern') is
                applied to a function, this closure executes.

            State and side effects:
                Mutates: (1) step_func.__pytest_bdd_step_definitions__ (appends Definition), (2) caller's module
                namespace (adds function under generated name, adds placeholder fixtures), (3) potentially triggers
                StepParser.build which imports parser modules. Reads the call stack via get_caller_module_locals.

            Architecture score:
                #arch-eval:reason_for_existence=5
                #arch-eval:owned_responsibility=5
                #arch-eval:delegation_boundary=5
                #arch-eval:cohesion=5
                #arch-eval:separation=5
                #arch-eval:consumer_clarity=4
                #arch-eval:state_invariants=4
                #arch-eval:entity_fullness=5
                #arch-eval:locational_stability=5
            """
            from pytest_bdd.parsers import StepParser

            step_definition = Definition(
                func=step_func,
                type_=step_type,
                parser=StepParser.build(step_parserlike),
                anonymous_group_names=anonymous_group_names,
                converters=converters,
                params_fixtures_mapping=params_fixtures_mapping,
                param_defaults=param_defaults,
                target_fixtures=resolved_target_fixtures,
                liberal=liberal,
                not_implemented=bool(getattr(step_func, "__pytest_bdd_not_implemented__", False)),
                tolerant=bool(getattr(step_func, "__pytest_bdd_tolerant__", False)),
            )

            step_definitions = cast(
                "set[Definition]",
                setdefaultattr(step_func, "__pytest_bdd_step_definitions__", value_factory=set),
            )
            step_definitions.add(step_definition)

            # Allow step function to have same names, so injecting same steps with generated names into module scope
            converted_name = format_as_python_identifier(f"step_{step_type or ''}_{step_parserlike}_{uuid4()}")
            namespace = get_caller_module_locals(stacklevel=stacklevel)
            namespace[converted_name] = step_func

            for fixture_name in step_definition.fixtures_mapped_from_step_definition:
                if fixture_name.startswith("pytest_"):
                    continue
                namespace.setdefault(fixture_name, _none_fixture(fixture_name))

            return step_func

        return decorator


def _none_fixture(name: str) -> object:
    """
    Create a pytest fixture function that returns None, registered under the given `name`.

    Responsibility:
        Creates a pytest fixture function that returns None, registered under the given `name`. Used as a placeholder
        fixture for step definition parameters that have been auto-mapped to fixtures but do not yet have a real user-
        defined fixture implementation. The fixture is created via @pytest.fixture(name=name) and its body simply
        returns None.

    Reason for existence:
        Exists because the step definition framework auto-discovers fixture dependencies from step parameters (via
        parser.arguments and params_fixtures_mapping) and must inject corresponding fixture names into the module
        namespace so pytest's fixture resolution does not fail during collection. These placeholder fixtures provide a
        safe default (returning None) until the user defines a real fixture with the same name. The placeholder fixture
        pattern keeps the framework working out of the box without requiring users to define fixtures for every step
        parameter upfront.

    Delegates:
        - @pytest.fixture(name=name): Registers the inner placeholder function as a pytest fixture with the given name.
        - Inner placeholder function: The actual fixture implementation that returns None.

    Cohesion:
        This function exists solely to support the step registration pipeline in decorator_builder's inner decorator. It
        is called for every auto-mapped fixture name.

    Separation:
        - decorator_builder decorator closure: Calls _none_fixture(fixture_name) for each derived fixture name and
        injects it via namespace.setdefault.
        - User-defined fixtures: Real fixtures with the same name override these placeholders in pytest's fixture resolution.

    Main consumers:
        - StepDefinitionManager.decorator_builder's inner decorator: Calls namespace.setdefault(fixture_name,
        _none_fixture(fixture_name)) for each auto-mapped fixture.

    State and side effects:
        The returned object is a pytest fixture function; when pytest processes the module, it registers this function
        as a fixture. The fixture itself has no side effects (returns None). The function creates a closure over `name`
        for the fixture registration.

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

    @pytest.fixture(name=name)  # type: ignore[untyped-decorator]  # pytest fixture decorator is intentionally untyped
    def placeholder() -> None:
        """
        Act as the actual pytest fixture function returned by _none_fixture.

        Responsibility:
            The actual pytest fixture function returned by _none_fixture. Returns None unconditionally, serving as a
            default/placeholder value for step definition parameters that have been auto-mapped to fixtures but do not
            yet have a user-defined fixture implementation. The @pytest.fixture(name=name) decorator registers it under
            the given name in pytest's fixture namespace.

        Reason for existence:
            This is the minimal valid pytest fixture implementation: it takes no parameters (no fixture dependencies),
            returns None, and has no side effects. It exists as a nested function inside _none_fixture so that the
            `name` parameter from the outer scope is captured and used as the fixture's registered name via the
            @pytest.fixture decorator.

        Delegates:
            - No delegation: returns None directly.

        Cohesion:
            The sole purpose is to return None as a placeholder fixture value. It is nested within _none_fixture to
            capture the fixture name.

        Separation:
            - User-defined fixtures: Override this placeholder when a real fixture with the same name is defined.
            - _none_fixture: The factory that creates and returns this function as a pytest fixture.

        Main consumers:
            - pytest's fixture resolution system: Invokes this fixture when a step function's parameter has this fixture
            name and no real fixture exists.

        State and side effects:
            None. Returns None with no side effects.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        return

    return placeholder
