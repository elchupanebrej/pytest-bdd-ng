"""Compatibility module for pytest."""

from __future__ import annotations

from operator import ge
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from os import PathLike

    from _pytest.scope import Scope, _ScopeName

import pytest
from _pytest.compat import NotSetType  # noqa: PLC2701
from _pytest.config import Config, ExitCode, PytestPluginManager  # noqa: PLC2701
from _pytest.config.argparsing import Parser  # noqa: PLC2701
from _pytest.fixtures import FixtureDef, FixtureLookupError, call_fixture_func  # noqa: PLC2701
from _pytest.main import Session, wrap_session  # noqa: PLC2701
from _pytest.mark import Mark, MarkDecorator, MarkMatcher  # noqa: PLC2701
from _pytest.mark import expression as _mark_expression  # noqa: PLC2701
from _pytest.nodes import Collector  # noqa: PLC2701
from _pytest.pytester import RunResult  # noqa: PLC2701
from _pytest.python import Metafunc  # noqa: PLC2701
from _pytest.reports import TestReport  # noqa: PLC2701
from _pytest.runner import CallInfo  # noqa: PLC2701
from _pytest.stash import Stash  # noqa: PLC2701
from _pytest.terminal import TerminalReporter  # noqa: PLC2701

from pytest_bdd.util.packaging import compare_distribution_version

__all__ = [
    "PYTEST81",
    "PYTEST83",
    "CallInfo",
    "Collector",
    "Config",
    "ExitCode",
    "Expression",
    "FixtureDef",
    "FixtureLookupError",
    "FixtureRequest",
    "Item",
    "Mark",
    "MarkDecorator",
    "MarkMatcher",
    "Metafunc",
    "Module",
    "ParseError",
    "Parser",
    "PytestPluginManager",
    "RunResult",
    "Session",
    "Stash",
    "TerminalReporter",
    "TestReport",
    "Testdir",
    "call_fixture_func",
    "wrap_session",
]


# region pytest version dependent imports
def is_pytest_version_greater_or_equal(version: str) -> bool:
    return compare_distribution_version("pytest", version, ge)


PYTEST8, PYTEST81, PYTEST83 = map(
    is_pytest_version_greater_or_equal,
    [
        "8.0",
        "8.1",
        "8.3",
    ],
)
# endregion

FixtureRequest = pytest.FixtureRequest
Testdir = pytest.Testdir

if TYPE_CHECKING:  # pragma: no cover
    from _pytest.nodes import Item as BaseItem

    class Item(BaseItem):
        """Represent item state."""

        _request: FixtureRequest

else:
    from _pytest.nodes import Item  # noqa: PLC2701


class Module(pytest.Module):
    """Represent a pytest module with path helpers."""

    @classmethod
    def build(cls, parent: Collector, file_path: str | PathLike[str]) -> Module:
        """
        Build module instance.

        Returns:
            Module instance configured with the given file path.

        """
        return cls.from_parent(parent, path=Path(file_path))

    def get_path(self) -> Path:
        """
        Get the module's path.

        Returns:
            Path to the module file.

        """
        return getattr(self, "path", Path(self.fspath))


def fail(reason: str, *, pytrace: bool = True) -> NoReturn:
    __tracebackhide__ = True
    pytest.fail(reason, pytrace=pytrace)


def is_set(obj: object) -> bool:
    return not isinstance(obj, NotSetType)


def is_testrun_success(exitstatus: int | pytest.ExitCode) -> bool:
    return (isinstance(exitstatus, int) and exitstatus == 0) or exitstatus is pytest.ExitCode.OK


class _LegacyFixtureDefFactory(Protocol):
    def __call__(  # noqa: PLR0913, PLR0917
        self,
        fixturemanager: object,
        baseid: str | None,
        argname: str,
        func: Callable[[], object],
        scope: _ScopeName | Scope | Callable[[str, Config], _ScopeName] | None,
        params: Sequence[object] | None,
        ids: tuple[object | None, ...] | Callable[[object], object | None] | None = None,
        *,
        _ispytest: bool = False,
    ) -> FixtureDef[object]: ...


def build_fixture_def(  # noqa: PLR0913
    request: FixtureRequest,
    *,
    baseid: str | None,
    argname: str,
    func: Callable[[], object],
    scope: _ScopeName | Scope | Callable[[str, Config], _ScopeName] | None,
    params: Sequence[object] | None,
) -> FixtureDef[object]:
    if PYTEST81:
        return FixtureDef(
            request.config,
            baseid,
            argname,
            func,
            scope,
            params,
            None,
            _ispytest=PYTEST8,
        )
    legacy_fixture_def = cast("_LegacyFixtureDefFactory", FixtureDef)
    return legacy_fixture_def(request._fixturemanager, baseid, argname, func, scope, params)  # noqa: SLF001


Expression = _mark_expression.Expression
ParseError = getattr(_mark_expression, "ParseError", ValueError)
