from __future__ import annotations

import pytest
from pytest_cuke.exceptions import (
    FeatureConcreteParseError,
    FeatureParseError,
    NoScenariosFound,
    PytestBDDError,
    ScenarioNotFound,
    ScenarioValidationError,
    StepDefinitionNotFoundError,
)

pytestmark = pytest.mark.unit


def test_exception_hierarchy() -> None:
    assert issubclass(ScenarioValidationError, PytestBDDError)
    assert issubclass(ScenarioNotFound, ScenarioValidationError)
    assert issubclass(StepDefinitionNotFoundError, PytestBDDError)
    assert issubclass(NoScenariosFound, PytestBDDError)
    assert issubclass(FeatureParseError, PytestBDDError)


def test_feature_concrete_parse_error() -> None:
    err = FeatureConcreteParseError("Error", 10, "Given step", "foo.feature")
    assert str(err) == "Error.\nLine number: 10.\nLine: Given step.\nFile: foo.feature"
    assert err.args == ("Error", 10, "Given step", "foo.feature")
    assert (err.parse_message, err.line, err.line_text, err.source_uri, err.column) == (
        "Error",
        10,
        "Given step",
        "foo.feature",
        1,
    )
    with pytest.raises(FeatureParseError):
        raise err
