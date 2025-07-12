import pytest


class PytestBDDStepDefinitionWarning(pytest.PytestWarning):
    __module__ = "pytest_bdd"
