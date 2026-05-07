from __future__ import annotations

from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager
from enum import Enum
from inspect import Signature, signature
from itertools import count, product, starmap
from types import FunctionType
from typing import TYPE_CHECKING, Protocol, cast

import pytest
from _pytest.mark import Mark
from decopatch import function_decorator
from makefun import wraps

from pytest_bdd.tag_expression import GherkinTagExpression, MarksTagExpression, TagExpression, TagExpressionType
from pytest_bdd.util.toolz_extra import ObjectCallable

if TYPE_CHECKING:
    from decopatch.main import _Decorator

    from pytest_bdd.compatibility.pytest import FixtureRequest

expression_count_gen = count()


class HookKind(Enum):
    mark = "mark"
    tag = "tag"


class HookConjunction(Enum):
    before = "before"
    after = "after"
    around = "around"


class _PickleTagProtocol(Protocol):
    name: str


class _HookFunctionProtocol(Protocol):
    def __call__(self, request: FixtureRequest, *args: object, **kwargs: object) -> Generator[None, None, None]: ...

    __pytest_bdd_is_hook__: bool
    __pytest_bdd_hook_name__: str
    __pytest_bdd_hook_expression__: str
    __pytest_bdd_hook_kind__: str
    __pytest_bdd_hook_conjunction__: str


class _AroundHookCallable(Protocol):
    def __call__(self, *args: object, **kwargs: object) -> Generator[None, None, None]: ...


def _get_conjunction_and_kind(
    *, conjunction: str | HookConjunction, kind: str | HookKind
) -> tuple[HookConjunction, HookKind]:
    conjunction_ = HookConjunction(conjunction) if isinstance(conjunction, str) else conjunction
    kind_ = HookKind(kind) if isinstance(kind, str) else kind
    return conjunction_, kind_


def _get_expression_type(*, _kind: HookKind) -> type[TagExpressionType]:
    return {
        HookKind.mark: MarksTagExpression,
        HookKind.tag: GherkinTagExpression,
    }[_kind]


def _get_marks(*, _kind: HookKind, request: FixtureRequest) -> list[Mark]:
    pickle_tags = cast(Iterable[_PickleTagProtocol], request.getfixturevalue("pickle").tags)
    return list(
        {
            HookKind.mark: request.node.iter_markers(),
            HookKind.tag: (
                Mark(
                    tag.name,
                    args=(),
                    kwargs={},
                    _ispytest=True,
                )
                for tag in pickle_tags
            ),
        }[_kind],
    )


def _get_args_kwargs(
    *,
    args: tuple[object, ...],
    kwargs: dict[str, object],
    func_sig: Signature,
    request: FixtureRequest,
) -> tuple[tuple[object, ...], dict[str, object]]:
    from pytest_bdd.model.scenario_run import Run

    return (
        args,
        {
            **kwargs,
            **({"request": request} if "request" in func_sig.parameters else {}),
            **({"run": Run.from_stash(request.config.stash)} if "run" in func_sig.parameters else {}),
        },
    )


def decorator_builder(conjunction: str | HookConjunction, kind: str | HookKind) -> _Decorator:
    conjunction_, kind_ = _get_conjunction_and_kind(conjunction=conjunction, kind=kind)

    @function_decorator
    def decorator_wrapper(
        expression: str | None = None,
        name: str | None = None,
    ) -> Callable[[object], Callable[[FixtureRequest], Generator[None, None, None]]]:
        expression_: str = expression if expression is not None else ""

        def decorator(func: object) -> Callable[[FixtureRequest], Generator[None, None, None]]:
            func_sig = signature(cast(FunctionType, func))

            fixture_decorator = pytest.fixture(
                name=f"{conjunction_.value}_{kind_.value}_expression_{expression_}_{next(expression_count_gen)}",
                autouse=True,
            )

            def hook(request: FixtureRequest, *args: object, **kwargs: object) -> Generator[None, None, None]:
                ExpressionType: type[TagExpressionType] = _get_expression_type(_kind=kind_)  # noqa:N806
                parsed_expression: TagExpression = ExpressionType.parse(expression_)

                is_matching = parsed_expression.evaluate(_get_marks(_kind=kind_, request=request))
                args_, kwargs_ = _get_args_kwargs(args=args, kwargs=kwargs, func_sig=func_sig, request=request)

                if is_matching:
                    if conjunction_ is HookConjunction.before:
                        cast(ObjectCallable, func)(*args_, **kwargs_)
                        yield None
                    elif conjunction_ is HookConjunction.after:
                        yield None
                        cast(ObjectCallable, func)(*args_, **kwargs_)
                    elif conjunction_ is HookConjunction.around:
                        with contextmanager(cast(_AroundHookCallable, func))(*args_, **kwargs_):
                            yield None
                    else:  # pragma: no cover
                        yield None
                else:
                    yield None

            hook = cast(_HookFunctionProtocol, wraps(func, prepend_args="request", remove_args="request")(hook))

            hook.__pytest_bdd_is_hook__ = True
            if name is not None:
                hook.__pytest_bdd_hook_name__ = name
            hook.__pytest_bdd_hook_expression__ = expression_
            hook.__pytest_bdd_hook_kind__ = kind_.value
            hook.__pytest_bdd_hook_conjunction__ = conjunction_.value

            return fixture_decorator(hook)

        return decorator

    return decorator_wrapper


before_mark, before_tag, after_mark, after_tag, around_mark, around_tag = starmap(
    decorator_builder,
    product(HookConjunction, HookKind),
)
