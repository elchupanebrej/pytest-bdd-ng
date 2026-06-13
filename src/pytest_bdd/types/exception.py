"""
Defines the complete exception class hierarchy for pytest-bdd, including stash access errors,
scenario validation err.

Responsibility:
    Defines the complete exception class hierarchy for pytest-bdd, including stash access errors,
    scenario validation errors, step definition lookup errors, feature parse errors, and message
    schema validation errors, each carrying domain-specific constructor metadata for precise error
    diagnostics.

Reason for existence:
    Exception types encode domain-specific failure context (stash keys, feature URIs, step text,
    scenario names) that generic Python exceptions cannot carry. Centralizing them in one module
    ensures consistent error message formatting and exception hierarchy design across all runtime
    layers.

Delegates:
    - Python builtins: delegates to Exception, LookupError, TypeError, ValueError base classes

Cohesion:
    All classes inherit from Exception and share the same domain-specific error reporting pattern.

Separation:
    - `pytest_bdd.types.failure_reasons`: provides StrEnum codes for categorizing these exception types.

Main consumers:
    - `pytest_bdd.model.stash_access`: raises PytestBDDStashError subclasses for stash access failures

State and side effects:
    None, exception classes hold only constructor-provided immutable error context strings.

Invariants:
    - Each exception __init__ formats a message that includes relevant diagnostic identifiers.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from os import PathLike


class _FeatureLike(Protocol):
    """
    Defines a structural typing contract requiring conforming objects to expose specific
    attributes, enabling duck-typing.

    Responsibility:
        Defines a structural typing contract requiring conforming objects to expose specific
        attributes, enabling duck-typing across pytest-bdd runtime objects without mandating concrete
        class inheritance for pytest plugin interoperability.

    Reason for existence:
        This Protocol exists as a named type so runtime code can use isinstance() checks and static
        type annotations against a documented contract rather than relying on ad-hoc hasattr() calls
        spread across the codebase.

    Delegates:
        - Protocol: _FeatureLike specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        Declares exactly the minimal attribute set required for its structural contract.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate _FeatureLike for error handling and type checking

    State and side effects:
        Pure type definition with zero runtime behavior or state.

    Invariants:
        - The Protocol declares only the attributes essential to its contract.

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

    uri: str


class _ScenarioLike(Protocol):
    """
    Defines a structural typing contract requiring conforming objects to expose specific
    attributes, enabling duck-typing.

    Responsibility:
        Defines a structural typing contract requiring conforming objects to expose specific
        attributes, enabling duck-typing across pytest-bdd runtime objects without mandating concrete
        class inheritance for pytest plugin interoperability.

    Reason for existence:
        This Protocol exists as a named type so runtime code can use isinstance() checks and static
        type annotations against a documented contract rather than relying on ad-hoc hasattr() calls
        spread across the codebase.

    Delegates:
        - Protocol: _ScenarioLike specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        Declares exactly the minimal attribute set required for its structural contract.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate _ScenarioLike for error handling and type checking

    State and side effects:
        Pure type definition with zero runtime behavior or state.

    Invariants:
        - The Protocol declares only the attributes essential to its contract.

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

    name: str


class _StepLike(Protocol):
    """
    Defines a structural typing contract requiring conforming objects to expose specific
    attributes, enabling duck-typing.

    Responsibility:
        Defines a structural typing contract requiring conforming objects to expose specific
        attributes, enabling duck-typing across pytest-bdd runtime objects without mandating concrete
        class inheritance for pytest plugin interoperability.

    Reason for existence:
        This Protocol exists as a named type so runtime code can use isinstance() checks and static
        type annotations against a documented contract rather than relying on ad-hoc hasattr() calls
        spread across the codebase.

    Delegates:
        - Protocol: _StepLike specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        Declares exactly the minimal attribute set required for its structural contract.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate _StepLike for error handling and type checking

    State and side effects:
        Pure type definition with zero runtime behavior or state.

    Invariants:
        - The Protocol declares only the attributes essential to its contract.

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

    text: str


class PytestBDDStashError(Exception):
    """
    Signals a PytestBDDStashError condition during pytest-bdd runtime operations, carrying domain-
    specific context that .

    Responsibility:
        Signals a PytestBDDStashError condition during pytest-bdd runtime operations, carrying domain-
        specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically PytestBDDStashError and constructor logic can format domain-
        specific diagnostic messages with relevant identifiers.

    Delegates:
        - Exception: PytestBDDStashError specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating PytestBDDStashError
        errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate PytestBDDStashError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of PytestBDDStashError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """


class PytestBDDStashLookupError(PytestBDDStashError, LookupError):
    """
    Signals a PytestBDDStashLookupError condition during pytest-bdd runtime operations, carrying
    domain-specific context .

    Responsibility:
        Signals a PytestBDDStashLookupError condition during pytest-bdd runtime operations, carrying
        domain-specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically PytestBDDStashLookupError and constructor logic can format
        domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - PytestBDDStashError, LookupError: PytestBDDStashLookupError specializes behavior from its parent(s) without
        duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating
        PytestBDDStashLookupError errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate PytestBDDStashLookupError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of PytestBDDStashLookupError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """


class PytestBDDStashAlreadyInitializedError(PytestBDDStashError):
    """
    Signals a PytestBDDStashAlreadyInitializedError condition during pytest-bdd runtime operations,
    carrying domain-speci.

    Responsibility:
        Signals a PytestBDDStashAlreadyInitializedError condition during pytest-bdd runtime operations,
        carrying domain-specific context that enables precise error reporting and targeted exception
        handling by callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically PytestBDDStashAlreadyInitializedError and constructor logic can
        format domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - PytestBDDStashError: PytestBDDStashAlreadyInitializedError specializes behavior from its parent(s) without
        duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating
        PytestBDDStashAlreadyInitializedError errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate PytestBDDStashAlreadyInitializedError for error handling and type
        checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of PytestBDDStashAlreadyInitializedError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """


class PytestBDDStashTypeMismatchError(PytestBDDStashError, TypeError):
    """
    Signals a PytestBDDStashTypeMismatchError condition during pytest-bdd runtime operations,
    carrying domain-specific co.

    Responsibility:
        Signals a PytestBDDStashTypeMismatchError condition during pytest-bdd runtime operations,
        carrying domain-specific context that enables precise error reporting and targeted exception
        handling by callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically PytestBDDStashTypeMismatchError and constructor logic can
        format domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - PytestBDDStashError, TypeError: PytestBDDStashTypeMismatchError specializes behavior from its parent(s)
        without duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating
        PytestBDDStashTypeMismatchError errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate PytestBDDStashTypeMismatchError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of PytestBDDStashTypeMismatchError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    def __init__(self, *, stash_key: str, actual_type: str, expected_type: str) -> None:
        """
        Initializ a new PytestBDDStashTypeMismatchError instance with domain-specific context.
        parameters, formatting a huma.

        Responsibility:
            Initializes a new PytestBDDStashTypeMismatchError instance with domain-specific context
            parameters, formatting a human-readable diagnostic message that includes relevant identifiers
            for debugging test failures in pytest output and log files.

        Reason for existence:
            The __init__ of PytestBDDStashTypeMismatchError is the constructor boundary where raw failure
            context is transformed into a formatted exception message. It is the single place where the
            diagnostic message format for this error type is defined.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __init__ operation on PytestBDDStashTypeMismatchError
            instances.

        Separation:
            - Other PytestBDDStashTypeMismatchError methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch PytestBDDStashTypeMismatchError implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        super().__init__(f"config.stash['{stash_key}'] contains {actual_type}, expected {expected_type}.")


class MessageSchemaValidationError(ValueError):
    """
    Signals a MessageSchemaValidationError condition during pytest-bdd runtime operations, carrying
    domain-specific conte.

    Responsibility:
        Signals a MessageSchemaValidationError condition during pytest-bdd runtime operations, carrying
        domain-specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically MessageSchemaValidationError and constructor logic can format
        domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - ValueError: MessageSchemaValidationError specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating
        MessageSchemaValidationError errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate MessageSchemaValidationError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of MessageSchemaValidationError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    def __init__(self, details: str) -> None:
        """
        Initializ a new MessageSchemaValidationError instance with domain-specific context.
        parameters, formatting a human-r.

        Responsibility:
            Initializes a new MessageSchemaValidationError instance with domain-specific context
            parameters, formatting a human-readable diagnostic message that includes relevant identifiers
            for debugging test failures in pytest output and log files.

        Reason for existence:
            The __init__ of MessageSchemaValidationError is the constructor boundary where raw failure
            context is transformed into a formatted exception message. It is the single place where the
            diagnostic message format for this error type is defined.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __init__ operation on MessageSchemaValidationError instances.

        Separation:
            - Other MessageSchemaValidationError methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch MessageSchemaValidationError implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        super().__init__(f"Schema-compatible message emission failed: {details}")


class ScenarioIsDecoratorOnlyError(Exception):
    """
    Signals a ScenarioIsDecoratorOnlyError condition during pytest-bdd runtime operations, carrying
    domain-specific conte.

    Responsibility:
        Signals a ScenarioIsDecoratorOnlyError condition during pytest-bdd runtime operations, carrying
        domain-specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically ScenarioIsDecoratorOnlyError and constructor logic can format
        domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - Exception: ScenarioIsDecoratorOnlyError specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating
        ScenarioIsDecoratorOnlyError errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate ScenarioIsDecoratorOnlyError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of ScenarioIsDecoratorOnlyError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """


class ScenarioValidationError(Exception):
    """
    Signals a ScenarioValidationError condition during pytest-bdd runtime operations, carrying
    domain-specific context th.

    Responsibility:
        Signals a ScenarioValidationError condition during pytest-bdd runtime operations, carrying
        domain-specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically ScenarioValidationError and constructor logic can format
        domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - Exception: ScenarioValidationError specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating ScenarioValidationError
        errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate ScenarioValidationError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of ScenarioValidationError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """


class ScenarioNotFoundError(ScenarioValidationError):
    """
    Signals a ScenarioNotFoundError condition during pytest-bdd runtime operations, carrying
    domain-specific context that.

    Responsibility:
        Signals a ScenarioNotFoundError condition during pytest-bdd runtime operations, carrying
        domain-specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically ScenarioNotFoundError and constructor logic can format domain-
        specific diagnostic messages with relevant identifiers.

    Delegates:
        - ScenarioValidationError: ScenarioNotFoundError specializes behavior from its parent(s) without duplicating
        their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating ScenarioNotFoundError
        errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate ScenarioNotFoundError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of ScenarioNotFoundError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """


class ExamplesNotValidError(ScenarioValidationError):
    """
    Signals a ExamplesNotValidError condition during pytest-bdd runtime operations, carrying
    domain-specific context that.

    Responsibility:
        Signals a ExamplesNotValidError condition during pytest-bdd runtime operations, carrying
        domain-specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically ExamplesNotValidError and constructor logic can format domain-
        specific diagnostic messages with relevant identifiers.

    Delegates:
        - ScenarioValidationError: ExamplesNotValidError specializes behavior from its parent(s) without duplicating
        their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating ExamplesNotValidError
        errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate ExamplesNotValidError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of ExamplesNotValidError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """


class ScenarioExamplesNotValidError(ScenarioValidationError):
    """
    Signals a ScenarioExamplesNotValidError condition during pytest-bdd runtime operations,
    carrying domain-specific cont.

    Responsibility:
        Signals a ScenarioExamplesNotValidError condition during pytest-bdd runtime operations,
        carrying domain-specific context that enables precise error reporting and targeted exception
        handling by callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically ScenarioExamplesNotValidError and constructor logic can format
        domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - ScenarioValidationError: ScenarioExamplesNotValidError specializes behavior from its parent(s) without
        duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating
        ScenarioExamplesNotValidError errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate ScenarioExamplesNotValidError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of ScenarioExamplesNotValidError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """


class FeatureExamplesNotValidError(ScenarioValidationError):
    """
    Signals a FeatureExamplesNotValidError condition during pytest-bdd runtime operations, carrying
    domain-specific conte.

    Responsibility:
        Signals a FeatureExamplesNotValidError condition during pytest-bdd runtime operations, carrying
        domain-specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically FeatureExamplesNotValidError and constructor logic can format
        domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - ScenarioValidationError: FeatureExamplesNotValidError specializes behavior from its parent(s) without
        duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating
        FeatureExamplesNotValidError errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate FeatureExamplesNotValidError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of FeatureExamplesNotValidError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """


class StepDefinitionNotFoundError(Exception):
    """
    Signals a StepDefinitionNotFoundError condition during pytest-bdd runtime operations, carrying
    domain-specific contex.

    Responsibility:
        Signals a StepDefinitionNotFoundError condition during pytest-bdd runtime operations, carrying
        domain-specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically StepDefinitionNotFoundError and constructor logic can format
        domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - Exception: StepDefinitionNotFoundError specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating
        StepDefinitionNotFoundError errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate StepDefinitionNotFoundError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of StepDefinitionNotFoundError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    undefined_parameter_type: tuple[str, str] | None

    def __init__(
        self,
        feature: _FeatureLike,
        scenario: _ScenarioLike,
        step: _StepLike,
        *args: object,
    ) -> None:
        """
        Initializ a new StepDefinitionNotFoundError instance with domain-specific context parameters,.
        formatting a human-re.

        Responsibility:
            Initializes a new StepDefinitionNotFoundError instance with domain-specific context parameters,
            formatting a human-readable diagnostic message that includes relevant identifiers for debugging
            test failures in pytest output and log files.

        Reason for existence:
            The __init__ of StepDefinitionNotFoundError is the constructor boundary where raw failure
            context is transformed into a formatted exception message. It is the single place where the
            diagnostic message format for this error type is defined.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __init__ operation on StepDefinitionNotFoundError instances.

        Separation:
            - Other StepDefinitionNotFoundError methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch StepDefinitionNotFoundError implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        self.undefined_parameter_type = None
        keyword = getattr(step, "keyword", getattr(step, "prefix", "<unknown>"))
        if keyword is None:
            keyword = "<unknown>"
        line_number = getattr(step, "line_number", "<unknown>")
        if line_number is None:
            line_number = "<unknown>"
        super().__init__(
            f'Step definition is not found: "{step.text}". '
            f'Step keyword: "{keyword}". '
            f"Line {line_number} "
            f'in scenario "{scenario.name}" '
            f'in the feature "{feature.uri}"',
            *args,
        )


class NoScenariosFoundError(Exception):
    """
    Signals a NoScenariosFoundError condition during pytest-bdd runtime operations, carrying
    domain-specific context that.

    Responsibility:
        Signals a NoScenariosFoundError condition during pytest-bdd runtime operations, carrying
        domain-specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically NoScenariosFoundError and constructor logic can format domain-
        specific diagnostic messages with relevant identifiers.

    Delegates:
        - Exception: NoScenariosFoundError specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating NoScenariosFoundError
        errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate NoScenariosFoundError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of NoScenariosFoundError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """


class FeatureParseError(Exception):
    """
    Signals a FeatureParseError condition during pytest-bdd runtime operations, carrying domain-
    specific context that en.

    Responsibility:
        Signals a FeatureParseError condition during pytest-bdd runtime operations, carrying domain-
        specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically FeatureParseError and constructor logic can format domain-
        specific diagnostic messages with relevant identifiers.

    Delegates:
        - Exception: FeatureParseError specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating FeatureParseError
        errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate FeatureParseError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of FeatureParseError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    def __init__(self, path: str | PathLike[str], *args: object) -> None:
        """
        Initializ a new FeatureParseError instance with domain-specific context parameters,.
        formatting a human-readable dia.

        Responsibility:
            Initializes a new FeatureParseError instance with domain-specific context parameters,
            formatting a human-readable diagnostic message that includes relevant identifiers for debugging
            test failures in pytest output and log files.

        Reason for existence:
            The __init__ of FeatureParseError is the constructor boundary where raw failure context is
            transformed into a formatted exception message. It is the single place where the diagnostic
            message format for this error type is defined.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __init__ operation on FeatureParseError instances.

        Separation:
            - Other FeatureParseError methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FeatureParseError implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        super().__init__(f"Unable to parse {path}", *args)


class FeatureConcreteParseError(FeatureParseError):
    """
    Signals a FeatureConcreteParseError condition during pytest-bdd runtime operations, carrying
    domain-specific context .

    Responsibility:
        Signals a FeatureConcreteParseError condition during pytest-bdd runtime operations, carrying
        domain-specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically FeatureConcreteParseError and constructor logic can format
        domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - FeatureParseError: FeatureConcreteParseError specializes behavior from its parent(s) without duplicating their
        contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating
        FeatureConcreteParseError errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate FeatureConcreteParseError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of FeatureConcreteParseError always carry the semantic meaning of their exception type.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    def __init__(self, message: object, line_no: object, line: object, file: object, *args: object) -> None:
        """
        Initializ a new FeatureConcreteParseError instance with domain-specific context parameters,.
        formatting a human-read.

        Responsibility:
            Initializes a new FeatureConcreteParseError instance with domain-specific context parameters,
            formatting a human-readable diagnostic message that includes relevant identifiers for debugging
            test failures in pytest output and log files.

        Reason for existence:
            The __init__ of FeatureConcreteParseError is the constructor boundary where raw failure context
            is transformed into a formatted exception message. It is the single place where the diagnostic
            message format for this error type is defined.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __init__ operation on FeatureConcreteParseError instances.

        Separation:
            - Other FeatureConcreteParseError methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FeatureConcreteParseError implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        Exception.__init__(self, message, line_no, line, file, *args)

    message = "{0}.\nLine number: {1}.\nLine: {2}.\nFile: {3}"

    def __str__(self) -> str:
        """
        Format the FeatureConcreteParseError instance into a human-readable string using the class-.
        level message template a.

        Responsibility:
            Formats the FeatureConcreteParseError instance into a human-readable string using the class-
            level message template and constructor positional arguments, enabling clear error display in
            pytest output and log files.

        Reason for existence:
            The __str__ method centralizes string formatting so the message template and argument mapping
            are defined in one place, ensuring consistent error display across all contexts where the
            exception is printed.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __str__ operation on FeatureConcreteParseError instances.

        Separation:
            - Other FeatureConcreteParseError methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch FeatureConcreteParseError implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return self.message.format(*self.args[:4])
