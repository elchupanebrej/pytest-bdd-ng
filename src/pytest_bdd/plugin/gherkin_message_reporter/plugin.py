"""
Provide plugin helpers.

Responsibility:
    Provide plugin helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.plugin` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _HookNamedService: owns nested behavior below this boundary
    - GherkinMessageReporter: owns nested behavior below this boundary
    - GherkinMessageReporterPlugin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `plugin`
    - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references `plugin`
    - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `plugin`
    - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references `plugin`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `plugin`

State and side effects:
    mutates plugin_name, path, self._restore_terminal_reporter, named_hook_service, logger; depends on
    __future__.annotations, logging, pathlib.Path, threading.Lock, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.plugin` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

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
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, ClassVar, Protocol, cast

from attrs import define, field

from pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly import (
    assemble_reporter_runtime,
    finalize_reporter_runtime,
    initialize_reporter_runtime,
)
from pytest_bdd.plugin.gherkin_message_reporter.session import (
    CucumberFormatterConfigurationError as _CucumberFormatterConfigurationError,
)
from pytest_bdd.plugin.gherkin_message_reporter.session import (
    CucumberFormatterRenderResult,
    CucumberFormatterRequest,
    render_live_formatter_runtime_assets,
    terminal_output_formatter_requests,
)

if TYPE_CHECKING:
    import tempfile
    from collections.abc import Callable
    from queue import Queue
    from threading import Event, Thread

    from cucumber_messages import (
        Envelope as Message,  # upstream library missing type stubs
    )

    from pytest_bdd.compatibility.pytest import Config, PytestPluginManager
    from pytest_bdd.model.cucumber_formatter_adapter import CucumberFormatterEnvelopeAdapter
    from pytest_bdd.model.message_outcome_mapping import OutcomeMappingRule
    from pytest_bdd.model.message_transport import ReportingTransportClient, ReportingTransportSession
    from pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime import AttachmentService
    from pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime import HookCatalogService
    from pytest_bdd.plugin.gherkin_message_reporter.ide_binding_runtime import IdeBindingService
    from pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime import LifecycleService
    from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime import (
        LiveFormatterProcess,
        LiveFormatterService,
    )
    from pytest_bdd.plugin.gherkin_message_reporter.runtime_support import HookRegistration
    from pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime import ScenarioService
    from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase
    from pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime import StepCatalogService
    from pytest_bdd.plugin.gherkin_message_reporter.transport_runtime import TransportService


class _HookNamedService(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.plugin._HookNamedService` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.plugin._HookNamedService`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
          `_HookNamedService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `_HookNamedService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
          `_HookNamedService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_HookNamedService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `_HookNamedService`

    State and side effects:
        mutates plugin_name.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.plugin._HookNamedService` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    plugin_name: str


logger = logging.getLogger(__name__)
CucumberFormatterConfigurationError = _CucumberFormatterConfigurationError


@define(eq=False, auto_attribs=False, slots=False)
class GherkinMessageReporter:
    """
    Represent gherkin message reporter state.

    Responsibility:
        Represent gherkin message reporter state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - __attrs_post_init__: owns nested behavior below this boundary
        - _resolve_output_path: owns nested behavior below this boundary
        - _terminal_output_formatter_requests: owns nested behavior below this boundary
        - activate_quiet_terminal_output: owns nested behavior below this boundary
        - restore_terminal_output: owns nested behavior below this boundary
        - services: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
          `GherkinMessageReporter`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `GherkinMessageReporter`
        - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
          `GherkinMessageReporter`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `GherkinMessageReporter`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
          `GherkinMessageReporter`

    State and side effects:
        mutates path, self._restore_terminal_reporter, named_hook_service, BEFORE_TEST_RUN_HOOK_ID,
        AFTER_TEST_RUN_HOOK_ID.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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

    BEFORE_TEST_RUN_HOOK_ID: ClassVar[str] = "pytest-bdd-ng.before-test-run"
    AFTER_TEST_RUN_HOOK_ID: ClassVar[str] = "pytest-bdd-ng.after-test-run"
    config: Config = field()
    parameter_type_registry: set[int]
    hook_registry: set[int]
    hook_registration_registry: dict[int, HookRegistration]
    npm_formatter_package: ClassVar[str] = "@cucumber/html-formatter"
    plugin_name: str = "pytest-bdd-internal-gherkin-message-reporter"

    process_messages_io_queue: Queue[str]
    process_messages_stop_event: Event
    process_messages_thread: Thread
    final_messages_file_path: Path
    messages_file_path: Path
    is_messages_file_temp: bool
    xdist_fragment_dir: Path | None
    _xdist_fragment_records: dict[str, dict[str, object]]
    xdist_transport_session: ReportingTransportSession | None
    xdist_transport_client: ReportingTransportClient | None
    _xdist_worker_temp_messages_path: Path | None
    _xdist_force_publish_failure: bool
    _xdist_compatibility_error: str | None
    _disabled_warning_emitted: bool
    _outcome_mapping_rules: list[OutcomeMappingRule]
    _mapping_diagnostics_count: int
    _emitted_step_definition_ids: set[str]
    _emitted_run_hook_definition_ids: set[str]
    requested_cucumber_formatters: tuple[CucumberFormatterRequest, ...]
    live_formatters: tuple[CucumberFormatterRequest, ...]
    deferred_formatters: tuple[CucumberFormatterRequest, ...]
    _live_formatter_process: LiveFormatterProcess | None
    _live_formatter_temp_dir: tempfile.TemporaryDirectory[str] | None
    _live_formatter_lock: Lock
    _live_formatter_stdout_thread: Thread | None
    _live_formatter_stderr_thread: Thread | None
    _live_formatter_failure_message: str | None
    _live_formatter_session_started: bool
    _live_formatter_envelope_adapter: CucumberFormatterEnvelopeAdapter
    _auto_provisioned_node_modules_roots: tuple[Path, ...]
    _restore_terminal_reporter: Callable[[], None] | None
    _process_messages_thread_error: Exception | None
    is_xdist_worker: bool
    is_xdist_controller: bool
    is_disabled: bool
    lifecycle_service: LifecycleService
    transport_service: TransportService
    hook_catalog_service: HookCatalogService
    step_catalog_service: StepCatalogService
    scenario_service: ScenarioService
    attachment_service: AttachmentService
    ide_binding_service: IdeBindingService
    live_formatter_service: LiveFormatterService
    _services: tuple[ReporterServiceBase, ...]
    _hook_services: tuple[ReporterServiceBase, ...]

    def __attrs_post_init__(self) -> None:
        """
        Initialize reporter runtime services.

        Responsibility:
            Initialize reporter runtime services. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.__attrs_post_init__` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - Lock: collaborator call used by this boundary
            - initialize_reporter_runtime: collaborator call used by this boundary
            - assemble_reporter_runtime: collaborator call used by this boundary
            - finalize_reporter_runtime: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `__attrs_post_init__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `__attrs_post_init__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `__attrs_post_init__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `__attrs_post_init__`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `__attrs_post_init__`

        State and side effects:
            mutates self._live_formatter_lock, service_graph, self.lifecycle_service, self.transport_service,
            self.hook_catalog_service.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.__attrs_post_init__` keeps its
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
        self._live_formatter_lock = Lock()
        initialize_reporter_runtime(self)
        service_graph = assemble_reporter_runtime(self)
        self.lifecycle_service = service_graph.lifecycle_service
        self.transport_service = service_graph.transport_service
        self.hook_catalog_service = service_graph.hook_catalog_service
        self.step_catalog_service = service_graph.step_catalog_service
        self.scenario_service = service_graph.scenario_service
        self.attachment_service = service_graph.attachment_service
        self.ide_binding_service = service_graph.ide_binding_service
        self.live_formatter_service = service_graph.live_formatter_service
        self._hook_services = cast("tuple[ReporterServiceBase, ...]", service_graph.hook_services)
        self._services = cast("tuple[ReporterServiceBase, ...]", service_graph.services)
        finalize_reporter_runtime(self)

    def _resolve_output_path(self, output_path: str) -> Path:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter._resolve_output_path` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter._resolve_output_path` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Path: collaborator call used by this boundary
            - path.is_absolute: collaborator call used by this boundary
            - path.resolve: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `_resolve_output_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `_resolve_output_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `_resolve_output_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_resolve_output_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `_resolve_output_path`

        State and side effects:
            mutates path.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter._resolve_output_path` keeps its
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
        path = Path(output_path)
        if not path.is_absolute():
            path = Path(self.config.rootpath) / path
        return path.resolve()

    @classmethod
    def _terminal_output_formatter_requests(
        cls,
        formatter_requests: list[CucumberFormatterRequest],
    ) -> list[CucumberFormatterRequest]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter._terminal_output_formatter_requests`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter._terminal_output_formatter_requests`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - terminal_output_formatter_requests: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `_terminal_output_formatter_requests`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `_terminal_output_formatter_requests`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `_terminal_output_formatter_requests`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_terminal_output_formatter_requests`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `_terminal_output_formatter_requests`

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
        return terminal_output_formatter_requests(formatter_requests)

    def activate_quiet_terminal_output(
        self,
        *,
        quiet_terminal_replacer: Callable[[Config], Callable[[], None] | None],
    ) -> None:
        """
        Handle activate quiet terminal output.

        Responsibility:
            Handle activate quiet terminal output. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.activate_quiet_terminal_output`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - type._terminal_output_formatter_requests: collaborator call used by this boundary
            - type: collaborator call used by this boundary
            - list: collaborator call used by this boundary
            - quiet_terminal_replacer: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `activate_quiet_terminal_output`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `activate_quiet_terminal_output`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `activate_quiet_terminal_output`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `activate_quiet_terminal_output`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `activate_quiet_terminal_output`

        State and side effects:
            mutates terminal_requests, self._restore_terminal_reporter.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.activate_quiet_terminal_output`
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
        terminal_requests = type(self)._terminal_output_formatter_requests(list(self.requested_cucumber_formatters))  # noqa: SLF001
        if not terminal_requests:
            return
        if not self._live_formatter_session_started:
            return
        if self._live_formatter_failure_message is not None:
            return
        self._restore_terminal_reporter = quiet_terminal_replacer(self.config)

    def restore_terminal_output(self) -> None:
        """
        Handle restore terminal output.

        Responsibility:
            Handle restore terminal output. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.restore_terminal_output` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._restore_terminal_reporter: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `restore_terminal_output`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `restore_terminal_output`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `restore_terminal_output`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `restore_terminal_output`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `restore_terminal_output`

        State and side effects:
            mutates self._restore_terminal_reporter.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.restore_terminal_output` keeps
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
        if self._restore_terminal_reporter is None:
            return
        self._restore_terminal_reporter()
        self._restore_terminal_reporter = None

    @property
    def services(self) -> tuple[object, ...]:
        """
        Handle services.

        Responsibility:
            Handle services. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.services` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references `services`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `services`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references `services`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `services`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references `services`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        return self._services

    def read_envelopes_from_path(self, messages_file_path: Path) -> list[Message]:
        """
        Read envelopes from a messages file.

        Args:
            messages_file_path: Path to messages NDJSON file.

        Returns:
            List of message envelopes.

        Responsibility:
            Read envelopes from a messages file. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.read_envelopes_from_path` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.transport_service.read_envelopes_from_path: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `read_envelopes_from_path`

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
        return self.transport_service.read_envelopes_from_path(messages_file_path)

    def render_requested_cucumber_formatters(
        self,
        envelopes: list[Message],
    ) -> CucumberFormatterRenderResult:
        """
        Render requested cucumber formatters.

        Args:
            envelopes: List of message envelopes.

        Returns:
            Render result.

        Responsibility:
            Render requested cucumber formatters. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.render_requested_cucumber_formatters`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.live_formatter_service.run_requested_cucumber_formatters: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `render_requested_cucumber_formatters`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `render_requested_cucumber_formatters`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `render_requested_cucumber_formatters`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `render_requested_cucumber_formatters`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `render_requested_cucumber_formatters`

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
        return self.live_formatter_service.run_requested_cucumber_formatters(envelopes)

    def render_requested_cucumber_formatters_from_path(
        self,
        messages_file_path: Path,
    ) -> CucumberFormatterRenderResult:
        """
        Render requested cucumber formatters from a file.

        Args:
            messages_file_path: Path to messages file.

        Returns:
            Render result.

        Responsibility:
            Render requested cucumber formatters from a file. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.render_requested_cucumber_formatters_from_path`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.read_envelopes_from_path: collaborator call used by this boundary
            - self.render_requested_cucumber_formatters: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `render_requested_cucumber_formatters_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `render_requested_cucumber_formatters_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `render_requested_cucumber_formatters_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `render_requested_cucumber_formatters_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `render_requested_cucumber_formatters_from_path`

        State and side effects:
            mutates envelopes.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.render_requested_cucumber_formatters_from_path`
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
        envelopes = self.read_envelopes_from_path(messages_file_path)
        return self.render_requested_cucumber_formatters(envelopes)

    def render_runtime_assets(
        self,
        formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
    ) -> dict[str, str]:
        """
        Render runtime assets for formatters.

        Args:
            formatter_requests: List of formatter requests.

        Returns:
            Dictionary of rendered assets.

        Responsibility:
            Render runtime assets for formatters. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.render_runtime_assets` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - render_live_formatter_runtime_assets: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `render_runtime_assets`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `render_runtime_assets`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `render_runtime_assets`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `render_runtime_assets`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `render_runtime_assets`

        State and side effects:
            mutates pluginmanager.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.render_runtime_assets` keeps its
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
        pluginmanager = getattr(self.config, "pluginmanager", None)
        return render_live_formatter_runtime_assets(formatter_requests, pluginmanager=pluginmanager)

    def register_hook_plugins(self, pluginmanager: PytestPluginManager) -> None:
        """
        Register hook plugins.

        Responsibility:
            Register hook plugins. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.register_hook_plugins` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - pluginmanager.register: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `register_hook_plugins`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `register_hook_plugins`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `register_hook_plugins`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `register_hook_plugins`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `register_hook_plugins`

        State and side effects:
            mutates named_hook_service.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.register_hook_plugins` keeps its
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
        for hook_service in self._hook_services:
            named_hook_service = cast("_HookNamedService", hook_service)
            pluginmanager.register(named_hook_service, name=named_hook_service.plugin_name)

    def unregister_hook_plugins(self, pluginmanager: PytestPluginManager) -> None:
        """
        Handle unregister hook plugins.

        Responsibility:
            Handle unregister hook plugins. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.unregister_hook_plugins` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - reversed: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - pluginmanager.unregister: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
              `unregister_hook_plugins`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `unregister_hook_plugins`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
              `unregister_hook_plugins`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `unregister_hook_plugins`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py: imports or references
              `unregister_hook_plugins`

        State and side effects:
            mutates named_hook_service.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.unregister_hook_plugins` keeps
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
        for hook_service in reversed(self._hook_services):
            named_hook_service = cast("_HookNamedService", hook_service)
            pluginmanager.unregister(named_hook_service)

    def configure(
        self,
        *,
        pluginmanager: PytestPluginManager,
        quiet_terminal_replacer: Callable[[Config], Callable[[], None] | None],
    ) -> None:
        """
        Configure configure.

        Responsibility:
            Configure configure. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.configure` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.live_formatter_service._start_live_formatters: collaborator call used by this boundary
            - self.activate_quiet_terminal_output: collaborator call used by this boundary
            - self.register_hook_plugins: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references `configure`
            - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references `configure`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `configure`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references `configure`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `configure`

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
        self.live_formatter_service._start_live_formatters()  # noqa: SLF001
        self.activate_quiet_terminal_output(quiet_terminal_replacer=quiet_terminal_replacer)
        self.register_hook_plugins(pluginmanager)

    def unconfigure(self, *, pluginmanager: PytestPluginManager) -> None:
        """
        Handle unconfigure.

        Responsibility:
            Handle unconfigure. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporter.unconfigure` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.restore_terminal_output: collaborator call used by this boundary
            - self.unregister_hook_plugins: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references `unconfigure`
            - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references `unconfigure`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
              `unconfigure`
            - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references `unconfigure`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `unconfigure`

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
        self.restore_terminal_output()
        self.unregister_hook_plugins(pluginmanager)


class GherkinMessageReporterPlugin(GherkinMessageReporter):
    """
    Represent gherkin message reporter plugin state.

    Responsibility:
        Represent gherkin message reporter plugin state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporterPlugin` because it keeps the nearest
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
        - src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py: imports or references
          `GherkinMessageReporterPlugin`
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
          `GherkinMessageReporterPlugin`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `GherkinMessageReporterPlugin`
        - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py: imports or references
          `GherkinMessageReporterPlugin`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `GherkinMessageReporterPlugin`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.plugin.GherkinMessageReporterPlugin` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """
