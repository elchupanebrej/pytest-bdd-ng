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


class PytestBDDStashError(PytestBDDError):
    """Base exception for stash access errors."""


class PytestBDDStashLookupError(PytestBDDStashError, LookupError):
    """Raised when a required stash key or type is not found."""


class PytestBDDStashTypeMismatchError(PytestBDDStashError, TypeError):
    """Raised when a stash entry exists but its type does not match expected type."""

    def __init__(self, stash_key: str, actual_type: str, expected_type: str) -> None:
        super().__init__(
            f"Stash key '{stash_key}' contains object of type '{actual_type}', expected '{expected_type}'."
        )
        self.stash_key = stash_key
        self.actual_type = actual_type
        self.expected_type = expected_type


class PytestBDDStashAlreadyInitializedError(PytestBDDStashError):
    """Raised when a stash key or type is already initialized."""
