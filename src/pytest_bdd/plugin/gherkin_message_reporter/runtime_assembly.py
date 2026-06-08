"""
Provide runtime assembly helpers.

Responsibility:
    Provide runtime assembly helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - ReporterServiceGraph: owns nested behavior below this boundary
    - initialize_reporter_runtime: owns nested behavior below this boundary
    - assemble_reporter_runtime: owns nested behavior below this boundary
    - finalize_reporter_runtime: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `runtime_assembly`

State and side effects:
    mutates lifecycle_service, transport_service, hook_catalog_service, step_catalog_service, scenario_service; depends
    on __future__.annotations, os, tempfile, pathlib.Path, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly` keeps its documented import path, ownership
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
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from attrs import frozen

from pytest_bdd.model.cucumber_formatter_adapter import CucumberFormatterEnvelopeAdapter
from pytest_bdd.model.message_stream_validation import default_outcome_mapping_rules
from pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime import AttachmentService
from pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime import HookCatalogService
from pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime import IdeBindingService
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
    """
    Represent reporter service graph state.

    Responsibility:
        Represent reporter service graph state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly.ReporterServiceGraph` because it keeps the nearest
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
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `ReporterServiceGraph`

    State and side effects:
        mutates lifecycle_service, transport_service, hook_catalog_service, step_catalog_service, scenario_service.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly.ReporterServiceGraph` keeps its documented import
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
        #arch-eval:locational_stability=3
    """

    lifecycle_service: LifecycleService
    transport_service: TransportService
    hook_catalog_service: HookCatalogService
    step_catalog_service: StepCatalogService
    scenario_service: ScenarioService
    attachment_service: AttachmentService
    ide_binding_service: IdeBindingService
    live_formatter_service: LiveFormatterService
    hook_services: tuple[object, ...]
    services: tuple[object, ...]


def initialize_reporter_runtime(reporter: GherkinMessageReporter) -> None:  # noqa: PLR0915
    """
    Handle initialize reporter runtime.

    Responsibility:
        Handle initialize reporter runtime. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly.initialize_reporter_runtime` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - set: collaborator call used by this boundary
        - tempfile.mkstemp: collaborator call used by this boundary
        - os.close: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - default_outcome_mapping_rules: collaborator call used by this boundary
        - _is_xdist_worker_process: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `initialize_reporter_runtime`

    State and side effects:
        mutates reporter._xdist_worker_temp_messages_path, reporter._xdist_force_publish_failure,
        reporter.is_messages_file_temp, handle, messages_file_path_raw.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly.initialize_reporter_runtime` keeps its documented
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
        #arch-eval:locational_stability=3
    """
    reporter.parameter_type_registry = set()
    reporter.hook_registry = set()
    reporter.hook_registration_registry = {}
    reporter._disabled_warning_emitted = False  # noqa: SLF001
    reporter._outcome_mapping_rules = default_outcome_mapping_rules()  # noqa: SLF001
    reporter._mapping_diagnostics_count = 0  # noqa: SLF001
    reporter._emitted_step_definition_ids = set()  # noqa: SLF001
    reporter._emitted_run_hook_definition_ids = set()  # noqa: SLF001
    reporter._auto_provisioned_node_modules_roots = ()  # noqa: SLF001
    reporter._xdist_fragment_records = {}  # noqa: SLF001
    reporter.xdist_fragment_dir = None
    reporter.xdist_transport_session = None
    reporter.xdist_transport_client = None
    reporter._xdist_worker_temp_messages_path = None  # noqa: SLF001
    reporter._xdist_force_publish_failure = False  # noqa: SLF001
    reporter._xdist_compatibility_error = None  # noqa: SLF001
    reporter.is_xdist_worker = _is_xdist_worker_process(reporter.config)
    reporter.is_xdist_controller = False
    reporter.requested_cucumber_formatters = resolve_requested_cucumber_formatters(
        reporter.config,
        resolve_output_path=reporter._resolve_output_path,  # noqa: SLF001
    )
    reporter.live_formatters = reporter.requested_cucumber_formatters
    reporter.deferred_formatters = ()
    reporter._live_formatter_process = None  # noqa: SLF001
    reporter._live_formatter_temp_dir = None  # noqa: SLF001
    reporter._live_formatter_stdout_thread = None  # noqa: SLF001
    reporter._live_formatter_stderr_thread = None  # noqa: SLF001
    reporter._live_formatter_failure_message = None  # noqa: SLF001
    reporter._live_formatter_session_started = False  # noqa: SLF001
    reporter._restore_terminal_reporter = None  # noqa: SLF001
    reporter._process_messages_thread_error = None  # noqa: SLF001
    reporter._live_formatter_envelope_adapter = CucumberFormatterEnvelopeAdapter()  # noqa: SLF001
    reporter.is_messages_file_temp = False
    reporter._services = ()  # noqa: SLF001
    reporter._hook_services = ()  # noqa: SLF001

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
        reporter.final_messages_file_path = reporter._resolve_output_path(reporter.config.option.messages_ndjson_path)  # noqa: SLF001
        reporter.final_messages_file_path.parent.mkdir(parents=True, exist_ok=True)
        if not reporter.is_xdist_worker:
            reporter.final_messages_file_path.write_text("", encoding="utf-8")

    reporter.messages_file_path = reporter.final_messages_file_path
    if reporter.is_xdist_worker:
        handle, messages_file_path_raw = tempfile.mkstemp(prefix="pytest-bdd-xdist-worker-", suffix=".ndjson")
        os.close(handle)
        reporter._xdist_worker_temp_messages_path = Path(messages_file_path_raw)  # noqa: SLF001
        reporter.messages_file_path = reporter._xdist_worker_temp_messages_path  # noqa: SLF001
        reporter._xdist_force_publish_failure = bool(  # noqa: SLF001
            getattr(reporter.config, "workerinput", {}).get("pytest_bdd_messages_force_publish_failure"),
        )


def assemble_reporter_runtime(reporter: GherkinMessageReporter) -> ReporterServiceGraph:
    """
    Assemble reporter runtime services.

    Returns:
        Reporter service graph.

    Responsibility:
        Assemble reporter runtime services. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly.assemble_reporter_runtime` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - LiveFormatterService: collaborator call used by this boundary
        - TransportService: collaborator call used by this boundary
        - LifecycleService: collaborator call used by this boundary
        - HookCatalogService: collaborator call used by this boundary
        - StepCatalogService: collaborator call used by this boundary
        - ScenarioService: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `assemble_reporter_runtime`

    State and side effects:
        mutates live_formatter_service, transport_service, lifecycle_service, hook_catalog_service,
        step_catalog_service.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly.assemble_reporter_runtime` keeps its documented
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
        #arch-eval:locational_stability=3

    """
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
    ide_binding_service = IdeBindingService(reporter=reporter, lifecycle_service=lifecycle_service)
    hook_services = (
        lifecycle_service,
        transport_service,
        hook_catalog_service,
        step_catalog_service,
        scenario_service,
        attachment_service,
        ide_binding_service,
    )
    return ReporterServiceGraph(
        lifecycle_service=lifecycle_service,
        transport_service=transport_service,
        hook_catalog_service=hook_catalog_service,
        step_catalog_service=step_catalog_service,
        scenario_service=scenario_service,
        attachment_service=attachment_service,
        ide_binding_service=ide_binding_service,
        live_formatter_service=live_formatter_service,
        hook_services=hook_services,
        services=(*hook_services, live_formatter_service),
    )


def finalize_reporter_runtime(reporter: GherkinMessageReporter) -> None:
    """
    Handle finalize reporter runtime.

    Responsibility:
        Handle finalize reporter runtime. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly.finalize_reporter_runtime` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - reporter.transport_service._ensure_xdist_worker_transport_client: collaborator call used by this boundary
        - reporter._resolve_output_path: collaborator call used by this boundary
        - html_report_path.parent.mkdir: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - reporter.live_formatter_service.check_npm_and_cucumber_packages: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `finalize_reporter_runtime`

    State and side effects:
        mutates html_report_path, reporter.config.option.cucumber_html_path.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly.finalize_reporter_runtime` keeps its documented
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
        #arch-eval:locational_stability=3
    """
    if reporter.is_disabled:
        return

    if reporter.is_xdist_worker:
        reporter.transport_service._ensure_xdist_worker_transport_client(require_sender=False)  # noqa: SLF001

    if reporter.config.option.cucumber_html_path is not None:
        html_report_path = reporter._resolve_output_path(reporter.config.option.cucumber_html_path)  # noqa: SLF001
        html_report_path.parent.mkdir(parents=True, exist_ok=True)
        reporter.config.option.cucumber_html_path = str(html_report_path)
        reporter.live_formatter_service.check_npm_and_cucumber_packages()
