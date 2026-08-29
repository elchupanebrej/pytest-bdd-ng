"""Various utility functions."""

import base64
import pickle
import re
from collections import defaultdict
from collections.abc import Callable, Collection, Mapping, Sequence
from contextlib import contextmanager, nullcontext, suppress
from enum import Enum
from functools import reduce
from inspect import getframeinfo, signature
from itertools import tee
from operator import attrgetter, getitem, itemgetter
from sys import _getframe
from typing import Any, Literal, Protocol, Union, cast, runtime_checkable
from urllib.parse import urlparse

import pytest

from pytest_bdd.const import ALPHA_REGEX, PYTHON_REPLACE_REGEX
from pytest_bdd.util.data_table import data_table_to_dicts
from pytest_bdd.util.temp_root import prefer_posix_temp_root

__all__ = [
    "DefaultMapping",
    "Empty",
    "IdGenerator",
    "PytestBDDIdGeneratorHandler",
    "collect_dumped_objects",
    "compose",
    "convert_str_to_python_name",
    "data_table_to_dicts",
    "deepattrgetter",
    "doesnt_raise",
    "dump_obj",
    "flip",
    "get_args",
    "get_caller_module_locals",
    "get_caller_module_path",
    "getitemdefault",
    "inject_fixture",
    "is_local_url",
    "is_url_parsable",
    "make_python_name",
    "prefer_posix_temp_root",
    "setdefaultattr",
    "stringify",
]


@runtime_checkable
class PytestBDDIdGeneratorHandler(Protocol):
    pytest_bdd_id_generator: Union["IdGenerator", Any]


def get_args(func: Callable) -> Sequence[str]:
    """Get a list of argument names for a function.

    :param func: The function to inspect.

    :return: A list of argument names.
    :rtype: list
    """
    params = signature(func).parameters.values()
    return [param.name for param in params if param.kind == param.POSITIONAL_OR_KEYWORD]


def get_caller_module_locals(stacklevel: int = 1) -> dict[str, Any]:
    """Get the caller module locals dictionary.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.
    """
    return _getframe(stacklevel).f_locals


def get_caller_module_path(stacklevel: int = 1) -> str:
    """Get the caller module path.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.
    """
    frame = _getframe(stacklevel)
    return getframeinfo(frame, context=0).filename


def convert_str_to_python_name(s: Any) -> str:
    s1: str = str(s)
    s2 = re.sub(r"[^.a-zA-Z0-9]", "_", s1)
    s3 = re.sub(r"_+", "_", s2)
    s4 = s3.strip("_")
    return f"_{s4}" if re.match(r"\d.*", s4) else s4


_DUMP_START = "_pytest_bdd_>>>"
_DUMP_END = "<<<_pytest_bdd_"


def dump_obj(*objects: Any) -> None:
    """Dump objects to stdout so that they can be inspected by the test suite."""
    for obj in objects:
        dump = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        encoded = base64.b64encode(dump).decode("ascii")
        print(f"{_DUMP_START}{encoded}{_DUMP_END}")


def collect_dumped_objects(result: Any) -> list[object]:
    """Collect dumped objects from test run result."""
    stdout = result.stdout.str() if hasattr(result.stdout, "str") else str(result.stdout)
    payloads = re.findall(rf"{_DUMP_START}(.*?){_DUMP_END}", stdout)
    return [pickle.loads(base64.b64decode(payload)) for payload in payloads]  # noqa: S301


@contextmanager
def doesnt_raise(
    expected_exception: type[BaseException] | tuple[type[BaseException], ...] = Exception,
    *,
    match: str | re.Pattern[str] | None = None,
    suppress_not_matched: bool = True,
):
    """Context manager asserting that a block does not raise specific exception(s)."""
    try:
        yield
    except expected_exception as ex:
        is_matched = True
        if match is not None:
            is_matched = bool(re.search(match, f"{ex}"))
        if is_matched:
            pytest.fail(f"{ex}")
        elif not suppress_not_matched:
            raise


def inject_fixture(request: Any, arg: str, value: Any) -> None:
    """Inject fixture value dynamically into active pytest fixture request."""
    try:
        from _pytest.fixtures import FixtureDef
    except ImportError:
        return

    try:
        fd = FixtureDef(  # type: ignore[call-arg]
            request.config,
            None,
            arg,
            lambda: value,
            "function",
            None,
            None,
            _ispytest=True,
        )
    except TypeError:
        legacy_fd = cast("Any", FixtureDef)
        fd = legacy_fd(request._fixturemanager, None, arg, lambda: value, "function", None)

    fd.cached_result = (value, 0, None)

    cached_defs = getattr(request, "_fixture_defs", {}) if hasattr(request, "_fixture_defs") else {}
    old_fd = cached_defs.get(arg)
    fixturenames = getattr(request, "fixturenames", [])
    add_fixturename = arg not in fixturenames

    def fin() -> None:
        if hasattr(request, "_fixturemanager") and hasattr(request._fixturemanager, "_arg2fixturedefs"):
            arg_defs = request._fixturemanager._arg2fixturedefs.get(arg, [])
            if fd in arg_defs:
                arg_defs.remove(fd)
        if hasattr(request, "_fixture_defs"):
            if old_fd is None:
                request._fixture_defs.pop(arg, None)
            else:
                request._fixture_defs[arg] = old_fd

        if add_fixturename and hasattr(request, "_pyfuncitem") and hasattr(request._pyfuncitem, "_fixtureinfo"):
            names = getattr(request._pyfuncitem._fixtureinfo, "names_closure", [])
            if arg in names:
                names.remove(arg)

    request.addfinalizer(fin)
    if hasattr(request, "_fixturemanager") and hasattr(request._fixturemanager, "_arg2fixturedefs"):
        request._fixturemanager._arg2fixturedefs.setdefault(arg, []).insert(0, fd)
    if hasattr(request, "_fixture_defs"):
        request._fixture_defs[arg] = fd
    if add_fixturename and hasattr(request, "_pyfuncitem") and hasattr(request._pyfuncitem, "_fixtureinfo"):
        request._pyfuncitem._fixtureinfo.names_closure.append(arg)


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
        cls, bool_or_items: Collection[str] | dict[str, Any] | Any = True, *, warm_up_keys=()
    ):
        if isinstance(bool_or_items, Collection):
            if not isinstance(bool_or_items, Mapping):
                bool_or_items = zip(*tee(iter(bool_or_items)), strict=False)
        else:
            bool_or_items = cast("dict", {...: ...} if bool_or_items else {...: DefaultMapping.Skip})
        return cls(bool_or_items, warm_up_keys=warm_up_keys)


def _itemgetter(*items):
    def func(obj):
        if len(items) == 0:
            return []
        if len(items) == 1:
            return [obj[items[0]]] if items[0] != "" else []
        return itemgetter(*items)(obj)

    return func


class _NoneException(Exception): ...


class Empty(Enum):
    empty = None


def getitemdefault(
    obj, index, default=Empty.empty, default_factory: Callable | None = None, treat_as_empty=Empty.empty
):
    if default is not Empty.empty:
        if default_factory is not None:
            raise ValueError("Both 'default' and 'default_factory' were specified")

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
    raise KeyError(f"{index}")


def deepattrgetter(*attrs, **kwargs):
    empty = object()
    default = kwargs.pop("default", empty)
    default_exception_type = AttributeError if default is not empty else _NoneException
    skip_missing = kwargs.pop("skip_missing", False)
    skip_missing_context = suppress(AttributeError) if skip_missing else nullcontext()
    if default is not empty and skip_missing:
        raise ValueError('Both "default" and "skip_missing" are specified')

    def fn(obj):
        def _():
            for attr in attrs:
                try:
                    with skip_missing_context:
                        yield attrgetter(attr)(obj)
                except default_exception_type:
                    yield default

        return tuple(_())

    return fn


def setdefaultattr(obj, key, value: Literal[Empty.empty] | Any = Empty.empty, value_factory: Callable | None = None):
    if value is not Empty.empty and value_factory is not None:
        raise ValueError("Both 'value' and 'value_factory' were specified")
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


def make_python_name(string: str) -> str:
    """Make python attribute name out of a given string."""
    string = re.sub(PYTHON_REPLACE_REGEX, "", string.replace(" ", "_"))
    return re.sub(ALPHA_REGEX, "", string).lower()


@runtime_checkable
class StringableProtocol(Protocol):
    def __str__(self) -> str: ...  # pragma: no cover


def stringify(value: StringableProtocol | str | bytes) -> str:
    return str(value, **({"encoding": "utf-8"} if isinstance(value, bytes) else {}))


class IdGenerator:
    pytest_bdd_id_generator = "pytest_bdd_id_generator"

    def __init__(self):
        self._id_counter = 0

    def __next__(self):
        try:
            return str(self._id_counter)
        finally:
            self._id_counter += 1

    get_next_id = __next__

    @classmethod
    def from_stash(cls, stash):
        if hasattr(stash, "get"):
            gen = stash.get(cls.pytest_bdd_id_generator, None)
            if gen is None:
                gen = cls()
                stash[cls.pytest_bdd_id_generator] = gen
            return gen
        return cls()


def is_local_url(urllike):
    try:
        return not any(attrgetter("scheme", "netloc")(urlparse(urllike)))
    except Exception:
        return False


def is_url_parsable(urllike):
    try:
        urlparse(str(urllike))
        return True
    except ValueError:
        return False
