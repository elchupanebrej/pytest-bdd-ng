"""Compatibility module for pytest"""

from __future__ import annotations

from operator import ge
from pathlib import Path
from typing import TYPE_CHECKING, Union, cast

import py
import pytest
from _pytest.compat import NotSetType
from _pytest.config import Config, ExitCode, PytestPluginManager
from _pytest.config.argparsing import Parser
from _pytest.fixtures import FixtureDef, FixtureLookupError, call_fixture_func
from _pytest.main import Session, wrap_session
from _pytest.mark import Mark, MarkDecorator, MarkMatcher
from _pytest.mark.expression import Expression, ParseError
from _pytest.nodes import Collector
from _pytest.pytester import RunResult
from _pytest.python import Metafunc
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.terminal import TerminalReporter

from pytest_bdd.util.packaging import compare_distribution_version

__all__ = [
    "PYTEST7",
    "PYTEST61",
    "PYTEST62",
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
    "TerminalReporter",
    "TestReport",
    "Testdir",
    "assert_outcomes",
    "call_fixture_func",
    "get_config_root_path",
    "wrap_session",
]


# region pytest version dependent imports
def is_pytest_version_greater_or_equal(version: str):
    return compare_distribution_version("pytest", version, ge)


PYTEST61, PYTEST62, PYTEST7, PYTEST8, PYTEST81, PYTEST83 = map(
    is_pytest_version_greater_or_equal,
    [
        "6.1",
        "6.2",
        "7.0",
        "8.0",
        "8.1",
        "8.3",
    ],
)


if PYTEST7:
    from pytest import Testdir  # noqa: PT013
else:
    from _pytest.pytester import Testdir  # type: ignore[no-redef, attr-defined]

if PYTEST62:
    from pytest import FixtureRequest  # noqa: PT013
else:
    from _pytest.fixtures import FixtureRequest
# endregion

if TYPE_CHECKING:  # pragma: no cover
    from _pytest.nodes import Item as BaseItem

    class Item(BaseItem):
        _request: FixtureRequest

else:
    from _pytest.nodes import Item


class Module(pytest.Module):
    @classmethod
    def build(cls, parent, file_path):
        if hasattr(cls, "from_parent"):
            collector = cls.from_parent(
                parent,
                **({"path": Path(file_path)} if PYTEST7 else {"fspath": py.path.local(file_path)}),  # noqa: PTH124
            )
        else:
            collector = cls(parent=parent, fspath=py.path.local(file_path))  # noqa: PTH124
        return collector

    def get_path(self):
        return getattr(self, "path", Path(self.fspath))


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
        errors=errors,
        passed=passed,
        skipped=skipped,
        failed=failed,
        xpassed=xpassed,
        xfailed=xfailed,
    )


def get_config_root_path(config: Config) -> Path:
    return Path(getattr(cast(Config, config), "rootpath" if PYTEST61 else "rootdir"))


def fail(reason, *, pytrace=True):
    __tracebackhide__ = True
    if PYTEST7:
        return pytest.fail(reason, pytrace=pytrace)
    return pytest.fail(msg=reason, pytrace=pytrace)


def is_set(obj):
    return not isinstance(obj, NotSetType)


def get_metafunc_call_arg(call, arg):
    return call.params[arg] if PYTEST8 else call.funcargs[arg]


def is_testrun_success(exitstatus: Union[int, pytest.ExitCode]) -> bool:
    return (isinstance(exitstatus, int) and exitstatus == 0) or exitstatus is pytest.ExitCode.OK


def build_fixture_def(request, *args, **kwargs):
    return FixtureDef(
        *args,
        **kwargs,
        **({"config": request.config} if PYTEST81 else {"fixturemanager": request._fixturemanager}),
        **({"_ispytest": True} if PYTEST8 else {}),
    )
