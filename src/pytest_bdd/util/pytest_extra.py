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
    """
    fd = build_fixture_def(
        request,
        baseid=None,
        argname=arg,
        func=lambda: value,
        scope="function",
        params=None,
    )
    fd.cached_result = (value, 0, None)

    old_fd: FixtureDef[object] | None = request._fixture_defs.get(arg)
    add_fixturename = arg not in request.fixturenames

    def fin() -> None:
        request._fixturemanager._arg2fixturedefs[arg].remove(fd)
        if old_fd is None:
            request._fixture_defs.pop(arg, None)
        else:
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
    """
    try:
        yield
    except expected_exception:  # type:ignore[misc]
        _ex_type, ex_value, _ex_traceback = sys.exc_info()
        is_matched = True
        if match is not None:
            is_matched = bool(re.search(match, f"{ex_value}"))
        if is_matched:
            fail(f"{ex_value}")
        elif not suppress_not_matched:
            raise
