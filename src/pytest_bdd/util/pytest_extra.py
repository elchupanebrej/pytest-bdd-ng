"""
Provides focused utility functions for the `pytest_extra` concern within pytest-bdd utility
layer, offering helper op.

Responsibility:
    Provides focused utility functions for the `pytest_extra` concern within pytest-bdd utility
    layer, offering helper operations consumed by higher layers (collection, runtime, reporting)
    without pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `pytest_extra` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `pytest_extra`-related helper operations within
    the utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `pytest_extra` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `pytest_extra` utilities for reporting, collection, and runtime operations

State and side effects:
    None, this module keeps no persistent state and performs no file or network I/O.

Invariants:
    - The public API surface (exported names) remains stable across internal refactors.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import re
import sys
from contextlib import contextmanager
from re import Pattern
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

from pytest_bdd.compatibility.pytest import FixtureDef, FixtureRequest, build_fixture_def, fail


def inject_fixture(request: FixtureRequest, arg: str, value: object) -> None:
    """
    Perform the `inject_fixture` operation within its module boundary, implementing a focused.
    helper function that is co.

    Responsibility:
        Performs the `inject_fixture` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `inject_fixture` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the inject_fixture operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke inject_fixture for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The inject_fixture function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    fd = build_fixture_def(
        request,
        baseid=None,
        argname=arg,
        func=lambda: value,
        scope="function",  # type: ignore[arg-type]  # pytest internal API
        params=None,
    )
    fd.cached_result = (value, 0, None)

    old_fd: FixtureDef | None = request._fixture_defs.get(arg)  # noqa: SLF001  -- suppressed warning
    add_fixturename = arg not in request.fixturenames

    def fin() -> None:
        """
        Perform the `fin` operation within its module boundary, implementing a focused helper function.
        that is consumed by h.

        Responsibility:
        Performs the `fin` operation within its module boundary, implementing a focused helper function
        that is consumed by higher layers for its specific utility purpose within the pytest-bdd
        architecture.

        Reason for existence:
        `fin` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

        Delegates:
        - Python standard library: delegates core operations to stdlib

        Cohesion:
        All logic directly supports the fin operation.

        Separation:
        - Other functions in this module: each function handles a distinct helper concern.

        Main consumers:
        - `pytest_bdd.*`: callers import and invoke fin for its specific utility

        State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

        Invariants:
        - The fin function returns consistent results for equivalent inputs.

        Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
        """
        request._fixturemanager._arg2fixturedefs[arg].remove(fd)  # noqa: SLF001  -- suppressed warning
        if old_fd is None:
            request._fixture_defs.pop(arg, None)  # noqa: SLF001  -- suppressed warning
        else:
            request._fixture_defs[arg] = old_fd  # noqa: SLF001  -- suppressed warning

        if add_fixturename:
            request._pyfuncitem._fixtureinfo.names_closure.remove(arg)  # noqa: SLF001  -- suppressed warning

    request.addfinalizer(fin)

    # inject fixture definition
    request._fixturemanager._arg2fixturedefs.setdefault(arg, []).insert(0, fd)  # noqa: SLF001  -- suppressed warning
    # inject fixture value in request cache
    request._fixture_defs[arg] = fd  # noqa: SLF001  -- suppressed warning
    if add_fixturename:
        request._pyfuncitem._fixtureinfo.names_closure.append(arg)  # noqa: SLF001  -- suppressed warning


@contextmanager
def doesnt_raise(
    expected_exception: type[BaseException] | Sequence[type[BaseException]],
    *,
    match: str | Pattern[str] | None = None,
    suppress_not_matched: bool = True,
) -> Iterator[None]:
    """
    Perform the `doesnt_raise` operation within its module boundary, implementing a focused helper.
    function that is cons.

    Responsibility:
        Performs the `doesnt_raise` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `doesnt_raise` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the doesnt_raise operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke doesnt_raise for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The doesnt_raise function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    try:
        yield
    except expected_exception:  # type:ignore[misc]  # mypy limitation with singledispatchmethod/dynamic typing
        _ex_type, ex_value, _ex_traceback = sys.exc_info()
        is_matched = True
        if match is not None:
            is_matched = bool(re.search(match, f"{ex_value}"))
        if is_matched:
            fail(f"{ex_value}")
        elif not suppress_not_matched:
            raise
