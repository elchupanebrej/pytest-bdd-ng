"""
StepDefinitionManager namespace class for backward compatibility.

Responsibility:
    StepDefinitionManager namespace class for backward compatibility. It directly owns the observable contract, local
    decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.steps.manager` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - StepDefinitionManager: owns nested behavior below this boundary
    - _none_fixture: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/steps/__init__.py: imports or references `manager`
    - src/pytest_bdd/steps/decorators.py: imports or references `manager`

State and side effects:
    mutates Registry, Matcher, Definition, StepProtocol, NamespaceStepRegistryProtocol; depends on
    __future__.annotations, warnings, collections.abc.Iterable, collections.abc.Mapping, collections.abc.Sequence.

Invariants:
    - `pytest_bdd.steps.manager` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable, Mapping, Sequence  # noqa: TC003
from typing import cast
from uuid import uuid4

import pytest
from cucumber_messages import PickleStepType  # noqa: TC002
from ordered_set import OrderedSet

from pytest_bdd.steps.definition import (
    ConverterT,
    Definition,
    ParamsFixturesMapping,
    StepDecorator,
    StepFunc,
)
from pytest_bdd.steps.matcher import Matcher
from pytest_bdd.steps.registry import Registry, StepProtocol, StepRegistryProtocol
from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning
from pytest_bdd.util.inspect_extra import get_caller_module_locals
from pytest_bdd.util.other import format_as_python_identifier
from pytest_bdd.util.toolz_extra import setdefaultattr


class StepDefinitionManager:
    """
    Step definition manager — namespace class exposing Registry, Matcher, Definition.

    This class exists for backward compatibility. Code that accesses
    ``StepDefinitionManager.Registry``, ``StepDefinitionManager.Matcher``,
    or ``StepDefinitionManager.Definition`` will continue to work.

    Responsibility:
        Step definition manager — namespace class exposing Registry, Matcher, Definition. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.manager.StepDefinitionManager` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - decorator_builder: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `StepDefinitionManager`
        - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `StepDefinitionManager`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `StepDefinitionManager`
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `StepDefinitionManager`
        - src/pytest_bdd/steps/__init__.py: imports or references `StepDefinitionManager`

    State and side effects:
        mutates Registry, Matcher, Definition, StepProtocol, NamespaceStepRegistryProtocol; depends on
        pytest_bdd.parsers.StepParser.

    Invariants:
        - `pytest_bdd.steps.manager.StepDefinitionManager` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    Registry = Registry
    Matcher = Matcher
    Definition = Definition
    StepProtocol = StepProtocol
    NamespaceStepRegistryProtocol = StepRegistryProtocol

    @staticmethod
    def decorator_builder(  # noqa: PLR0913, PLR0917
        step_type: str | PickleStepType | None,
        step_parserlike: object,
        anonymous_group_names: Iterable[str] | None = None,
        converters: Mapping[str, ConverterT] | None = None,
        target_fixture: str | None = None,
        target_fixtures: Sequence[str] | None = None,
        params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa:FBT002
        param_defaults: Mapping[str, object] | None = None,
        *,
        liberal: bool | None = None,
        stacklevel: int = 2,
    ) -> StepDecorator:
        """
        Step decorator for the type and the name.

        Args:
            step_type: Step type (CONTEXT, ACTION or OUTCOME).
            step_parserlike: Step name as in the feature file.
            anonymous_group_names: Grant names for anonymous groups of parserlike
            converters: Optional step arguments converters mapping
            target_fixture: Optional fixture name to replace by step definition
            target_fixtures: Target fixture names to be replaced by steps definition function.
            params_fixtures_mapping: Step parameters would be injected as fixtures
            param_defaults: Default parameters for step definition
            liberal: Could step definition be used with other keywords
            stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture

        Returns:
            Decorator function for the step.

        Responsibility:
            Step decorator for the type and the name. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.manager.StepDefinitionManager.decorator_builder`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - decorator: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `decorator_builder`
            - src/pytest_bdd/steps/__init__.py: imports or references `decorator_builder`
            - src/pytest_bdd/steps/decorators.py: imports or references `decorator_builder`

        State and side effects:
            mutates converters, param_defaults, resolved_target_fixtures, step_definition, step_definitions; depends on
            pytest_bdd.parsers.StepParser.

        Invariants:
            - `pytest_bdd.steps.manager.StepDefinitionManager.decorator_builder` keeps its documented import path,
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
        converters = dict(converters or {})
        param_defaults = dict(param_defaults or {})
        if target_fixture is not None and target_fixtures is not None:
            warnings.warn(
                PytestBDDStepDefinitionWarning("Both target_fixture and target_fixtures are specified"),
                stacklevel=2,
            )
        resolved_target_fixtures: list[str] = list(
            OrderedSet(
                [
                    *([target_fixture] if target_fixture is not None else []),
                    *(target_fixtures if target_fixtures is not None else []),
                ],
            ),
        )

        def decorator(step_func: StepFunc) -> StepFunc:
            """
            Apply step decorator to function.

            Args:
                step_func: Step definition function

            Returns:
                Decorated step function.

            Responsibility:
                Apply step decorator to function. It directly owns the observable contract, local decisions, and
                maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
                distinguish owned work from collaborators before editing.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.steps.manager.StepDefinitionManager.decorator_builder.decorator` because it keeps the
                nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - bool: collaborator call used by this boundary
                - getattr: collaborator call used by this boundary
                - Definition: collaborator call used by this boundary
                - StepParser.build: collaborator call used by this boundary
                - cast: collaborator call used by this boundary
                - setdefaultattr: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/hook.py: imports or references `decorator`
                - src/pytest_bdd/plugin/code_generator/rendering.py: imports or references `decorator`
                - src/pytest_bdd/plugin/code_generator/rewrite.py: imports or references `decorator`
                - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references `decorator`
                - src/pytest_bdd/scenario.py: imports or references `decorator`

            State and side effects:
                mutates step_definition, step_definitions, converted_name, namespace; depends on
                pytest_bdd.parsers.StepParser.

            Invariants:
                - `pytest_bdd.steps.manager.StepDefinitionManager.decorator_builder.decorator` keeps its documented
                  import path, ownership boundary, and observable behavior stable for callers.

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
            from pytest_bdd.parsers import StepParser  # noqa: PLC0415

            step_definition = Definition(
                func=step_func,
                type_=step_type,
                parser=StepParser.build(step_parserlike),
                anonymous_group_names=anonymous_group_names,
                converters=converters,
                params_fixtures_mapping=params_fixtures_mapping,
                param_defaults=param_defaults,
                target_fixtures=resolved_target_fixtures,
                liberal=liberal,
                not_implemented=bool(getattr(step_func, "__pytest_bdd_not_implemented__", False)),
                tolerant=bool(getattr(step_func, "__pytest_bdd_tolerant__", False)),
            )

            step_definitions = cast(
                "set[Definition]",
                setdefaultattr(step_func, "__pytest_bdd_step_definitions__", value_factory=set),
            )
            step_definitions.add(step_definition)

            # Allow step function to have same names, so injecting same steps with generated names into module scope
            converted_name = format_as_python_identifier(f"step_{step_type or ''}_{step_parserlike}_{uuid4()}")
            namespace = get_caller_module_locals(stacklevel=stacklevel)
            namespace[converted_name] = step_func

            for fixture_name in step_definition.fixtures_mapped_from_step_definition:
                if fixture_name.startswith("pytest_"):
                    continue
                namespace.setdefault(fixture_name, _none_fixture(fixture_name))

            return step_func

        return decorator


def _none_fixture(name: str) -> object:
    """
    Create a placeholder fixture for step-injected values.

    Returns:
        Pytest fixture function returning ``None``.

    Responsibility:
        Create a placeholder fixture for step-injected values. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.steps.manager._none_fixture` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - placeholder: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/steps/__init__.py: imports or references `_none_fixture`
        - src/pytest_bdd/steps/decorators.py: imports or references `_none_fixture`

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
        #arch-eval:locational_stability=3
    """

    @pytest.fixture(name=name)  # type: ignore[untyped-decorator]  # pytest fixture decorator is intentionally untyped
    def placeholder() -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.steps.manager._none_fixture.placeholder` owns documented
            function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.steps.manager._none_fixture.placeholder` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - pytest.fixture: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/html_report.py: imports or references `placeholder`
            - src/pytest_bdd/steps/__init__.py: imports or references `placeholder`
            - src/pytest_bdd/steps/decorators.py: imports or references `placeholder`

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
        return

    return placeholder
