"""pytest-bdd public API."""

from __future__ import annotations

from pytest_bdd import parsers
from pytest_bdd.mimetype import Mimetype, Suffix
from pytest_bdd.model import DataTable, DocString, Feature, Scenario, Step
from pytest_bdd.packaging import get_distribution_version
from pytest_bdd.scenario import FeaturePathType, scenario, scenarios
from pytest_bdd.steps import given, not_implemented, step, then, tolerant, when
from pytest_bdd.warning_types import PytestBDDStepDefinitionWarning

Table = DataTable
__version__ = str(get_distribution_version("pytest-bdd-ng"))

__all__ = [
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
