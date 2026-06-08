"""
Step matching with three-pass strategy (strict, unspecified, liberal).

Responsibility:
    Step matching with three-pass strategy (strict, unspecified, liberal). It directly owns the observable contract,
    local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.steps.matcher` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - Matcher: owns nested behavior below this boundary
    - _parser_specificity: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/parser.py: imports or references `matcher`
    - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `matcher`
    - src/pytest_bdd/steps/__init__.py: imports or references `matcher`
    - src/pytest_bdd/steps/manager.py: imports or references `matcher`

State and side effects:
    mutates is_step_definition_liberal, self.request, self.feature, self.pickle, self.step; depends on
    __future__.annotations, collections.abc.Callable, collections.abc.Iterator, collections.abc.Sequence,
    contextlib.suppress.

Invariants:
    - `pytest_bdd.steps.matcher` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Failure semantics:
    Raises or re-raises self.MatchNotFoundError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence  # noqa: TC003
from contextlib import suppress
from typing import TYPE_CHECKING
from warnings import warn

from attrs import field
from cucumber_messages import Feature, Pickle, PickleStepType

from pytest_bdd.compatibility.pytest import Config, FixtureRequest  # noqa: TC001
from pytest_bdd.const import Steps
from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning

if TYPE_CHECKING:
    from pytest_bdd.steps.definition import Definition
    from pytest_bdd.steps.registry import Registry

# Import Step as alias for PickleStep
from cucumber_messages import (
    PickleStep as Step,  # upstream type stubs missing this attribute
)


class Matcher:
    """
    Match scenario steps to registered step definitions.

    Responsibility:
        Match scenario steps to registered step definitions. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.matcher.Matcher` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - MatchNotFoundError: owns nested behavior below this boundary
        - __init__: owns nested behavior below this boundary
        - __call__: owns nested behavior below this boundary
        - strict_matcher: owns nested behavior below this boundary
        - unspecified_matcher: owns nested behavior below this boundary
        - liberal_matcher: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `Matcher`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references `Matcher`
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `Matcher`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `Matcher`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `Matcher`

    State and side effects:
        mutates is_step_definition_liberal, self.request, self.feature, self.pickle, self.step.

    Invariants:
        - `pytest_bdd.steps.matcher.Matcher` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Failure semantics:
        Raises or re-raises self.MatchNotFoundError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    class MatchNotFoundError(RuntimeError):
        """
        Raised when no step definition matches a scenario step.

        Responsibility:
            Raised when no step definition matches a scenario step. It directly owns the observable contract, local
            decisions, and maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.matcher.Matcher.MatchNotFoundError` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `MatchNotFoundError`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `MatchNotFoundError`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `MatchNotFoundError`
            - src/pytest_bdd/plugin/pickle_runner/plugin/_plugin.py: imports or references `MatchNotFoundError`
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `MatchNotFoundError`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Invariants:
            - `pytest_bdd.steps.matcher.Matcher.MatchNotFoundError` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=4
        """

    def __init__(self, config: Config) -> None:
        """
        Initialize matcher with config and unset fields (populated via __call__).

        Responsibility:
            Initialize matcher with config and unset fields (populated via __call__). It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.matcher.Matcher.__init__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - field: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates self.config, self.request, self.feature, self.pickle, self.step.

        Invariants:
            - `pytest_bdd.steps.matcher.Matcher.__init__` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        self.config: Config = config
        self.request: FixtureRequest = field(init=False)  # type narrowing workaround for mypy
        self.feature: Feature = field(init=False)  # type narrowing workaround for mypy
        self.pickle: Pickle = field(init=False)  # type narrowing workaround for mypy
        self.step: Step = field(init=False)  # type narrowing workaround for mypy
        self.previous_step: Step | None = field(init=False)  # type narrowing workaround for mypy
        self.step_registry: Registry = field(init=False)  # type narrowing workaround for mypy
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

        Responsibility:
            Match a runtime step to this definition. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.matcher.Matcher.__call__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - len: collaborator call used by this boundary
            - list: collaborator call used by this boundary
            - self.find_step_definition_matches: collaborator call used by this boundary
            - warn: collaborator call used by this boundary
            - PytestBDDStepDefinitionWarning: collaborator call used by this boundary
            - self.MatchNotFoundError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/steps/__init__.py: imports or references `__call__`
            - src/pytest_bdd/steps/manager.py: imports or references `__call__`

        State and side effects:
            mutates self.request, self.feature, self.pickle, self.step, self.previous_step.

        Invariants:
            - `pytest_bdd.steps.matcher.Matcher.__call__` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises self.MatchNotFoundError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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

        Responsibility:
            Check if step definition strictly matches. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.matcher.Matcher.strict_matcher` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - step_definition.parser.is_matching: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `strict_matcher`
            - src/pytest_bdd/steps/__init__.py: imports or references `strict_matcher`
            - src/pytest_bdd/steps/manager.py: imports or references `strict_matcher`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Check if step definition matches with unspecified type. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.matcher.Matcher.unspecified_matcher` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - step_definition.parser.is_matching: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `unspecified_matcher`
            - src/pytest_bdd/steps/__init__.py: imports or references `unspecified_matcher`
            - src/pytest_bdd/steps/manager.py: imports or references `unspecified_matcher`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Check if step definition matches using liberal matching. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.matcher.Matcher.liberal_matcher` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - self.config.getini: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - all: collaborator call used by this boundary
            - self.unspecified_matcher: collaborator call used by this boundary
            - step_definition.parser.is_matching: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `liberal_matcher`
            - src/pytest_bdd/steps/__init__.py: imports or references `liberal_matcher`
            - src/pytest_bdd/steps/manager.py: imports or references `liberal_matcher`

        State and side effects:
            mutates is_step_definition_liberal.

        Invariants:
            - `pytest_bdd.steps.matcher.Matcher.liberal_matcher` keeps its documented import path, ownership boundary,
              and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

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

        Responsibility:
            Find step definition matches. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.matcher.Matcher.find_step_definition_matches`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - matcher: collaborator call used by this boundary
            - matching_definitions.sort: collaborator call used by this boundary
            - suppress: collaborator call used by this boundary
            - Matcher.find_step_definition_matches: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `find_step_definition_matches`
            - src/pytest_bdd/steps/__init__.py: imports or references `find_step_definition_matches`
            - src/pytest_bdd/steps/manager.py: imports or references `find_step_definition_matches`

        State and side effects:
            mutates found_matches, matching_definitions.

        Invariants:
            - `pytest_bdd.steps.matcher.Matcher.find_step_definition_matches` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4

        """
        if registry:
            found_matches = False
            for matcher in matchers:
                matching_definitions = [step_definition for step_definition in registry if matcher(step_definition)]
                matching_definitions.sort(key=_parser_specificity, reverse=True)
                for step_definition in matching_definitions:
                    found_matches = True
                    yield step_definition
                if found_matches:
                    break
            if not found_matches:
                with suppress(AttributeError):
                    yield from Matcher.find_step_definition_matches(registry.parent, matchers)


def _parser_specificity(step_definition: Definition) -> int:
    """
    Return a coarse specificity score for stable same-pass match ordering.

    Returns:
        Specificity score used for same-pass sorting.

    Responsibility:
        Return a coarse specificity score for stable same-pass match ordering. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.matcher._parser_specificity` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/steps/__init__.py: imports or references `_parser_specificity`
        - src/pytest_bdd/steps/manager.py: imports or references `_parser_specificity`

    State and side effects:
        mutates parser_type.

    Invariants:
        - `pytest_bdd.steps.matcher._parser_specificity` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    parser_type = step_definition.parser.type
    if parser_type in {
        StepDefinitionPatternType.pytest_bdd_string_expression,  # type: ignore[attr-defined]  # extended enum member
        StepDefinitionPatternType.pytest_bdd_parse_expression,  # type: ignore[attr-defined]  # extended enum member
        StepDefinitionPatternType.pytest_bdd_cfparse_expression,  # type: ignore[attr-defined]  # extended enum member
        StepDefinitionPatternType.cucumber_expression,
    }:
        return 2
    if parser_type in {
        StepDefinitionPatternType.regular_expression,
        StepDefinitionPatternType.pytest_bdd_regular_expression,  # type: ignore[attr-defined]  # extended enum member
    }:
        return 1
    return 0
