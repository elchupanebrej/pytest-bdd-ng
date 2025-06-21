import re
import sys
from collections.abc import Sequence
from contextlib import contextmanager
from re import Pattern
from typing import Any, Optional, Union

from _pytest.fixtures import FixtureDef, FixtureRequest

from pytest_bdd.compatibility.pytest import PYTEST8, PYTEST81, fail


def inject_fixture(request: FixtureRequest, arg: str, value: Any) -> None:
    """Inject fixture into pytest fixture request.
    :param request: pytest fixture request
    :param arg: argument name
    :param value: argument value
    """
    fd = FixtureDef(
        **(
            {"config": request.config} if PYTEST81 else {"fixturemanager": request._fixturemanager}  # type:ignore
        ),
        baseid=None,
        argname=arg,
        func=lambda: value,
        scope="function",
        params=None,
        **({"_ispytest": True} if PYTEST8 else {}),  # type:ignore[arg-type]
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


@contextmanager
def doesnt_raise(
    expected_exception: Union[type[Exception], Sequence[type[Exception]]],
    *,
    match: Optional[Union[str, Pattern[str]]] = None,
    suppress_not_matched=True,
):
    """:param expected_exception: Expected exception/s which don't have to be raised; If it raised - test fails
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
