"""
Provides miscellaneous general-purpose utility functions and constants that do not warrant
their own dedicated module.

Responsibility:
    Provides miscellaneous general-purpose utility functions and constants that do not warrant
    their own dedicated module, offering helper operations consumed by multiple layers across the
    pytest-bdd codebase where a single-function module would be excessive.

Reason for existence:
    Small utilities that are too focused for a separate module but too broadly useful to inline at
    each call site live here as a pragmatic catch-all. This module serves as the last-resort home
    for genuinely shared helper functions that resist further architectural decomposition.

Delegates:
    - Python standard library: delegates core operations to stdlib modules

Cohesion:
    All functions are standalone pure utilities that each serve a single independent helper
    purpose.

Separation:
    - `pytest_bdd.util.matrix`: matrix provides parameterized test utilities while other provides general helpers.

Main consumers:
    - `pytest_bdd.*`: widely imported across multiple layers for general-purpose helpers

State and side effects:
    None, all functions are pure and stateless with no side effects.

Invariants:
    - Each function is independently usable without module-level initialization or ordering dependencies.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=3
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

import re
from typing import ClassVar, Protocol, runtime_checkable

from gherkin.stream.id_generator import IdGenerator as BaseIdGenerator

from pytest_bdd.const import ALPHA_REGEX, PYTHON_REPLACE_REGEX
from pytest_bdd.model.stash_access import StashBound


def format_as_python_identifier(s: object) -> str:
    """
    Perform the `format_as_python_identifier` operation within its module boundary, implementing a.
    focused helper functi.

    Responsibility:
        Performs the `format_as_python_identifier` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `format_as_python_identifier` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the format_as_python_identifier operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke format_as_python_identifier for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The format_as_python_identifier function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    s1: str = str(s)
    s2 = re.sub(r"[^.a-zA-Z0-9]", "_", s1)
    s3 = re.sub(r"_+", "_", s2)
    s4 = s3.strip("_")
    return f"_{s4}" if re.match(r"\d.*", s4) else s4


def format_as_simplified_python_identifier(string: str) -> str:
    """
    Perform the `format_as_simplified_python_identifier` operation within its module boundary,.
    implementing a focused he.

    Responsibility:
        Performs the `format_as_simplified_python_identifier` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `format_as_simplified_python_identifier` exists as a standalone function because it
        encapsulates an operation that does not require shared instance state and benefits from being
        independently callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the format_as_simplified_python_identifier operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke format_as_simplified_python_identifier for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The format_as_simplified_python_identifier function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    string = re.sub(PYTHON_REPLACE_REGEX, "", string.replace(" ", "_"))
    return re.sub(ALPHA_REGEX, "", string).lower()


@runtime_checkable
class StringRepresentable(Protocol):
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
        - Protocol: StringRepresentable specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        Declares exactly the minimal attribute set required for its structural contract.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate StringRepresentable for error handling and type checking

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

    def __str__(self) -> str:
        """
        Format the StringRepresentable instance into a human-readable string using the class-level.
        message template and cons.

        Responsibility:
            Formats the StringRepresentable instance into a human-readable string using the class-level
            message template and constructor positional arguments, enabling clear error display in pytest
            output and log files.

        Reason for existence:
            The __str__ method centralizes string formatting so the message template and argument mapping
            are defined in one place, ensuring consistent error display across all contexts where the
            exception is printed.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __str__ operation on StringRepresentable instances.

        Separation:
            - Other StringRepresentable methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch StringRepresentable implicitly invoke this method

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
        ...  # pragma: no cover


def normalize_to_string(value: StringRepresentable | str | bytes) -> str:
    """
    Perform the `normalize_to_string` operation within its module boundary, implementing a focused.
    helper function that .

    Responsibility:
        Performs the `normalize_to_string` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `normalize_to_string` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the normalize_to_string operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke normalize_to_string for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The normalize_to_string function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return str(value, **({"encoding": "utf-8"} if isinstance(value, bytes) else {}))


class IdGenerator(BaseIdGenerator, StashBound):
    """
    Encapsulates the IdGenerator concern within pytest-bdd, providing a focused set of
    collaborating operations that toge.

    Responsibility:
        Encapsulates the IdGenerator concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        IdGenerator is a distinct class because its methods share internal state and collaborate on a
        cohesive task that would be awkward to express as standalone functions with shared mutable
        parameters.

    Delegates:
        - BaseIdGenerator, StashBound: IdGenerator specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single IdGenerator domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate IdGenerator for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of IdGenerator maintain internal consistency across all method calls.

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

    STASH_KEY: ClassVar[str] = "_pytest_bdd_id_generator"

    def __init__(self) -> None:
        """
        Initializ a new IdGenerator instance with domain-specific context parameters, formatting a.
        human-readable diagnosti.

        Responsibility:
            Initializes a new IdGenerator instance with domain-specific context parameters, formatting a
            human-readable diagnostic message that includes relevant identifiers for debugging test
            failures in pytest output and log files.

        Reason for existence:
            The __init__ of IdGenerator is the constructor boundary where raw failure context is
            transformed into a formatted exception message. It is the single place where the diagnostic
            message format for this error type is defined.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __init__ operation on IdGenerator instances.

        Separation:
            - Other IdGenerator methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch IdGenerator implicitly invoke this method

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
        self._id_counter = 0

    def __next__(self) -> str:
        """
        Perform the __next__ operation within the IdGenerator boundary, handling its specific sub-task.
        as part of the broade.

        Responsibility:
            Performs the __next__ operation within the IdGenerator boundary, handling its specific sub-task
            as part of the broader IdGenerator responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            __next__ is a distinct method because it encapsulates a specific behavioral concern that must
            be independently callable and potentially overridable by subclasses of IdGenerator without
            affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __next__ operation on IdGenerator instances.

        Separation:
            - Other IdGenerator methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch IdGenerator implicitly invoke this method

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
        try:
            return str(self._id_counter)
        finally:
            self._id_counter += 1

    get_next_id = __next__

    @classmethod
    def stash_missing_message(cls) -> str:
        """
        Perform the stash_missing_message operation within the IdGenerator boundary, handling its.
        specific sub-task as part .

        Responsibility:
            Performs the stash_missing_message operation within the IdGenerator boundary, handling its
            specific sub-task as part of the broader IdGenerator responsibility in the pytest-bdd runtime
            lifecycle.

        Reason for existence:
            stash_missing_message is a distinct method because it encapsulates a specific behavioral
            concern that must be independently callable and potentially overridable by subclasses of
            IdGenerator without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the stash_missing_message operation on IdGenerator instances.

        Separation:
            - Other IdGenerator methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch IdGenerator implicitly invoke this method

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
        return (
            "`pytest_bdd_id_generator` is unavailable in config.stash. "
            "Execution and collection plugins must initialize stash-backed runtime services before use."
        )

    @classmethod
    def stash_duplicate_message(cls) -> str:
        """
        Perform the stash_duplicate_message operation within the IdGenerator boundary, handling its.
        specific sub-task as par.

        Responsibility:
            Performs the stash_duplicate_message operation within the IdGenerator boundary, handling its
            specific sub-task as part of the broader IdGenerator responsibility in the pytest-bdd runtime
            lifecycle.

        Reason for existence:
            stash_duplicate_message is a distinct method because it encapsulates a specific behavioral
            concern that must be independently callable and potentially overridable by subclasses of
            IdGenerator without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the stash_duplicate_message operation on IdGenerator instances.

        Separation:
            - Other IdGenerator methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch IdGenerator implicitly invoke this method

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
        return (
            "`pytest_bdd_id_generator` is already initialized in config.stash. "
            "Framework bootstrap must initialize it exactly once."
        )
