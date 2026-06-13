"""
Public API facade for the step definition subsystem.

Responsibility:
    Public API facade for the step definition subsystem. Re-exports all core types needed by consumers: the step
    decorator functions (given, when, then, step, tolerant, not_implemented), the Definition class representing a
    registered step binding, protocol types (StepFunc, StepProtocol, StepRegistryProtocol), type aliases (StepDecorator,
    ConverterT, ParamsFixturesMapping), the StepDefinitionManager orchestrator, the Matcher engine, and the Registry
    container. Also re-exports PickleStep from cucumber_messages as Step for convenient access.

Reason for existence:
    This package is the information expert for all step-definition lifecycle concerns: registration (via decorators in
    managers.py), storage and discovery (via Registry in registry.py), pattern matching (via Matcher in matcher.py), and
    the canonical Definition data model (in definition.py). It is kept as a separate architectural layer
    (step_definition, order 4) rather than being merged into collection or runtime because step definitions are authored
    by end users independently of how they are collected or executed—the definition is the contract between user code
    and the BDD framework, and changes to registration, matching, or storage should not affect collection or runtime
    layers. The __init__.py facade ensures consumers import from a stable single point.

Delegates:
    - decorators.py: Provides the thin @given, @when, @then, @step, @tolerant, @not_implemented decorator functions that
    call StepDefinitionManager.decorator_builder with the appropriate step_type.
    - definition.py: Defines the Definition attrs class, StepFunc protocol, type aliases (StepDecorator, ConverterT,
    ParamsFixturesMapping), and _resolve_callable_source_location.
    - manager.py: Implements StepDefinitionManager.decorator_builder, the factory that constructs @given/@when/@then
    decorators, creates Definition objects, attaches them to decorated functions, and injects placeholder fixtures.
    - matcher.py: Implements Matcher, the step-to-definition matching engine with strict/unspecified/liberal strategies,
    MatchNotFoundError, and _parser_specificity scoring.
    - registry.py: Implements Registry (lazy-discovery ordered set backed by cached_property), StepProtocol,
    StepRegistryProtocol, and inject_registry_fixture for pytest fixture integration.

Cohesion:
    All modules in this package operate on the same core concept: binding a user-written Python function (StepFunc) to a
    Gherkin step pattern via a parser, storing that binding as a Definition, organizing definitions into registries, and
    matching pickle steps against definitions at runtime. Every module is a distinct facet of this single concern. There
    are no unrelated utilities or cross-cutting concerns mixed in.

Separation:
    - pytest_bdd.parsers: The parsing layer (order 2) provides StepParser implementations; this layer (order 4) consumes
    them via Definition.parser but does not own how patterns are parsed—it only owns how parsed patterns are bound to
    functions and matched against steps.
    - pytest_bdd.collector / pytest_bdd.plugin.scenario_test_collector: The collection layer (order 5) discovers
    features and generates tests; it reads step registries but does not own their structure or lifecycle.
    - pytest_bdd.plugin.pickle_runner: The runtime layer (order 6) executes matched steps; it uses Matcher and
    Definition.get_parameters but does not own the matching algorithm or the Definition data model.

Main consumers:
    - pytest_bdd.plugin.scenario_test_collector: Builds collection-time Registry via Registry(namespace=module,
    definitions=OrderedSet(...)) and passes registries to Matcher for step binding during test generation.
    - pytest_bdd.plugin.pickle_runner: Uses Matcher to find the matching Definition for each PickleStep at execution
    time, then calls Definition.get_parameters and invokes the step function.
    - End-user test files: Import @given, @when, @then, @step directly from pytest_bdd.steps (or via the top-level
    pytest_bdd re-export) to decorate step functions.
    - pytest_bdd.hook: Consumes Definition and StepFunc types when managing before/after/around lifecycle hooks.

State and side effects:
    None, keeps no persistent state. The __init__.py is purely a re-export module. State lives in the sub-modules:
    Registry.registry is a cached_property that lazily discovers definitions from a namespace;
    StepDefinitionManager.decorator_builder mutates the caller's module namespace to inject placeholder fixtures.

Invariants:
    - Every Definition must have a non-None parser attribute that satisfies StepParserProtocol.
    - The Registry.registry cached_property must be recomputed if the underlying namespace's step definitions change; it
    is not invalidated automatically.
    - Step decorator functions (given, when, then, step) must all delegate to StepDefinitionManager.decorator_builder
    with only the step_type differing.

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

from __future__ import annotations

__all__: list[str] = [
    "ConverterT",
    "Definition",
    "Matcher",
    "ParamsFixturesMapping",
    "Registry",
    "Step",
    "StepDecorator",
    "StepDefinitionManager",
    "StepFunc",
    "StepProtocol",
    "StepRegistryProtocol",
    "_resolve_callable_source_location",
    "given",
    "not_implemented",
    "step",
    "then",
    "tolerant",
    "when",
]

from cucumber_messages import (
    PickleStep as Step,  # upstream type stubs missing this attribute
)

from pytest_bdd.steps.decorators import given, not_implemented, step, then, tolerant, when
from pytest_bdd.steps.definition import (
    ConverterT,
    Definition,
    ParamsFixturesMapping,
    StepDecorator,
    StepFunc,
    _resolve_callable_source_location,
)
from pytest_bdd.steps.manager import StepDefinitionManager
from pytest_bdd.steps.matcher import Matcher
from pytest_bdd.steps.registry import Registry, StepProtocol, StepRegistryProtocol
