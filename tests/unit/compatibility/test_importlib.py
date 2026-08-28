from __future__ import annotations

from pytest_bdd.compatibility.importlib.metadata import version
from pytest_bdd.compatibility.importlib.resources import files


def test_importlib_metadata_version() -> None:
    pytest_ver = version("pytest")
    assert pytest_ver is not None


def test_importlib_resources_files() -> None:
    res = files("pytest_bdd")
    assert res is not None
