"""
Owns the public step definition decorator functions (given, when, then, step) and behavior-modifying decorators (not_.

Responsibility:
    Owns the public step definition decorator functions (given, when, then, step) and behavior-modifying decorators
    (not_implemented, tolerant) that end-user test code uses to register BDD step definitions. Each of
    given/when/then/step is a thin delegation wrapper that calls StepDefinitionManager.decorator_builder() with the
    appropriate PickleStepType (context/action/outcome/unknown), forwarding all parser configuration parameters
    (parserlike, anonymous_group_names, converters, target_fixture, target_fixtures, params_fixtures_mapping,
    param_defaults, liberal, stacklevel). The not_implemented and tolerant decorators stamp metadata attributes
    (__pytest_bdd_not_implemented__, __pytest_bdd_tolerant__) onto step functions and their associated Definition
    objects to control error handling and reporting behavior.

Reason for existence:
    This module is the primary public API that BDD test authors interact with. It provides the familiar given/when/then
    DSL that makes pytest-bdd readable and expressive. The thin delegation pattern (each decorator simply forwards to
    StepDefinitionManager.decorator_builder) keeps the public API surface clean while centralizing the complex decorator
    logic in the manager class. The not_implemented and tolerant decorators modify step behavior without changing the
    step registration pipeline — they are orthogonal concerns that modify metadata on already-registered step functions.

Delegates:
    - StepDefinitionManager.decorator_builder (from pytest_bdd.steps.manager): The actual decorator factory that creates
    step decorators and registers step definitions with the plugin's step registry.
    - PickleStepType (from cucumber_messages): The enum values (context for Given, action for When, outcome for Then,
    unknown for step) that classify step keyword types.
    - pytest_bdd.steps.definition.Definition: The Definition objects whose metadata attributes are modified by
    not_implemented and tolerant.

Cohesion:
    All entities in this module serve the same purpose: providing the public step definition API. The
    given/when/then/step quartet follows identical patterns (forwarding to manager.decorator_builder with a
    PickleStepType), and not_implemented/tolerant follow an identical pattern (stamping metadata on step functions and
    their Definition objects). The module is a pure delegation layer with zero business logic.

Separation:
    - pytest_bdd.steps.manager.StepDefinitionManager: Kept separate because the manager owns the actual decorator
    implementation (parser building, step registration, fixture creation) while this module provides the public API
    surface — implementation vs interface.
    - pytest_bdd.hook: Kept separate because hook.py owns lifecycle hook decorators (before_mark, after_tag, etc.) while
    this module owns step definition decorators (given, when, then) — hooks vs steps, completely different execution
    models.

Main consumers:
    - End-user test code (conftest.py, test files): Import given, when, then, step, not_implemented, tolerant for step
    definition registration.
    - pytest_bdd.steps (top-level module): Re-exports these decorators as the primary step definition API.

State and side effects:
    None at module level. The decorator functions are stateless — all state management is delegated to
    StepDefinitionManager and the step registry. not_implemented and tolerant mutate metadata attributes on the
    decorated function object (in-place modification), which is an intentional side effect on the function object.

Invariants:
    - given must always use PickleStepType.context, when must use PickleStepType.action, then must use
    PickleStepType.outcome, step must use PickleStepType.unknown — these mappings align with the Gherkin specification's
    Given/When/Then keyword semantics.
    - All decorators must increment stacklevel by 1 before passing to manager.decorator_builder to ensure correct stack
    frame resolution for source code introspection.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=3
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from collections.abc import (  # noqa: TC003  -- needed at runtime for attrs validators and generic type checks in step decorators
    Iterable,
    Mapping,
    Sequence,
)
from typing import Any, cast

from cucumber_messages import PickleStepType

from pytest_bdd.steps.definition import (
    ConverterT,
    Definition,
    ParamsFixturesMapping,
    StepDecorator,
    StepFunc,
)
from pytest_bdd.steps.manager import StepDefinitionManager


def not_implemented(step_func: StepFunc) -> StepFunc:
    """
    Decorate a step function as "not implemented" for reporting purposes.

    Responsibility:
        Decorator that marks a step function as "not implemented" for reporting purposes. Sets the
        __pytest_bdd_not_implemented__ attribute to True on the function object and iterates over any attached
        Definition objects (stored in __pytest_bdd_step_definitions__), setting their not_implemented flag to True. This
        causes the step reporter to display the step as not-yet-implemented rather than failed, helping teams track
        implementation progress across scenarios.

    Reason for existence:
        In BDD workflows, teams often write scenarios before implementing step definitions (specification-first
        development). The not_implemented decorator allows step functions to exist as stubs that are recognized as
        pending rather than failing, providing accurate progress reporting. The decorator modifies both the function-
        level attribute (for quick checks) and each Definition object (for detailed reporting in formatters like
        cucumber_json and cucumber_pretty).

    Delegates:
        - cast("Any", step_func).__pytest_bdd_not_implemented__: Sets the module-level marker attribute on the function.
        - Definition.not_implemented: Sets the flag on each Definition object associated with the step function for
        formatter-level visibility.

    Cohesion:

    Args:
        step_func: The step definition function to decorate.

    Returns:
        The decorated step function with metadata attributes set.
        The function performs one coherent operation: mark a step definition and all its associated Definition objects
        as not implemented. The function-level attribute and per-Definition iteration serve the same purpose at
        different granularities.

    Separation:
        - tolerant: Kept separate because tolerant marks steps as "should not fail on error" while not_implemented marks
        steps as "not yet done" — different semantics, though they share the same metadata-stamping pattern.

    Main consumers:
        - End-user test code: @not_implemented applied as a secondary decorator on step functions.
        - pytest_bdd.plugin.cucumber_json and cucumber_pretty: Read the not_implemented flag during reporting to display
        correct step status.

    State and side effects:
        Mutates the step_func object in place (sets __pytest_bdd_not_implemented__ attribute) and mutates each
        Definition object in place (sets definition.not_implemented). These are intentional side effects on the
        decorated function and its metadata.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4

    """
    cast("Any", step_func).__pytest_bdd_not_implemented__ = True
    for definition in getattr(step_func, "__pytest_bdd_step_definitions__", ()):
        if isinstance(definition, Definition):
            definition.not_implemented = True
    return step_func


def tolerant(step_func: StepFunc) -> StepFunc:
    """
    Decorate a step function as "tolerant"; failures within this step should be reported as warnings rather than errors.

    Responsibility:
        Decorator that marks a step function as "tolerant" — failures within this step should be reported as warnings
        rather than errors, allowing the scenario to continue execution. Sets the __pytest_bdd_tolerant__ attribute to
        True on the function object and iterates over attached Definition objects, setting their tolerant flag to True.
        This enables "soft assertion" behavior where non-critical steps can fail without aborting the entire scenario.

    Reason for existence:
        Some step definitions perform non-critical operations (logging, cleanup, optional checks) where failure should
        not halt the scenario. The tolerant decorator provides a declarative way to mark such steps, complementing the
        liberal_steps configuration option which applies globally. The per-Definition flag allows formatters to
        distinguish between critical and non-critical step failures in reports.

    Delegates:
        - cast("Any", step_func).__pytest_bdd_tolerant__: Sets the function-level marker attribute.
        - Definition.tolerant: Sets the flag on each Definition object for formatter visibility.

    Cohesion:

    Args:
        step_func: The step definition function to decorate.

    Returns:
        The decorated step function with metadata attributes set.
        The function performs one operation: mark a step and its Definitions as tolerant of failure. Identical pattern
        to not_implemented, applied to a different semantic concern.

    Separation:
        - not_implemented: Kept separate because tolerant means "don't fail on error" while not_implemented means "not
        yet done" — different semantics, identical implementation pattern.

    Main consumers:
        - End-user test code: @tolerant as a secondary decorator.
        - pytest_bdd.plugin.pickle_runner: Checks the tolerant flag during step execution to decide whether to abort on failure.

    State and side effects:
        Mutates step_func and Definition objects in place — intentional side effects on decorated function metadata.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4

    """
    cast("Any", step_func).__pytest_bdd_tolerant__ = True
    for definition in getattr(step_func, "__pytest_bdd_step_definitions__", ()):
        if isinstance(definition, Definition):
            definition.tolerant = True
    return step_func


def given(  # noqa: PLR0913, PLR0917  -- step decorator exposes full BDD step configuration surface; arguments mirror manager.decorator_builder
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002  -- boolean default is the documented public API contract for param-to-fixture mapping
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    Public decorator for registering BDD "Given" step definitions.

    Responsibility:
        Public decorator for registering BDD "Given" step definitions. Delegates to
        StepDefinitionManager.decorator_builder() with PickleStepType.context (the Gherkin keyword type for Given),
        forwarding all parser configuration parameters: parserlike (the step pattern), anonymous_group_names,
        converters, target_fixture, target_fixtures, params_fixtures_mapping, param_defaults, liberal (per-step liberal
        matching override), and stacklevel (incremented for correct stack inspection). Returns a StepDecorator that can
        be applied to step implementation functions.

    Reason for existence:
        This is the "Given" entry point in the BDD given-when-then pattern, representing preconditions or setup context
        for scenarios. The thin delegation to manager.decorator_builder keeps the public API clean while the manager
        handles the complex decorator factory logic. The PickleStepType.context classification ensures that step
        reporters and formatters correctly display "Given" steps in output.

    Delegates:
        - StepDefinitionManager.decorator_builder: The actual decorator factory that handles parser building, step
        registration, and fixture creation.
        - PickleStepType.context: Classifies this as a Given step for message serialization and reporting.

    Cohesion:

    Args:
        *args: Positional arguments for step pattern and configuration (pattern, target_fixture, etc.).
        **kwargs: Keyword arguments for step configuration ( converters, target_fixture, etc.).

    Returns:
        A StepDecorator callable that registers the step definition.
        Performs exactly one operation: forward to manager with Given type. All parameters are passed through unchanged
        except stacklevel which is incremented.

    Separation:
        - when, then, step: Kept separate because each uses a different PickleStepType (action, outcome, unknown) —
        different Gherkin keyword semantics, identical delegation pattern.

    Main consumers:
        - End-user test code: @given(parsers.parse("...")) applied to step functions.

    State and side effects:
        None. Pure delegation call — all state management is in StepDefinitionManager.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=2
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.context,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def when(  # noqa: PLR0913, PLR0917  -- step decorator exposes full BDD step configuration surface; arguments mirror manager.decorator_builder
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002  -- boolean default is the documented public API contract for param-to-fixture mapping
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    Public decorator for registering BDD "When" step definitions, representing actions or events that trigger state changes.

    Responsibility:
        Public decorator for registering BDD "When" step definitions, representing actions or events that trigger state
        changes. Delegates to StepDefinitionManager.decorator_builder() with PickleStepType.action, forwarding all
        parser configuration parameters identically to given(). Returns a StepDecorator for application to step
        implementation functions that perform actions in the scenario.

    Reason for existence:
        The "When" keyword represents the action/event step in BDD (e.g., "When I submit the form"). This decorator is
        structurally identical to given/then/step but classified with PickleStepType.action to ensure correct reporting
        and Gherkin keyword representation in formatters and message serialization.

    Delegates:
        - StepDefinitionManager.decorator_builder: The decorator factory handling parser construction and step registration.
        - PickleStepType.action: Classifies this as a When step for reporting and serialization.

    Cohesion:

    Args:
        *args: Positional arguments for step pattern and configuration (pattern, target_fixture, etc.).
        **kwargs: Keyword arguments for step configuration ( converters, target_fixture, etc.).

    Returns:
        A StepDecorator callable that registers the step definition.
        Identical delegation pattern to given/then/step — single purpose, zero logic beyond type selection.

    Separation:
        - given, then, step: Kept separate because each maps to a distinct PickleStepType with different Gherkin
        semantics — context/action/outcome/unknown.

    Main consumers:
        - End-user test code: @when(parsers.re(r"...")) applied to step functions.

    State and side effects:
        None. Pure delegation.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=2
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.action,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def then(  # noqa: PLR0913, PLR0917  -- step decorator exposes full BDD step configuration surface; arguments mirror manager.decorator_builder
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002  -- boolean default is the documented public API contract for param-to-fixture mapping
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    Public decorator for registering BDD "Then" step definitions, representing expected outcomes or assertions that verif.

    Responsibility:
        Public decorator for registering BDD "Then" step definitions, representing expected outcomes or assertions that
        verify state after actions. Delegates to StepDefinitionManager.decorator_builder() with PickleStepType.outcome,
        forwarding all parser configuration parameters identically to given() and when(). Returns a StepDecorator for
        application to assertion/verification step functions.

    Reason for existence:
        The "Then" keyword represents the outcome/verification step in BDD (e.g., "Then I should see the success
        message"). Classified with PickleStepType.outcome for correct reporting. Structurally identical to other step
        decorators but semantically distinct as the assertion phase of the given-when-then pattern.

    Delegates:
        - StepDefinitionManager.decorator_builder: The decorator factory.
        - PickleStepType.outcome: Classifies this as a Then step for reporting and serialization.

    Cohesion:

    Args:
        *args: Positional arguments for step pattern and configuration (pattern, target_fixture, etc.).
        **kwargs: Keyword arguments for step configuration ( converters, target_fixture, etc.).

    Returns:
        A StepDecorator callable that registers the step definition.
        Single delegation with type selection. Zero business logic.

    Separation:
        - given, when, step: Each uses a different PickleStepType — context/action/outcome/unknown.

    Main consumers:
        - End-user test code: @then(parsers.parse("...")) applied to step functions.

    State and side effects:
        None. Pure delegation.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=2
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.outcome,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def step(  # noqa: PLR0913, PLR0917  -- step decorator exposes full BDD step configuration surface; arguments mirror manager.decorator_builder
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002  -- boolean default is the documented public API contract for param-to-fixture mapping
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    Public decorator for registering generic BDD step definitions that can match any Gherkin keyword (Given, When, or Then).

    Responsibility:
        Public decorator for registering generic BDD step definitions that can match any Gherkin keyword (Given, When,
        or Then). Delegates to StepDefinitionManager.decorator_builder() with PickleStepType.unknown, enabling step
        definitions that are not restricted to a specific keyword type. This is useful for reusable steps (e.g., login
        steps) that can appear as any keyword in different scenarios.

    Reason for existence:
        Some step definitions are keyword-agnostic — the same step implementation can serve as a Given, When, or Then
        depending on the scenario context. The `step` decorator with PickleStepType.unknown enables this flexibility,
        allowing the step to match regardless of the Gherkin keyword used. This avoids the need to register the same
        step definition three times under given, when, and then.

    Delegates:
        - StepDefinitionManager.decorator_builder: The decorator factory.
        - PickleStepType.unknown: Classifies this as a keyword-agnostic step.

    Cohesion:

    Args:
        *args: Positional arguments for step pattern and configuration (pattern, target_fixture, etc.).
        **kwargs: Keyword arguments for step configuration ( converters, target_fixture, etc.).

    Returns:
        A StepDecorator callable that registers the step definition.
        Single delegation with type selection. Identical pattern to given/when/then.

    Separation:
        - given, when, then: Kept separate because those restrict matching to specific keywords, while step matches any
        keyword — specific vs generic keyword matching.

    Main consumers:
        - End-user test code: @step(parsers.parse("...")) applied to reusable step functions.

    State and side effects:
        None. Pure delegation.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=2
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.unknown,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )
