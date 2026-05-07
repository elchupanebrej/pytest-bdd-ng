"""pytest-bdd Exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from os import PathLike


class _FeatureLike(Protocol):
    uri: str


class _ScenarioLike(Protocol):
    name: str


class _StepLike(Protocol):
    text: str


class PytestBDDStashError(Exception):
    """Base class for pytest-bdd stash access failures."""


class PytestBDDStashLookupError(PytestBDDStashError, LookupError):
    """Requested pytest-bdd stash object is missing."""


class PytestBDDStashAlreadyInitializedError(PytestBDDStashError):
    """Stash object is being initialized more than once."""


class PytestBDDStashTypeMismatchError(PytestBDDStashError, TypeError):
    """Stash key is occupied by a value of unexpected type."""

    def __init__(self, *, stash_key: str, actual_type: str, expected_type: str) -> None:
        super().__init__(f"config.stash['{stash_key}'] contains {actual_type}, expected {expected_type}.")


class MessageSchemaValidationError(ValueError):
    """Schema-compatible emitted message does not satisfy the canonical schema."""

    def __init__(self, details: str) -> None:
        super().__init__(f"Schema-compatible message emission failed: {details}")


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
    """Step definition not found."""

    undefined_parameter_type: tuple[str, str] | None

    def __init__(
        self,
        feature: _FeatureLike,
        scenario: _ScenarioLike,
        step: _StepLike,
        *args: object,
    ) -> None:
        self.undefined_parameter_type = None
        keyword = getattr(step, "keyword", getattr(step, "prefix", "<unknown>"))
        if keyword is None:
            keyword = "<unknown>"
        line_number = getattr(step, "line_number", "<unknown>")
        if line_number is None:
            line_number = "<unknown>"
        super().__init__(
            f'Step definition is not found: "{step.text}". '
            f'Step keyword: "{keyword}". '
            f"Line {line_number} "
            f'in scenario "{scenario.name}" '
            f'in the feature "{feature.uri}"',
            *args,
        )


class NoScenariosFoundError(Exception):
    """No scenarios found."""


class FeatureParseError(Exception):
    """Feature parse error."""

    def __init__(self, path: str | PathLike[str], *args: object) -> None:
        super().__init__(f"Unable to parse {path}", *args)


class FeatureConcreteParseError(FeatureParseError):
    """Feature parse error."""

    def __init__(self, message: object, line_no: object, line: object, file: object, *args: object) -> None:
        Exception.__init__(self, message, line_no, line, file, *args)

    message = "{0}.\nLine number: {1}.\nLine: {2}.\nFile: {3}"

    def __str__(self) -> str:
        """String representation."""
        return self.message.format(*self.args[:4])
