"""Provide hook catalog runtime helpers."""

from __future__ import annotations

import logging
from inspect import getfile, signature
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import pytest
from _pytest.mark import Mark  # noqa: PLC2701
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]
from cucumber_messages import Hook, HookType, JavaMethod, JavaStackTraceElement, Location, SourceReference

from pytest_bdd.compatibility.path import resolvepath
from pytest_bdd.plugin.gherkin_message_reporter.runtime_support import HookRegistration
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase
from pytest_bdd.tag_expression import GherkinTagExpression, MarksTagExpression
from pytest_bdd.util.inspect_extra import get_first_source_line
from pytest_bdd.util.other import IdGenerator

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytest_bdd.compatibility.pytest import Config, FixtureDef, FixtureRequest
    from pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime import LifecycleService
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter

logger = logging.getLogger(__name__)


class _ScenarioTag(Protocol):
    name: str


class _PickleWithTags(Protocol):
    tags: list[_ScenarioTag]


class HookCatalogService(ReporterServiceBase):
    """
    Represent hook catalog service state.

    Yields:
        Generated values.

    """

    plugin_suffix = "fixtures"

    def __init__(self, reporter: GherkinMessageReporter, *, lifecycle_service: LifecycleService) -> None:
        """Initialize the hook catalog service."""
        super().__init__(reporter)
        self.lifecycle_service = lifecycle_service

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef: FixtureDef, request: FixtureRequest) -> Iterator[None]:
        """
        Handle the pytest fixture setup pytest hook.

        Yields:
            Generated values.

        """
        if self.reporter.is_disabled:
            yield
            return
        func = fixturedef.func
        func_id = id(func)

        if func_id in self.reporter.hook_registry:
            yield
            return

        config = request.config

        if hasattr(func, "__pytest_bdd_is_hook__"):
            self.reporter.hook_registry.add(func_id)

            hook_name = getattr(func, "__pytest_bdd_hook_name__", None)
            hook_expression = getattr(func, "__pytest_bdd_hook_expression__", None)
            hook_kind = getattr(func, "__pytest_bdd_hook_kind__", "tag")
            hook_conjunction = getattr(func, "__pytest_bdd_hook_conjunction__", "before")
            hook_type = {
                "before": HookType.before_test_case,
                "after": HookType.after_test_case,
                "around": HookType.before_test_case,
            }.get(str(hook_conjunction))
            parameter_types = list(signature(func).parameters.keys())
            source_file = getfile(func)
            source_line = get_first_source_line(func)

            hook_message_id = next(IdGenerator.from_stash(cast("Config", config).stash))
            hook_message = Hook(
                id=hook_message_id,
                **({"name": hook_name} if hook_name is not None else {}),
                source_reference=SourceReference(
                    uri=Path(resolvepath(source_file, config.rootpath)).as_uri(),
                    location=Location(line=source_line, column=1),
                    java_method=JavaMethod(
                        class_name=str(getattr(func, "__module__", "pytest_bdd.hook")),
                        method_name=str(getattr(func, "__name__", "hook")),
                        method_parameter_types=parameter_types,
                    ),
                    java_stack_trace_element=JavaStackTraceElement(
                        class_name=str(getattr(func, "__module__", "pytest_bdd.hook")),
                        file_name=Path(source_file).name,
                        method_name=str(getattr(func, "__name__", "hook")),
                    ),
                ),
                **({"tag_expression": hook_expression} if hook_expression is not None else {}),
                **({"type": hook_type} if hook_type is not None else {}),
            )
            self.reporter.hook_registration_registry[func_id] = HookRegistration(
                hook_message_id=hook_message_id,
                expression="" if hook_expression is None else str(hook_expression),
                kind=str(hook_kind),
            )

            self.lifecycle_service._emit_envelope(config, Message(hook=hook_message))  # noqa: SLF001

        yield

    def _iter_matching_hook_registrations(
        self,
        request: FixtureRequest,
        pickle: _PickleWithTags,
    ) -> Iterator[HookRegistration]:
        for hook_registration in self.reporter.hook_registration_registry.values():
            if self._hook_expression_matches(
                request=request,
                pickle=pickle,
                expression=hook_registration.expression,
                kind=hook_registration.kind,
            ):
                yield hook_registration

    @staticmethod
    def _hook_expression_matches(
        *,
        request: FixtureRequest,
        pickle: _PickleWithTags,
        expression: str,
        kind: str,
    ) -> bool:
        if not expression.strip():
            return True

        try:
            if kind == "mark":
                mark_expression = MarksTagExpression.parse(expression)
                return bool(mark_expression.evaluate(list(request.node.iter_markers())))
            if kind == "tag":
                tag_expression = GherkinTagExpression.parse(expression)
                scenario_tags = []
                for tag in pickle.tags:
                    mark = Mark(tag.name, args=(), kwargs={}, _ispytest=True)
                    scenario_tags.append(mark)
                return bool(tag_expression.evaluate(scenario_tags))
        except Exception:  # noqa: BLE001
            logger.warning("Failed to evaluate hook expression %r", expression, exc_info=True)
            return False

        return False
