"""
Provide scenario runtime helpers.

Responsibility:
    Provide scenario runtime helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - ScenarioService: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `scenario_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `scenario_runtime`

State and side effects:
    mutates config, reporting_state, step, test_case_started_id, test_step_id; depends on __future__.annotations, re,
    typing.TYPE_CHECKING, typing.cast, cucumber_expressions.errors.UndefinedParameterTypeError.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, cast

from cucumber_expressions.errors import UndefinedParameterTypeError
from cucumber_messages import (
    Duration,
    Snippet,
    Suggestion,
    TestCaseFinished,
    TestCaseStarted,
    TestStepFinished,
    TestStepResult,
    TestStepResultStatus,
    TestStepStarted,
    Timestamp,
    UndefinedParameterType,
)
from cucumber_messages import (
    Envelope as Message,  # upstream type stubs missing this attribute
)
from cucumber_messages import Exception as CucumberException

from pytest_bdd.model.run_access import require_step_object
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase
from pytest_bdd.util.other import IdGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytest_bdd.compatibility.pytest import Config, FixtureRequest
    from pytest_bdd.model.run import Run
    from pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime import LifecycleService
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter
    from pytest_bdd.plugin.gherkin_message_reporter.transport_runtime import TransportService
    from pytest_bdd.steps import Definition


class ScenarioService(ReporterServiceBase):
    """
    Represent scenario service state.

    Responsibility:
        Represent scenario service state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _step_keyword_to_decorator: owns nested behavior below this boundary
        - _build_suggestion_snippet: owns nested behavior below this boundary
        - _extract_undefined_parameter_type: owns nested behavior below this boundary
        - pytest_bdd_step_func_lookup_error: owns nested behavior below this boundary
        - pytest_bdd_before_scenario: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `ScenarioService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `ScenarioService`

    State and side effects:
        mutates config, reporting_state, step, test_case_started_id, test_step_id.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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

    plugin_suffix = "scenario"

    def __init__(
        self,
        reporter: GherkinMessageReporter,
        *,
        lifecycle_service: LifecycleService,
        transport_service: TransportService,
    ) -> None:
        """
        Initialize the scenario service.

        Responsibility:
            Initialize the scenario service. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.__init__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

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
            mutates self.lifecycle_service, self.transport_service.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.__init__` keeps its
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
        self.transport_service = transport_service

    @staticmethod
    def _step_keyword_to_decorator(keyword: str | None) -> str:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._step_keyword_to_decorator`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._step_keyword_to_decorator`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - normalized.startswith: collaborator call used by this boundary
            - strip.lower: collaborator call used by this boundary
            - strip: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `_step_keyword_to_decorator`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_step_keyword_to_decorator`

        State and side effects:
            mutates normalized.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._step_keyword_to_decorator`
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
            #arch-eval:locational_stability=3
        """
        normalized = (keyword or "").strip().lower()
        if normalized.startswith("when"):
            return "when"
        if normalized.startswith("then"):
            return "then"
        return "given"

    def _build_suggestion_snippet(self, step: object) -> str:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._build_suggestion_snippet` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._build_suggestion_snippet`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - self._step_keyword_to_decorator: collaborator call used by this boundary
            - str.replace: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `_build_suggestion_snippet`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_build_suggestion_snippet`

        State and side effects:
            mutates decorator, step_text.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._build_suggestion_snippet`
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
            #arch-eval:locational_stability=3
        """
        decorator = self._step_keyword_to_decorator(getattr(step, "keyword", None))
        step_text = str(getattr(step, "text", "")).replace('"', '\\"')
        return f'@{decorator}("{step_text}")\ndef step_impl():\n    raise NotImplementedError\n'

    @staticmethod
    def _extract_undefined_parameter_type(
        *,
        exception: Exception,
        fallback_expression: str,
    ) -> tuple[str, str] | None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._extract_undefined_parameter_type`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._extract_undefined_parameter_type`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - len: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - re.search: collaborator call used by this boundary
            - matched_name.group: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `_extract_undefined_parameter_type`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_extract_undefined_parameter_type`

        State and side effects:
            mutates explicit, expression, parameter_name, message, matched_name.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._extract_undefined_parameter_type`
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
            #arch-eval:locational_stability=3
        """
        explicit = getattr(exception, "undefined_parameter_type", None)
        if isinstance(explicit, tuple) and len(explicit) == 2:  # noqa: PLR2004
            return str(explicit[0]), str(explicit[1])

        for candidate in (exception, getattr(exception, "__cause__", None)):
            if isinstance(candidate, UndefinedParameterTypeError):
                expression = str(candidate.args[1]) if len(candidate.args) > 1 else fallback_expression
                parameter_name = str(candidate.args[2]) if len(candidate.args) > 2 else ""  # noqa: PLR2004
                if parameter_name:
                    return expression, parameter_name

            message = str(candidate or "")
            matched_name = re.search(r"Undefined parameter type \\{([^}]+)\\}", message)
            if matched_name:
                return fallback_expression, matched_name.group(1)

        return None

    def pytest_bdd_step_func_lookup_error(
        self,
        request: FixtureRequest,
        run: Run,
        exception: Exception,
    ) -> None:
        """
        Handle the pytest bdd step func lookup error pytest hook.

        Responsibility:
            Handle the pytest bdd step func lookup error pytest hook. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_step_func_lookup_error`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - self.lifecycle_service._emit_envelope: collaborator call used by this boundary
            - Message: collaborator call used by this boundary
            - require_step_object: collaborator call used by this boundary
            - next: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `pytest_bdd_step_func_lookup_error`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_bdd_step_func_lookup_error`

        State and side effects:
            mutates step, config, pickle_step_id, suggestion_id, suggestion.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_step_func_lookup_error`
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
            #arch-eval:locational_stability=3
        """
        if self.reporter.is_disabled:
            return
        step = require_step_object(run, hook_name="pytest_bdd_step_func_lookup_error")
        config = request.config
        pickle_step_id = getattr(step, "id", None)
        if pickle_step_id is None:
            return

        suggestion_id = next(IdGenerator.from_stash(cast("Config", config).stash))
        suggestion = Suggestion(
            id=suggestion_id,
            pickle_step_id=str(pickle_step_id),
            snippets=[Snippet(code=self._build_suggestion_snippet(step), language="python")],
        )
        self.lifecycle_service._emit_envelope(config, Message(suggestion=suggestion))  # noqa: SLF001

        undefined_parameter = self._extract_undefined_parameter_type(
            exception=exception,
            fallback_expression=str(getattr(step, "text", "")),
        )
        if undefined_parameter is not None:
            expression, parameter_name = undefined_parameter
            self.lifecycle_service._emit_envelope(  # noqa: SLF001
                config,
                Message(
                    undefined_parameter_type=UndefinedParameterType(
                        expression=expression,
                        name=parameter_name,
                    ),
                ),
            )

    def pytest_bdd_before_scenario(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> None:
        """
        Handle the pytest bdd before scenario pytest hook.

        Responsibility:
            Handle the pytest bdd before scenario pytest hook. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_before_scenario`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - self.transport_service._current_reporting_worker_id: collaborator call used by this boundary
            - TestCaseStarted: collaborator call used by this boundary
            - next: collaborator call used by this boundary
            - IdGenerator.from_stash: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `pytest_bdd_before_scenario`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_bdd_before_scenario`

        State and side effects:
            mutates config, reporting_state, test_case_id, attempt_index, worker_id.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_before_scenario`
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
            #arch-eval:locational_stability=3
        """
        if self.reporter.is_disabled:
            return
        config = request.config
        reporting_state = run.reporting_state
        test_case_id = reporting_state.active_test_case_id
        if test_case_id is None:
            return
        attempt_index = getattr(request.node, "execution_count", 0)
        worker_id = self.transport_service._current_reporting_worker_id(cast("Config", config))  # noqa: SLF001
        test_case_start = TestCaseStarted(
            attempt=attempt_index,
            id=next(IdGenerator.from_stash(cast("Config", config).stash)),
            test_case_id=test_case_id,
            worker_id=worker_id,
            timestamp=self.lifecycle_service.get_timestamp(),
        )
        reporting_state.active_test_case_started_id = test_case_start.id
        reporting_state.scenario_attempt_context = {
            "scenario_attempt_id": test_case_start.id,
            "attempt_index": attempt_index,
            "worker_id": worker_id,
        }
        self.lifecycle_service._emit_envelope(  # noqa: SLF001
            config,
            Message(test_case_started=test_case_start),
        )

    def pytest_bdd_after_scenario(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> None:
        """
        Handle the pytest bdd after scenario pytest hook.

        Responsibility:
            Handle the pytest bdd after scenario pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_after_scenario`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.lifecycle_service._emit_envelope: collaborator call used by this boundary
            - Message: collaborator call used by this boundary
            - TestCaseFinished: collaborator call used by this boundary
            - self.lifecycle_service.get_timestamp: collaborator call used by this boundary
            - reporting_state.reset_scenario_scope: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `pytest_bdd_after_scenario`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_bdd_after_scenario`

        State and side effects:
            mutates reporting_state, test_case_started_id, config.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_after_scenario`
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
            #arch-eval:locational_stability=3
        """
        if self.reporter.is_disabled:
            return
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config
        self.lifecycle_service._emit_envelope(  # noqa: SLF001
            config,
            Message(
                test_case_finished=TestCaseFinished(
                    test_case_started_id=test_case_started_id,
                    timestamp=self.lifecycle_service.get_timestamp(),
                    will_be_retried=False,
                ),
            ),
        )
        reporting_state.reset_scenario_scope()

    @staticmethod
    def _duration_between(start_timestamp: Timestamp | None, finish_timestamp: Timestamp) -> Duration:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._duration_between` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._duration_between` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Duration: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_duration_between`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_duration_between`

        State and side effects:
            mutates duration_total_nanos, duration_seconds, duration_nanos.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService._duration_between` keeps its
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
            #arch-eval:locational_stability=3
        """
        if start_timestamp is None:
            return Duration(seconds=0, nanos=0)

        duration_total_nanos = (finish_timestamp.seconds * 10**9 + finish_timestamp.nanos) - (
            start_timestamp.seconds * 10**9 + start_timestamp.nanos
        )
        duration_seconds = duration_total_nanos // 10**9
        duration_nanos = duration_total_nanos - duration_seconds * 10**9
        return Duration(seconds=duration_seconds, nanos=duration_nanos)

    def pytest_bdd_before_step(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: object,  # noqa: ARG002
    ) -> None:
        """
        Handle the pytest bdd before step pytest hook.

        Responsibility:
            Handle the pytest bdd before step pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_before_step` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - require_step_object: collaborator call used by this boundary
            - self.lifecycle_service._resolve_test_step_id_for_runtime_step: collaborator call used by this boundary
            - self.lifecycle_service.get_timestamp: collaborator call used by this boundary
            - TestStepStarted: collaborator call used by this boundary
            - self.lifecycle_service._emit_envelope: collaborator call used by this boundary
            - Message: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `pytest_bdd_before_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_bdd_before_step`

        State and side effects:
            mutates step, reporting_state, test_case_started_id, config, test_step_id.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_before_step` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

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
        if self.reporter.is_disabled:
            return
        step = require_step_object(run, hook_name="pytest_bdd_before_step")
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config

        test_step_id = self.lifecycle_service._resolve_test_step_id_for_runtime_step(request=request, step=step)  # noqa: SLF001
        if test_step_id is None:
            return

        step_start_timestamp = self.lifecycle_service.get_timestamp()
        reporting_state.step_started_timestamp = step_start_timestamp  # type: ignore[assignment]  # Timestamp stored as JSON-compatible
        reporting_state.active_test_step_id = test_step_id
        test_step_started = TestStepStarted(
            test_case_started_id=test_case_started_id,
            timestamp=step_start_timestamp,
            test_step_id=test_step_id,
        )

        self.lifecycle_service._emit_envelope(  # noqa: SLF001
            config,
            Message(test_step_started=test_step_started),
        )

    def pytest_bdd_after_step(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: object,  # noqa: ARG002
    ) -> None:
        """
        Handle the pytest bdd after step pytest hook.

        Responsibility:
            Handle the pytest bdd after step pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_after_step` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - require_step_object: collaborator call used by this boundary
            - self.lifecycle_service._resolve_test_step_id_for_runtime_step: collaborator call used by this boundary
            - self.lifecycle_service.get_timestamp: collaborator call used by this boundary
            - self._duration_between: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - self.lifecycle_service._emit_envelope: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `pytest_bdd_after_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_bdd_after_step`

        State and side effects:
            mutates step, reporting_state, test_case_started_id, config, test_step_id.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_after_step` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

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
        if self.reporter.is_disabled:
            return
        step = require_step_object(run, hook_name="pytest_bdd_after_step")
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config

        test_step_id = self.lifecycle_service._resolve_test_step_id_for_runtime_step(request=request, step=step)  # noqa: SLF001
        if test_step_id is None:
            return
        step_finish_timestamp = self.lifecycle_service.get_timestamp()
        reporting_state.step_finished_timestamp = step_finish_timestamp  # type: ignore[assignment]  # Timestamp stored as JSON-compatible
        step_duration = self._duration_between(
            start_timestamp=cast("Timestamp | None", reporting_state.step_started_timestamp),
            finish_timestamp=step_finish_timestamp,
        )

        self.lifecycle_service._emit_envelope(  # noqa: SLF001
            config,
            Message(
                test_step_finished=TestStepFinished(
                    test_case_started_id=test_case_started_id,
                    timestamp=step_finish_timestamp,
                    test_step_id=test_step_id,
                    test_step_result=TestStepResult(duration=step_duration, status=TestStepResultStatus.passed),
                ),
            ),
        )
        reporting_state.active_test_step_id = None

    def pytest_bdd_step_error(  # noqa: PLR0913, PLR0917
        self,
        request: FixtureRequest,
        run: Run,
        step_func: object,  # noqa: ARG002
        step_func_args: Mapping[str, object],  # noqa: ARG002
        exception: Exception,
        step_definition: Definition,  # noqa: ARG002
    ) -> None:
        """
        Handle the pytest bdd step error pytest hook.

        Responsibility:
            Handle the pytest bdd step error pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_step_error` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - require_step_object: collaborator call used by this boundary
            - self.lifecycle_service._resolve_test_step_id_for_runtime_step: collaborator call used by this boundary
            - self.lifecycle_service.get_timestamp: collaborator call used by this boundary
            - self._duration_between: collaborator call used by this boundary
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `pytest_bdd_step_error`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_bdd_step_error`

        State and side effects:
            mutates step, reporting_state, test_case_started_id, config, test_step_id.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime.ScenarioService.pytest_bdd_step_error` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

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
        if self.reporter.is_disabled:
            return
        step = require_step_object(run, hook_name="pytest_bdd_step_error")
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config

        test_step_id = self.lifecycle_service._resolve_test_step_id_for_runtime_step(request=request, step=step)  # noqa: SLF001
        if test_step_id is None:
            return
        step_finish_timestamp = self.lifecycle_service.get_timestamp()
        reporting_state.step_finished_timestamp = step_finish_timestamp  # type: ignore[assignment]  # Timestamp stored as JSON-compatible
        step_duration = self._duration_between(
            start_timestamp=cast("Timestamp | None", reporting_state.step_started_timestamp),
            finish_timestamp=step_finish_timestamp,
        )

        self.lifecycle_service._emit_envelope(  # noqa: SLF001
            config,
            Message(
                test_step_finished=TestStepFinished(
                    test_case_started_id=test_case_started_id,
                    timestamp=step_finish_timestamp,
                    test_step_id=test_step_id,
                    test_step_result=TestStepResult(
                        duration=step_duration,
                        status=TestStepResultStatus.failed,
                        message=str(exception),
                        exception=CucumberException(
                            type=type(exception).__name__,
                            message=str(exception),
                            stack_trace=repr(exception),
                        ),
                    ),
                ),
            ),
        )
        reporting_state.active_test_step_id = None
