from __future__ import annotations

from functools import reduce
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


def compose(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    return reduce(lambda f, g: lambda *args, **kwargs: f(g(*args, **kwargs)), funcs)


def flip(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        return func(args[-1], *args[1:-1], args[0], **kwargs) if len(args) > 1 else func(*args, **kwargs)

    return wrapped
