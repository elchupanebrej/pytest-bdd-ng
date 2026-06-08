"""
Provide pytest extra helpers.

Responsibility:
    Provide pytest extra helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.pytest_extra` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - inject_fixture: owns nested behavior below this boundary
    - doesnt_raise: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `pytest_extra`

State and side effects:
    mutates is_matched, fd, fd.cached_result, old_fd, add_fixturename; depends on __future__.annotations, re, sys,
    contextlib.contextmanager, re.Pattern.

Invariants:
    - `pytest_bdd.util.pytest_extra` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises re-raise; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
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
    Inject fixture into pytest fixture request.

    :param request: pytest fixture request
    :param arg: argument name
    :param value: argument value

    Responsibility:
        Inject fixture into pytest fixture request. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.pytest_extra.inject_fixture` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - fin: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `inject_fixture`

    State and side effects:
        mutates fd, fd.cached_result, old_fd, add_fixturename.

    Invariants:
        - `pytest_bdd.util.pytest_extra.inject_fixture` keeps its documented import path, ownership boundary, and
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
    fd = build_fixture_def(
        request,
        baseid=None,
        argname=arg,
        func=lambda: value,
        scope="function",  # type: ignore[arg-type]  # pytest internal API
        params=None,
    )
    fd.cached_result = (value, 0, None)

    old_fd: FixtureDef | None = request._fixture_defs.get(arg)  # noqa: SLF001
    add_fixturename = arg not in request.fixturenames

    def fin() -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.util.pytest_extra.inject_fixture.fin` owns documented function
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.pytest_extra.inject_fixture.fin` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - remove: collaborator call used by this boundary
            - request._fixture_defs.pop: collaborator call used by this boundary
            - request._pyfuncitem._fixtureinfo.names_closure.remove: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `fin`

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
        request._fixturemanager._arg2fixturedefs[arg].remove(fd)  # noqa: SLF001
        if old_fd is None:
            request._fixture_defs.pop(arg, None)  # noqa: SLF001
        else:
            request._fixture_defs[arg] = old_fd  # noqa: SLF001

        if add_fixturename:
            request._pyfuncitem._fixtureinfo.names_closure.remove(arg)  # noqa: SLF001

    request.addfinalizer(fin)

    # inject fixture definition
    request._fixturemanager._arg2fixturedefs.setdefault(arg, []).insert(0, fd)  # noqa: SLF001
    # inject fixture value in request cache
    request._fixture_defs[arg] = fd  # noqa: SLF001
    if add_fixturename:
        request._pyfuncitem._fixtureinfo.names_closure.append(arg)  # noqa: SLF001


@contextmanager
def doesnt_raise(
    expected_exception: type[BaseException] | Sequence[type[BaseException]],
    *,
    match: str | Pattern[str] | None = None,
    suppress_not_matched: bool = True,
) -> Iterator[None]:
    """
    Temporarily allow a configured exception.

    :param expected_exception: Expected exception/s which don't have to be raised; If it raised - test fails
    :param match: Message which will be count as failing test. If message is not matched - function passes
    :param suppress_not_matched: If specified - all non-matched exceptions will be suppressed
    :return:

    Responsibility:
        Temporarily allow a configured exception. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.pytest_extra.doesnt_raise` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - sys.exc_info: collaborator call used by this boundary
        - bool: collaborator call used by this boundary
        - re.search: collaborator call used by this boundary
        - fail: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `doesnt_raise`

    State and side effects:
        mutates is_matched, _ex_type, ex_value, _ex_traceback.

    Invariants:
        - `pytest_bdd.util.pytest_extra.doesnt_raise` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises re-raise; callers must treat these as boundary failures.

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
