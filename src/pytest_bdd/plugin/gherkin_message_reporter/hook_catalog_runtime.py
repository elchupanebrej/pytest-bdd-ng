"""
Provide hook catalog runtime helpers.

Responsibility:
    Provide hook catalog runtime helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime` because
    it keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _evaluate_hook_expression: owns nested behavior below this boundary
    - _ScenarioTag: owns nested behavior below this boundary
    - _PickleWithTags: owns nested behavior below this boundary
    - HookCatalogService: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `hook_catalog_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `hook_catalog_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
      `hook_catalog_runtime`

State and side effects:
    mutates logger, mark_expression, tag_expression, scenario_tags, name; depends on __future__.annotations, logging,
    inspect.getfile, inspect.signature, pathlib.Path.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

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

import logging
from inspect import getfile, signature
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import pytest
from cucumber_messages import (
    Envelope as Message,  # upstream type stubs missing this attribute
)
from cucumber_messages import Hook, HookType, JavaMethod, JavaStackTraceElement, Location, SourceReference

from pytest_bdd.compatibility.path import resolvepath
from pytest_bdd.compatibility.pytest import make_mark
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


def _evaluate_hook_expression(
    *,
    kind: str,
    expression: str,
    request: FixtureRequest,
    pickle: _PickleWithTags,
) -> bool:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime._evaluate_hook_expression` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime._evaluate_hook_expression` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - bool: collaborator call used by this boundary
        - MarksTagExpression.parse: collaborator call used by this boundary
        - mark_expression.evaluate: collaborator call used by this boundary
        - list: collaborator call used by this boundary
        - request.node.iter_markers: collaborator call used by this boundary
        - GherkinTagExpression.parse: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_evaluate_hook_expression`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `_evaluate_hook_expression`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `_evaluate_hook_expression`

    State and side effects:
        mutates mark_expression, tag_expression, scenario_tags.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime._evaluate_hook_expression` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

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
    if kind == "mark":
        mark_expression = MarksTagExpression.parse(expression)
        return bool(mark_expression.evaluate(list(request.node.iter_markers())))
    if kind == "tag":
        tag_expression = GherkinTagExpression.parse(expression)
        scenario_tags = [make_mark(tag.name) for tag in pickle.tags]
        return bool(tag_expression.evaluate(scenario_tags))
    return False


class _ScenarioTag(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime._ScenarioTag`
        owns documented class behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime._ScenarioTag` because it keeps the nearest
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
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_ScenarioTag`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `_ScenarioTag`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `_ScenarioTag`

    State and side effects:
        mutates name.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime._ScenarioTag` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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

    name: str


class _PickleWithTags(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime._PickleWithTags` owns documented class
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime._PickleWithTags` because it keeps the nearest
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
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_PickleWithTags`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `_PickleWithTags`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `_PickleWithTags`

    State and side effects:
        mutates tags.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime._PickleWithTags` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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

    tags: list[_ScenarioTag]


class HookCatalogService(ReporterServiceBase):
    """
    Represent hook catalog service state.

    Yields:
        Generated values.

    Responsibility:
        Represent hook catalog service state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime.HookCatalogService` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - pytest_fixture_setup: owns nested behavior below this boundary
        - _iter_matching_hook_registrations: owns nested behavior below this boundary
        - _hook_expression_matches: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `HookCatalogService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `HookCatalogService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `HookCatalogService`

    State and side effects:
        mutates plugin_suffix, self.lifecycle_service, func, func_id, config.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime.HookCatalogService` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

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

    plugin_suffix = "fixtures"

    def __init__(self, reporter: GherkinMessageReporter, *, lifecycle_service: LifecycleService) -> None:
        """
        Initialize the hook catalog service.

        Responsibility:
            Initialize the hook catalog service. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime.HookCatalogService.__init__` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

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
            mutates self.lifecycle_service.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime.HookCatalogService.__init__` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        super().__init__(reporter)
        self.lifecycle_service = lifecycle_service

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef: FixtureDef, request: FixtureRequest) -> Iterator[None]:
        """
        Handle the pytest fixture setup pytest hook.

        Yields:
            Generated values.

        Responsibility:
            Handle the pytest fixture setup pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime.HookCatalogService.pytest_fixture_setup`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - id: collaborator call used by this boundary
            - hasattr: collaborator call used by this boundary
            - self.reporter.hook_registry.add: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `pytest_fixture_setup`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_fixture_setup`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `pytest_fixture_setup`

        State and side effects:
            mutates func, func_id, config, hook_name, hook_expression.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime.HookCatalogService.pytest_fixture_setup`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime.HookCatalogService._iter_matching_hook_registrations`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime.HookCatalogService._iter_matching_hook_registrations`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.reporter.hook_registration_registry.values: collaborator call used by this boundary
            - self._hook_expression_matches: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `_iter_matching_hook_registrations`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_iter_matching_hook_registrations`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `_iter_matching_hook_registrations`

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
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime.HookCatalogService._hook_expression_matches`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime.HookCatalogService._hook_expression_matches`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - expression.strip: collaborator call used by this boundary
            - _evaluate_hook_expression: collaborator call used by this boundary
            - logger.warning: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_hook_expression_matches`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_hook_expression_matches`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `_hook_expression_matches`

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
        if not expression.strip():
            return True

        try:
            return _evaluate_hook_expression(
                kind=kind,
                expression=expression,
                request=request,
                pickle=pickle,
            )
        except ValueError:
            logger.warning("Failed to evaluate hook expression %r", expression, exc_info=True)
            return False
