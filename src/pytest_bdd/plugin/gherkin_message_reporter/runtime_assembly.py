"""Provide runtime assembly helpers."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from attrs import frozen

from pytest_bdd.model.cucumber_formatter_adapter import CucumberFormatterEnvelopeAdapter
from pytest_bdd.model.message_validation import default_outcome_mapping_rules
from pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime import AttachmentService
from pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime import HookCatalogService
from pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime import LifecycleService
from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime import LiveFormatterService
from pytest_bdd.plugin.gherkin_message_reporter.runtime_support import _is_xdist_worker_process
from pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime import ScenarioService
from pytest_bdd.plugin.gherkin_message_reporter.session import resolve_requested_cucumber_formatters
from pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime import StepCatalogService
from pytest_bdd.plugin.gherkin_message_reporter.transport_runtime import TransportService

if TYPE_CHECKING:
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter


@frozen
class ReporterServiceGraph:
    """Represent reporter service graph state."""

    lifecycle_service: LifecycleService
    transport_service: TransportService
    hook_catalog_service: HookCatalogService
    step_catalog_service: StepCatalogService
    scenario_service: ScenarioService
    attachment_service: AttachmentService
    live_formatter_service: LiveFormatterService
    hook_services: tuple[object, ...]
    services: tuple[object, ...]


def initialize_reporter_runtime(reporter: GherkinMessageReporter) -> None:
    """Handle initialize reporter runtime."""
    reporter.parameter_type_registry = set()
    reporter.hook_registry = set()
    reporter.hook_registration_registry = {}
    reporter._disabled_warning_emitted = False
    reporter._outcome_mapping_rules = default_outcome_mapping_rules()
    reporter._mapping_diagnostics_count = 0
    reporter._emitted_step_definition_ids = set()
    reporter._emitted_run_hook_definition_ids = set()
    reporter._auto_provisioned_node_modules_roots = ()
    reporter._xdist_fragment_records = {}
    reporter.xdist_fragment_dir = None
    reporter.xdist_transport_session = None
    reporter.xdist_transport_client = None
    reporter._xdist_worker_temp_messages_path = None
    reporter._xdist_force_publish_failure = False
    reporter._xdist_compatibility_error = None
    reporter.is_xdist_worker = _is_xdist_worker_process(reporter.config)
    reporter.is_xdist_controller = False
    reporter.requested_cucumber_formatters = resolve_requested_cucumber_formatters(
        reporter.config,
        resolve_output_path=reporter._resolve_output_path,
    )
    reporter.live_formatters = reporter.requested_cucumber_formatters
    reporter.deferred_formatters = ()
    reporter._live_formatter_process = None
    reporter._live_formatter_temp_dir = None
    reporter._live_formatter_stdout_thread = None
    reporter._live_formatter_stderr_thread = None
    reporter._live_formatter_failure_message = None
    reporter._live_formatter_session_started = False
    reporter._restore_terminal_reporter = None
    reporter._process_messages_thread_error = None
    reporter._live_formatter_envelope_adapter = CucumberFormatterEnvelopeAdapter()
    reporter.is_messages_file_temp = False
    reporter._services = ()
    reporter._hook_services = ()

    reporter.is_disabled = all(
        [
            reporter.config.option.messages_ndjson_path is None,
            reporter.config.option.cucumber_html_path is None,
            not reporter.requested_cucumber_formatters,
        ],
    )

    if reporter.is_disabled:
        return

    reporter.is_messages_file_temp = reporter.config.option.messages_ndjson_path is None
    if reporter.is_messages_file_temp:
        handle, messages_file_path_raw = tempfile.mkstemp(suffix=".ndjson")
        os.close(handle)
        reporter.final_messages_file_path = Path(messages_file_path_raw)
    else:
        reporter.final_messages_file_path = reporter._resolve_output_path(reporter.config.option.messages_ndjson_path)
        reporter.final_messages_file_path.parent.mkdir(parents=True, exist_ok=True)
        if not reporter.is_xdist_worker:
            reporter.final_messages_file_path.write_text("", encoding="utf-8")

    reporter.messages_file_path = reporter.final_messages_file_path
    if reporter.is_xdist_worker:
        handle, messages_file_path_raw = tempfile.mkstemp(prefix="pytest-bdd-xdist-worker-", suffix=".ndjson")
        os.close(handle)
        reporter._xdist_worker_temp_messages_path = Path(messages_file_path_raw)
        reporter.messages_file_path = reporter._xdist_worker_temp_messages_path
        reporter._xdist_force_publish_failure = bool(
            getattr(reporter.config, "workerinput", {}).get("pytest_bdd_messages_force_publish_failure"),
        )


def assemble_reporter_runtime(reporter: GherkinMessageReporter) -> ReporterServiceGraph:
    """Handle assemble reporter runtime."""
    live_formatter_service = LiveFormatterService(reporter=reporter)
    transport_service = TransportService(reporter=reporter, live_formatter_service=live_formatter_service)
    lifecycle_service = LifecycleService(
        reporter=reporter,
        transport_service=transport_service,
        live_formatter_service=live_formatter_service,
    )
    hook_catalog_service = HookCatalogService(reporter=reporter, lifecycle_service=lifecycle_service)
    step_catalog_service = StepCatalogService(
        reporter=reporter,
        lifecycle_service=lifecycle_service,
        hook_catalog_service=hook_catalog_service,
    )
    scenario_service = ScenarioService(
        reporter=reporter,
        lifecycle_service=lifecycle_service,
        transport_service=transport_service,
    )
    attachment_service = AttachmentService(reporter=reporter, lifecycle_service=lifecycle_service)
    hook_services = (
        lifecycle_service,
        transport_service,
        hook_catalog_service,
        step_catalog_service,
        scenario_service,
        attachment_service,
    )
    return ReporterServiceGraph(
        lifecycle_service=lifecycle_service,
        transport_service=transport_service,
        hook_catalog_service=hook_catalog_service,
        step_catalog_service=step_catalog_service,
        scenario_service=scenario_service,
        attachment_service=attachment_service,
        live_formatter_service=live_formatter_service,
        hook_services=hook_services,
        services=(*hook_services, live_formatter_service),
    )


def finalize_reporter_runtime(reporter: GherkinMessageReporter) -> None:
    """Handle finalize reporter runtime."""
    if reporter.is_disabled:
        return

    if reporter.is_xdist_worker:
        reporter.transport_service._ensure_xdist_worker_transport_client(require_sender=False)

    if reporter.config.option.cucumber_html_path is not None:
        html_report_path = reporter._resolve_output_path(reporter.config.option.cucumber_html_path)
        html_report_path.parent.mkdir(parents=True, exist_ok=True)
        reporter.config.option.cucumber_html_path = str(html_report_path)
        reporter.live_formatter_service.check_npm_and_cucumber_packages()
