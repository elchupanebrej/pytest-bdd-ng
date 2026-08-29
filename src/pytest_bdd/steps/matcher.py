from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING
from warnings import warn

from pytest_bdd.const import Steps
from pytest_bdd.model.step import StepType
from pytest_bdd.steps.types import _parser_specificity, _step_text
from pytest_bdd.warning_types import PytestBDDStepDefinitionWarning

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

    from pytest_bdd.compatibility.pytest import Config, FixtureRequest
    from pytest_bdd.model.feature import Feature
    from pytest_bdd.model.scenario import Scenario
    from pytest_bdd.model.step import Step
    from pytest_bdd.steps.definition import Definition
    from pytest_bdd.steps.registry import Registry


class Matcher:
    class MatchNotFoundError(RuntimeError):
        pass

    def __init__(self, config: Config) -> None:
        self.config = config
        self.request: FixtureRequest = None  # type: ignore[assignment]
        self.feature: Feature = None  # type: ignore[assignment]
        self.scenario: Scenario = None  # type: ignore[assignment]
        self.step: Step = None  # type: ignore[assignment]
        self.previous_step: Step | None = None
        self.step_registry: Registry = None  # type: ignore[assignment]
        self.step_type_context: StepType | str | None = None

    def __call__(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        previous_step: Step | None,
        step_registry: Registry,
    ) -> Definition:
        self.request, self.feature, self.scenario = request, feature, scenario
        self.step, self.previous_step, self.step_registry = step, previous_step, step_registry
        if self.step.type not in {StepType.unknown, "Unknown", None} or self.step_type_context is None:
            self.step_type_context = self.step.type
        matchers = (self.strict_matcher, self.unspecified_matcher, self.liberal_matcher)
        matches = list(self.find_step_definition_matches(self.step_registry, matchers))
        if matches:
            if len(matches) > 1:
                warn(PytestBDDStepDefinitionWarning(f"Alternative step definitions are found: {matches}"), stacklevel=2)
            return matches[0]
        raise self.MatchNotFoundError(_step_text(self.step))

    def strict_matcher(self, defn: Definition) -> bool:
        return defn.type_ == self.step_type_context and defn.parser.is_matching(self.request, _step_text(self.step))

    def unspecified_matcher(self, defn: Definition) -> bool:
        has_unk = ({self.step_type_context, defn.type_} & {StepType.unknown, "Unknown"}) != set()
        return has_unk and defn.parser.is_matching(self.request, _step_text(self.step))

    def liberal_matcher(self, defn: Definition) -> bool:
        if defn.liberal is None:
            opt = getattr(getattr(self.config, "option", None), str(Steps.Cli.LIBERAL_OPTION), None)
            getini = getattr(self.config, "getini", lambda _: False)
            is_lib = getini(str(Steps.Ini.LIBERAL_OPTION)) if opt is None else opt
        else:
            is_lib = defn.liberal
        return all(
            (
                not self.unspecified_matcher(defn),
                bool(is_lib),
                defn.type_ != self.step_type_context,
                defn.parser.is_matching(self.request, _step_text(self.step)),
            )
        )

    @staticmethod
    def find_step_definition_matches(
        registry: Registry | None, matchers: Sequence[Callable[[Definition], bool]]
    ) -> Iterator[Definition]:
        if registry:
            found = False
            for matcher in matchers:
                for d in sorted((x for x in registry if matcher(x)), key=_parser_specificity, reverse=True):
                    found = True
                    yield d
                if found:
                    break
            if not found:
                with suppress(AttributeError):
                    yield from Matcher.find_step_definition_matches(registry.parent, matchers)
