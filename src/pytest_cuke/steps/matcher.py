from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any
from warnings import warn

from pytest_cuke.const import Steps
from pytest_cuke.model.step import StepType
from pytest_cuke.steps.types import _parser_specificity, _step_text
from pytest_cuke.warning_types import PytestBDDStepDefinitionWarning

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

    from pytest_cuke.compatibility.pytest import Config, FixtureRequest
    from pytest_cuke.model.feature import Feature
    from pytest_cuke.model.scenario import Scenario
    from pytest_cuke.model.step import Step
    from pytest_cuke.steps.definition import Definition
    from pytest_cuke.steps.registry import Registry


class Matcher:
    class MatchNotFoundError(RuntimeError):
        def __init__(
            self,
            message: str,
            *,
            undefined_parameter_types: dict[tuple[str, str], BaseException | None] | None = None,
        ) -> None:
            super().__init__(message)
            self.undefined_parameter_types = tuple((undefined_parameter_types or {}).keys())

    def __init__(self, config: Config) -> None:
        self.config = config
        self.request: FixtureRequest = None  # type: ignore[assignment]  # The matcher call initializes per-scenario state before lookups.
        self.feature: Feature = None  # type: ignore[assignment]  # The matcher call initializes per-scenario state before lookups.
        self.scenario: Scenario = None  # type: ignore[assignment]  # The matcher call initializes per-scenario state before lookups.
        self.step: Step = None  # type: ignore[assignment]  # The matcher call initializes per-scenario state before lookups.
        self.previous_step: Step | None = None
        self.step_registry: Registry = None  # type: ignore[assignment]  # The matcher call initializes per-scenario state before lookups.
        self.step_type_context: StepType | str | None = None
        self._undefined_parameter_types: dict[tuple[str, str], BaseException | None] = {}
        self._undefined_parameter_type_causes: list[BaseException] = []
        self.last_matches: tuple[Definition, ...] = ()

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
        self._undefined_parameter_types = {}
        self._undefined_parameter_type_causes = []
        self.last_matches = ()
        step_type = self.step.type
        if isinstance(step_type, StepType):
            step_type_str = step_type.value.lower()
        elif step_type is not None:
            step_type_str = str(step_type).lower()
        else:
            step_type_str = ""

        if step_type_str in ("context", "given"):
            step_type = StepType.context
        elif step_type_str in ("action", "when"):
            step_type = StepType.action
        elif step_type_str in ("outcome", "then"):
            step_type = StepType.outcome
        elif step_type_str in ("conjunction", "and", "but", "*"):
            step_type = "Conjunction"
        elif not step_type:
            kw = (getattr(self.step, "keyword", "") or "").strip().lower()
            if kw == "given":
                step_type = StepType.context
            elif kw == "when":
                step_type = StepType.action
            elif kw == "then":
                step_type = StepType.outcome
            elif kw in ("and", "but", "*"):
                step_type = "Conjunction"
            else:
                step_type = StepType.unknown

        if step_type in {StepType.context, StepType.action, StepType.outcome}:
            self.step_type_context = step_type
        elif self.step_type_context is None:
            prev_type = getattr(previous_step, "type", None) if previous_step else None
            self.step_type_context = (
                prev_type if prev_type in {StepType.context, StepType.action, StepType.outcome} else StepType.context
            )
        matchers = (self.strict_matcher, self.unspecified_matcher, self.liberal_matcher)
        matches = list(self.find_step_definition_matches(self.step_registry, matchers))
        self.last_matches = tuple(matches)
        if matches:
            if len(matches) > 1:
                warn(PytestBDDStepDefinitionWarning(f"Alternative step definitions are found: {matches}"), stacklevel=2)
            return matches[0]
        not_found = self.MatchNotFoundError(
            _step_text(self.step), undefined_parameter_types=self._undefined_parameter_types
        )
        cause = next(iter(self._undefined_parameter_type_causes), None)
        if cause is not None:
            raise not_found from cause
        raise not_found

    def strict_matcher(self, defn: Definition) -> bool:
        return defn.type_ == self.step_type_context and self._parser_matches(defn.parser)

    def unspecified_matcher(self, defn: Definition) -> bool:
        has_unk = ({self.step_type_context, defn.type_} & {StepType.unknown, "Unknown"}) != set()
        return has_unk and self._parser_matches(defn.parser)

    def liberal_matcher(self, defn: Definition) -> bool:
        if defn.liberal is None:
            cli_name = getattr(Steps.Cli.LIBERAL_OPTION, "value", str(Steps.Cli.LIBERAL_OPTION))
            ini_name = getattr(Steps.Ini.LIBERAL_OPTION, "value", str(Steps.Ini.LIBERAL_OPTION))
            opt = getattr(getattr(self.config, "option", None), cli_name, None)
            if opt is None:
                try:
                    is_lib = getattr(self.config, "getini", lambda _: False)(ini_name)
                except (ValueError, KeyError):
                    is_lib = False
            else:
                is_lib = opt
        else:
            is_lib = defn.liberal
        return all(
            (
                not self.unspecified_matcher(defn),
                bool(is_lib),
                defn.type_ != self.step_type_context,
                self._parser_matches(defn.parser),
            )
        )

    def _parser_matches(self, parser: Any) -> bool:
        matched = bool(parser.is_matching(self.request, _step_text(self.step)))
        self._collect_undefined_parameter_types(parser)
        return matched

    def _collect_undefined_parameter_types(self, parser: Any) -> None:
        pending = [parser]
        visited: set[int] = set()
        while pending:
            current = pending.pop()
            if id(current) in visited:
                continue
            visited.add(id(current))

            diagnostics = getattr(current, "last_undefined_parameter_types", ())
            if not isinstance(diagnostics, tuple):
                diagnostics = ()
            if not diagnostics:
                diagnostic = getattr(current, "last_undefined_parameter_type", None)
                diagnostics = (diagnostic,) if isinstance(diagnostic, tuple) else ()
            error = getattr(current, "last_undefined_parameter_type_error", None)
            captured_diagnostic = False
            for diagnostic in diagnostics:
                if (
                    isinstance(diagnostic, tuple)
                    and len(diagnostic) == 2
                    and isinstance(diagnostic[0], str)
                    and isinstance(diagnostic[1], str)
                    and diagnostic[1]
                ):
                    key = diagnostic
                    if key not in self._undefined_parameter_types or self._undefined_parameter_types[key] is None:
                        self._undefined_parameter_types[key] = error if isinstance(error, BaseException) else None
                    captured_diagnostic = True

            if captured_diagnostic and isinstance(error, BaseException) and all(
                error is not cause for cause in self._undefined_parameter_type_causes
            ):
                self._undefined_parameter_type_causes.append(error)

            pending.extend(getattr(current, "parser_by_priorities", ()) or ())

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
