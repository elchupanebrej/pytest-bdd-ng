"""
LifecycleService class — core runtime for the gherkin message reporter.

Responsibility:
    LifecycleService class — core runtime for the gherkin message reporter. It directly owns the observable contract,
    local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core`
    because it keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - LifecycleService: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references `_core`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references `_core`

State and side effects:
    mutates message_text, self.reporter._mapping_diagnostics_count, _, config, run_started_id; depends on
    __future__.annotations, json, logging, os, sys.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Failure semantics:
    Raises or re-raises RuntimeError, TypeError, MessageSchemaValidationError; callers must treat these as boundary
    failures.

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

import json
import logging
import os
import sys
from inspect import getfile
from pathlib import Path
from platform import machine, processor, system, version
from time import time_ns
from typing import TYPE_CHECKING, cast

import pytest
from cucumber_messages import (  # upstream library missing type stubs
    Duration,
    GherkinDocument,
    Hook,
    HookType,
    JavaMethod,
    JavaStackTraceElement,
    Location,
    Meta,
    Pickle,
    Product,
    Source,
    SourceReference,
    TestRunHookFinished,
    TestRunHookStarted,
    TestRunStarted,
    TestStepResult,
    TestStepResultStatus,
    Timestamp,
)
from cucumber_messages import (
    Envelope as Message,  # upstream type stubs missing this attribute
)

from pytest_bdd.compatibility.path import resolvepath
from pytest_bdd.compatibility.pytest import Config, is_set
from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_extension import get_payload_kind, has_single_payload
from pytest_bdd.model.message_outcome_mapping import resolve_outcome_mapping
from pytest_bdd.model.message_registry import EnvelopeRegistry
from pytest_bdd.model.message_schema_validation import validate_envelope_dict_against_schema
from pytest_bdd.model.message_serialization import MessageSerializationProfile
from pytest_bdd.model.message_stream_validation import observed_outcome_from_envelope
from pytest_bdd.model.message_validation_xdist import validate_xdist_reporting_compatibility
from pytest_bdd.model.run import Run
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase
from pytest_bdd.plugin.gherkin_message_reporter.session import format_requested_cucumber_formatter_labels
from pytest_bdd.types.exception import MessageSchemaValidationError
from pytest_bdd.util.inspect_extra import get_first_source_line
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.packaging import get_distribution_version

from ._ci import _build_ci_message
from ._hooks import _pytest_sessionfinish

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytest_bdd.compatibility.pytest import FixtureRequest, Session
    from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime import LiveFormatterService
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter
    from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRequest
    from pytest_bdd.plugin.gherkin_message_reporter.transport_runtime import TransportService

logger = logging.getLogger(__name__)


class LifecycleService(ReporterServiceBase):
    """
    Represent lifecycle service state.

    Yields:
        Generated values.

    Raises:
        TypeError: If the operation cannot be completed.
        MessageSchemaValidationError: If the operation cannot be completed.
        RuntimeError: If the operation cannot be completed.

    Responsibility:
        Represent lifecycle service state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _emit_disabled_warning_once: owns nested behavior below this boundary
        - _emit_envelope: owns nested behavior below this boundary
        - _check_derived_output_consistency: owns nested behavior below this boundary
        - _format_requested_cucumber_formatter_labels: owns nested behavior below this boundary
        - get_timestamp: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references `LifecycleService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `LifecycleService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
          `LifecycleService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
          `LifecycleService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
          `LifecycleService`

    State and side effects:
        mutates message_text, self.reporter._mapping_diagnostics_count, _, config, run_started_id.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError, TypeError, MessageSchemaValidationError; callers must treat these as boundary
        failures.

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

    plugin_suffix = "lifecycle"

    def __init__(
        self,
        reporter: GherkinMessageReporter,
        *,
        transport_service: TransportService,
        live_formatter_service: LiveFormatterService,
    ) -> None:
        """
        Initialize the lifecycle service.

        Responsibility:
            Initialize the lifecycle service. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.__init__` because it
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
            mutates self.transport_service, self.live_formatter_service.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.__init__` keeps its
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
        self.transport_service = transport_service
        self.live_formatter_service = live_formatter_service

    def _emit_disabled_warning_once(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._emit_disabled_warning_once`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._emit_disabled_warning_once`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - logger.warning: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `_emit_disabled_warning_once`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `_emit_disabled_warning_once`

        State and side effects:
            mutates self.reporter._disabled_warning_emitted.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._emit_disabled_warning_once`
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
        if self.reporter._disabled_warning_emitted:  # noqa: SLF001
            return
        self.reporter._disabled_warning_emitted = True  # noqa: SLF001
        logger.warning("Message reporting disabled; message-output guarantees were skipped for this run.")

    def _emit_envelope(self, config: Config, message: Message) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._emit_envelope` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._emit_envelope` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - logger.warning: collaborator call used by this boundary
            - has_single_payload: collaborator call used by this boundary
            - TypeError: collaborator call used by this boundary
            - observed_outcome_from_envelope: collaborator call used by this boundary
            - resolve_outcome_mapping: collaborator call used by this boundary
            - config.hook.pytest_bdd_message: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `_emit_envelope`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `_emit_envelope`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `_emit_envelope`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `_emit_envelope`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `_emit_envelope`

        State and side effects:
            mutates self.reporter._mapping_diagnostics_count, message_text, observed_outcome, selected_rule,
            is_ambiguous.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._emit_envelope` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

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
        if not has_single_payload(message):
            message_text = "Envelope must include exactly one payload"
            raise TypeError(message_text)
        observed_outcome = observed_outcome_from_envelope(message)
        if observed_outcome is not None:
            selected_rule, is_ambiguous = resolve_outcome_mapping(
                self.reporter._outcome_mapping_rules,  # noqa: SLF001
                outcome_scope=observed_outcome.outcome_scope,
                outcome_status=observed_outcome.outcome_status,
            )
            if is_ambiguous:
                self.reporter._mapping_diagnostics_count += 1  # noqa: SLF001
                logger.warning(
                    "Ambiguous outcome mapping for %s:%s",
                    observed_outcome.outcome_scope,
                    observed_outcome.outcome_status,
                )
            elif selected_rule is None:
                self.reporter._mapping_diagnostics_count += 1  # noqa: SLF001
                logger.warning(
                    "No outcome mapping rule for %s:%s",
                    observed_outcome.outcome_scope,
                    observed_outcome.outcome_status,
                )
        config.hook.pytest_bdd_message(config=config, message=message)

    @staticmethod
    def _check_derived_output_consistency(envelopes: list[Message]) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._check_derived_output_consistency`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._check_derived_output_consistency`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - get_payload_kind: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `_check_derived_output_consistency`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `_check_derived_output_consistency`

        State and side effects:
            mutates payload_kinds.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._check_derived_output_consistency`
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
        payload_kinds = [get_payload_kind(envelope) for envelope in envelopes]
        return "test_run_started" in payload_kinds and "test_run_finished" in payload_kinds

    @staticmethod
    def _format_requested_cucumber_formatter_labels(
        formatter_requests: tuple[CucumberFormatterRequest, ...] | list[CucumberFormatterRequest],
    ) -> str:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._format_requested_cucumber_formatter_labels`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._format_requested_cucumber_formatter_labels`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - format_requested_cucumber_formatter_labels: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `_format_requested_cucumber_formatter_labels`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `_format_requested_cucumber_formatter_labels`

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
        return format_requested_cucumber_formatter_labels(formatter_requests)

    @staticmethod
    def get_timestamp() -> Timestamp:
        """
        Get current timestamp.

        Returns:
            Current timestamp.

        Responsibility:
            Get current timestamp. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.get_timestamp` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - time_ns: collaborator call used by this boundary
            - Timestamp: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `get_timestamp`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `get_timestamp`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `get_timestamp`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `get_timestamp`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references `get_timestamp`

        State and side effects:
            mutates timestamp, test_run_started_seconds, test_run_started_nanos.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.get_timestamp` keeps
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
            #arch-eval:locational_stability=4

        """
        timestamp = time_ns()
        test_run_started_seconds = timestamp // 10**9
        test_run_started_nanos = timestamp - test_run_started_seconds * 10**9
        return Timestamp(seconds=test_run_started_seconds, nanos=test_run_started_nanos)

    def pytest_bdd_message(
        self,
        config: Config,
        message: Message,
    ) -> None:
        """
        Handle the pytest bdd message pytest hook.

        Raises:
            TypeError: If the operation cannot be completed.
            MessageSchemaValidationError: If the operation cannot be completed.
            RuntimeError: If the operation cannot be completed.

        Responsibility:
            Handle the pytest bdd message pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.pytest_bdd_message`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - EnvelopeRegistry.register_envelope_in_pytest_stash: collaborator call used by this boundary
            - ExecutionMessageAdapter.serialize: collaborator call used by this boundary
            - has_single_payload: collaborator call used by this boundary
            - TypeError: collaborator call used by this boundary
            - ExecutionMessageAdapter.serialize_to_dict: collaborator call used by this boundary
            - validate_envelope_dict_against_schema: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `pytest_bdd_message`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `pytest_bdd_message`

        State and side effects:
            mutates message_text, message, schema_compatible_message, schema_violations, details.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.pytest_bdd_message`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises TypeError, MessageSchemaValidationError, RuntimeError; callers must treat these as
            boundary failures.

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
        message = ExecutionMessageAdapter.serialize(message)
        if not has_single_payload(message):
            message_text = "Cannot emit envelope with zero or multiple payloads"
            raise TypeError(message_text)

        if self.reporter.is_disabled:
            EnvelopeRegistry.register_envelope_in_pytest_stash(config.stash, message)
            return

        schema_compatible_message = ExecutionMessageAdapter.serialize_to_dict(
            message,
            profile=MessageSerializationProfile.schema_compatible,
        )
        schema_violations = validate_envelope_dict_against_schema(schema_compatible_message)
        if schema_violations:
            details = "; ".join(violation.message for violation in schema_violations)
            raise MessageSchemaValidationError(details)

        EnvelopeRegistry.register_envelope_in_pytest_stash(config.stash, message)
        try:
            message_json = json.dumps(schema_compatible_message)
        except Exception as exc:
            logger.warning("Message emission failed while serializing envelope", exc_info=True)
            message_text = "Message emission failed while serializing envelope"
            raise RuntimeError(message_text) from exc

        self.live_formatter_service._emit_live_formatter_json_lines([message_json], source="local envelope emission")  # noqa: SLF001

        self.reporter.process_messages_io_queue.put_nowait(message_json)

    def pytest_bdd_source_read(self, config: Config, gherkin_document: GherkinDocument, source: Source) -> None:
        """
        Handle the pytest bdd source read pytest hook.

        Responsibility:
            Handle the pytest bdd source read pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.pytest_bdd_source_read`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._emit_envelope: collaborator call used by this boundary
            - Message: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `pytest_bdd_source_read`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `pytest_bdd_source_read`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `pytest_bdd_source_read`

        State and side effects:
            mutates _.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.pytest_bdd_source_read`
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
        _ = gherkin_document
        self._emit_envelope(config, Message(source=source))

    def pytest_bdd_feature_read(self, config: Config, gherkin_document: GherkinDocument) -> None:
        """
        Handle the pytest bdd feature read pytest hook.

        Responsibility:
            Handle the pytest bdd feature read pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.pytest_bdd_feature_read`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._emit_envelope: collaborator call used by this boundary
            - Message: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `pytest_bdd_feature_read`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `pytest_bdd_feature_read`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `pytest_bdd_feature_read`

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
        self._emit_envelope(config, Message(gherkin_document=gherkin_document))

    def pytest_bdd_pickle_read(self, config: Config, gherkin_document: GherkinDocument, pickle: Pickle) -> None:
        """
        Handle the pytest bdd pickle read pytest hook.

        Responsibility:
            Handle the pytest bdd pickle read pytest hook. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.pytest_bdd_pickle_read`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._emit_envelope: collaborator call used by this boundary
            - Message: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `pytest_bdd_pickle_read`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `pytest_bdd_pickle_read`
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `pytest_bdd_pickle_read`

        State and side effects:
            mutates _.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.pytest_bdd_pickle_read`
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
        _ = gherkin_document
        self._emit_envelope(config, Message(pickle=pickle))

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtestloop(self, session: Session) -> Iterator[None]:
        """
        Handle the pytest runtestloop pytest hook.

        Yields:
            Generated values.

        Responsibility:
            Handle the pytest runtestloop pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.pytest_runtestloop`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._emit_envelope: collaborator call used by this boundary
            - Message: collaborator call used by this boundary
            - self.get_timestamp: collaborator call used by this boundary
            - self._require_run_started_id: collaborator call used by this boundary
            - TestRunStarted: collaborator call used by this boundary
            - next: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `pytest_runtestloop`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `pytest_runtestloop`

        State and side effects:
            mutates config, run_started_id, before_test_run_hook_started_id, run_root,
            run_root.reporting_state.test_run_hook_started_id.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.pytest_runtestloop`
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
            yield
            return
        config: Config = session.config
        run_started_id = self._require_run_started_id(config=config)
        self._emit_envelope(
            config,
            Message(test_run_started=TestRunStarted(id=run_started_id, timestamp=self.get_timestamp())),
        )

        before_test_run_hook_started_id = next(IdGenerator.from_stash(config.stash))
        run_root = Run.from_stash(config.stash)
        run_root.reporting_state.test_run_hook_started_id = before_test_run_hook_started_id
        self._emit_run_hook_definition(
            config,
            hook_id=self.reporter.BEFORE_TEST_RUN_HOOK_ID,
            hook_type=HookType.before_test_run,
            hook_name="before-test-run",
        )
        self._emit_envelope(
            config,
            Message(
                test_run_hook_started=TestRunHookStarted(
                    hook_id=self.reporter.BEFORE_TEST_RUN_HOOK_ID,
                    id=before_test_run_hook_started_id,
                    test_run_started_id=run_started_id,
                    timestamp=self.get_timestamp(),
                    worker_id=self.transport_service._current_reporting_worker_id(config),  # noqa: SLF001
                ),
            ),
        )
        yield
        self._emit_envelope(
            config,
            Message(
                test_run_hook_finished=TestRunHookFinished(
                    test_run_hook_started_id=before_test_run_hook_started_id,
                    timestamp=self.get_timestamp(),
                    result=TestStepResult(
                        duration=Duration(seconds=0, nanos=0),
                        status=TestStepResultStatus.passed,
                        message="before-test-run hook completed",
                    ),
                ),
            ),
        )

    def pytest_sessionstart(self, session: Session) -> None:
        """
        Handle the pytest sessionstart pytest hook.

        Raises:
            RuntimeError: If the operation cannot be completed.

        Responsibility:
            Handle the pytest sessionstart pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.pytest_sessionstart`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Product: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - RuntimeError: collaborator call used by this boundary
            - get_distribution_version: collaborator call used by this boundary
            - self._emit_run_hook_definition: collaborator call used by this boundary
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_sessionstart`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `pytest_sessionstart`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `pytest_sessionstart`

        State and side effects:
            mutates pluginmanager, dsession_plugin, compatibility, config, ci.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.pytest_sessionstart`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
        if self.reporter.is_xdist_worker:
            os.environ.pop("PYTEST_BDD_XDIST_IS_WORKER", None)

        if self.reporter.is_disabled:
            self._emit_disabled_warning_once()
            return

        self.transport_service._ensure_xdist_worker_transport_client(require_sender=True)  # noqa: SLF001
        pluginmanager = getattr(self.reporter.config, "pluginmanager", None)
        dsession_plugin = pluginmanager.getplugin("dsession") if pluginmanager is not None else None

        if (
            not self.reporter.is_xdist_worker
            and dsession_plugin is not None
            and self.reporter.xdist_fragment_dir is None
        ):
            self.transport_service._activate_xdist_controller_mode()  # noqa: SLF001

        compatibility = validate_xdist_reporting_compatibility(
            xdist_active=self.reporter.is_xdist_worker or dsession_plugin is not None,
            is_worker=self.reporter.is_xdist_worker,
            is_controller=self.reporter.is_xdist_controller,
            remote_module_available=True,
            controller_event_patch_installed=self.reporter._xdist_compatibility_error is None,  # noqa: SLF001
            worker_sender_available=self.reporter.xdist_transport_client is not None,
        )
        if not compatibility.is_valid:
            raise RuntimeError(str(compatibility.reason))
        if self.reporter._xdist_compatibility_error is not None:  # noqa: SLF001
            raise RuntimeError(self.reporter._xdist_compatibility_error)  # noqa: SLF001

        if not self.reporter._live_formatter_session_started and self.reporter._live_formatter_failure_message is None:  # noqa: SLF001
            self.live_formatter_service._start_live_formatters()  # noqa: SLF001
        self.transport_service.start_process_messages_thread()

        config = session.config

        ci = self._build_ci_message(os.environ)

        self._emit_envelope(
            config,
            Message(
                meta=Meta(
                    protocol_version=str(get_distribution_version("cucumber-messages")),
                    implementation=Product(
                        name="pytest-bdd-ng",
                        version=str(get_distribution_version("pytest-bdd-ng")),
                    ),
                    runtime=Product(name="Python", version=sys.version),
                    os=Product(name=system(), version=version()),
                    cpu=Product(name=machine(), version=processor()),
                    ci=ci,
                ),
            ),
        )
        self._emit_run_hook_definition(
            cast("Config", config),
            hook_id=self.reporter.BEFORE_TEST_RUN_HOOK_ID,
            hook_type=HookType.before_test_run,
            hook_name="before-test-run",
        )
        self._emit_run_hook_definition(
            cast("Config", config),
            hook_id=self.reporter.AFTER_TEST_RUN_HOOK_ID,
            hook_type=HookType.after_test_run,
            hook_name="after-test-run",
        )

    # Delegate CI helpers to _ci module functions.
    _build_ci_message = staticmethod(_build_ci_message)

    @staticmethod
    def _require_run_started_id(*, config: Config) -> str:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._require_run_started_id`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._require_run_started_id`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Run.from_stash: collaborator call used by this boundary
            - RuntimeError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `_require_run_started_id`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `_require_run_started_id`

        State and side effects:
            mutates run_started_id, msg.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._require_run_started_id`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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
        run_started_id = Run.from_stash(config.stash).reporting_state.run_started_id
        if run_started_id is None:
            msg = (
                "Execution context run_started_id is unavailable in config.stash. "
                "Execution plugins must initialize session root state before reporter lifecycle emission."
            )
            raise RuntimeError(msg)
        return run_started_id

    @staticmethod
    def _resolve_gherkin_document_and_pickle(*, run: Run) -> tuple[object | None, object | None]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._resolve_gherkin_document_and_pickle`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._resolve_gherkin_document_and_pickle`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - is_set: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `_resolve_gherkin_document_and_pickle`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `_resolve_gherkin_document_and_pickle`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
              `_resolve_gherkin_document_and_pickle`

        State and side effects:
            mutates scenario_run.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._resolve_gherkin_document_and_pickle`
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
        scenario_run = run.active_scenario_run
        if scenario_run is None:
            return None, None
        if not is_set(scenario_run.gherkin_document) or not is_set(scenario_run.pickle):
            return None, None
        return scenario_run.gherkin_document, scenario_run.pickle

    def _emit_run_hook_definition(self, config: Config, *, hook_id: str, hook_type: HookType, hook_name: str) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._emit_run_hook_definition`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._emit_run_hook_definition`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - type: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - self.reporter._emitted_run_hook_definition_ids.add: collaborator call used by this boundary
            - getfile: collaborator call used by this boundary
            - get_first_source_line: collaborator call used by this boundary
            - self._emit_envelope: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `_emit_run_hook_definition`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `_emit_run_hook_definition`

        State and side effects:
            mutates hook_method, source_file, source_line.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._emit_run_hook_definition`
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
        if hook_id in self.reporter._emitted_run_hook_definition_ids:  # noqa: SLF001
            return
        self.reporter._emitted_run_hook_definition_ids.add(hook_id)  # noqa: SLF001
        hook_method = (
            type(self).pytest_sessionstart if hook_type == HookType.before_test_run else type(self).pytest_sessionfinish
        )
        source_file = getfile(hook_method)
        source_line = get_first_source_line(hook_method)
        self._emit_envelope(
            config,
            Message(
                hook=Hook(
                    id=hook_id,
                    name=hook_name,
                    type=hook_type,
                    source_reference=SourceReference(
                        uri=Path(resolvepath(source_file, config.rootpath)).as_uri(),
                        location=Location(line=source_line, column=1),
                        java_method=JavaMethod(
                            class_name=type(self).__module__,
                            method_name=hook_method.__name__,
                            method_parameter_types=[],
                        ),
                        java_stack_trace_element=JavaStackTraceElement(
                            class_name=type(self).__module__,
                            file_name=Path(source_file).name,
                            method_name=hook_method.__name__,
                        ),
                    ),
                ),
            ),
        )

    @staticmethod
    def _resolve_test_step_id_for_runtime_step(*, request: FixtureRequest, step: object) -> str | None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._resolve_test_step_id_for_runtime_step`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._resolve_test_step_id_for_runtime_step`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Run.from_stash: collaborator call used by this boundary
            - run.resolve_test_step_id_for_runtime_step: collaborator call used by this boundary
            - logger.warning: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `_resolve_test_step_id_for_runtime_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `_resolve_test_step_id_for_runtime_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `_resolve_test_step_id_for_runtime_step`

        State and side effects:
            mutates run, test_step_id.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService._resolve_test_step_id_for_runtime_step`
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
        run = Run.from_stash(request.config.stash)
        test_step_id = run.resolve_test_step_id_for_runtime_step(pickle_step=step)  # type: ignore[arg-type]  # runtime object dispatch
        if test_step_id is None:
            logger.warning("Unable to resolve cucumber TestStep id for runtime step object: %r", step)
        return test_step_id

    def resolve_test_step_id_for_runtime_step(self, *, request: FixtureRequest, step: object) -> str | None:
        """
        Resolve test step ID for runtime step.

        Returns:
            Test step ID or None.

        Responsibility:
            Resolve test step ID for runtime step. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core.LifecycleService.resolve_test_step_id_for_runtime_step`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._resolve_test_step_id_for_runtime_step: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `resolve_test_step_id_for_runtime_step`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/facade.py: imports or references
              `resolve_test_step_id_for_runtime_step`

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
        return self._resolve_test_step_id_for_runtime_step(request=request, step=step)

    pytest_sessionfinish = _pytest_sessionfinish
