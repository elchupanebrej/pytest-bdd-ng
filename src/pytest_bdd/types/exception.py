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

    def __init__(self, feature, scenario, step, *args):
        super().__init__(
            f'Step definition is not found: "{step.text}". '
            f'Step keyword: "{step.keyword}". '
            f"Line {step.line_number} "
            f'in scenario "{scenario.name}" '
            f'in the feature "{feature.uri}"',
            *args,
        )


class NoScenariosFoundError(Exception):
    """No scenarios found."""


class FeatureParseError(Exception):
    """Feature parse error."""

    def __init__(self, path, *args):
        super().__init__(f"Unable to parse {path}", *args)


class FeatureConcreteParseError(FeatureParseError):
    """Feature parse error."""

    def __init__(self, message, line_no, line, file, *args):
        Exception.__init__(self, message, line_no, line, file, *args)

    message = "{0}.\nLine number: {1}.\nLine: {2}.\nFile: {3}"

    def __str__(self):
        """String representation."""
        return self.message.format(*self.args[:3])
