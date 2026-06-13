"""
Defines pytest-bdd-specific warning classes that extend pytest's PytestWarning base, allowing
the library to emit cat.

Responsibility:
    Defines pytest-bdd-specific warning classes that extend pytest's PytestWarning base, allowing
    the library to emit categorized warnings through pytest's standard warning reporting
    infrastructure without colliding with user warnings.

Reason for existence:
    Extending PytestWarning instead of UserWarning ensures pytest-bdd warnings appear under
    pytest's warning filter rules and can be managed via pytest's -W flag and filterwarnings ini
    options alongside other pytest diagnostics.

Delegates:
    - `_pytest.warning_types.PytestWarning`: provides the pytest-compatible warning base class

Cohesion:
    Single warning class extending PytestWarning focused on one diagnostic concern.

Separation:
    - `pytest_bdd.types.exception`: exception raises hard errors while warning emits non-fatal diagnostics.

Main consumers:
    - `pytest_bdd.steps`: emits step definition warnings during step registration and matching

State and side effects:
    None, warning classes are stateless type definitions with no runtime state.

Invariants:
    - Warnings subclass PytestWarning so they are filterable through pytest standard warning mechanisms.

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

from _pytest.warning_types import PytestWarning


class PytestBDDStepDefinitionWarning(PytestWarning):
    """
    Signals a PytestBDDStepDefinitionWarning condition during pytest-bdd runtime operations,
    carrying domain-specific con.

    Responsibility:
        Signals a PytestBDDStepDefinitionWarning condition during pytest-bdd runtime operations,
        carrying domain-specific context that enables precise error reporting and targeted exception
        handling by callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically PytestBDDStepDefinitionWarning and constructor logic can format
        domain-specific diagnostic messages with relevant identifiers.

    Delegates:
        - PytestWarning: PytestBDDStepDefinitionWarning specializes behavior from its parent(s) without duplicating
        their contracts

    Args:
        *args: Positional arguments forwarded to PytestWarning (typically a message string).

    Cohesion:
        All attributes and methods support the single purpose of communicating
        PytestBDDStepDefinitionWarning errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate PytestBDDStepDefinitionWarning for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of PytestBDDStepDefinitionWarning always carry the semantic meaning of their exception type.

    Returns:
        A warning instance that can be raised or passed to warnings.warn().

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

    __module__ = "pytest_bdd"
