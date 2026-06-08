# mypy: ignore-errors
# nested ParamSpec from decopatch not supported by mypy (valid-type error)
"""
Provide hook helpers.

Responsibility:
    Provide hook helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.hook` because it keeps the nearest code, data shape, call
    signature, and failure knowledge together.

Delegates:
    - HookKind: owns nested behavior below this boundary
    - HookConjunction: owns nested behavior below this boundary
    - _PickleTagProtocol: owns nested behavior below this boundary
    - _HookFunctionProtocol: owns nested behavior below this boundary
    - _AroundHookCallable: owns nested behavior below this boundary
    - _get_conjunction_and_kind: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `hook`
    - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `hook`
    - src/pytest_bdd/plugin/debug_mcp/artifacts.py: imports or references `hook`
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `hook`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `hook`

State and side effects:
    mutates conjunction_, kind_, expression_count_gen, mark, tag; depends on __future__.annotations,
    contextlib.contextmanager, enum.Enum, inspect.Signature, inspect.signature.

Invariants:
    - `pytest_bdd.hook` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from contextlib import contextmanager
from enum import Enum
from inspect import Signature, signature
from itertools import count, product, starmap
from typing import TYPE_CHECKING, Any, Protocol, cast

import pytest
from decopatch import function_decorator
from makefun import wraps

from pytest_bdd.compatibility.pytest import Mark, make_mark
from pytest_bdd.model.run import Run
from pytest_bdd.tag_expression import GherkinTagExpression, MarksTagExpression, TagExpression, TagExpressionType

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable
    from types import FunctionType

    from decopatch.main import _Decorator

    from pytest_bdd.compatibility.pytest import FixtureRequest
    from pytest_bdd.util.toolz_extra import ObjectCallable

expression_count_gen = count()


class HookKind(Enum):
    """
    Represent hook kind state.

    Responsibility:
        Represent hook kind state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.hook.HookKind` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `HookKind`

    State and side effects:
        mutates mark, tag.

    Invariants:
        - `pytest_bdd.hook.HookKind` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    mark = "mark"
    tag = "tag"


class HookConjunction(Enum):
    """
    Represent hook conjunction state.

    Responsibility:
        Represent hook conjunction state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.hook.HookConjunction` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `HookConjunction`

    State and side effects:
        mutates before, after, around.

    Invariants:
        - `pytest_bdd.hook.HookConjunction` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    before = "before"
    after = "after"
    around = "around"


class _PickleTagProtocol(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.hook._PickleTagProtocol` owns documented class behavior. It directly
        owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.hook._PickleTagProtocol` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `_PickleTagProtocol`

    State and side effects:
        mutates name.

    Invariants:
        - `pytest_bdd.hook._PickleTagProtocol` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    name: str


class _HookFunctionProtocol(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.hook._HookFunctionProtocol` owns documented class behavior. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.hook._HookFunctionProtocol` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `_HookFunctionProtocol`

    State and side effects:
        mutates __pytest_bdd_is_hook__, __pytest_bdd_hook_name__, __pytest_bdd_hook_expression__,
        __pytest_bdd_hook_kind__, __pytest_bdd_hook_conjunction__.

    Invariants:
        - `pytest_bdd.hook._HookFunctionProtocol` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    def __call__(self, request: FixtureRequest, *args: object, **kwargs: object) -> Generator[None, None, None]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.hook._HookFunctionProtocol.__call__` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.hook._HookFunctionProtocol.__call__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `__call__`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        ...

    __pytest_bdd_is_hook__: bool
    __pytest_bdd_hook_name__: str
    __pytest_bdd_hook_expression__: str
    __pytest_bdd_hook_kind__: str
    __pytest_bdd_hook_conjunction__: str


class _AroundHookCallable(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.hook._AroundHookCallable` owns documented class behavior. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.hook._AroundHookCallable` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `_AroundHookCallable`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.hook._AroundHookCallable` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    def __call__(self, *args: object, **kwargs: object) -> Generator[None, None, None]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.hook._AroundHookCallable.__call__` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.hook._AroundHookCallable.__call__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `__call__`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        ...


def _get_conjunction_and_kind(
    *,
    conjunction: str | HookConjunction,
    kind: str | HookKind,
) -> tuple[HookConjunction, HookKind]:
    """
    Parse hook conjunction and kind from string or enum.

    Args:
        conjunction: Hook conjunction (before, after, around).
        kind: Hook kind (mark, tag).

    Returns:
        Tuple of (conjunction, kind) enums.

    Responsibility:
        Parse hook conjunction and kind from string or enum. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.hook._get_conjunction_and_kind` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - HookConjunction: collaborator call used by this boundary
        - HookKind: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `_get_conjunction_and_kind`

    State and side effects:
        mutates conjunction_, kind_.

    Invariants:
        - `pytest_bdd.hook._get_conjunction_and_kind` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    conjunction_ = HookConjunction(conjunction) if isinstance(conjunction, str) else conjunction
    kind_ = HookKind(kind) if isinstance(kind, str) else kind
    return conjunction_, kind_


def _get_expression_type(*, _kind: HookKind) -> type[TagExpressionType]:
    """
    Get the expression type for a hook kind.

    Args:
        _kind: Hook kind.

    Returns:
        Tag expression type class.

    Responsibility:
        Get the expression type for a hook kind. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.hook._get_expression_type` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `_get_expression_type`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3

    """
    return {
        HookKind.mark: MarksTagExpression,
        HookKind.tag: GherkinTagExpression,
    }[_kind]


def _get_marks(*, _kind: HookKind, request: FixtureRequest) -> list[Mark]:
    """
    Get marks from the request based on hook kind.

    Args:
        _kind: Hook kind.
        request: Pytest fixture request.

    Returns:
        List of marks.

    Responsibility:
        Get marks from the request based on hook kind. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.hook._get_marks` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary
        - request.getfixturevalue: collaborator call used by this boundary
        - list: collaborator call used by this boundary
        - request.node.iter_markers: collaborator call used by this boundary
        - make_mark: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `_get_marks`

    State and side effects:
        mutates pickle_tags.

    Invariants:
        - `pytest_bdd.hook._get_marks` keeps its documented import path, ownership boundary, and observable behavior
          stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    pickle_tags = cast("Iterable[_PickleTagProtocol]", request.getfixturevalue("pickle").tags)
    return list(
        {
            HookKind.mark: request.node.iter_markers(),
            HookKind.tag: (make_mark(tag.name) for tag in pickle_tags),
        }[_kind],
    )


def _get_args_kwargs(
    *,
    args: tuple[object, ...],
    kwargs: dict[str, object],
    func_sig: Signature,
    request: FixtureRequest,
) -> tuple[tuple[object, ...], dict[str, object]]:
    """
    Get processed args and kwargs for hook function.

    Args:
        args: Positional arguments.
        kwargs: Keyword arguments.
        func_sig: Function signature.
        request: Pytest fixture request.

    Returns:
        Tuple of (args, kwargs).

    Responsibility:
        Get processed args and kwargs for hook function. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.hook._get_args_kwargs` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - Run.from_stash: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `_get_args_kwargs`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    return (
        args,
        {
            **kwargs,
            **({"request": request} if "request" in func_sig.parameters else {}),
            **({"run": Run.from_stash(request.config.stash)} if "run" in func_sig.parameters else {}),
        },
    )


def decorator_builder(conjunction: str | HookConjunction, kind: str | HookKind) -> _Decorator[..., Any]:
    """
    Build a hook decorator for the requested conjunction and kind.

    Args:
        conjunction: Hook conjunction (before, after, around).
        kind: Hook kind (mark, tag).

    Returns:
        Decorator function.

    Responsibility:
        Build a hook decorator for the requested conjunction and kind. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.hook.decorator_builder` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - decorator_wrapper: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `decorator_builder`
        - src/pytest_bdd/steps/decorators.py: imports or references `decorator_builder`

    State and side effects:
        mutates conjunction_, kind_, expression_, func_sig, fixture_decorator.

    Invariants:
        - `pytest_bdd.hook.decorator_builder` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    conjunction_, kind_ = _get_conjunction_and_kind(conjunction=conjunction, kind=kind)

    @function_decorator
    def decorator_wrapper(
        expression: str | None = None,
        name: str | None = None,
    ) -> Callable[[object], Callable[[FixtureRequest], Generator[None, None, None]]]:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.hook.decorator_builder.decorator_wrapper` owns documented
            function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.hook.decorator_builder.decorator_wrapper` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - decorator: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `decorator_wrapper`

        State and side effects:
            mutates expression_, func_sig, fixture_decorator, ExpressionType, parsed_expression.

        Invariants:
            - `pytest_bdd.hook.decorator_builder.decorator_wrapper` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        expression_: str = expression if expression is not None else ""

        def decorator(func: object) -> Callable[[FixtureRequest], Generator[None, None, None]]:
            """
            Responsibility:
                Responsibility: Responsibility: `pytest_bdd.hook.decorator_builder.decorator_wrapper.decorator` owns
                documented function behavior. It directly owns the observable contract, local decisions, and maintenance
                boundary for this function.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.hook.decorator_builder.decorator_wrapper.decorator` because it keeps the nearest code, data
                shape, call signature, and failure knowledge together.

            Delegates:
                - hook: owns nested behavior below this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/plugin/code_generator/rendering.py: imports or references `decorator`
                - src/pytest_bdd/plugin/code_generator/rewrite.py: imports or references `decorator`
                - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references `decorator`
                - src/pytest_bdd/plugin/pickle_runner/api_compatibility.py: imports or references `decorator`
                - src/pytest_bdd/scenario.py: imports or references `decorator`

            State and side effects:
                mutates func_sig, fixture_decorator, ExpressionType, parsed_expression, is_matching.

            Invariants:
                - `pytest_bdd.hook.decorator_builder.decorator_wrapper.decorator` keeps its documented import path,
                  ownership boundary, and observable behavior stable for callers.

            Architecture score:
                #arch-eval:reason_for_existence=4
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=4
                #arch-eval:cohesion=4
                #arch-eval:separation=3
                #arch-eval:consumer_clarity=4
                #arch-eval:state_invariants=4
                #arch-eval:entity_fullness=4
                #arch-eval:locational_stability=4
            """
            func_sig = signature(cast("FunctionType", func))

            fixture_decorator = pytest.fixture(
                name=f"{conjunction_.value}_{kind_.value}_expression_{expression_}_{next(expression_count_gen)}",
                autouse=True,
            )

            def hook(request: FixtureRequest, *args: object, **kwargs: object) -> Generator[None, None, None]:
                """
                Responsibility:
                    Responsibility: Responsibility: `pytest_bdd.hook.decorator_builder.decorator_wrapper.decorator.hook`
                    owns documented function behavior. It directly owns the observable contract, local decisions, and
                    maintenance boundary for this function.

                Reason for existence:
                    This entity is the information expert for
                    `pytest_bdd.hook.decorator_builder.decorator_wrapper.decorator.hook` because it keeps the nearest
                    code, data shape, call signature, and failure knowledge together.

                Delegates:
                    - cast: collaborator call used by this boundary
                    - contextmanager: collaborator call used by this boundary
                    - _get_expression_type: collaborator call used by this boundary
                    - ExpressionType.parse: collaborator call used by this boundary
                    - parsed_expression.evaluate: collaborator call used by this boundary
                    - _get_marks: collaborator call used by this boundary

                Cohesion:
                    The implementation stays together because its imports, calls, state writes, and return contract
                    describe one maintainable decision unit.

                Separation:
                    - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                      changeable without widening caller knowledge.

                Main consumers:
                    - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `hook`
                    - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `hook`
                    - src/pytest_bdd/plugin/debug_mcp/artifacts.py: imports or references `hook`
                    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `hook`
                    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
                      `hook`

                State and side effects:
                    mutates ExpressionType, parsed_expression, is_matching, args_, kwargs_.

                Invariants:
                    - `pytest_bdd.hook.decorator_builder.decorator_wrapper.decorator.hook` keeps its documented import
                      path, ownership boundary, and observable behavior stable for callers.

                Architecture score:
                    #arch-eval:reason_for_existence=4
                    #arch-eval:owned_responsibility=4
                    #arch-eval:delegation_boundary=4
                    #arch-eval:cohesion=4
                    #arch-eval:separation=3
                    #arch-eval:consumer_clarity=4
                    #arch-eval:state_invariants=4
                    #arch-eval:entity_fullness=4
                    #arch-eval:locational_stability=4
                """
                ExpressionType: type[TagExpressionType] = _get_expression_type(_kind=kind_)  # noqa:N806
                parsed_expression: TagExpression = ExpressionType.parse(expression_)

                is_matching = parsed_expression.evaluate(_get_marks(_kind=kind_, request=request))
                args_, kwargs_ = _get_args_kwargs(args=args, kwargs=kwargs, func_sig=func_sig, request=request)

                if is_matching:
                    if conjunction_ is HookConjunction.before:
                        cast("ObjectCallable", func)(*args_, **kwargs_)
                        yield None
                    elif conjunction_ is HookConjunction.after:
                        yield None
                        cast("ObjectCallable", func)(*args_, **kwargs_)
                    elif conjunction_ is HookConjunction.around:
                        with contextmanager(cast("_AroundHookCallable", func))(*args_, **kwargs_):
                            yield None
                    else:  # pragma: no cover
                        yield None
                else:
                    yield None

            hook = cast("_HookFunctionProtocol", wraps(func, prepend_args="request", remove_args="request")(hook))

            hook.__pytest_bdd_is_hook__ = True
            if name is not None:
                hook.__pytest_bdd_hook_name__ = name
            hook.__pytest_bdd_hook_expression__ = expression_
            hook.__pytest_bdd_hook_kind__ = kind_.value
            hook.__pytest_bdd_hook_conjunction__ = conjunction_.value

            return cast("Callable[[FixtureRequest], Generator[None, None, None]]", fixture_decorator(hook))

        return decorator

    return decorator_wrapper


before_mark, before_tag, after_mark, after_tag, around_mark, around_tag = starmap(
    decorator_builder,
    product(HookConjunction, HookKind),
)
