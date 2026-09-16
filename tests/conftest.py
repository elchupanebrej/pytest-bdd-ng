from pathlib import Path

import pytest

from pytest_bdd.compatibility.pytest import PYTEST6

pytest_plugins = "pytester"

SLOW_TESTS_FILE = Path(__file__).with_name("slow-tests.txt")


def slow_node_prefixes():
    """Return the curated slow-test node-id prefixes from tests/slow-tests.txt."""
    lines = SLOW_TESTS_FILE.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
    """Mark items in the curated slow-test list; must run before -m deselection."""
    prefixes = tuple(slow_node_prefixes())
    for item in items:
        if item.nodeid.startswith(prefixes):
            item.add_marker(pytest.mark.slow)


def pytest_generate_tests(metafunc):
    if "pytest_params" in metafunc.fixturenames:
        if PYTEST6:
            parametrizations = [
                pytest.param([], id="no-import-mode"),
                pytest.param(["--import-mode=prepend"], id="--import-mode=prepend"),
                pytest.param(["--import-mode=append"], id="--import-mode=append"),
                pytest.param(["--import-mode=importlib"], id="--import-mode=importlib"),
            ]
        else:
            parametrizations = [[]]
        metafunc.parametrize(
            "pytest_params",
            parametrizations,
        )
