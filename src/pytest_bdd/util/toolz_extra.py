from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Collection, Mapping
from contextlib import nullcontext, suppress
from enum import Enum
from functools import reduce
from itertools import chain, tee
from operator import attrgetter, getitem, itemgetter
from typing import Any, Literal, cast


class DefaultMapping(defaultdict):
    Skip = object()

    def __init__(self, *args, default_factory=None, warm_up_keys=(), **kwargs):
        super().__init__(default_factory, *args, **kwargs)
        self.warm_up(*warm_up_keys)

    def __missing__(self, key):
        if ... in self.keys():
            intercessor = self[...]
            if intercessor is self.Skip:
                raise KeyError(key)
            if isinstance(intercessor, Callable):
                value = intercessor(key)
            elif intercessor is ...:
                value = key
            else:
                value = intercessor
            self[key] = value
            return value
        return super().__missing__(key)

    def warm_up(self, *items):
        for item in items:
            with suppress(KeyError):
                getitem(self, item)

    @classmethod
    def instantiate_from_collection_or_bool(
        cls,
        bool_or_items: Collection[str] | dict[str, Any] | Any = True,  # noqa:FBT002
        *,
        warm_up_keys=(),
    ):
        if isinstance(bool_or_items, Collection):
            if not isinstance(bool_or_items, Mapping):
                bool_or_items = zip(*tee(iter(bool_or_items)), strict=False)
        else:
            bool_or_items = cast(dict, {...: ...} if bool_or_items else {...: DefaultMapping.Skip})
        return cls(bool_or_items, warm_up_keys=warm_up_keys)


def itemgetter_(*items):
    def func(obj):
        if len(items) == 0:
            return []
        if len(items) == 1:
            return [obj[items[0]]]
        return itemgetter(*items)(obj)

    return func


class Empty(Enum):
    empty = None


def getitemdefault(
    obj,
    index,
    default=Empty.empty,
    default_factory: Callable | None = None,
    treat_as_empty=Empty.empty,
):
    if default is not Empty.empty:
        if default_factory is not None:
            msg = "Both 'default' and 'default_factory' were specified"
            raise ValueError(msg)

        def default_factory():
            return default

    try:
        item = getitem(obj, index)
    except KeyError:
        if default_factory is None:
            raise
        item = default_factory()
    if item is not treat_as_empty:
        return item
    msg = f"{index}"
    raise KeyError(msg)


def deepattrgetter(*attrs, **kwargs):
    empty = object()
    default = kwargs.pop("default", empty)
    skip_missing = kwargs.pop("skip_missing", False)

    if default is not empty and skip_missing:
        msg = 'Both "default" and "skip_missing" are specified'
        raise ValueError(msg)

    default_exception_type = AttributeError if default is not empty else _NoneExceptionError
    skip_missing_context = suppress(AttributeError) if skip_missing else nullcontext()

    def fn(obj):
        def _():
            for attr in attrs:
                try:
                    with skip_missing_context:
                        yield attrgetter(attr)(obj)
                except default_exception_type:  # noqa:PERF203
                    yield default

        return tuple(_())

    return fn


def setdefaultattr(
    obj,
    key,
    value: Literal[Empty.empty] | Any = Empty.empty,
    value_factory: Callable | None = None,
):
    if value is not Empty.empty and value_factory is not None:
        msg = "Both 'value' and 'value_factory' were specified"
        raise ValueError(msg)
    with suppress(AttributeError):
        return getattr(obj, key)
    if value_factory is not None:
        value = value_factory()
    setattr(obj, key, value)
    return value


def compose(*funcs):
    return reduce(lambda f, g: lambda *args, **kwargs: f(g(*args, **kwargs)), funcs)


def flip(func):
    def wrapped(*args, **kwargs):
        if len(args) > 1:
            first, *other, last = args
            return func(last, *other, first, **kwargs)
        return func(*args, **kwargs)

    return wrapped


class _NoneExceptionError(Exception): ...


chain_map = compose(chain.from_iterable, map)
