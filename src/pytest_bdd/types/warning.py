"""Provide warning helpers."""

import pytest


class PytestBDDStepDefinitionWarning(pytest.PytestWarning):
    """Represent pytest bddstep definition warning warnings."""

    __module__ = "pytest_bdd"
