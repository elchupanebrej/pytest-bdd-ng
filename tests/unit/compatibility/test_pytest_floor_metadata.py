from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from packaging.markers import default_environment
from packaging.requirements import Requirement

pytestmark = pytest.mark.unit

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _project_requirements() -> list[Requirement]:
    project = tomllib.loads((_PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    lines = [*project["dependencies"], *project["optional-dependencies"]["test"]]
    return [Requirement(line) for line in lines]


def _pytest_requirements() -> list[Requirement]:
    return [requirement for requirement in _project_requirements() if requirement.name.casefold() == "pytest"]


def _accepts(python_version: str, pytest_version: str) -> bool:
    environment = {**default_environment(), "python_version": python_version}
    return all(
        requirement.specifier.contains(pytest_version)
        for requirement in _pytest_requirements()
        if requirement.marker is None or requirement.marker.evaluate(environment)
    )


def test_metadata_requires_the_declared_pytest_floor_for_each_python_version() -> None:
    assert _accepts("3.11", "8.0.0")
    assert not _accepts("3.11", "7.99.0")

    assert not _accepts("3.14", "8.4.1")
    assert _accepts("3.14", "8.4.2")

    assert not _accepts("3.15", "9.1.0")
    assert _accepts("3.15", "9.1.1")


def test_metadata_pytest_markers_do_not_select_an_implementation() -> None:
    for requirement in _pytest_requirements():
        if requirement.marker is None:
            continue
        marker = str(requirement.marker).casefold()
        assert "implementation_name" not in marker
        assert "platform_python_implementation" not in marker
