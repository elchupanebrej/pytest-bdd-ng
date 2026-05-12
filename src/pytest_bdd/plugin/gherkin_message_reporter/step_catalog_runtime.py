"""Provide step catalog runtime helpers."""

from __future__ import annotations

import logging
from contextlib import suppress
from inspect import getfile, signature
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]
from cucumber_messages import (
    Group,
    JavaMethod,
    JavaStackTraceElement,
    Location,
    ParameterType,
    Pickle,
    SourceReference,
    StepMatchArgument,
    StepMatchArgumentsList,
    TestCase,
    TestStep,
)
from returns.maybe import Nothing

from pytest_bdd.compatibility.path import resolvepath
from pytest_bdd.compatibility.pytest import Config, FixtureLookupError, FixtureRequest
from pytest_bdd.model.run import Run
from pytest_bdd.parsers import _CucumberExpression
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.util.inspect_extra import get_first_source_line
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.toolz_extra import deepattrgetter

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from cucumber_expressions.group import Group as CucumberExpressionGroup
    from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

    from pytest_bdd.compatibility.pytest import Item
    from pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime import HookCatalogService
    from pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime import LifecycleService
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter


logger = logging.getLogger(__name__)


class StepCatalogService(ReporterServiceBase):
    """
    Represent step catalog service state.

    Yields:
        Generated values.

    """

    plugin_suffix = "steps"

    def __init__(
        self,
        reporter: GherkinMessageReporter,
        *,
        lifecycle_service: LifecycleService,
        hook_catalog_service: HookCatalogService,
    ) -> None:
        """Initialize the step catalog service."""
        super().__init__(reporter)
        self.lifecycle_service = lifecycle_service
        self.hook_catalog_service = hook_catalog_service

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_setup(self, item: Item) -> Iterator[None]:  # noqa: PLR0914
        """
        Handle the pytest runtest setup pytest hook.

        Yields:
            Generated values.

        """
        yield
        if self.reporter.is_disabled:
            return

        session = item.session
        config: Config = cast("Config", session.config)
        hook_handler = cast("Config", config).hook
        request = item._request  # noqa: SLF001
        run = Run.from_stash(request.config.stash)
        scenario_run = run.active_scenario_run
        if scenario_run is None:
            logger.warning(
                "Execution context unavailable during pytest_runtest_setup; "
                "skipping context-backed correlation writes.",
            )
            return
        gherkin_document, pickle = self.lifecycle_service._resolve_gherkin_document_and_pickle(run=run)  # noqa: SLF001
        if gherkin_document is None or pickle is None:
            logger.warning("Execution context does not carry runtime feature/pickle during pytest_runtest_setup.")
            return
        runtime_pickle = cast("Pickle", pickle)

        self._report_step_definitions(config, request)
        self._register_parameter_types(config, request)
        reporting_state = run.reporting_state
        test_steps = []
        previous_step = None
        reporting_state.runtime_step_to_pickle_step_id.clear()

        test_steps.extend(
            [
                TestStep(
                    id=next(IdGenerator.from_stash(cast("Config", config).stash)),
                    hook_id=hook_registration.hook_message_id,
                )
                for hook_registration in self.hook_catalog_service._iter_matching_hook_registrations(  # noqa: SLF001
                    request=request,
                    pickle=runtime_pickle,
                )
            ],
        )

        for step in runtime_pickle.steps:
            try:
                scenario_run.step_object = step
                scenario_run.previous_step_object = previous_step
                step_definition = hook_handler.pytest_bdd_match_step_definition_to_step(
                    request=request,
                    run=run,
                )
            except StepDefinitionManager.Matcher.MatchNotFoundError:  # noqa: PERF203
                pass
            else:
                step_match_arguments_lists = self._build_step_match_arguments_lists(
                    request=request,
                    step_definition=step_definition,
                    step_text=step.text,
                )
                test_step = TestStep(
                    id=next(IdGenerator.from_stash(cast("Config", config).stash)),
                    pickle_step_id=step.id,
                    step_definition_ids=[step_definition.as_message(config).id],
                    **(
                        {"step_match_arguments_lists": step_match_arguments_lists} if step_match_arguments_lists else {}
                    ),
                )
                test_steps.append(test_step)
                run.map_runtime_step_to_test_step_id(
                    pickle_step=step,
                    test_step_id=test_step.id,
                )
            finally:
                previous_step = step

        resolved_run_started_id = Run.from_stash(cast("Config", config).stash).reporting_state.run_started_id
        test_case = TestCase(
            id=next(IdGenerator.from_stash(cast("Config", config).stash)),
            pickle_id=runtime_pickle.id,
            test_steps=test_steps,
            **({"test_run_started_id": resolved_run_started_id} if resolved_run_started_id is not None else {}),
        )
        reporting_state.active_test_case_id = test_case.id
        self.lifecycle_service._emit_envelope(  # noqa: SLF001
            cast("Config", config),
            Message(test_case=test_case),
        )

    def _report_step_definitions(self, config: Config, request: FixtureRequest) -> None:
        try:
            step_registry = request.getfixturevalue("step_registry")
        except (FixtureLookupError, AssertionError):
            return
        seen_steps: set[int] = set()
        while step_registry is not None:
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    seen_steps.add(id(step_definition))
                    step_definition_message = step_definition.as_message(config=config)
                    if step_definition_message.id in self.reporter._emitted_step_definition_ids:  # noqa: SLF001
                        continue
                    self.reporter._emitted_step_definition_ids.add(step_definition_message.id)  # noqa: SLF001
                    self.lifecycle_service._emit_envelope(  # noqa: SLF001
                        config,
                        Message(step_definition=step_definition_message),
                    )
            step_registry = step_registry.parent

    def report_step_definitions(self, config: Config, request: FixtureRequest) -> None:
        """Handle report step definitions."""
        self._report_step_definitions(config, request)

    @staticmethod
    def _build_step_match_arguments_lists(
        *,
        request: FixtureRequest,
        step_definition: StepDefinitionManager.Definition,
        step_text: str,
    ) -> list[StepMatchArgumentsList]:
        parser = step_definition.parser

        if isinstance(parser, _CucumberExpression):
            matches = parser.rebuild_expression_in_test_context(request).match(step_text)
            if matches:

                def build_group(group: CucumberExpressionGroup) -> Group:
                    return Group(
                        **({"start": group.start} if group.start is not None else {}),
                        **({"value": group.value} if group.value is not None else {}),
                        children=[build_group(child) for child in (group.children or [])],
                    )

                step_match_arguments = []
                for i, match in enumerate(matches):
                    anon_groups = (
                        list(step_definition.anonymous_group_names) if step_definition.anonymous_group_names else []
                    )
                    parameter_name = anon_groups[i] if i < len(anon_groups) else None
                    step_match_arguments.append(
                        StepMatchArgument(
                            group=build_group(match.group),
                            **({"parameter_type_name": str(parameter_name)} if parameter_name is not None else {}),
                        ),
                    )
                return [StepMatchArgumentsList(step_match_arguments=step_match_arguments)]

        parsed_arguments = (
            step_definition.parser.parse_arguments(
                request,
                step_text,
                anonymous_group_names=step_definition.anonymous_group_names,
            )
            or {}
        )
        if not parsed_arguments:
            return []

        parsed_step_match_arguments: list[StepMatchArgument] = []
        for parameter_name, parameter_value in parsed_arguments.items():
            parameter_value_text = "" if parameter_value is None else str(parameter_value)
            parameter_start_index = step_text.find(parameter_value_text) if parameter_value_text else -1
            group = Group(
                **({"start": parameter_start_index} if parameter_start_index >= 0 else {}),
                **({"value": parameter_value_text} if parameter_value_text else {}),
            )
            parsed_step_match_arguments.append(
                StepMatchArgument(
                    group=group,
                    **({"parameter_type_name": str(parameter_name)} if parameter_name is not None else {}),
                ),
            )
        return [StepMatchArgumentsList(step_match_arguments=parsed_step_match_arguments)]

    @staticmethod
    def _build_parameter_type_source_reference(config: Config, parameter_type: object) -> SourceReference | None:
        transformer = getattr(parameter_type, "transformer", None)
        if transformer is None:
            return Nothing.value_or(None)

        with suppress(OSError, TypeError, ValueError):
            source_file = getfile(transformer)
            source_line = get_first_source_line(transformer)
            parameter_types = list(signature(transformer).parameters.keys())
            return SourceReference(
                uri=Path(resolvepath(source_file, config.rootpath)).as_uri(),
                location=Location(line=source_line, column=1),
                java_method=JavaMethod(
                    class_name=str(getattr(transformer, "__module__", "pytest_bdd.parameter_type")),
                    method_name=str(getattr(transformer, "__name__", "transformer")),
                    method_parameter_types=parameter_types,
                ),
                java_stack_trace_element=JavaStackTraceElement(
                    class_name=str(getattr(transformer, "__module__", "pytest_bdd.parameter_type")),
                    file_name=Path(source_file).name,
                    method_name=str(getattr(transformer, "__name__", "transformer")),
                ),
            )
        return Nothing.value_or(None)

    def _register_parameter_types(self, config: Config, request: FixtureRequest) -> None:
        try:
            step_registry = request.getfixturevalue("step_registry")
        except (FixtureLookupError, AssertionError):
            return
        seen_steps: set[int] = set()
        while step_registry is not None:
            for step_definition in step_registry:
                if id(step_definition) not in seen_steps:
                    parameter_type_registry_getter_candidate = deepattrgetter(
                        "_get_parameter_type_registry",
                        default=None,
                    )(step_definition.parser)[0]

                    if parameter_type_registry_getter_candidate is None:
                        continue

                    parameter_type_registry_getter = cast(
                        "Callable[[FixtureRequest], ParameterTypeRegistry]",
                        parameter_type_registry_getter_candidate,
                    )
                    parameter_type_registry = parameter_type_registry_getter(request)
                    parameter_types = {
                        id(parameter_type): parameter_type for parameter_type in parameter_type_registry.parameter_types
                    }
                    not_yet_registered_parameter_types = {
                        key: parameter_type
                        for key, parameter_type in parameter_types.items()
                        if key not in self.reporter.parameter_type_registry
                    }

                    for parameter_type in not_yet_registered_parameter_types.values():
                        parameter_type_source_reference = self._build_parameter_type_source_reference(
                            cast("Config", config),
                            parameter_type,
                        )
                        self.lifecycle_service._emit_envelope(  # noqa: SLF001
                            config,
                            Message(
                                parameter_type=ParameterType(
                                    name=parameter_type.name,
                                    regular_expressions=parameter_type.regexps,
                                    prefer_for_regular_expression_match=parameter_type._prefer_for_regexp_match,  # noqa: SLF001
                                    use_for_snippets=parameter_type._use_for_snippets,  # noqa: SLF001
                                    id=next(IdGenerator.from_stash(cast("Config", config).stash)),
                                    **(
                                        {"source_reference": parameter_type_source_reference}
                                        if parameter_type_source_reference is not None
                                        else {}
                                    ),
                                ),
                            ),
                        )
                    self.reporter.parameter_type_registry |= not_yet_registered_parameter_types.keys()
            step_registry = step_registry.parent
