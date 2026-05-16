"""StepDefinitionManager namespace class for backward compatibility."""

from __future__ import annotations

import warnings
from collections.abc import Iterable, Mapping, Sequence  # noqa: TC003
from typing import cast
from uuid import uuid4

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
from pytest_bdd.steps.registry import NamespaceStepRegistryProtocol, Registry, StepProtocol
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
    """

    Registry = Registry
    Matcher = Matcher
    Definition = Definition
    StepProtocol = StepProtocol
    NamespaceStepRegistryProtocol = NamespaceStepRegistryProtocol

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
            )

            step_definitions = cast(
                "set[Definition]",
                setdefaultattr(step_func, "__pytest_bdd_step_definitions__", value_factory=set),
            )
            step_definitions.add(step_definition)

            # Allow step function to have same names, so injecting same steps with generated names into module scope
            converted_name = format_as_python_identifier(f"step_{step_type or ''}_{step_parserlike}_{uuid4()}")
            get_caller_module_locals(stacklevel=stacklevel)[converted_name] = step_func

            return step_func

        return decorator
