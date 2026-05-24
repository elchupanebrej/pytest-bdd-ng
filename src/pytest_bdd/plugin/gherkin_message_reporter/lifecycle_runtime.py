"""Provide lifecycle runtime helpers."""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
from inspect import getfile
from pathlib import Path
from platform import machine, processor, system, version
from time import time_ns
from typing import TYPE_CHECKING, cast

import pytest
from ci_environment import detect_ci_environment
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    Ci,
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
    TestRunFinished,
    TestRunHookFinished,
    TestRunHookStarted,
    TestRunStarted,
    TestStepResult,
    TestStepResultStatus,
    Timestamp,
)
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]
from cucumber_messages import Exception as CucumberException
from returns.maybe import Nothing

from pytest_bdd.compatibility.path import resolvepath
from pytest_bdd.compatibility.pytest import Config, is_set, is_testrun_success
from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter
from pytest_bdd.model.message_converter import message_converter
from pytest_bdd.model.message_extension import get_payload_kind, has_single_payload
from pytest_bdd.model.message_outcome_mapping import resolve_outcome_mapping
from pytest_bdd.model.message_registry import EnvelopeRegistry
from pytest_bdd.model.message_schema_validation import validate_envelope_dict_against_schema
from pytest_bdd.model.message_serialization import MessageSerializationProfile
from pytest_bdd.model.message_stream_validation import observed_outcome_from_envelope, validate_message_stream
from pytest_bdd.model.message_transport import WorkerCompletionManifest
from pytest_bdd.model.message_validation_xdist import validate_xdist_reporting_compatibility
from pytest_bdd.model.run import Run
from pytest_bdd.plugin.gherkin_message_reporter.runtime_support import _resolve_reporting_worker_identity
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase
from pytest_bdd.plugin.gherkin_message_reporter.session import format_requested_cucumber_formatter_labels
from pytest_bdd.types.exception import MessageSchemaValidationError
from pytest_bdd.util.inspect_extra import get_first_source_line
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.packaging import get_distribution_version

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from pytest_bdd.compatibility.pytest import ExitCode, FixtureRequest, Session
    from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime import LiveFormatterService
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter
    from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRequest
    from pytest_bdd.plugin.gherkin_message_reporter.transport_runtime import TransportService
    from pytest_bdd.types.json import JSONObject

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

    """

    plugin_suffix = "lifecycle"

    def __init__(
        self,
        reporter: GherkinMessageReporter,
        *,
        transport_service: TransportService,
        live_formatter_service: LiveFormatterService,
    ) -> None:
        """Initialize the lifecycle service."""
        super().__init__(reporter)
        self.transport_service = transport_service
        self.live_formatter_service = live_formatter_service

    def _emit_disabled_warning_once(self) -> None:
        if self.reporter._disabled_warning_emitted:  # noqa: SLF001
            return
        self.reporter._disabled_warning_emitted = True  # noqa: SLF001
        logger.warning("Message reporting disabled; message-output guarantees were skipped for this run.")

    def _emit_envelope(self, config: Config, message: Message) -> None:
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
        payload_kinds = [get_payload_kind(envelope) for envelope in envelopes]
        return "test_run_started" in payload_kinds and "test_run_finished" in payload_kinds

    @staticmethod
    def _format_requested_cucumber_formatter_labels(
        formatter_requests: tuple[CucumberFormatterRequest, ...] | list[CucumberFormatterRequest],
    ) -> str:
        return format_requested_cucumber_formatter_labels(formatter_requests)

    @staticmethod
    def get_timestamp() -> Timestamp:
        """
        Get current timestamp.

        Returns:
            Current timestamp.

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
        """Handle the pytest bdd source read pytest hook."""
        _ = gherkin_document
        self._emit_envelope(config, Message(source=source))

    def pytest_bdd_feature_read(self, config: Config, gherkin_document: GherkinDocument) -> None:
        """Handle the pytest bdd feature read pytest hook."""
        self._emit_envelope(config, Message(gherkin_document=gherkin_document))

    def pytest_bdd_pickle_read(self, config: Config, gherkin_document: GherkinDocument, pickle: Pickle) -> None:
        """Handle the pytest bdd pickle read pytest hook."""
        _ = gherkin_document
        self._emit_envelope(config, Message(pickle=pickle))

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtestloop(self, session: Session) -> Iterator[None]:
        """
        Handle the pytest runtestloop pytest hook.

        Yields:
            Generated values.

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
                    worker_id=self.transport_service._current_reporting_worker_id(cast("Config", config)),  # noqa: SLF001
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

        """
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

    @staticmethod
    def _build_ci_message(env: Mapping[str, str]) -> Ci | None:
        ci_payload = detect_ci_environment(env)
        if ci_payload is None:
            return Nothing.value_or(None)
        enriched_payload = LifecycleService._enrich_ci_payload(ci_payload, env)
        return message_converter.from_dict(enriched_payload, Ci)

    @staticmethod
    def _enrich_ci_payload(ci_payload: JSONObject, env: Mapping[str, str]) -> JSONObject:
        """
        Patch CI payload with branch when detector omits it for PR-style builds.

        `ci_environment` provides a solid baseline payload, but some providers
        expose branch only via platform-specific env vars in merge-request
        pipelines. We enrich only the missing branch field to keep emitted
        metadata stable without overriding detector-provided values.

        Returns:
            Enriched CI payload.

        """
        payload = dict(ci_payload)
        git_payload_raw = payload.get("git")
        git_payload = dict(git_payload_raw) if isinstance(git_payload_raw, dict) else {}
        if not git_payload.get("branch"):
            branch = LifecycleService._resolve_ci_branch(env)
            if branch:
                git_payload["branch"] = branch
        if git_payload:
            payload["git"] = git_payload
        return payload

    @staticmethod
    def _resolve_ci_branch(env: Mapping[str, str]) -> str | None:
        """
        Resolve VCS branch name from common CI env var conventions.

        Returns:
            Branch name or None.

        """
        github_ref_type = (env.get("GITHUB_REF_TYPE") or "").strip().lower()
        github_ref = (env.get("GITHUB_REF") or "").strip()
        github_ref_name = (env.get("GITHUB_REF_NAME") or "").strip()
        github_head_ref = (env.get("GITHUB_HEAD_REF") or "").strip()
        if github_ref_type == "branch" and github_ref_name:
            return github_ref_name
        if github_ref.startswith("refs/heads/"):
            return github_ref.removeprefix("refs/heads/")
        if github_head_ref:
            return github_head_ref

        for name in (
            "CI_COMMIT_BRANCH",
            "CI_COMMIT_REF_NAME",
            "GIT_BRANCH",
            "BRANCH_NAME",
            "BUILD_SOURCEBRANCHNAME",
        ):
            value = (env.get(name) or "").strip()
            if value:
                return value.removeprefix("refs/heads/")
        return Nothing.value_or(None)

    @staticmethod
    def _require_run_started_id(*, config: Config) -> str:
        run_started_id = Run.from_stash(config.stash).reporting_state.run_started_id
        if run_started_id is None:
            msg = (
                "Execution context run_started_id is unavailable in config.stash. "
                "Execution plugins must initialize session root state before reporter lifecycle emission."
            )
            raise RuntimeError(msg)
        return cast("str", run_started_id)

    @staticmethod
    def _resolve_gherkin_document_and_pickle(*, run: Run) -> tuple[object | None, object | None]:
        scenario_run = run.active_scenario_run
        if scenario_run is None:
            return Nothing.value_or(None), None
        if not is_set(scenario_run.gherkin_document) or not is_set(scenario_run.pickle):
            return Nothing.value_or(None), None
        return scenario_run.gherkin_document, scenario_run.pickle

    def _emit_run_hook_definition(self, config: Config, *, hook_id: str, hook_type: HookType, hook_name: str) -> None:
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
        run = Run.from_stash(request.config.stash)
        test_step_id = cast("str | None", run.resolve_test_step_id_for_runtime_step(pickle_step=step))
        if test_step_id is None:
            logger.warning("Unable to resolve cucumber TestStep id for runtime step object: %r", step)
        return test_step_id

    def resolve_test_step_id_for_runtime_step(self, *, request: FixtureRequest, step: object) -> str | None:
        """
        Resolve test step ID for runtime step.

        Returns:
            Test step ID or None.

        """
        return self._resolve_test_step_id_for_runtime_step(request=request, step=step)

    def pytest_sessionfinish(self, session: Session, exitstatus: int | ExitCode) -> None:  # noqa: C901, PLR0912
        """Handle the pytest sessionfinish pytest hook."""
        if self.reporter.is_disabled:
            return
        config = session.config
        run_started_id = self._require_run_started_id(config=cast("Config", config))
        run_success = is_testrun_success(exitstatus)
        run_exception = (
            CucumberException(type="PytestExitCode", message=str(exitstatus), stack_trace=str(exitstatus))
            if not run_success
            else None
        )
        after_test_run_hook_started_id = next(IdGenerator.from_stash(cast("Config", config).stash))
        self._emit_run_hook_definition(
            cast("Config", config),
            hook_id=self.reporter.AFTER_TEST_RUN_HOOK_ID,
            hook_type=HookType.after_test_run,
            hook_name="after-test-run",
        )
        self._emit_envelope(
            config,
            Message(
                test_run_hook_started=TestRunHookStarted(
                    hook_id=self.reporter.AFTER_TEST_RUN_HOOK_ID,
                    id=after_test_run_hook_started_id,
                    test_run_started_id=run_started_id,
                    timestamp=self.get_timestamp(),
                    worker_id=self.transport_service._current_reporting_worker_id(cast("Config", config)),  # noqa: SLF001
                ),
            ),
        )
        self._emit_envelope(
            config,
            Message(
                test_run_hook_finished=TestRunHookFinished(
                    test_run_hook_started_id=after_test_run_hook_started_id,
                    timestamp=self.get_timestamp(),
                    result=TestStepResult(
                        duration=Duration(seconds=0, nanos=0),
                        status=TestStepResultStatus.passed if run_success else TestStepResultStatus.failed,
                        message="after-test-run hook completed",
                        **({"exception": run_exception} if run_exception is not None else {}),
                    ),
                ),
            ),
        )
        self._emit_envelope(
            config,
            Message(
                test_run_finished=TestRunFinished(
                    timestamp=self.get_timestamp(),
                    success=run_success,
                    test_run_started_id=run_started_id,
                    message=f"pytest session exit status: {exitstatus}",
                    **({"exception": run_exception} if run_exception is not None else {}),
                ),
            ),
        )

        self.transport_service.finish_process_messages_thread()
        if self.reporter.is_xdist_worker:
            workeroutput = cast("dict[str, object]", getattr(config, "workeroutput", {}))
            worker_id, gateway_mode = _resolve_reporting_worker_identity(config)
            if self.reporter.xdist_transport_client is not None:
                workeroutput["pytest_bdd_messages_manifest"] = self.reporter.xdist_transport_client.build_manifest(
                    complete=True,
                ).as_dict()
            else:
                workeroutput["pytest_bdd_messages_manifest"] = WorkerCompletionManifest(
                    worker_id=str(worker_id),
                    complete=False,
                    last_batch_sequence=None,
                    transferred_batch_count=0,
                    transferred_envelope_count=0,
                    interruption_reason="transport client was not initialized",
                    gateway_mode=gateway_mode,
                ).as_dict()
            workeroutput["pytest_bdd_messages_fragment_worker_id"] = str(worker_id)
            if (
                self.reporter._xdist_worker_temp_messages_path is not None  # noqa: SLF001
                and self.reporter._xdist_worker_temp_messages_path.exists()  # noqa: SLF001
            ):
                self.reporter._xdist_worker_temp_messages_path.unlink()  # noqa: SLF001
            return

        if self.reporter.is_xdist_controller:
            self.reporter._xdist_fragment_records["master"] = {  # noqa: SLF001
                "worker_id": "master",
                "role": "controller",
                "path": self.reporter.messages_file_path,
                "complete": True,
                "manifest_received": True,
            }
            envelopes = self.transport_service._finalize_xdist_messages_file()  # noqa: SLF001
        else:
            envelopes = self.transport_service.read_envelopes_from_path(self.reporter.final_messages_file_path)
        validation_result = validate_message_stream(
            envelopes,
            latest_protocol_version=str(get_distribution_version("cucumber-messages")),
            track_coverage=False,
        )
        if not validation_result.is_valid:
            logger.error(
                "Canonical message stream validation failed with %s violation(s).",
                len(validation_result.violations),
            )
        if self.reporter._mapping_diagnostics_count:  # noqa: SLF001
            logger.error(
                "Detected %s mapping diagnostic warning(s) in message emission flow.",
                self.reporter._mapping_diagnostics_count,  # noqa: SLF001
            )
        if not self._check_derived_output_consistency(envelopes):
            logger.error("Derived-output consistency check failed: required run lifecycle envelopes are incomplete.")

        if (
            self.reporter.requested_cucumber_formatters
            and not self.reporter._live_formatter_session_started  # noqa: SLF001
            and self.reporter._live_formatter_failure_message is None  # noqa: SLF001
        ):
            self.live_formatter_service._record_live_formatter_failure(  # noqa: SLF001
                "Requested cucumber formatters were not attached to a live session; "
                "post-run replay is disabled for live formatter runs.",
            )
        if self.reporter.config.option.cucumber_html_path is not None:
            self.live_formatter_service.generate_html_report()
        if self.reporter.is_messages_file_temp:
            Path(self.reporter.final_messages_file_path).unlink()
        if self.reporter.xdist_fragment_dir is not None and self.reporter.xdist_fragment_dir.exists():
            shutil.rmtree(self.reporter.xdist_fragment_dir)
