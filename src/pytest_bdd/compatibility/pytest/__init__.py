"""Compatibility module for pytest"""

from __future__ import annotations

from operator import ge
from pathlib import Path
from typing import TYPE_CHECKING, Union, cast

import pytest
from _pytest.compat import NotSetType
from _pytest.config import Config, ExitCode, PytestPluginManager
from _pytest.config.argparsing import Parser
from _pytest.fixtures import FixtureDef, FixtureLookupError, call_fixture_func
from _pytest.main import Session, wrap_session
from _pytest.mark import Mark, MarkDecorator, MarkMatcher
from _pytest.mark import expression as _mark_expression
from _pytest.nodes import Collector
from _pytest.pytester import RunResult
from _pytest.python import Metafunc
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.stash import Stash
from _pytest.terminal import TerminalReporter

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
    "assert_outcomes",
    "call_fixture_func",
    "get_config_root_path",
    "wrap_session",
]


# region pytest version dependent imports
def is_pytest_version_greater_or_equal(version: str):
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
        _request: FixtureRequest

else:
    from _pytest.nodes import Item


class Module(pytest.Module):
    @classmethod
    def build(cls, parent, file_path):
        return cls.from_parent(parent, path=Path(file_path))

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
    return Path(cast(Config, config).rootpath)


def fail(reason, *, pytrace=True):
    __tracebackhide__ = True
    return pytest.fail(reason, pytrace=pytrace)


def is_set(obj):
    return not isinstance(obj, NotSetType)


def get_metafunc_call_arg(call, arg):
    return call.params[arg] if PYTEST8 else call.funcargs[arg]


def is_testrun_success(exitstatus: int | pytest.ExitCode) -> bool:
    return (isinstance(exitstatus, int) and exitstatus == 0) or exitstatus is pytest.ExitCode.OK


def build_fixture_def(request, *args, **kwargs):
    return FixtureDef(
        *args,
        **kwargs,
        **({"config": request.config} if PYTEST81 else {"fixturemanager": request._fixturemanager}),
        **({"_ispytest": True} if PYTEST8 else {}),
    )


Expression = _mark_expression.Expression
ParseError = getattr(_mark_expression, "ParseError", ValueError)
