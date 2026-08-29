from __future__ import annotations

import inspect

import pytest_bdd


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
