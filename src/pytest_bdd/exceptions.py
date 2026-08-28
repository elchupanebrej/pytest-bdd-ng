"""pytest-bdd Exceptions."""

from __future__ import annotations


class PytestBDDError(Exception):
    """Base pytest-bdd exception."""


class ScenarioIsDecoratorOnly(PytestBDDError):
    """Scenario can be only used as decorator."""


class ScenarioValidationError(PytestBDDError):
    """Base class for scenario validation."""


class ScenarioNotFound(ScenarioValidationError):
    """Scenario Not Found."""


class ExamplesNotValidError(ScenarioValidationError):
    """Example table is not valid."""


class ScenarioExamplesNotValidError(ScenarioValidationError):
    """Scenario steps parameters do not match declared scenario examples."""


class FeatureExamplesNotValidError(ScenarioValidationError):
    """Feature example table is not valid."""


class StepDefinitionNotFoundError(PytestBDDError):
    """StepHandler definition not found."""


class NoScenariosFound(PytestBDDError):
    """No scenarios found."""


class FeatureParseError(PytestBDDError):
    """Feature parse error."""


class FeatureConcreteParseError(FeatureParseError):
    """Feature parse error."""

    message = "{0}.\nLine number: {1}.\nLine: {2}.\nFile: {3}"

    def __str__(self) -> str:
        """String representation."""
        return self.message.format(*self.args)
