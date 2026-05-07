from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, ClassVar, Protocol, cast

from attrs import define, field

from pytest_bdd.compatibility.pytest import (
    Config,
    PytestPluginManager,
    get_config_root_path,
)
from pytest_bdd.plugin.gherkin_message_reporter.runtime_assembly import (
    assemble_reporter_runtime,
    finalize_reporter_runtime,
    initialize_reporter_runtime,
)
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase
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

    from cucumber_messages import Envelope as Message  # type:ignore[attr-defined, import-untyped]

    from pytest_bdd.model.cucumber_formatter_adapter import CucumberFormatterEnvelopeAdapter
    from pytest_bdd.model.message_outcome_mapping import OutcomeMappingRule
    from pytest_bdd.model.message_transport import ReportingTransportClient, ReportingTransportSession
    from pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime import AttachmentService
    from pytest_bdd.plugin.gherkin_message_reporter.hook_catalog_runtime import HookCatalogService
    from pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime import LifecycleService
    from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime import (
        LiveFormatterProcess,
        LiveFormatterService,
    )
    from pytest_bdd.plugin.gherkin_message_reporter.runtime_support import HookRegistration
    from pytest_bdd.plugin.gherkin_message_reporter.scenario_runtime import ScenarioService
    from pytest_bdd.plugin.gherkin_message_reporter.step_catalog_runtime import StepCatalogService
    from pytest_bdd.plugin.gherkin_message_reporter.transport_runtime import TransportService


class _HookNamedService(Protocol):
    plugin_name: str


logger = logging.getLogger(__name__)
CucumberFormatterConfigurationError = _CucumberFormatterConfigurationError


@define(eq=False, auto_attribs=False, slots=False)
class GherkinMessageReporter:
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
    _live_formatter_temp_dir: tempfile.TemporaryDirectory | None
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
    live_formatter_service: LiveFormatterService
    _services: tuple[ReporterServiceBase, ...]
    _hook_services: tuple[ReporterServiceBase, ...]

    def __attrs_post_init__(self) -> None:
        """Initialize reporter runtime services."""
        self._live_formatter_lock = Lock()
        initialize_reporter_runtime(self)
        service_graph = assemble_reporter_runtime(self)
        self.lifecycle_service = service_graph.lifecycle_service
        self.transport_service = service_graph.transport_service
        self.hook_catalog_service = service_graph.hook_catalog_service
        self.step_catalog_service = service_graph.step_catalog_service
        self.scenario_service = service_graph.scenario_service
        self.attachment_service = service_graph.attachment_service
        self.live_formatter_service = service_graph.live_formatter_service
        self._hook_services = cast(tuple[ReporterServiceBase, ...], service_graph.hook_services)
        self._services = cast(tuple[ReporterServiceBase, ...], service_graph.services)
        finalize_reporter_runtime(self)

    def _resolve_output_path(self, output_path: str) -> Path:
        path = Path(output_path)
        if not path.is_absolute():
            path = get_config_root_path(self.config) / path
        return path.resolve()

    @classmethod
    def _terminal_output_formatter_requests(
        cls,
        formatter_requests: list[CucumberFormatterRequest],
    ) -> list[CucumberFormatterRequest]:
        return terminal_output_formatter_requests(formatter_requests)

    def activate_quiet_terminal_output(
        self,
        *,
        quiet_terminal_replacer: Callable[[Config], Callable[[], None] | None],
    ) -> None:
        terminal_requests = type(self)._terminal_output_formatter_requests(list(self.requested_cucumber_formatters))
        if not terminal_requests:
            return
        if not self._live_formatter_session_started:
            return
        if self._live_formatter_failure_message is not None:
            return
        self._restore_terminal_reporter = quiet_terminal_replacer(self.config)

    def restore_terminal_output(self) -> None:
        if self._restore_terminal_reporter is None:
            return
        self._restore_terminal_reporter()
        self._restore_terminal_reporter = None

    @property
    def services(self) -> tuple[object, ...]:
        return self._services

    def read_envelopes_from_path(self, messages_file_path: Path) -> list[Message]:
        return self.transport_service.read_envelopes_from_path(messages_file_path)

    def render_requested_cucumber_formatters(
        self,
        envelopes: list[Message],
    ) -> CucumberFormatterRenderResult:
        return self.live_formatter_service.run_requested_cucumber_formatters(envelopes)

    def render_requested_cucumber_formatters_from_path(
        self,
        messages_file_path: Path,
    ) -> CucumberFormatterRenderResult:
        envelopes = self.read_envelopes_from_path(messages_file_path)
        return self.render_requested_cucumber_formatters(envelopes)

    def render_runtime_assets(
        self,
        formatter_requests: list[CucumberFormatterRequest] | tuple[CucumberFormatterRequest, ...],
    ) -> dict[str, str]:
        pluginmanager = getattr(self.config, "pluginmanager", None)
        return render_live_formatter_runtime_assets(formatter_requests, pluginmanager=pluginmanager)

    def register_hook_plugins(self, pluginmanager: PytestPluginManager) -> None:
        for hook_service in self._hook_services:
            named_hook_service = cast(_HookNamedService, hook_service)
            pluginmanager.register(named_hook_service, name=named_hook_service.plugin_name)

    def unregister_hook_plugins(self, pluginmanager: PytestPluginManager) -> None:
        for hook_service in reversed(self._hook_services):
            named_hook_service = cast(_HookNamedService, hook_service)
            pluginmanager.unregister(name=named_hook_service.plugin_name)

    def configure(
        self,
        *,
        pluginmanager: PytestPluginManager,
        quiet_terminal_replacer: Callable[[Config], Callable[[], None] | None],
    ) -> None:
        self.live_formatter_service._start_live_formatters()
        self.activate_quiet_terminal_output(quiet_terminal_replacer=quiet_terminal_replacer)
        self.register_hook_plugins(pluginmanager)

    def unconfigure(self, *, pluginmanager: PytestPluginManager) -> None:
        self.restore_terminal_output()
        self.unregister_hook_plugins(pluginmanager)
