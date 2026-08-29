from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest_bdd

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def test_public_api_exports() -> None:
    expected_exports = [
        "DataTable",
        "DocString",
        "Feature",
        "FeaturePathType",
        "Mimetype",
        "PytestBDDStepDefinitionWarning",
        "Scenario",
        "Step",
        "Suffix",
        "Table",
        "__version__",
        "given",
        "not_implemented",
        "parsers",
        "scenario",
        "scenarios",
        "step",
        "then",
        "tolerant",
        "when",
    ]
    for name in expected_exports:
        assert hasattr(pytest_bdd, name), f"Missing export: {name}"
        assert name in pytest_bdd.__all__, f"Missing from __all__: {name}"


def test_public_api_callables_and_types() -> None:
    for name in ["given", "when", "then", "step", "tolerant", "not_implemented", "scenario", "scenarios"]:
        obj = getattr(pytest_bdd, name)
        assert callable(obj), f"Expected callable for {name}"

    for name in ["Feature", "Scenario", "Step", "Table", "DataTable", "DocString", "Mimetype", "Suffix"]:
        obj = getattr(pytest_bdd, name)
        assert inspect.isclass(obj), f"Expected class for {name}"

    assert isinstance(pytest_bdd.__version__, str)
    assert hasattr(pytest_bdd.parsers, "parse")


def test_pytest11_entrypoint_registered() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    pyproject_path = repo_root / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    entry_points = data.get("project", {}).get("entry-points", {}).get("pytest11", {})
    assert entry_points.get("pytest-bdd") == "pytest_bdd.plugin"
