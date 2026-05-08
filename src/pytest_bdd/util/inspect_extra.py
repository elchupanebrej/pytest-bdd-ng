"""Provide inspect extra helpers."""

from __future__ import annotations

from inspect import getframeinfo, getsourcelines, signature
from sys import _getframe
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import CodeType, FrameType, FunctionType, MethodType, ModuleType, TracebackType


class ObjectCallable(Protocol):
    """Represent object callable state."""

    def __call__(self, *args: object, **kwargs: object) -> object:
        """Handle call."""
        ...


def get_args(func: ObjectCallable) -> Sequence[str]:
    """
    Get a list of argument names for a function.

    :param func: The function to inspect.

    :return: A list of argument names.
    :rtype: list

    Returns:
        List of positional argument names.

    """
    params = signature(func).parameters.values()
    return [param.name for param in params if param.kind == param.POSITIONAL_OR_KEYWORD]


def get_first_source_line(obj: object) -> int:
    """
    Get the first source line number of an object.

    Args:
        obj: Object to inspect.

    Returns:
        First source line number.

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
    Get the caller module locals dictionary.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.

    Returns:
        Caller's module locals dictionary.

    """
    return _getframe(stacklevel).f_locals


def get_caller_module_path(stacklevel: int = 1) -> str:
    """
    Get the caller module path.

    We use sys._getframe instead of inspect.stack(0) because the latter is way slower, since it iterates over
    all the frames in the stack.

    Returns:
        Path to the caller's module file.

    """
    frame = _getframe(stacklevel)
    return getframeinfo(frame, context=0).filename
