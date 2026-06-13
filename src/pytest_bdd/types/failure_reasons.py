"""
Defines the complete catalog of StrEnum failure reason codes used throughout the pytest-bdd
runtime to classify error.

Responsibility:
    Defines the complete catalog of StrEnum failure reason codes used throughout the pytest-bdd
    runtime to classify error conditions during stash access, scenario execution, message
    validation, feature location, collection, and parsing.

Reason for existence:
    All error classification knowledge lives in one module so error-handling code across all layers
    matches against symbolic constants rather than fragile magic strings. This module is the single
    source of truth for the entire failure taxonomy of the pytest-bdd BDD runtime.

Delegates:
    - `pytest_bdd.compatibility.enum.StrEnum`: provides the base class with string interop

Cohesion:
    Every class is a StrEnum defining a distinct failure domain; all share the same base class and
    import.

Separation:
    - `pytest_bdd.types.exception`: exception raises errors while failure_reasons provides enum codes for categorization.

Main consumers:
    - `pytest_bdd.model.stash_access`: uses StashFailure enum for stash error classification

State and side effects:
    None, all enum values are immutable strings defined at class creation time.

Invariants:
    - Each StrEnum value is a non-empty string uniquely identifying a single failure condition.

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

from __future__ import annotations

from pytest_bdd.compatibility.enum import StrEnum


class StashFailure(StrEnum):
    """
    Enumerates the possible states for the StashFailure domain as a StrEnum, providing symbolic
    constants that replace ma.

    Responsibility:
        Enumerates the possible states for the StashFailure domain as a StrEnum, providing symbolic
        constants that replace magic strings in error classification and reporting code throughout the
        pytest-bdd runtime.

    Reason for existence:
        Using StrEnum instead of plain strings for StashFailure ensures compile-time validation of
        failure codes, enables IDE autocompletion for error handlers, and centralizes the catalog of
        possible states so new codes cannot be introduced silently.

    Delegates:
        - StrEnum: StashFailure specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All members are string enum values representing distinct states within the StashFailure domain.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate StashFailure for error handling and type checking

    State and side effects:
        Stores only immutable string enum values defined at class creation time.

    Invariants:
        - Each member is a non-empty string uniquely identifying a StashFailure state.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    NOT_FOUND = "not_found"
    TYPE_MISMATCH = "type_mismatch"
    ALREADY_INITIALIZED = "already_initialized"


class ScenarioRunFailure(StrEnum):
    """
    Enumerates the possible states for the ScenarioRunFailure domain as a StrEnum, providing
    symbolic constants that repl.

    Responsibility:
        Enumerates the possible states for the ScenarioRunFailure domain as a StrEnum, providing
        symbolic constants that replace magic strings in error classification and reporting code
        throughout the pytest-bdd runtime.

    Reason for existence:
        Using StrEnum instead of plain strings for ScenarioRunFailure ensures compile-time validation
        of failure codes, enables IDE autocompletion for error handlers, and centralizes the catalog of
        possible states so new codes cannot be introduced silently.

    Delegates:
        - StrEnum: ScenarioRunFailure specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All members are string enum values representing distinct states within the ScenarioRunFailure
        domain.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate ScenarioRunFailure for error handling and type checking

    State and side effects:
        Stores only immutable string enum values defined at class creation time.

    Invariants:
        - Each member is a non-empty string uniquely identifying a ScenarioRunFailure state.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    FEATURE_NOT_BOUND = "feature_not_bound"
    STEP_NOT_FOUND = "step_not_found"
    INVALID_STAGE = "invalid_stage"
    BINDING_FAILED = "binding_failed"


class MessageValidationFailure(StrEnum):
    """
    Enumerates the possible states for the MessageValidationFailure domain as a StrEnum, providing
    symbolic constants tha.

    Responsibility:
        Enumerates the possible states for the MessageValidationFailure domain as a StrEnum, providing
        symbolic constants that replace magic strings in error classification and reporting code
        throughout the pytest-bdd runtime.

    Reason for existence:
        Using StrEnum instead of plain strings for MessageValidationFailure ensures compile-time
        validation of failure codes, enables IDE autocompletion for error handlers, and centralizes the
        catalog of possible states so new codes cannot be introduced silently.

    Delegates:
        - StrEnum: MessageValidationFailure specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All members are string enum values representing distinct states within the
        MessageValidationFailure domain.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate MessageValidationFailure for error handling and type checking

    State and side effects:
        Stores only immutable string enum values defined at class creation time.

    Invariants:
        - Each member is a non-empty string uniquely identifying a MessageValidationFailure state.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    SCHEMA_LOAD_ERROR = "schema_load_error"
    VALIDATION_FAILED = "validation_failed"
    INVALID_ENVELOPE = "invalid_envelope"


class FeatureLocatorFailure(StrEnum):
    """
    Enumerates the possible states for the FeatureLocatorFailure domain as a StrEnum, providing
    symbolic constants that r.

    Responsibility:
        Enumerates the possible states for the FeatureLocatorFailure domain as a StrEnum, providing
        symbolic constants that replace magic strings in error classification and reporting code
        throughout the pytest-bdd runtime.

    Reason for existence:
        Using StrEnum instead of plain strings for FeatureLocatorFailure ensures compile-time
        validation of failure codes, enables IDE autocompletion for error handlers, and centralizes the
        catalog of possible states so new codes cannot be introduced silently.

    Delegates:
        - StrEnum: FeatureLocatorFailure specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All members are string enum values representing distinct states within the
        FeatureLocatorFailure domain.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate FeatureLocatorFailure for error handling and type checking

    State and side effects:
        Stores only immutable string enum values defined at class creation time.

    Invariants:
        - Each member is a non-empty string uniquely identifying a FeatureLocatorFailure state.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    FILE_NOT_FOUND = "file_not_found"
    PARSE_FAILED = "parse_failed"
    RESOLUTION_FAILED = "resolution_failed"


class CollectorFailure(StrEnum):
    """
    Enumerates the possible states for the CollectorFailure domain as a StrEnum, providing symbolic
    constants that replac.

    Responsibility:
        Enumerates the possible states for the CollectorFailure domain as a StrEnum, providing symbolic
        constants that replace magic strings in error classification and reporting code throughout the
        pytest-bdd runtime.

    Reason for existence:
        Using StrEnum instead of plain strings for CollectorFailure ensures compile-time validation of
        failure codes, enables IDE autocompletion for error handlers, and centralizes the catalog of
        possible states so new codes cannot be introduced silently.

    Delegates:
        - StrEnum: CollectorFailure specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All members are string enum values representing distinct states within the CollectorFailure
        domain.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate CollectorFailure for error handling and type checking

    State and side effects:
        Stores only immutable string enum values defined at class creation time.

    Invariants:
        - Each member is a non-empty string uniquely identifying a CollectorFailure state.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    PARSE_FAILED = "parse_failed"
    READ_FAILED = "read_failed"
    BATCH_FAILED = "batch_failed"


class ParserFailure(StrEnum):
    """
    Enumerates the possible states for the ParserFailure domain as a StrEnum, providing symbolic
    constants that replace m.

    Responsibility:
        Enumerates the possible states for the ParserFailure domain as a StrEnum, providing symbolic
        constants that replace magic strings in error classification and reporting code throughout the
        pytest-bdd runtime.

    Reason for existence:
        Using StrEnum instead of plain strings for ParserFailure ensures compile-time validation of
        failure codes, enables IDE autocompletion for error handlers, and centralizes the catalog of
        possible states so new codes cannot be introduced silently.

    Delegates:
        - StrEnum: ParserFailure specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All members are string enum values representing distinct states within the ParserFailure
        domain.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate ParserFailure for error handling and type checking

    State and side effects:
        Stores only immutable string enum values defined at class creation time.

    Invariants:
        - Each member is a non-empty string uniquely identifying a ParserFailure state.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    SYNTAX_ERROR = "syntax_error"
    UNSUPPORTED_MIMETYPE = "unsupported_mimetype"


class GenericFailure(StrEnum):
    """
    Enumerates the possible states for the GenericFailure domain as a StrEnum, providing symbolic
    constants that replace .

    Responsibility:
        Enumerates the possible states for the GenericFailure domain as a StrEnum, providing symbolic
        constants that replace magic strings in error classification and reporting code throughout the
        pytest-bdd runtime.

    Reason for existence:
        Using StrEnum instead of plain strings for GenericFailure ensures compile-time validation of
        failure codes, enables IDE autocompletion for error handlers, and centralizes the catalog of
        possible states so new codes cannot be introduced silently.

    Delegates:
        - StrEnum: GenericFailure specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All members are string enum values representing distinct states within the GenericFailure
        domain.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate GenericFailure for error handling and type checking

    State and side effects:
        Stores only immutable string enum values defined at class creation time.

    Invariants:
        - Each member is a non-empty string uniquely identifying a GenericFailure state.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    UNEXPECTED_ERROR = "unexpected_error"
