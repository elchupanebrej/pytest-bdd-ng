import pytest
from _pytest.python import Metafunc


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
