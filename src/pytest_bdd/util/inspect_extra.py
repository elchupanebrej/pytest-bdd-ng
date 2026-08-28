from __future__ import annotations

import sys
from inspect import getframeinfo, getsourcelines, signature
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


def get_args(func: Callable[..., Any]) -> Sequence[str]:
    return [p.name for p in signature(func).parameters.values() if p.kind == p.POSITIONAL_OR_KEYWORD]


def get_first_source_line(obj: object) -> int:
    try:
        return getsourcelines(obj)[1]  # type: ignore[arg-type]
    except (OSError, TypeError):
        code = getattr(obj, "__code__", None)
        return int(code.co_firstlineno) if code else 1


def get_caller_module_locals(stacklevel: int = 1) -> dict[str, Any]:
    return sys._getframe(stacklevel).f_locals


def get_caller_module_path(stacklevel: int = 1) -> str:
    return getframeinfo(sys._getframe(stacklevel), context=0).filename
