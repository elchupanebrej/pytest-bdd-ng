"""Provide conftest helpers."""

import pytest

from pytest_bdd.compatibility.pytest import Config, Item, Metafunc, Parser, TestReport
from pytest_bdd.util.temp_root import prefer_posix_temp_root
from pytest_bdd.util.tests_group_ordering import (
    apply_group_ordering,
    record_group_barrier_report,
    register_group_config_options,
    wait_for_group_barrier,
)

_POSIX_TEMP_ROOT_SELECTED = prefer_posix_temp_root()


def pytest_addoption(parser: Parser) -> None:
    """Handle addoption."""
    register_group_config_options(parser)


def pytest_generate_tests(metafunc: Metafunc) -> None:
    """Handle generate tests."""
    if "pytest_params" in metafunc.fixturenames:
        metafunc.parametrize(
            "pytest_params",
            [
                pytest.param([], id="no-import-mode"),
                pytest.param(["--import-mode=prepend"], id="--import-mode=prepend"),
                pytest.param(["--import-mode=append"], id="--import-mode=append"),
                pytest.param(["--import-mode=importlib"], id="--import-mode=importlib"),
            ],
        )


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """Handle collection modifyitems."""
    apply_group_ordering(config, items)


def pytest_runtest_setup(item: Item) -> None:
    """Handle runtest setup."""
    wait_for_group_barrier(item)


def pytest_runtest_logreport(report: TestReport) -> None:
    """Handle runtest logreport."""
    record_group_barrier_report(report)
