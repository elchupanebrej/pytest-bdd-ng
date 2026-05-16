"""Step matching with three-pass strategy (strict, unspecified, liberal)."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence  # noqa: TC003
from contextlib import suppress
from typing import TYPE_CHECKING
from warnings import warn

from attrs import field
from cucumber_messages import Feature, Pickle, PickleStepType

from pytest_bdd.compatibility.pytest import Config, FixtureRequest  # noqa: TC001
from pytest_bdd.plugin.pickle_runner.const import Steps
from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning

if TYPE_CHECKING:
    from pytest_bdd.steps.definition import Definition
    from pytest_bdd.steps.registry import Registry

# Import Step as alias for PickleStep
from cucumber_messages import PickleStep as Step  # type:ignore[attr-defined]


class Matcher:
    """Match scenario steps to registered step definitions."""

    class MatchNotFoundError(RuntimeError):
        """Raised when no step definition matches a scenario step."""

    def __init__(self) -> None:
        """Initialize matcher with unset fields (populated via __call__)."""
        self.config: Config = field()  # type: ignore[assignment]
        self.request: FixtureRequest = field(init=False)  # type: ignore[assignment]
        self.feature: Feature = field(init=False)  # type: ignore[assignment]
        self.pickle: Pickle = field(init=False)  # type: ignore[assignment]
        self.step: Step = field(init=False)  # type: ignore[assignment]
        self.previous_step: Step | None = field(init=False)  # type: ignore[assignment]
        self.step_registry: Registry = field(init=False)  # type: ignore[assignment]
        self.step_type_context: PickleStepType | None = None

    def __call__(  # noqa: PLR0913, PLR0917
        self,
        request: FixtureRequest,
        feature: Feature,
        pickle: Pickle,
        step: Step,
        previous_step: Step | None,
        step_registry: Registry,
    ) -> Definition:
        """
        Match a runtime step to this definition.

        Returns:
            Matched step definition.

        """
        self.request = request
        self.feature = feature
        self.pickle = pickle
        self.step = step
        self.previous_step = previous_step
        self.step_registry = step_registry

        self.step_type_context = (
            self.step_type_context
            if self.step.type is PickleStepType.unknown and self.step_type_context is not None
            else self.step.type
        )

        step_definitions = list(
            self.find_step_definition_matches(
                self.step_registry,
                (
                    self.strict_matcher,
                    self.unspecified_matcher,
                    self.liberal_matcher,
                ),
            ),
        )

        if len(step_definitions) > 0:
            if len(step_definitions) > 1:
                warn(
                    PytestBDDStepDefinitionWarning(f"Alternative step definitions are found: {step_definitions}"),
                    stacklevel=2,
                )
            return step_definitions[0]
        raise self.MatchNotFoundError(self.step.text)

    def strict_matcher(self, step_definition: Definition) -> bool:
        """
        Check if step definition strictly matches.

        Returns:
            True if step definition matches strictly.

        """
        return step_definition.type_ == self.step_type_context and step_definition.parser.is_matching(
            self.request,
            self.step.text,
        )

    def unspecified_matcher(self, step_definition: Definition) -> bool:
        """
        Check if step definition matches with unspecified type.

        Returns:
            True if matches with unspecified type.

        """
        return (
            PickleStepType.unknown in {self.step_type_context, step_definition.type_}
        ) and step_definition.parser.is_matching(
            self.request,
            self.step.text,
        )

    def liberal_matcher(self, step_definition: Definition) -> bool:
        """
        Check if step definition matches using liberal matching.

        Returns:
            True if liberal matching applies, False otherwise.

        """
        if step_definition.liberal is None:
            if self.config.option.liberal_steps is None:
                is_step_definition_liberal = self.config.getini(str(Steps.Ini.LIBERAL_OPTION))
            else:
                is_step_definition_liberal = getattr(self.config.option, str(Steps.Cli.LIBERAL_OPTION), False)
        else:
            is_step_definition_liberal = step_definition.liberal

        return all(
            (
                not self.unspecified_matcher(step_definition),
                is_step_definition_liberal,
                step_definition.type_ != self.step_type_context,
                step_definition.parser.is_matching(self.request, self.step.text),
            ),
        )

    @staticmethod
    def find_step_definition_matches(
        registry: Registry | None,
        matchers: Sequence[Callable[[Definition], bool]],
    ) -> Iterator[Definition]:
        """
        Find step definition matches.

        Yields:
            Generated values.

        """
        if registry:
            found_matches = False
            for matcher in matchers:
                for step_definition in registry:
                    if matcher(step_definition):
                        found_matches = True
                        yield step_definition
                if found_matches:
                    break
            if not found_matches:
                with suppress(AttributeError):
                    yield from Matcher.find_step_definition_matches(registry.parent, matchers)
