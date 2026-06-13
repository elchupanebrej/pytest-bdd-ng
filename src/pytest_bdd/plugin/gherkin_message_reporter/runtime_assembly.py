"""
Implement plugin module operations for pytest-bdd.

Responsibility:
    Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
    consumed by the broader BDD infrastructure.

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion and serve as the information
    expert for its domain concepts.

Delegates:
    - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

Cohesion:
    All logic within this entity operates on a single responsibility domain with focused imports and control flow.

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

Main consumers:
    - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

State and side effects:
    None, keeps no persistent state beyond local scope.

Invariants:
    - All public API contracts defined by this entity must be honored by callers.

Architecture score:
    #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
    #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
    #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
    #arch-eval:cohesion=4  # Internal logic focus (1-5)
    #arch-eval:separation=4  # Distinctness from peers (1-5)
    #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
    #arch-eval:state_invariants=4  # Control of state mutations (1-5)
    #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
    #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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


def initialize_reporter_runtime(reporter: GherkinMessageReporter) -> None:  # noqa: PLR0915  -- suppressed warning
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    reporter.parameter_type_registry = set()
    reporter.hook_registry = set()
    reporter.hook_registration_registry = {}
    reporter._disabled_warning_emitted = False  # noqa: SLF001  -- suppressed warning
    reporter._outcome_mapping_rules = default_outcome_mapping_rules()  # noqa: SLF001  -- suppressed warning
    reporter._mapping_diagnostics_count = 0  # noqa: SLF001  -- suppressed warning
    reporter._emitted_step_definition_ids = set()  # noqa: SLF001  -- suppressed warning
    reporter._emitted_run_hook_definition_ids = set()  # noqa: SLF001  -- suppressed warning
    reporter._auto_provisioned_node_modules_roots = ()  # noqa: SLF001  -- suppressed warning
    reporter._xdist_fragment_records = {}  # noqa: SLF001  -- suppressed warning
    reporter.xdist_fragment_dir = None
    reporter.xdist_transport_session = None
    reporter.xdist_transport_client = None
    reporter._xdist_worker_temp_messages_path = None  # noqa: SLF001  -- suppressed warning
    reporter._xdist_force_publish_failure = False  # noqa: SLF001  -- suppressed warning
    reporter._xdist_compatibility_error = None  # noqa: SLF001  -- suppressed warning
    reporter.is_xdist_worker = _is_xdist_worker_process(reporter.config)
    reporter.is_xdist_controller = False
    reporter.requested_cucumber_formatters = resolve_requested_cucumber_formatters(
        reporter.config,
        resolve_output_path=reporter._resolve_output_path,  # noqa: SLF001  -- suppressed warning
    )
    reporter.live_formatters = reporter.requested_cucumber_formatters
    reporter.deferred_formatters = ()
    reporter._live_formatter_process = None  # noqa: SLF001  -- suppressed warning
    reporter._live_formatter_temp_dir = None  # noqa: SLF001  -- suppressed warning
    reporter._live_formatter_stdout_thread = None  # noqa: SLF001  -- suppressed warning
    reporter._live_formatter_stderr_thread = None  # noqa: SLF001  -- suppressed warning
    reporter._live_formatter_failure_message = None  # noqa: SLF001  -- suppressed warning
    reporter._live_formatter_session_started = False  # noqa: SLF001  -- suppressed warning
    reporter._restore_terminal_reporter = None  # noqa: SLF001  -- suppressed warning
    reporter._process_messages_thread_error = None  # noqa: SLF001  -- suppressed warning
    reporter._live_formatter_envelope_adapter = CucumberFormatterEnvelopeAdapter()  # noqa: SLF001  -- suppressed warning
    reporter.is_messages_file_temp = False
    reporter._services = ()  # noqa: SLF001  -- suppressed warning
    reporter._hook_services = ()  # noqa: SLF001  -- suppressed warning

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
        reporter.final_messages_file_path = reporter._resolve_output_path(reporter.config.option.messages_ndjson_path)  # noqa: SLF001  -- suppressed warning
        reporter.final_messages_file_path.parent.mkdir(parents=True, exist_ok=True)
        if not reporter.is_xdist_worker:
            reporter.final_messages_file_path.write_text("", encoding="utf-8")

    reporter.messages_file_path = reporter.final_messages_file_path
    if reporter.is_xdist_worker:
        handle, messages_file_path_raw = tempfile.mkstemp(prefix="pytest-bdd-xdist-worker-", suffix=".ndjson")
        os.close(handle)
        reporter._xdist_worker_temp_messages_path = Path(messages_file_path_raw)  # noqa: SLF001  -- suppressed warning
        reporter.messages_file_path = reporter._xdist_worker_temp_messages_path  # noqa: SLF001  -- suppressed warning
        reporter._xdist_force_publish_failure = bool(  # noqa: SLF001  -- suppressed warning
            getattr(reporter.config, "workerinput", {}).get("pytest_bdd_messages_force_publish_failure"),
        )


def assemble_reporter_runtime(reporter: GherkinMessageReporter) -> ReporterServiceGraph:
    """
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    if reporter.is_disabled:
        return

    if reporter.is_xdist_worker:
        reporter.transport_service._ensure_xdist_worker_transport_client(require_sender=False)  # noqa: SLF001  -- suppressed warning

    if reporter.config.option.cucumber_html_path is not None:
        html_report_path = reporter._resolve_output_path(reporter.config.option.cucumber_html_path)  # noqa: SLF001  -- suppressed warning
        html_report_path.parent.mkdir(parents=True, exist_ok=True)
        reporter.config.option.cucumber_html_path = str(html_report_path)
        reporter.live_formatter_service.check_npm_and_cucumber_packages()
