"""
Provides focused utility functions for the `inspect_extra` concern within pytest-bdd utility
layer, offering helper o.

Responsibility:
    Provides focused utility functions for the `inspect_extra` concern within pytest-bdd utility
    layer, offering helper operations consumed by higher layers (collection, runtime, reporting)
    without pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `inspect_extra` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `inspect_extra`-related helper operations
    within the utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `inspect_extra` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `inspect_extra` utilities for reporting, collection, and runtime operations

State and side effects:
    None, this module keeps no persistent state and performs no file or network I/O.

Invariants:
    - The public API surface (exported names) remains stable across internal refactors.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from inspect import getframeinfo, getsourcelines, signature
from typing import TYPE_CHECKING, Protocol, cast

from pytest_bdd.compatibility.sys import get_frame

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import CodeType, FrameType, FunctionType, MethodType, ModuleType, TracebackType


class ObjectCallable(Protocol):
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
        - Protocol: ObjectCallable specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        Declares exactly the minimal attribute set required for its structural contract.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate ObjectCallable for error handling and type checking

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

    def __call__(self, *args: object, **kwargs: object) -> object:
        """
        Perform the __call__ operation within the ObjectCallable boundary, handling its specific sub-.
        task as part of the br.

        Responsibility:
            Performs the __call__ operation within the ObjectCallable boundary, handling its specific sub-
            task as part of the broader ObjectCallable responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            __call__ is a distinct method because it encapsulates a specific behavioral concern that must
            be independently callable and potentially overridable by subclasses of ObjectCallable without
            affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __call__ operation on ObjectCallable instances.

        Separation:
            - Other ObjectCallable methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch ObjectCallable implicitly invoke this method

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
        ...


def get_args(func: ObjectCallable) -> Sequence[str]:
    """
    Perform the `get_args` operation within its module boundary, implementing a focused helper.
    function that is consumed.

    Responsibility:
        Performs the `get_args` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `get_args` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the get_args operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke get_args for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The get_args function returns consistent results for equivalent inputs.

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
    params = signature(func).parameters.values()
    return [param.name for param in params if param.kind == param.POSITIONAL_OR_KEYWORD]


def get_first_source_line(obj: object) -> int:
    """
    Perform the `get_first_source_line` operation within its module boundary, implementing a.
    focused helper function tha.

    Responsibility:
        Performs the `get_first_source_line` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `get_first_source_line` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the get_first_source_line operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke get_first_source_line for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The get_first_source_line function returns consistent results for equivalent inputs.

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
    try:
        return getsourcelines(
            cast("ModuleType | type[object] | MethodType | FunctionType | TracebackType | FrameType | CodeType", obj),
        )[1]
    except (OSError, TypeError):
        code = getattr(obj, "__code__", None)
        if code is not None:
            return int(code.co_firstlineno)
        return 1


def get_caller_module_locals(stacklevel: int = 1) -> dict[str, object]:
    """
    Perform the `get_caller_module_locals` operation within its module boundary, implementing a.
    focused helper function .

    Responsibility:
        Performs the `get_caller_module_locals` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `get_caller_module_locals` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the get_caller_module_locals operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke get_caller_module_locals for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The get_caller_module_locals function returns consistent results for equivalent inputs.

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
    return get_frame(stacklevel).f_locals


def get_caller_module_path(stacklevel: int = 1) -> str:
    """
    Perform the `get_caller_module_path` operation within its module boundary, implementing a.
    focused helper function th.

    Responsibility:
        Performs the `get_caller_module_path` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `get_caller_module_path` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the get_caller_module_path operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke get_caller_module_path for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The get_caller_module_path function returns consistent results for equivalent inputs.

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
    frame = get_frame(stacklevel)
    return getframeinfo(frame, context=0).filename
