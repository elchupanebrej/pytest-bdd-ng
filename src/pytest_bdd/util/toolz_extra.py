"""Provide toolz extra helpers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Collection, Mapping
from contextlib import nullcontext, suppress
from enum import Enum
from functools import reduce
from itertools import chain, tee
from operator import attrgetter, getitem, itemgetter
from typing import TYPE_CHECKING, Literal, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Iterable

_MISSING = object()


class DefaultMapping(defaultdict[object, object]):
    """
    Represent default mapping state.

    Raises:
        KeyError: If the operation cannot be completed.

    """

    Skip = object()

    def __init__(
        self,
        *args: object,
        default_factory: Callable[[], object] | None = None,
        warm_up_keys: Collection[object] = (),
        **kwargs: object,
    ) -> None:
        """Initialize the default mapping."""
        super().__init__(default_factory, *args, **kwargs)
        self.warm_up(*warm_up_keys)

    def __missing__(self, key: object) -> object:
        """
        Return a fallback value for missing keys.

        Args:
            key: Missing key to look up.

        Returns:
            Fallback value for the key.

        Raises:
            KeyError: If missing-key fallback is disabled or unavailable.

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
        """Handle warm up."""
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
        Create a DefaultMapping from a collection or boolean.

        Args:
            bool_or_items: Collection, boolean, or missing sentinel.
            warm_up_keys: Keys to warm up on creation.

        Returns:
            New DefaultMapping instance.

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
    Create an itemgetter that handles missing items.

    Args:
        items: Items to get from object.

    Returns:
        Item getter function.

    """
    getter = cast("Callable[[object], object]", itemgetter(*items))

    def func(obj: object) -> object:
        if len(items) == 0:
            return []
        result = getter(obj)
        if len(items) == 1:
            return [result]
        return result

    return func


class Empty(Enum):
    """Represent empty state."""

    empty = None


def getitemdefault(
    obj: object,
    index: object,
    default: object = Empty.empty,
    default_factory: Callable[[], object] | None = None,
    treat_as_empty: object = Empty.empty,
) -> object:
    """
    Get item from object with default handling.

    Args:
        obj: Object to get item from.
        index: Index/key to retrieve.
        default: Default value if key missing.
        default_factory: Factory for default value.
        treat_as_empty: Value to treat as empty.

    Returns:
        Retrieved item or default.

    Raises:
        KeyError: If the operation cannot be completed.
        ValueError: If the operation cannot be completed.

    """
    if default is not Empty.empty:
        if default_factory is not None:
            msg = "Both 'default' and 'default_factory' were specified"
            raise ValueError(msg)

        def default_factory() -> object:
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
    Get nested attributes from an object.

    Args:
        attrs: Attribute chain to traverse.
        **kwargs: Additional keyword arguments. Accepts "default" (default value if attribute missing)
            and "skip_missing" (whether to skip missing attributes).
        default: Default value if attribute missing.
        skip_missing: Whether to skip missing attributes.

    Returns:
        Function that extracts nested attributes.

    Raises:
        ValueError: If the operation cannot be completed.

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
        def _() -> Iterable[object]:
            for attr in attrs:
                try:
                    with skip_missing_context:
                        yield attrgetter(attr)(obj)
                except default_exception_type:  # noqa: PERF203
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
    Set attribute with default value handling.

    Args:
        obj: Object to modify.
        key: Attribute name to set.
        value: Value to set, or Empty.empty.
        value_factory: Factory for value if not provided.

    Returns:
        The value that was set.

    Raises:
        ValueError: If the operation cannot be completed.

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
    """Represent object callable state."""

    def __call__(self, *args: object, **kwargs: object) -> object:
        """Handle call."""
        ...


def compose(*funcs: ObjectCallable) -> ObjectCallable:
    """
    Compose multiple functions into one.

    Args:
        funcs: Functions to compose (applied left to right).

    Returns:
        Composed function.

    """
    return cast("ObjectCallable", reduce(lambda f, g: lambda *args, **kwargs: f(g(*args, **kwargs)), funcs))


def flip(func: ObjectCallable | Callable) -> ObjectCallable | Callable:
    """
    Flip argument order of a binary function.

    Args:
        func: Function to flip.

    Returns:
        Function with flipped arguments.

    """

    def wrapped(*args: object, **kwargs: object) -> object:
        if len(args) > 1:
            first, *other, last = args
            return func(last, *other, first, **kwargs)
        return func(*args, **kwargs)

    return wrapped


class _NoneExceptionError(Exception): ...


chain_map: ObjectCallable = compose(cast("ObjectCallable", chain.from_iterable), cast("ObjectCallable", map))
is_of_type = flip(isinstance)
