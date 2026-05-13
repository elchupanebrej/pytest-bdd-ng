"""Provide conftest helpers."""

import os
import tempfile
from pathlib import Path

import pytest

from pytest_bdd.util.tests_group_ordering import (
    apply_group_ordering,
    record_group_barrier_report,
    register_group_config_options,
    wait_for_group_barrier,
)


def _prefer_posix_temp_root() -> bool:
    """Use POSIX temp storage when WSL inherits a Windows temp root."""
    if os.name != "posix":
        return False

    posix_temp_root = Path("/tmp")  # noqa: S108
    if not posix_temp_root.is_dir():
        return False

    current_temp_root = Path(tempfile.gettempdir()).resolve()
    try:
        current_temp_root.relative_to("/mnt")
    except ValueError:
        return False

    temp_root = str(posix_temp_root)
    for env_name in ("TMPDIR", "TEMP", "TMP"):
        os.environ[env_name] = temp_root
    tempfile.tempdir = None
    return True


_POSIX_TEMP_ROOT_SELECTED = _prefer_posix_temp_root()


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
