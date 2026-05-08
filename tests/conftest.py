"""Provide conftest helpers."""

import pytest

from pytest_bdd.util.tests_group_ordering import (
    apply_group_ordering,
    record_group_barrier_report,
    register_group_config_options,
    wait_for_group_barrier,
)


def pytest_addoption(parser):
    """Handle addoption."""
    register_group_config_options(parser)


def pytest_generate_tests(metafunc):
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
def pytest_collection_modifyitems(config, items):
    """Handle collection modifyitems."""
    apply_group_ordering(config, items)


def pytest_runtest_setup(item):
    """Handle runtest setup."""
    wait_for_group_barrier(item)


def pytest_runtest_logreport(report):
    """Handle runtest logreport."""
    record_group_barrier_report(report)
