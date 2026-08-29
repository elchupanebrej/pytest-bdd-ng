"""
Compatibility module for pytest
"""

from __future__ import annotations

from operator import ge
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Protocol, Sequence, cast

import pytest
from _pytest.config import Config, PytestPluginManager
from _pytest.config.argparsing import Parser
from _pytest.fixtures import FixtureDef, FixtureLookupError, call_fixture_func
from _pytest.main import Session, wrap_session
from _pytest.mark import Mark, MarkDecorator
from _pytest.outcomes import Exit, Failed
from _pytest.python import Metafunc
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.terminal import TerminalReporter
from pytest import Module as PytestModule
from pytest import Package
from pytest import fail as _pytest_fail

from pytest_bdd.compatibility.typing import TypeAlias
from pytest_bdd.packaging import compare_distribution_version

__all__ = [
    "PYTEST6",
    "PYTEST7",
    "CallInfo",
    "Config",
    "Exit",
    "ExitCode",
    "Failed",
    "FixtureDef",
    "FixtureLookupError",
    "FixtureRequest",
    "Item",
    "Mark",
    "MarkDecorator",
    "Metafunc",
    "Module",
    "Package",
    "Parser",
    "PytestPluginManager",
    "RunResult",
    "Session",
    "TerminalReporter",
    "TestReport",
    "Testdir",
    "assert_outcomes",
    "build_fixture_def",
    "call_fixture_func",
    "get_config_root_path",
    "inject_fixture",
    "is_testrun_success",
    "make_mark",
    "make_mark_decorator",
    "wrap_session",
]


# region pytest version dependent imports
def is_pytest_version_greater_or_equal(version: str):
    return compare_distribution_version("pytest", version, ge)


PYTEST6, PYTEST61, PYTEST62, PYTEST7, PYTEST8, PYTEST81, PYTEST83 = map(
    is_pytest_version_greater_or_equal,
    [
        "6.0",
        "6.1",
        "6.2",
        "7.0",
        "8.0",
        "8.1",
        "8.3",
    ],
)

if PYTEST6:
    # noinspection PyUnresolvedReferences
    from _pytest.compat import NotSetType
    from _pytest.config import ExitCode

    # noinspection PyUnresolvedReferences
    from _pytest.mark import MarkMatcher

    try:
        from _pytest.mark.expression import Expression, ParseError
    except ImportError:
        from _pytest.mark.expression import Expression  # type: ignore[no-redef]

        ParseError = Exception  # type: ignore[misc, assignment]

    __all__ += [
        "Expression",
        "MarkMatcher",
        "ParseError",
    ]
else:
    ExitCode: TypeAlias = int  # type:ignore[no-redef]

if PYTEST7:
    if TYPE_CHECKING:
        from pytest import Testdir
else:
    import py

    if TYPE_CHECKING:
        from _pytest.pytester import Testdir  # type: ignore[no-redef, attr-defined]

if PYTEST62:
    from pytest import FixtureRequest
else:
    from _pytest.fixtures import FixtureRequest
# endregion

if TYPE_CHECKING:  # pragma: no cover
    from _pytest.nodes import Item as BaseItem
    from _pytest.pytester import RunResult

    class Item(BaseItem):
        _request: FixtureRequest

else:
    from _pytest.nodes import Item


class Module(PytestModule):
    @classmethod
    def build(cls, parent, file_path):
        if hasattr(cls, "from_parent"):
            collector = cls.from_parent(
                parent, **(dict(path=Path(file_path)) if PYTEST7 else dict(fspath=py.path.local(file_path)))
            )
        else:
            collector = cls(parent=parent, fspath=py.path.local(file_path))
        return collector

    def get_path(self):
        return getattr(self, "path", Path(self.fspath))


if PYTEST6:

    def assert_outcomes(
        result: RunResult,
        passed: int = 0,
        skipped: int = 0,
        failed: int = 0,
        errors: int = 0,
        xpassed: int = 0,
        xfailed: int = 0,
    ) -> None:
        """Compatibility function for result.assert_outcomes"""
        result.assert_outcomes(
            errors=errors, passed=passed, skipped=skipped, failed=failed, xpassed=xpassed, xfailed=xfailed
        )

else:

    def assert_outcomes(
        result: RunResult,
        passed: int = 0,
        skipped: int = 0,
        failed: int = 0,
        errors: int = 0,
        xpassed: int = 0,
        xfailed: int = 0,
    ) -> None:
        """Compatibility function for result.assert_outcomes"""
        result.assert_outcomes(  # type: ignore[call-arg]
            #  Pytest < 6 uses the singular form
            error=errors,
            passed=passed,
            skipped=skipped,
            failed=failed,
            xpassed=xpassed,
            xfailed=xfailed,
        )


def get_config_root_path(config: Config) -> Path:
    return Path(getattr(cast(Config, config), "rootpath" if PYTEST61 else "rootdir"))


def fail(reason, pytrace=True):
    __tracebackhide__ = True
    if PYTEST7:
        return _pytest_fail(reason, pytrace=pytrace)
    else:
        return _pytest_fail(msg=reason, pytrace=pytrace)


if PYTEST6:

    def is_set(obj):
        return not isinstance(obj, NotSetType)

else:

    def is_set(obj):
        return type(obj) is not object


def get_metafunc_call_arg(call, arg):
    return call.params[arg] if PYTEST8 else call.funcargs[arg]


def is_testrun_success(exitstatus: int | pytest.ExitCode) -> bool:
    return (isinstance(exitstatus, int) and exitstatus == 0) or exitstatus is pytest.ExitCode.OK


class _LegacyFixtureDefFactory(Protocol):
    def __call__(
        self,
        fixturemanager: object,
        baseid: str | None,
        argname: str,
        func: Callable[[], object],
        scope: object,
        params: Sequence[object] | None,
        ids: tuple[object | None, ...] | Callable[[object], object | None] | None = None,
        *,
        _ispytest: bool = False,
    ) -> FixtureDef: ...


def build_fixture_def(
    request: FixtureRequest,
    *,
    baseid: str | None,
    argname: str,
    func: Callable[[], object],
    scope: object,
    params: Sequence[object] | None,
) -> FixtureDef:
    if PYTEST81:
        return FixtureDef(  # type: ignore[call-arg]
            request.config,
            baseid,
            argname,
            func,
            scope,  # type: ignore[arg-type]
            params,
            None,
            _ispytest=PYTEST8,
        )
    legacy_fixture_def = cast("_LegacyFixtureDefFactory", FixtureDef)
    return legacy_fixture_def(request._fixturemanager, baseid, argname, func, scope, params)


def make_mark(
    name: str,
    args: tuple[object, ...] = (),
    kwargs: dict[str, object] | None = None,
) -> Mark:
    if kwargs is None:
        kwargs = {}
    return Mark(name, args=args, kwargs=kwargs, _ispytest=True)  # type: ignore[call-arg]


def make_mark_decorator(mark: Mark) -> MarkDecorator:
    return MarkDecorator(mark, _ispytest=True)  # type: ignore[call-arg]


def inject_fixture(request: FixtureRequest, arg: str, value: object) -> None:
    fd = build_fixture_def(
        request,
        baseid=None,
        argname=arg,
        func=lambda: value,
        scope="function",
        params=None,
    )
    fd.cached_result = (value, 0, None)

    cached_defs = getattr(request, "_fixture_defs", {}) if hasattr(request, "_fixture_defs") else {}
    old_fd: FixtureDef | None = cached_defs.get(arg)
    fixturenames = getattr(request, "fixturenames", [])
    add_fixturename = arg not in fixturenames

    def fin() -> None:
        if hasattr(request, "_fixturemanager") and hasattr(request._fixturemanager, "_arg2fixturedefs"):
            arg_defs = request._fixturemanager._arg2fixturedefs.get(arg, [])
            if fd in arg_defs:
                arg_defs.remove(fd)
        if hasattr(request, "_fixture_defs"):
            if old_fd is None:
                request._fixture_defs.pop(arg, None)
            else:
                request._fixture_defs[arg] = old_fd

        if add_fixturename and hasattr(request, "_pyfuncitem") and hasattr(request._pyfuncitem, "_fixtureinfo"):
            names = getattr(request._pyfuncitem._fixtureinfo, "names_closure", [])
            if arg in names:
                names.remove(arg)

    if hasattr(request, "addfinalizer"):
        request.addfinalizer(fin)

    if hasattr(request, "_fixturemanager") and hasattr(request._fixturemanager, "_arg2fixturedefs"):
        request._fixturemanager._arg2fixturedefs.setdefault(arg, []).insert(0, fd)
    if hasattr(request, "_fixture_defs"):
        request._fixture_defs[arg] = fd
    if add_fixturename and hasattr(request, "_pyfuncitem") and hasattr(request._pyfuncitem, "_fixtureinfo"):
        getattr(request._pyfuncitem._fixtureinfo, "names_closure", []).append(arg)
