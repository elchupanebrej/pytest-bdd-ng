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
    """
    Test target:
    Enforce framework invariants and stable API contracts.
    Test type:
    E2E/Acceptance test
    Test scenario:
    Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    for name in PUBLIC_API_NAMES:
        obj = getattr(pytest_bdd, name)
        actual = inspect.unwrap(obj)
        doc = actual.__doc__
        assert doc is not None, f"{name} has no docstring"
        assert doc.strip(), f"{name} has no docstring"
        assert "Args:" in doc or "Parameters" in doc, f"{name} docstring missing Args/Parameters section"
        assert "Returns:" in doc or "Return:" in doc, f"{name} docstring missing Returns section"
