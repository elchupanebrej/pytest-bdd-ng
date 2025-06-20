"""pytest-bdd Exceptions."""


class ScenarioIsDecoratorOnlyError(Exception):
    """Scenario can be only used as decorator."""


class ScenarioValidationError(Exception):
    """Base class for scenario validation."""


class ScenarioNotFoundError(ScenarioValidationError):
    """Scenario Not Found."""


class ExamplesNotValidError(ScenarioValidationError):
    """Example table is not valid."""


class ScenarioExamplesNotValidError(ScenarioValidationError):
    """Scenario steps parameters do not match declared scenario examples."""


class FeatureExamplesNotValidError(ScenarioValidationError):
    """Feature example table is not valid."""


class StepDefinitionNotFoundError(Exception):
    """StepHandler definition not found."""


class NoScenariosFoundError(Exception):
    """No scenarios found."""


class FeatureParseError(Exception):
    """Feature parse error."""


class FeatureConcreteParseError(FeatureParseError):
    """Feature parse error."""

    message = "{0}.\nLine number: {1}.\nLine: {2}.\nFile: {3}"

    def __str__(self):
        """String representation."""
        return self.message.format(*self.args)
