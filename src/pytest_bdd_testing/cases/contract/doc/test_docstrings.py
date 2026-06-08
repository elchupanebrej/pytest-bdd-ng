import inspect

import pytest

import pytest_bdd

PUBLIC_API_NAMES = [
    "FeaturePathType",
    "PytestBDDStepDefinitionWarning",
    "given",
    "not_implemented",
    "scenario",
    "scenarios",
    "step",
    "then",
    "tolerant",
    "when",
]


@pytest.mark.unit
def test_all_exports_have_docstrings() -> None:
    for name in PUBLIC_API_NAMES:
        obj = getattr(pytest_bdd, name)
        actual = inspect.unwrap(obj)
        doc = actual.__doc__
        assert doc is not None, f"{name} has no docstring"
        assert doc.strip(), f"{name} has no docstring"
        assert "Args:" in doc or "Parameters" in doc, f"{name} docstring missing Args/Parameters section"
        assert "Returns:" in doc or "Return:" in doc, f"{name} docstring missing Returns section"
