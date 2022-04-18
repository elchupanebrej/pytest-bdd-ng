"""Various utility functions."""
from __future__ import annotations

import base64
import pickle
import re
from collections import defaultdict
from contextlib import suppress
from functools import partial, reduce
from inspect import getframeinfo, signature
from itertools import tee
from operator import getitem, itemgetter
from sys import _getframe
from typing import TYPE_CHECKING, Callable, Collection, Mapping, cast

from _pytest.fixtures import FixtureDef
from attr import Factory, attrib, attrs
from marshmallow import post_load
from ordered_set import OrderedSet

from pytest_bdd.const import STEP_PREFIXES, TAG

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any

    from _pytest.config import Config
    from _pytest.pytester import RunResult

CONFIG_STACK: list[Config] = []


def get_args(func: Callable) -> list[str]:
    """Get a list of argument names for a function.

    :param func: The function to inspect.

    :return: A list of argument names.
    :rtype: list
    """
    params = signature(func).parameters.values()
    return [param.name for param in params if param.kind == param.POSITIONAL_OR_KEYWORD]


def get_caller_module_locals(depth: int = 2) -> dict[str, Any]:
    """Get the caller module locals dictionary.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.
    """
    return _getframe(depth).f_locals


def get_caller_module_path(depth: int = 2) -> str:
    """Get the caller module path.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.
    """
    frame = _getframe(depth)
    return getframeinfo(frame, context=0).filename


_DUMP_START = "_pytest_bdd_>>>"
_DUMP_END = "<<<_pytest_bdd_"


def dump_obj(*objects: Any) -> None:
    """Dump objects to stdout so that they can be inspected by the test suite."""
    for obj in objects:
        dump = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        encoded = base64.b64encode(dump).decode("ascii")
        print(f"{_DUMP_START}{encoded}{_DUMP_END}")


def collect_dumped_objects(result: RunResult):
    """Parse all the objects dumped with `dump_object` from the result.

    Note: You must run the result with output to stdout enabled.
    For example, using ``testdir.runpytest("-s")``.
    """
    stdout = result.stdout.str()  # pytest < 6.2, otherwise we could just do str(result.stdout)
    payloads = re.findall(rf"{_DUMP_START}(.*?){_DUMP_END}", stdout)
    return [pickle.loads(base64.b64decode(payload)) for payload in payloads]


@attrs
class SimpleMapping(Mapping):
    _dict: dict = attrib(default=Factory(dict), kw_only=True)

    def __getitem__(self, item):
        return self._dict[item]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)


def apply_tag(feature_context, pickle, tag, function):
    config = CONFIG_STACK[-1]

    def compose(*func):
        return reduce(lambda f, g: lambda x: f(g(x)), func, lambda x: x)

    return compose(
        *config.hook.pytest_bdd_convert_tag_to_marks(feature=feature_context, scenario=pickle, example=None, tag=tag)
    )(function)


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
            elif isinstance(intercessor, Callable):
                value = intercessor(key)
            elif intercessor is ...:
                value = key
            else:
                value = intercessor
            self[key] = value
            return value
        else:
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
                bool_or_items = zip(*tee(iter(bool_or_items)))
        else:
            bool_or_items = cast(dict, {...: ...} if bool_or_items else {...: DefaultMapping.Skip})
        return cls(bool_or_items, warm_up_keys=warm_up_keys)


def inject_fixture(request, arg, value):
    """Inject fixture into pytest fixture request.

    :param request: pytest fixture request
    :param arg: argument name
    :param value: argument value
    """

    fd = FixtureDef(
        fixturemanager=request._fixturemanager,
        baseid=None,
        argname=arg,
        func=lambda: value,
        scope="function",
        params=None,
    )
    fd.cached_result = (value, 0, None)

    old_fd = request._fixture_defs.get(arg)
    add_fixturename = arg not in request.fixturenames

    def fin():
        request._fixturemanager._arg2fixturedefs[arg].remove(fd)
        request._fixture_defs[arg] = old_fd

        if add_fixturename:
            request._pyfuncitem._fixtureinfo.names_closure.remove(arg)

    request.addfinalizer(fin)

    # inject fixture definition
    request._fixturemanager._arg2fixturedefs.setdefault(arg, []).insert(0, fd)
    # inject fixture value in request cache
    request._fixture_defs[arg] = fd
    if add_fixturename:
        request._pyfuncitem._fixtureinfo.names_closure.append(arg)


def get_tags(line: str | None) -> OrderedSet[str]:
    """Get tags out of the given line.

    :param str line: Feature file text line.

    :return: List of tags.
    """
    if not line or not line.strip().startswith(STEP_PREFIXES[TAG]):
        return OrderedSet()
    return OrderedSet(
        [tag.lstrip(STEP_PREFIXES[TAG]) for tag in line.strip().split(f" {STEP_PREFIXES[TAG]}") if len(tag) > 1]
    )


class ModelSchemaPostlLoadable:
    postbuild_attrs: list[str] = []

    @staticmethod
    def build_from_schema(cls, data, many, **kwargs):
        return cls.postbuild_attr_builder(cls, data, cls.postbuild_attrs)

    @classmethod
    def schema_post_loader(cls):
        return post_load(partial(cls.build_from_schema, cls))

    @staticmethod
    def postbuild_attr_builder(cls, data, postbuild_args):
        _data = {**data}
        empty = object()
        postbuildable_args = []
        for argument in postbuild_args:
            value = _data.pop(argument, empty)
            if value is not empty:
                postbuildable_args.append((argument, value))
        instance = cls(**_data)
        for argument, value in postbuildable_args:
            setattr(instance, argument, value)
        return instance


def _itemgetter(*items):
    def func(obj):
        if len(items) == 0:
            return []
        elif len(items) == 1:
            return [obj[items[0]]]
        else:
            return itemgetter(*items)(obj)

    return func
