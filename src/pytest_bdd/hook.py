from __future__ import annotations

from contextlib import contextmanager, suppress
from enum import Enum
from inspect import signature
from itertools import count, product, starmap
from typing import TYPE_CHECKING

import pytest
from _pytest.mark import Mark
from decopatch import function_decorator
from makefun import wraps

from pytest_bdd.compatibility.pytest import PYTEST7, FixtureLookupError, FixtureRequest
from pytest_bdd.tag_expression import GherkinTagExpression, MarksTagExpression, TagExpression, TagExpressionType

if TYPE_CHECKING:
    from decopatch.main import _Decorator

expression_count_gen = count()


class HookKind(Enum):
    mark = "mark"
    tag = "tag"


class HookConjunction(Enum):
    before = "before"
    after = "after"
    around = "around"


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


def _get_marks(*, _kind: HookKind, request: FixtureRequest) -> list:
    return list(
        {
            HookKind.mark: request.node.iter_markers(),
            HookKind.tag: (
                Mark(  # type: ignore[no-any-return]
                    tag.name,
                    args=(),
                    kwargs={},
                    **({"_ispytest": True} if PYTEST7 else {}),  # type:ignore[arg-type]
                )
                for tag in request.getfixturevalue("scenario").tags
            ),
        }[_kind],
    )


def _get_args_kwargs(*, args: tuple, kwargs: dict, func_sig, request: FixtureRequest) -> tuple[tuple, dict]:
    run = getattr(request, "run", None)
    if run is None:
        run = getattr(request.node, "_pytest_bdd_run", None)
    if run is None and "run" in func_sig.parameters:
        try:
            from pytest_bdd.plugin.scenario_runner.run_access import resolve_request_run, resolve_scenario_run
            from pytest_bdd.plugin.scenario_runner.run_store import RunStore

            feature = request.getfixturevalue("gherkin_document")
            scenario = request.getfixturevalue("scenario")
            scenario_run = resolve_scenario_run(
                request,
                run_store=RunStore(),
                feature=feature,
                scenario=scenario,
            )
            run = resolve_request_run(request)
            if run is None:
                run = getattr(scenario_run, "run", None)
        except FixtureLookupError:  # pragma: no cover - non-bdd test nodes don't expose these fixtures
            run = None

    if run is not None:
        with suppress(AttributeError):
            request.run = run

    return (
        args,
        {
            **kwargs,
            **({"request": request} if "request" in func_sig.parameters else {}),
            **({"run": run} if "run" in func_sig.parameters else {}),
        },
    )


def decorator_builder(conjunction: str | HookConjunction, kind: str | HookKind) -> _Decorator:
    conjunction_, kind_ = _get_conjunction_and_kind(conjunction=conjunction, kind=kind)

    @function_decorator
    def decorator_wrapper(expression: str | None = None, name: str | None = None):
        expression_: str = expression if expression is not None else ""

        def decorator(func):
            func_sig = signature(func)

            fixture_decorator = pytest.fixture(
                name=f"{conjunction_.value}_{kind_.value}_expression_{expression_}_{next(expression_count_gen)}",
                autouse=True,
            )

            @wraps(func, prepend_args="request", remove_args="request")
            def hook(request: FixtureRequest, *args, **kwargs):
                ExpressionType: type[TagExpressionType] = _get_expression_type(_kind=kind_)  # noqa:N806
                parsed_expression: TagExpression = ExpressionType.parse(expression_)

                is_matching = parsed_expression.evaluate(_get_marks(_kind=kind_, request=request))
                args_, kwargs_ = _get_args_kwargs(args=args, kwargs=kwargs, func_sig=func_sig, request=request)

                if is_matching:
                    if conjunction_ is HookConjunction.before:
                        yield func(*args_, **kwargs_)
                    elif conjunction_ is HookConjunction.after:
                        yield
                        func(*args_, **kwargs_)
                    elif conjunction_ is HookConjunction.around:
                        with contextmanager(func)(*args_, **kwargs_):
                            yield
                    else:  # pragma: no cover
                        yield
                else:
                    yield

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
