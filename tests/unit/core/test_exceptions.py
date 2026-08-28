from __future__ import annotations

import pytest
from pytest_bdd.exceptions import (
    FeatureConcreteParseError,
    FeatureParseError,
    NoScenariosFound,
    PytestBDDError,
    ScenarioNotFound,
    ScenarioValidationError,
    StepDefinitionNotFoundError,
)


def test_exception_hierarchy() -> None:
    assert issubclass(ScenarioValidationError, PytestBDDError)
    assert issubclass(ScenarioNotFound, ScenarioValidationError)
    assert issubclass(StepDefinitionNotFoundError, PytestBDDError)
    assert issubclass(NoScenariosFound, PytestBDDError)
    assert issubclass(FeatureParseError, PytestBDDError)


def test_feature_concrete_parse_error() -> None:
    err = FeatureConcreteParseError("Error", 10, "Given step", "foo.feature")
    assert str(err) == "Error.\nLine number: 10.\nLine: Given step.\nFile: foo.feature"
    with pytest.raises(FeatureParseError):
        raise err
