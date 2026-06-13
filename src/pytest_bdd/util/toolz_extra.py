"""
Provides focused utility functions for the `toolz_extra` concern within pytest-bdd utility
layer, offering helper ope.

Responsibility:
    Provides focused utility functions for the `toolz_extra` concern within pytest-bdd utility
    layer, offering helper operations consumed by higher layers (collection, runtime, reporting)
    without pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `toolz_extra` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `toolz_extra`-related helper operations within
    the utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `toolz_extra` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `toolz_extra` utilities for reporting, collection, and runtime operations

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

from collections import defaultdict
from collections.abc import Callable, Collection, Mapping
from contextlib import nullcontext, suppress
from enum import Enum
from functools import reduce
from itertools import chain, tee
from operator import attrgetter, getitem, itemgetter
from typing import TYPE_CHECKING, Any, Literal, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Iterable

_MISSING = object()


class DefaultMapping(defaultdict[object, object]):
    """
    Encapsulates the DefaultMapping concern within pytest-bdd, providing a focused set of
    collaborating operations that t.

    Responsibility:
        Encapsulates the DefaultMapping concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        DefaultMapping is a distinct class because its methods share internal state and collaborate on
        a cohesive task that would be awkward to express as standalone functions with shared mutable
        parameters.

    Delegates:
        - defaultdict[object, object]: DefaultMapping specializes behavior from its parent(s) without duplicating their
        contracts

    Cohesion:
        All methods and attributes serve the single DefaultMapping domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate DefaultMapping for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of DefaultMapping maintain internal consistency across all method calls.

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

    Skip = object()

    def __init__(
        self,
        *args: object,
        default_factory: Callable[[], object] | None = None,
        warm_up_keys: Collection[object] = (),
        **kwargs: object,
    ) -> None:
        """
        Initializ a new DefaultMapping instance with domain-specific context parameters, formatting a.
        human-readable diagno.

        Responsibility:
            Initializes a new DefaultMapping instance with domain-specific context parameters, formatting a
            human-readable diagnostic message that includes relevant identifiers for debugging test
            failures in pytest output and log files.

        Reason for existence:
            The __init__ of DefaultMapping is the constructor boundary where raw failure context is
            transformed into a formatted exception message. It is the single place where the diagnostic
            message format for this error type is defined.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __init__ operation on DefaultMapping instances.

        Separation:
            - Other DefaultMapping methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch DefaultMapping implicitly invoke this method

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
        super().__init__(default_factory, *args, **kwargs)
        self.warm_up(*warm_up_keys)

    def __missing__(self, key: object) -> object:
        """
        Perform the __missing__ operation within the DefaultMapping boundary, handling its specific.
        sub-task as part of the .

        Responsibility:
            Performs the __missing__ operation within the DefaultMapping boundary, handling its specific
            sub-task as part of the broader DefaultMapping responsibility in the pytest-bdd runtime
            lifecycle.

        Reason for existence:
            __missing__ is a distinct method because it encapsulates a specific behavioral concern that
            must be independently callable and potentially overridable by subclasses of DefaultMapping
            without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __missing__ operation on DefaultMapping instances.

        Separation:
            - Other DefaultMapping methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch DefaultMapping implicitly invoke this method

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
        if ... in self.keys():
            intercessor = self[...]
            if intercessor is self.Skip:
                raise KeyError(key)
            if callable(intercessor):
                value = intercessor(key)
            elif intercessor is ...:
                value = key
            else:
                value = intercessor
            self[key] = value
            return value
        return super().__missing__(key)

    def warm_up(self, *items: object) -> None:
        """
        Perform the warm_up operation within the DefaultMapping boundary, handling its specific sub-.
        task as part of the bro.

        Responsibility:
            Performs the warm_up operation within the DefaultMapping boundary, handling its specific sub-
            task as part of the broader DefaultMapping responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            warm_up is a distinct method because it encapsulates a specific behavioral concern that must be
            independently callable and potentially overridable by subclasses of DefaultMapping without
            affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the warm_up operation on DefaultMapping instances.

        Separation:
            - Other DefaultMapping methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch DefaultMapping implicitly invoke this method

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
        for item in items:
            with suppress(KeyError):
                getitem(self, item)

    @classmethod
    def instantiate_from_collection_or_bool(
        cls,
        bool_or_items: object = _MISSING,
        *,
        warm_up_keys: Collection[object] = (),
    ) -> DefaultMapping:
        """
        Perform the instantiate_from_collection_or_bool operation within the DefaultMapping boundary,.
        handling its specific .

        Responsibility:
            Performs the instantiate_from_collection_or_bool operation within the DefaultMapping boundary,
            handling its specific sub-task as part of the broader DefaultMapping responsibility in the
            pytest-bdd runtime lifecycle.

        Reason for existence:
            instantiate_from_collection_or_bool is a distinct method because it encapsulates a specific
            behavioral concern that must be independently callable and potentially overridable by
            subclasses of DefaultMapping without affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the instantiate_from_collection_or_bool operation on DefaultMapping
            instances.

        Separation:
            - Other DefaultMapping methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch DefaultMapping implicitly invoke this method

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
        if bool_or_items is _MISSING:
            bool_or_items = True
        if isinstance(bool_or_items, Collection):
            items: object = bool_or_items
            if not isinstance(bool_or_items, Mapping):
                items = zip(*tee(iter(bool_or_items)), strict=False)
        else:
            items = cast("dict[object, object]", {...: ...} if bool_or_items else {...: DefaultMapping.Skip})
        return cls(items, warm_up_keys=warm_up_keys)


def itemgetter_(*items: object) -> Callable[[object], object]:
    """
    Perform the `itemgetter_` operation within its module boundary, implementing a focused helper.
    function that is consu.

    Responsibility:
        Performs the `itemgetter_` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `itemgetter_` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the itemgetter_ operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke itemgetter_ for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The itemgetter_ function returns consistent results for equivalent inputs.

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
    getter = cast("Callable[[object], object]", itemgetter(*items))

    def func(obj: object) -> object:
        """
        Perform the `func` operation within its module boundary, implementing a focused helper.
        function that is consumed by .

        Responsibility:
        Performs the `func` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

        Reason for existence:
        `func` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

        Delegates:
        - Python standard library: delegates core operations to stdlib

        Cohesion:
        All logic directly supports the func operation.

        Separation:
        - Other functions in this module: each function handles a distinct helper concern.

        Main consumers:
        - `pytest_bdd.*`: callers import and invoke func for its specific utility

        State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

        Invariants:
        - The func function returns consistent results for equivalent inputs.

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
        if len(items) == 0:
            return []
        result = getter(obj)
        if len(items) == 1:
            return [result]
        return result

    return func


class Empty(Enum):
    """
    Enumerates the possible states for the Empty domain as a StrEnum, providing symbolic constants
    that replace magic str.

    Responsibility:
        Enumerates the possible states for the Empty domain as a StrEnum, providing symbolic constants
        that replace magic strings in error classification and reporting code throughout the pytest-bdd
        runtime.

    Reason for existence:
        Using StrEnum instead of plain strings for Empty ensures compile-time validation of failure
        codes, enables IDE autocompletion for error handlers, and centralizes the catalog of possible
        states so new codes cannot be introduced silently.

    Delegates:
        - Enum: Empty specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All members are string enum values representing distinct states within the Empty domain.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate Empty for error handling and type checking

    State and side effects:
        Stores only immutable string enum values defined at class creation time.

    Invariants:
        - Each member is a non-empty string uniquely identifying a Empty state.

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

    empty = None


def getitemdefault(
    obj: object,
    index: object,
    default: object = Empty.empty,
    default_factory: Callable[[], object] | None = None,
    treat_as_empty: object = Empty.empty,
) -> object:
    """
    Perform the `getitemdefault` operation within its module boundary, implementing a focused.
    helper function that is co.

    Responsibility:
        Performs the `getitemdefault` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `getitemdefault` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the getitemdefault operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke getitemdefault for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The getitemdefault function returns consistent results for equivalent inputs.

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
    if default is not Empty.empty:
        if default_factory is not None:
            msg = "Both 'default' and 'default_factory' were specified"
            raise ValueError(msg)

        def default_factory() -> object:
            """
            Perform the `default_factory` operation within its module boundary, implementing a focused.
            helper function that is c.

            Responsibility:
            Performs the `default_factory` operation within its module boundary, implementing a focused
            helper function that is consumed by higher layers for its specific utility purpose within the
            pytest-bdd architecture.

            Reason for existence:
            `default_factory` exists as a standalone function because it encapsulates an operation that
            does not require shared instance state and benefits from being independently callable and
            testable without class instantiation overhead.

            Delegates:
            - Python standard library: delegates core operations to stdlib

            Cohesion:
            All logic directly supports the default_factory operation.

            Separation:
            - Other functions in this module: each function handles a distinct helper concern.

            Main consumers:
            - `pytest_bdd.*`: callers import and invoke default_factory for its specific utility

            State and side effects:
            None, this function is stateless and produces its output purely from input arguments.

            Invariants:
            - The default_factory function returns consistent results for equivalent inputs.

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
            return default

    getitem_ = cast("Callable[[object, object], object]", getitem)

    try:
        item = getitem_(obj, index)
    except KeyError:
        if default_factory is None:
            raise
        item = default_factory()
    if item is not treat_as_empty:
        return item
    msg = f"{index}"
    raise KeyError(msg)


def deepattrgetter(*attrs: str, **kwargs: object) -> Callable[[object], tuple[object, ...]]:
    """
    Perform the `deepattrgetter` operation within its module boundary, implementing a focused.
    helper function that is co.

    Responsibility:
        Performs the `deepattrgetter` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `deepattrgetter` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the deepattrgetter operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke deepattrgetter for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The deepattrgetter function returns consistent results for equivalent inputs.

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
    empty = object()
    default = kwargs.pop("default", empty)
    skip_missing = bool(kwargs.pop("skip_missing", False))

    if default is not empty and skip_missing:
        msg = 'Both "default" and "skip_missing" are specified'
        raise ValueError(msg)

    default_exception_type = AttributeError if default is not empty else _NoneExceptionError
    skip_missing_context = suppress(AttributeError) if skip_missing else nullcontext()

    def fn(obj: object) -> tuple[object, ...]:
        """
        Perform the `fn` operation within its module boundary, implementing a focused helper function.
        that is consumed by hi.

        Responsibility:
        Performs the `fn` operation within its module boundary, implementing a focused helper function
        that is consumed by higher layers for its specific utility purpose within the pytest-bdd
        architecture.

        Reason for existence:
        `fn` exists as a standalone function because it encapsulates an operation that does not require
        shared instance state and benefits from being independently callable and testable without class
        instantiation overhead.

        Delegates:
        - Python standard library: delegates core operations to stdlib

        Cohesion:
        All logic directly supports the fn operation.

        Separation:
        - Other functions in this module: each function handles a distinct helper concern.

        Main consumers:
        - `pytest_bdd.*`: callers import and invoke fn for its specific utility

        State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

        Invariants:
        - The fn function returns consistent results for equivalent inputs.

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

        def _() -> Iterable[object]:
            """
            Perform the `_` operation within its module boundary, implementing a focused helper function.
            that is consumed by hig.

            Responsibility:
            Performs the `_` operation within its module boundary, implementing a focused helper function
            that is consumed by higher layers for its specific utility purpose within the pytest-bdd
            architecture.

            Reason for existence:
            `_` exists as a standalone function because it encapsulates an operation that does not require
            shared instance state and benefits from being independently callable and testable without class
            instantiation overhead.

            Delegates:
            - Python standard library: delegates core operations to stdlib

            Cohesion:
            All logic directly supports the _ operation.

            Separation:
            - Other functions in this module: each function handles a distinct helper concern.

            Main consumers:
            - `pytest_bdd.*`: callers import and invoke _ for its specific utility

            State and side effects:
            None, this function is stateless and produces its output purely from input arguments.

            Invariants:
            - The _ function returns consistent results for equivalent inputs.

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
            for attr in attrs:
                try:
                    with skip_missing_context:
                        yield attrgetter(attr)(obj)
                except default_exception_type:  # noqa: PERF203  -- suppressed warning
                    yield default

        return tuple(_())

    return fn


def setdefaultattr(
    obj: object,
    key: str,
    value: Literal[Empty.empty] | object = Empty.empty,
    value_factory: Callable[[], object] | None = None,
) -> object:
    """
    Perform the `setdefaultattr` operation within its module boundary, implementing a focused.
    helper function that is co.

    Responsibility:
        Performs the `setdefaultattr` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `setdefaultattr` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the setdefaultattr operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke setdefaultattr for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The setdefaultattr function returns consistent results for equivalent inputs.

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
    if value is not Empty.empty and value_factory is not None:
        msg = "Both 'value' and 'value_factory' were specified"
        raise ValueError(msg)
    with suppress(AttributeError):
        return getattr(obj, key)
    if value_factory is not None:
        value = value_factory()
    setattr(obj, key, value)
    return value


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


def compose(*funcs: ObjectCallable) -> ObjectCallable:
    """
    Perform the `compose` operation within its module boundary, implementing a focused helper.
    function that is consumed .

    Responsibility:
        Performs the `compose` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `compose` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the compose operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke compose for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The compose function returns consistent results for equivalent inputs.

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
    return reduce(lambda f, g: lambda *args, **kwargs: f(g(*args, **kwargs)), funcs)


def flip(func: ObjectCallable | Callable[..., Any]) -> ObjectCallable | Callable[..., Any]:
    """
    Perform the `flip` operation within its module boundary, implementing a focused helper.
    function that is consumed by .

    Responsibility:
        Performs the `flip` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `flip` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the flip operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke flip for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The flip function returns consistent results for equivalent inputs.

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

    def wrapped(*args: object, **kwargs: object) -> object:
        """
        Perform the `wrapped` operation within its module boundary, implementing a focused helper.
        function that is consumed .

        Responsibility:
        Performs the `wrapped` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

        Reason for existence:
        `wrapped` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

        Delegates:
        - Python standard library: delegates core operations to stdlib

        Cohesion:
        All logic directly supports the wrapped operation.

        Separation:
        - Other functions in this module: each function handles a distinct helper concern.

        Main consumers:
        - `pytest_bdd.*`: callers import and invoke wrapped for its specific utility

        State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

        Invariants:
        - The wrapped function returns consistent results for equivalent inputs.

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
        if len(args) > 1:
            first, *other, last = args
            return func(last, *other, first, **kwargs)
        return func(*args, **kwargs)

    return wrapped


class _NoneExceptionError(Exception):
    """
    Signals a _NoneExceptionError condition during pytest-bdd runtime operations, carrying domain-
    specific context that .

    Responsibility:
        Signals a _NoneExceptionError condition during pytest-bdd runtime operations, carrying domain-
        specific context that enables precise error reporting and targeted exception handling by
        callers without intercepting unrelated runtime errors.

    Reason for existence:
        This exception exists as a distinct type rather than using a generic Exception so error
        handlers can catch specifically _NoneExceptionError and constructor logic can format domain-
        specific diagnostic messages with relevant identifiers.

    Delegates:
        - Exception: _NoneExceptionError specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All attributes and methods support the single purpose of communicating _NoneExceptionError
        errors.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate _NoneExceptionError for error handling and type checking

    State and side effects:
        Stores only constructor-provided immutable error context strings.

    Invariants:
        - Instances of _NoneExceptionError always carry the semantic meaning of their exception type.

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


chain_map: ObjectCallable = compose(cast("ObjectCallable", chain.from_iterable), cast("ObjectCallable", map))
is_of_type = flip(isinstance)
