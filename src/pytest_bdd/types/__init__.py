"""
Defines the `types` type definitions for pytest-bdd, providing domain-specific type constructs
consumed by higher arc.

Responsibility:
    Defines the `types` type definitions for pytest-bdd, providing domain-specific type constructs
    consumed by higher architectural layers for type checking, error classification, and structural
    contract enforcement throughout the BDD runtime.

Reason for existence:
    The `types` types are kept in their own module within the types package to maintain clean
    separation between distinct type domains (enums, protocols, exceptions, JSON types, warnings)
    so consumers import only the types they need.

Delegates:
    - Python stdlib `typing`: delegates type system primitives to the standard library

Cohesion:
    All symbols define type-level constructs for the `types` domain.

Separation:
    - Sibling type modules: each sub-module handles a distinct type domain within the foundation layer.

Main consumers:
    - `pytest_bdd.*`: imports `types` types for static type checking and error handling

State and side effects:
    None, this module defines only type aliases and class definitions with no runtime state.

Invariants:
    - All symbols in this module are importable without side effects or initialization ordering.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=2
    #arch-eval:locational_stability=4
"""

from pytest_bdd.types.failure_reasons import (
    CollectorFailure,
    FeatureLocatorFailure,
    GenericFailure,
    MessageValidationFailure,
    ParserFailure,
    ScenarioRunFailure,
    StashFailure,
)
