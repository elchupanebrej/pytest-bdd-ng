"""Provide scenario runtime helpers."""

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
from cucumber_messages import Envelope as Message  # noqa: A005
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
    """Represent scenario service state."""

    plugin_suffix = "scenario"

    def __init__(
        self,
        reporter: GherkinMessageReporter,
        *,
        lifecycle_service: LifecycleService,
        transport_service: TransportService,
    ) -> None:
        """Initialize the scenario service."""
        super().__init__(reporter)
        self.lifecycle_service = lifecycle_service
        self.transport_service = transport_service

    @staticmethod
    def _step_keyword_to_decorator(keyword: str | None) -> str:
        normalized = (keyword or "").strip().lower()
        if normalized.startswith("when"):
            return "when"
        if normalized.startswith("then"):
            return "then"
        return "given"

    def _build_suggestion_snippet(self, step: object) -> str:
        decorator = self._step_keyword_to_decorator(getattr(step, "keyword", None))
        step_text = str(getattr(step, "text", "")).replace('"', '\\"')
        return f'@{decorator}("{step_text}")\ndef step_impl():\n    raise NotImplementedError\n'

    @staticmethod
    def _extract_undefined_parameter_type(
        *,
        exception: Exception,
        fallback_expression: str,
    ) -> tuple[str, str] | None:
        explicit = getattr(exception, "undefined_parameter_type", None)
        if isinstance(explicit, tuple) and len(explicit) == 2:
            return str(explicit[0]), str(explicit[1])

        for candidate in (exception, getattr(exception, "__cause__", None)):
            if isinstance(candidate, UndefinedParameterTypeError):
                expression = str(candidate.args[1]) if len(candidate.args) > 1 else fallback_expression
                parameter_name = str(candidate.args[2]) if len(candidate.args) > 2 else ""
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
        """Handle the pytest bdd step func lookup error pytest hook."""
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
        self.lifecycle_service._emit_envelope(config, Message(suggestion=suggestion))

        undefined_parameter = self._extract_undefined_parameter_type(
            exception=exception,
            fallback_expression=str(getattr(step, "text", "")),
        )
        if undefined_parameter is not None:
            expression, parameter_name = undefined_parameter
            self.lifecycle_service._emit_envelope(
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
        """Handle the pytest bdd before scenario pytest hook."""
        if self.reporter.is_disabled:
            return
        config = request.config
        reporting_state = run.reporting_state
        test_case_id = reporting_state.active_test_case_id
        if test_case_id is None:
            return
        attempt_index = getattr(request.node, "execution_count", 0)
        worker_id = self.transport_service._current_reporting_worker_id(cast("Config", config))
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
        self.lifecycle_service._emit_envelope(
            config,
            Message(test_case_started=test_case_start),
        )

    def pytest_bdd_after_scenario(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> None:
        """Handle the pytest bdd after scenario pytest hook."""
        if self.reporter.is_disabled:
            return
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config
        self.lifecycle_service._emit_envelope(
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
        step_func: object,
    ) -> None:
        """Handle the pytest bdd before step pytest hook."""
        if self.reporter.is_disabled:
            return
        step = require_step_object(run, hook_name="pytest_bdd_before_step")
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config

        test_step_id = self.lifecycle_service._resolve_test_step_id_for_runtime_step(request=request, step=step)
        if test_step_id is None:
            return

        step_start_timestamp = self.lifecycle_service.get_timestamp()
        reporting_state.step_started_timestamp = step_start_timestamp  # type: ignore[assignment]
        reporting_state.active_test_step_id = test_step_id
        test_step_started = TestStepStarted(
            test_case_started_id=test_case_started_id,
            timestamp=step_start_timestamp,
            test_step_id=test_step_id,
        )

        self.lifecycle_service._emit_envelope(
            config,
            Message(test_step_started=test_step_started),
        )

    def pytest_bdd_after_step(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: object,
    ) -> None:
        """Handle the pytest bdd after step pytest hook."""
        if self.reporter.is_disabled:
            return
        step = require_step_object(run, hook_name="pytest_bdd_after_step")
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config

        test_step_id = self.lifecycle_service._resolve_test_step_id_for_runtime_step(request=request, step=step)
        if test_step_id is None:
            return
        step_finish_timestamp = self.lifecycle_service.get_timestamp()
        reporting_state.step_finished_timestamp = step_finish_timestamp  # type: ignore[assignment]
        step_duration = self._duration_between(
            start_timestamp=cast("Timestamp | None", reporting_state.step_started_timestamp),
            finish_timestamp=step_finish_timestamp,
        )

        self.lifecycle_service._emit_envelope(
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

    def pytest_bdd_step_error(  # noqa: PLR0913
        self,
        request: FixtureRequest,
        run: Run,
        step_func: object,
        step_func_args: Mapping[str, object],
        exception: Exception,
        step_definition: Definition,
    ) -> None:
        """Handle the pytest bdd step error pytest hook."""
        if self.reporter.is_disabled:
            return
        step = require_step_object(run, hook_name="pytest_bdd_step_error")
        reporting_state = run.reporting_state
        test_case_started_id = reporting_state.active_test_case_started_id
        if test_case_started_id is None:
            return
        config = request.config

        test_step_id = self.lifecycle_service._resolve_test_step_id_for_runtime_step(request=request, step=step)
        if test_step_id is None:
            return
        step_finish_timestamp = self.lifecycle_service.get_timestamp()
        reporting_state.step_finished_timestamp = step_finish_timestamp  # type: ignore[assignment]
        step_duration = self._duration_between(
            start_timestamp=cast("Timestamp | None", reporting_state.step_started_timestamp),
            finish_timestamp=step_finish_timestamp,
        )

        self.lifecycle_service._emit_envelope(
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
