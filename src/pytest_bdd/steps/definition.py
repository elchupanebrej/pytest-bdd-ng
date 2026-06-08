"""
Step definition data class and shared type aliases.

Responsibility:
    Step definition data class and shared type aliases. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.steps.definition` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - StepFunc: owns nested behavior below this boundary
    - _resolve_callable_source_location: owns nested behavior below this boundary
    - Definition: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `definition`
    - src/pytest_bdd/steps/__init__.py: imports or references `definition`
    - src/pytest_bdd/steps/decorators.py: imports or references `definition`
    - src/pytest_bdd/steps/manager.py: imports or references `definition`
    - src/pytest_bdd/steps/matcher.py: imports or references `definition`

State and side effects:
    mutates converted_params, wildcard_params_strategy, source_line, expression_type, source_file; depends on
    __future__.annotations, collections.abc.Callable, collections.abc.Collection, collections.abc.Iterable,
    collections.abc.Mapping.

Invariants:
    - `pytest_bdd.steps.definition` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Failure semantics:
    Raises or re-raises TypeError; callers must treat these as boundary failures.

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

from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from inspect import getfile, getsourcelines
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, cast

from attrs import define, field
from cucumber_messages import (  # upstream library missing type stubs
    JavaMethod,
    JavaStackTraceElement,
    Location,
    PickleStepType,
    SourceReference,
    StepDefinition,
    StepDefinitionPattern,
)
from cucumber_messages import (
    PickleStep as Step,  # upstream type stubs missing this attribute
)
from typing_extensions import Protocol

from pytest_bdd.compatibility.path import resolvepath
from pytest_bdd.compatibility.pytest import Config, FixtureRequest  # noqa: TC001
from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers import StepParser  # noqa: TC001
from pytest_bdd.types.protocol import HasPytestStash  # noqa: TC001
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.toolz_extra import getitemdefault

if TYPE_CHECKING:
    from types import FunctionType


class StepFunc(Protocol):
    """
    Represent step func state.

    Responsibility:
        Represent step func state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.definition.StepFunc` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/hook.py: imports or references `StepFunc`
        - src/pytest_bdd/steps/__init__.py: imports or references `StepFunc`
        - src/pytest_bdd/steps/decorators.py: imports or references `StepFunc`
        - src/pytest_bdd/steps/manager.py: imports or references `StepFunc`
        - src/pytest_bdd/steps/matcher.py: imports or references `StepFunc`

    State and side effects:
        mutates __name__.

    Invariants:
        - `pytest_bdd.steps.definition.StepFunc` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    __name__: str


StepDecorator: TypeAlias = Callable[[StepFunc], StepFunc]
ConverterT: TypeAlias = Callable[[object], object]
ParamsFixturesMapping: TypeAlias = bool | Collection[str] | Mapping[object, str | None]


def _resolve_callable_source_location(func: StepFunc) -> tuple[str, int]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.steps.definition._resolve_callable_source_location` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.definition._resolve_callable_source_location`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - getfile: collaborator call used by this boundary
        - getsourcelines: collaborator call used by this boundary
        - int: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/steps/__init__.py: imports or references `_resolve_callable_source_location`
        - src/pytest_bdd/steps/decorators.py: imports or references `_resolve_callable_source_location`
        - src/pytest_bdd/steps/manager.py: imports or references `_resolve_callable_source_location`
        - src/pytest_bdd/steps/matcher.py: imports or references `_resolve_callable_source_location`
        - src/pytest_bdd/steps/registry.py: imports or references `_resolve_callable_source_location`

    State and side effects:
        mutates source_line, typed_func, source_file.

    Invariants:
        - `pytest_bdd.steps.definition._resolve_callable_source_location` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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
    typed_func = cast("FunctionType", func)
    source_file = getfile(typed_func)
    try:
        source_line = getsourcelines(typed_func)[1]
    except (OSError, TypeError):
        source_line = getattr(getattr(func, "__code__", None), "co_firstlineno", 1) or 1
    return source_file, int(source_line)


@define(eq=False)
class Definition:
    """
    Registered step definition.

    Responsibility:
        Registered step definition. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.definition.Definition` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - fixtures_mapped_from_step_definition: owns nested behavior below this boundary
        - as_message: owns nested behavior below this boundary
        - get_parameters: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references `Definition`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `Definition`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or references
          `Definition`
        - src/pytest_bdd/plugin/pickle_runner/hook.py: imports or references `Definition`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `Definition`

    State and side effects:
        mutates converted_params, wildcard_params_strategy, expression_type, message, func.

    Invariants:
        - `pytest_bdd.steps.definition.Definition` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Failure semantics:
        Raises or re-raises TypeError; callers must treat these as boundary failures.

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

    func: StepFunc = field()
    type_: str | PickleStepType | None = field()
    parser: StepParser = field()
    anonymous_group_names: Iterable[str] | None = field()
    converters: Mapping[str, ConverterT] = field()
    params_fixtures_mapping: ParamsFixturesMapping = field()
    param_defaults: Mapping[str, object] = field()
    target_fixtures: Sequence[str] = field()
    liberal: bool | None = field()
    not_implemented: bool = field(default=False)
    tolerant: bool = field(default=False)

    id: str = field(init=False)
    __cache: dict[int, StepDefinition] = field(factory=dict)

    @property
    def fixtures_mapped_from_step_definition(self) -> set[str]:
        """
        Handle fixtures mapped from step definition.

        Responsibility:
            Handle fixtures mapped from step definition. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.steps.definition.Definition.fixtures_mapped_from_step_definition` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - set: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - fixture_names.update: collaborator call used by this boundary
            - self.params_fixtures_mapping.values: collaborator call used by this boundary
            - getitemdefault: collaborator call used by this boundary
            - bool: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/steps/__init__.py: imports or references `fixtures_mapped_from_step_definition`
            - src/pytest_bdd/steps/decorators.py: imports or references `fixtures_mapped_from_step_definition`
            - src/pytest_bdd/steps/manager.py: imports or references `fixtures_mapped_from_step_definition`
            - src/pytest_bdd/steps/matcher.py: imports or references `fixtures_mapped_from_step_definition`
            - src/pytest_bdd/steps/registry.py: imports or references `fixtures_mapped_from_step_definition`

        State and side effects:
            mutates converted_params, wildcard_params_strategy, known_params, fixture_names, bypassed_params.

        Invariants:
            - `pytest_bdd.steps.definition.Definition.fixtures_mapped_from_step_definition` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        known_params = (
            set(self.parser.arguments) if self.anonymous_group_names is None else set(self.anonymous_group_names)
        )

        fixture_names = {*self.target_fixtures}
        converted_params: set[str]
        wildcard_params_strategy: object

        if isinstance(self.params_fixtures_mapping, Mapping):
            converted_params = {param for param in self.params_fixtures_mapping if isinstance(param, str)}
            fixture_names.update(
                fixture_name for fixture_name in self.params_fixtures_mapping.values() if isinstance(fixture_name, str)
            )
            wildcard_params_strategy = getitemdefault(self.params_fixtures_mapping, ..., default=...)
        elif isinstance(self.params_fixtures_mapping, Collection):
            converted_params = set()
            wildcard_params_strategy = None
            fixture_names.update(self.params_fixtures_mapping)
        elif bool(self.params_fixtures_mapping):
            converted_params = set()
            wildcard_params_strategy = ...
        else:
            converted_params = set()
            wildcard_params_strategy = None

        if wildcard_params_strategy is ...:
            bypassed_params = known_params.difference(converted_params)
            fixture_names.update(bypassed_params)
        return fixture_names

    def as_message(self, config: Config | HasPytestStash) -> StepDefinition:
        """
        Convert to message representation.

        Returns:
            Step definition message.

        Raises:
            TypeError: If the operation cannot be completed.

        Responsibility:
            Convert to message representation. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.definition.Definition.as_message` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - id: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - IdGenerator.from_stash: collaborator call used by this boundary
            - id_generator.get_next_id: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `as_message`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or
              references `as_message`
            - src/pytest_bdd/steps/__init__.py: imports or references `as_message`
            - src/pytest_bdd/steps/decorators.py: imports or references `as_message`
            - src/pytest_bdd/steps/manager.py: imports or references `as_message`

        State and side effects:
            mutates expression_type, message, id_generator, self.id, parser_expression_type.

        Invariants:
            - `pytest_bdd.steps.definition.Definition.as_message` keeps its documented import path, ownership boundary,
              and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises TypeError; callers must treat these as boundary failures.

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
        id_generator = IdGenerator.from_stash(config.stash)
        try:
            message = self.__cache[id(id_generator)]
        except KeyError:
            self.id = id_generator.get_next_id()

            parser_expression_type = self.parser.type

            expression_type: StepDefinitionPatternType
            if isinstance(parser_expression_type, StepDefinitionPatternType):
                expression_type = parser_expression_type
            else:
                try:
                    expression_type = StepDefinitionPatternType(str(parser_expression_type))  # type: ignore[call-arg]  # pydantic model __init__ via **kwargs
                except ValueError as exc:
                    msg = f"Unsupported step definition pattern type: {parser_expression_type!r}"
                    raise TypeError(msg) from exc

            pattern = StepDefinitionPattern(source=str(self.parser), type=expression_type)
            source_file, source_line = _resolve_callable_source_location(self.func)
            message = self.__cache[id(id_generator)] = StepDefinition(
                id=self.id,
                pattern=pattern,
                source_reference=SourceReference(
                    uri=Path(resolvepath(source_file, getattr(config, "rootpath", Path.cwd()))).as_uri(),
                    location=Location(line=source_line, column=1),
                    java_method=JavaMethod(
                        class_name="pytest_bdd.steps.StepDefinition",
                        method_name=str(self.func.__name__),
                        method_parameter_types=[],
                    ),
                    java_stack_trace_element=JavaStackTraceElement(
                        class_name="pytest_bdd.steps.StepDefinition",
                        file_name=Path(source_file).name,
                        method_name=str(self.func.__name__),
                    ),
                ),
            )
        return message

    def get_parameters(self, request: FixtureRequest, step: Step) -> dict[str, object]:
        """
        Get step parameters from parsed arguments.

        Returns:
            Dictionary of parameter names to values.

        Responsibility:
            Get step parameters from parsed arguments. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.definition.Definition.get_parameters` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.converters.get: collaborator call used by this boundary
            - self.parser.parse_arguments: collaborator call used by this boundary
            - parsed_arguments.items: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `get_parameters`
            - src/pytest_bdd/steps/__init__.py: imports or references `get_parameters`
            - src/pytest_bdd/steps/decorators.py: imports or references `get_parameters`
            - src/pytest_bdd/steps/manager.py: imports or references `get_parameters`
            - src/pytest_bdd/steps/matcher.py: imports or references `get_parameters`

        State and side effects:
            mutates parsed_arguments.

        Invariants:
            - `pytest_bdd.steps.definition.Definition.get_parameters` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

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
        parsed_arguments = (
            self.parser.parse_arguments(request, step.text, anonymous_group_names=self.anonymous_group_names) or {}
        )
        return {
            **self.param_defaults,
            **{arg: self.converters.get(arg, lambda value: value)(value) for arg, value in parsed_arguments.items()},  # type: ignore[no-untyped-call]  # dynamic converter call
        }
