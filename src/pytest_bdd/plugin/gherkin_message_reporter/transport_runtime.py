"""
Provide transport runtime helpers.

Responsibility:
    Provide transport runtime helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _WorkerNode: owns nested behavior below this boundary
    - _configured_transport_fail_worker_ids: owns nested behavior below this boundary
    - TransportService: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
      `transport_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `transport_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `transport_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references `transport_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references `transport_runtime`

State and side effects:
    mutates msg, self.reporter._xdist_compatibility_error, worker_id, workeroutput,
    self.reporter._process_messages_thread_error; depends on __future__.annotations, json, logging, shutil,
    pathlib.Path.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Failure semantics:
    Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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

import json
import logging
import shutil
from pathlib import Path
from pprint import pformat
from queue import Empty, Queue
from threading import Event, Thread
from time import monotonic, sleep
from typing import TYPE_CHECKING, Protocol, cast

import pytest
from filelock import FileLock

from pytest_bdd.model.message_consolidation import MessageFragment, consolidate_message_fragments
from pytest_bdd.model.message_converter import envelope_from_dict
from pytest_bdd.model.message_transport import (
    REPORTING_BATCH_EVENT,
    ReportingTransportClient,
    ReportingTransportSession,
    WorkerCompletionManifest,
    resolve_reporting_event_sender,
)
from pytest_bdd.plugin.gherkin_message_reporter.message_stream import ensure_xdist_controller_batch_patch
from pytest_bdd.plugin.gherkin_message_reporter.runtime_support import (
    _format_reporting_worker_id,
    _is_xdist_worker_process,
    _resolve_reporting_worker_identity,
)
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase
from pytest_bdd.util.live_reporting import (
    node_gateway_mode,
    node_worker_id,
)


class _WorkerNode(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime._WorkerNode` owns
        documented class behavior. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime._WorkerNode` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `_WorkerNode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `_WorkerNode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `_WorkerNode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references `_WorkerNode`
        - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references `_WorkerNode`

    State and side effects:
        mutates workerinput, workeroutput.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime._WorkerNode` keeps its documented import path,
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

    workerinput: dict[str, object]
    workeroutput: dict[str, object]


if TYPE_CHECKING:
    from cucumber_messages import Envelope as Message

    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runtime import LiveFormatterService
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter
    from pytest_bdd.types.json import JSONObject

logger = logging.getLogger(__name__)


def _configured_transport_fail_worker_ids(config: Config) -> set[str]:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime._configured_transport_fail_worker_ids` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime._configured_transport_fail_worker_ids` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - worker_id.strip: collaborator call used by this boundary
        - str.strip: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - raw_value.split: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_configured_transport_fail_worker_ids`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
          `_configured_transport_fail_worker_ids`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `_configured_transport_fail_worker_ids`
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
          `_configured_transport_fail_worker_ids`
        - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
          `_configured_transport_fail_worker_ids`

    State and side effects:
        mutates raw_value.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime._configured_transport_fail_worker_ids` keeps its
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
    raw_value = str(getattr(config, "getini", lambda _name: "")("pytest_bdd_transport_fail_workers") or "").strip()
    if not raw_value:
        return set()
    return {worker_id.strip() for worker_id in raw_value.split(",") if worker_id.strip()}


class TransportService(ReporterServiceBase):
    """
    Represent transport service state.

    Raises:
        RuntimeError: If the operation cannot be completed.

    Responsibility:
        Represent transport service state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _run_process_messages_thread: owns nested behavior below this boundary
        - _ensure_xdist_worker_transport_client: owns nested behavior below this boundary
        - _current_reporting_worker_id: owns nested behavior below this boundary
        - _activate_xdist_controller_mode: owns nested behavior below this boundary
        - pytest_configure_node: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `TransportService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `TransportService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `TransportService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references `TransportService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
          `TransportService`

    State and side effects:
        mutates msg, self.reporter._xdist_compatibility_error, worker_id, self.reporter._process_messages_thread_error,
        gateway_mode.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises RuntimeError; callers must treat these as boundary failures.

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

    plugin_suffix = "transport"

    def __init__(self, reporter: GherkinMessageReporter, *, live_formatter_service: LiveFormatterService) -> None:
        """
        Initialize the transport service.

        Responsibility:
            Initialize the transport service. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.__init__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

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
            mutates self.live_formatter_service.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.__init__` keeps its
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
        self.live_formatter_service = live_formatter_service

    def _run_process_messages_thread(self, *, force_transport_publish_failure: bool) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._run_process_messages_thread`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._run_process_messages_thread`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - type.process_messages: collaborator call used by this boundary
            - type: collaborator call used by this boundary
            - logger.exception: collaborator call used by this boundary
            - self.reporter.process_messages_stop_event.set: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_run_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `_run_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_run_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `_run_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `_run_process_messages_thread`

        State and side effects:
            mutates self.reporter._process_messages_thread_error.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._run_process_messages_thread`
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
        try:
            type(self).process_messages(
                self.reporter.process_messages_io_queue,
                self.reporter.process_messages_stop_event,
                self.reporter.messages_file_path,
                self.reporter.xdist_transport_client if self.reporter.is_xdist_worker else None,
                force_transport_publish_failure=force_transport_publish_failure,
            )
        except Exception as exc:  # pragma: no cover - exercised via finish_process_messages_thread
            self.reporter._process_messages_thread_error = exc  # noqa: SLF001
            logger.exception("Message writer thread crashed before queued envelopes were drained.")
            self.reporter.process_messages_stop_event.set()

    def _ensure_xdist_worker_transport_client(self, *, require_sender: bool) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._ensure_xdist_worker_transport_client`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._ensure_xdist_worker_transport_client`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _is_xdist_worker_process: collaborator call used by this boundary
            - _resolve_reporting_worker_identity: collaborator call used by this boundary
            - resolve_reporting_event_sender: collaborator call used by this boundary
            - ReportingTransportClient: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_ensure_xdist_worker_transport_client`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `_ensure_xdist_worker_transport_client`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_ensure_xdist_worker_transport_client`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `_ensure_xdist_worker_transport_client`
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `_ensure_xdist_worker_transport_client`

        State and side effects:
            mutates self.reporter._xdist_compatibility_error, self.reporter.is_xdist_worker, transport_worker_id,
            gateway_mode, sender.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._ensure_xdist_worker_transport_client`
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
        self.reporter.is_xdist_worker = _is_xdist_worker_process(self.reporter.config)
        if not self.reporter.is_xdist_worker or self.reporter.xdist_transport_client is not None:
            return
        transport_worker_id, gateway_mode = _resolve_reporting_worker_identity(self.reporter.config)
        sender = resolve_reporting_event_sender(self.reporter.config)
        if sender is None:
            if require_sender:
                self.reporter._xdist_compatibility_error = (  # noqa: SLF001
                    "Distributed reporting requires the xdist remote-module adapter; "
                    "worker channel sender was not installed."
                )
            return
        self.reporter.xdist_transport_client = ReportingTransportClient(
            worker_id=str(transport_worker_id),
            sender=sender,
            gateway_mode=gateway_mode or None,
        )
        self.reporter._xdist_compatibility_error = None  # noqa: SLF001

    @staticmethod
    def _current_reporting_worker_id(config: Config) -> str:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._current_reporting_worker_id`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._current_reporting_worker_id`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _resolve_reporting_worker_identity: collaborator call used by this boundary
            - _format_reporting_worker_id: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_current_reporting_worker_id`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `_current_reporting_worker_id`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `_current_reporting_worker_id`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_current_reporting_worker_id`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `_current_reporting_worker_id`

        State and side effects:
            mutates worker_id, gateway_mode.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._current_reporting_worker_id`
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
        worker_id, gateway_mode = _resolve_reporting_worker_identity(config)
        return _format_reporting_worker_id(worker_id, gateway_mode)

    def _activate_xdist_controller_mode(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._activate_xdist_controller_mode`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._activate_xdist_controller_mode`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - ensure_xdist_controller_batch_patch: collaborator call used by this boundary
            - ReportingTransportSession: collaborator call used by this boundary
            - self.reporter.xdist_fragment_dir.exists: collaborator call used by this boundary
            - shutil.rmtree: collaborator call used by this boundary
            - self.reporter.xdist_fragment_dir.mkdir: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_activate_xdist_controller_mode`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `_activate_xdist_controller_mode`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_activate_xdist_controller_mode`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `_activate_xdist_controller_mode`
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `_activate_xdist_controller_mode`

        State and side effects:
            mutates self.reporter._xdist_compatibility_error, self.reporter.is_xdist_controller,
            self.reporter.xdist_transport_session, self.reporter.xdist_fragment_dir, self.reporter.messages_file_path.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._activate_xdist_controller_mode`
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
        if self.reporter.is_disabled or self.reporter.is_xdist_worker or self.reporter.is_xdist_controller:
            return
        if not ensure_xdist_controller_batch_patch():
            self.reporter._xdist_compatibility_error = (  # noqa: SLF001
                "pytest-xdist is active but controller batch-event integration could not be installed."
            )
            return
        self.reporter.is_xdist_controller = True
        self.reporter.xdist_transport_session = ReportingTransportSession()
        self.reporter.xdist_fragment_dir = self.reporter.final_messages_file_path.parent / (
            f".{self.reporter.final_messages_file_path.name}.pytest-bdd-xdist"
        )
        if self.reporter.xdist_fragment_dir.exists():
            shutil.rmtree(self.reporter.xdist_fragment_dir)
        self.reporter.xdist_fragment_dir.mkdir(parents=True, exist_ok=True)
        self.reporter.messages_file_path = self.reporter.xdist_fragment_dir / "controller.ndjson"
        self.reporter._xdist_fragment_records["master"] = {  # noqa: SLF001
            "worker_id": "master",
            "role": "controller",
            "path": self.reporter.messages_file_path,
            "complete": False,
            "manifest_received": True,
        }

    @pytest.hookimpl(optionalhook=True)
    def pytest_configure_node(self, node: _WorkerNode) -> None:
        """
        Handle the pytest configure node pytest hook.

        Responsibility:
            Handle the pytest configure node pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.pytest_configure_node`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._activate_xdist_controller_mode: collaborator call used by this boundary
            - node_worker_id: collaborator call used by this boundary
            - self.reporter.xdist_transport_session.register_expected_worker: collaborator call used by this boundary
            - node_gateway_mode: collaborator call used by this boundary
            - _configured_transport_fail_worker_ids: collaborator call used by this boundary
            - pytest.hookimpl: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_configure_node`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `pytest_configure_node`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_configure_node`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `pytest_configure_node`
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `pytest_configure_node`

        State and side effects:
            mutates worker_id.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.pytest_configure_node`
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
            return
        self._activate_xdist_controller_mode()
        if not self.reporter.is_xdist_controller or self.reporter.xdist_transport_session is None:
            return
        worker_id = node_worker_id(node)
        self.reporter.xdist_transport_session.register_expected_worker(worker_id)
        node.workerinput["pytest_bdd_messages_fragment_worker_id"] = worker_id
        node.workerinput["pytest_bdd_messages_gateway_mode"] = node_gateway_mode(node)
        node.workerinput["pytest_bdd_messages_force_publish_failure"] = (
            worker_id in _configured_transport_fail_worker_ids(self.reporter.config)
        )
        self.reporter._xdist_fragment_records[worker_id] = {  # noqa: SLF001
            "worker_id": worker_id,
            "role": "worker",
            "path": None,
            "complete": False,
            "manifest_received": False,
        }

    def pytest_bdd_xdist_message_batch(self, config: Config, node: object, batch: JSONObject) -> None:
        """
        Handle the pytest bdd xdist message batch pytest hook.

        Responsibility:
            Handle the pytest bdd xdist message batch pytest hook. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.pytest_bdd_xdist_message_batch`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.reporter.xdist_transport_session.receive_remote_event: collaborator call used by this boundary
            - batch.get: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - self.live_formatter_service._emit_live_formatter_json_lines: collaborator call used by this boundary
            - json.dumps: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_bdd_xdist_message_batch`
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
              `pytest_bdd_xdist_message_batch`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `pytest_bdd_xdist_message_batch`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_bdd_xdist_message_batch`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `pytest_bdd_xdist_message_batch`

        State and side effects:
            mutates _, raw_envelopes, envelopes.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.pytest_bdd_xdist_message_batch`
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
        _ = config, node
        if (
            self.reporter.is_disabled
            or not self.reporter.is_xdist_controller
            or self.reporter.xdist_transport_session is None
        ):
            return
        self.reporter.xdist_transport_session.receive_remote_event(REPORTING_BATCH_EVENT, {"batch": batch})
        raw_envelopes = batch.get("envelopes", [])
        envelopes = raw_envelopes if isinstance(raw_envelopes, list) else []
        self.live_formatter_service._emit_live_formatter_json_lines(  # noqa: SLF001
            [json.dumps(envelope_dict) for envelope_dict in envelopes],
            source="xdist worker batch forwarding",
        )

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node: _WorkerNode, error: object | None) -> None:
        """
        Handle the pytest testnodedown pytest hook.

        Responsibility:
            Handle the pytest testnodedown pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.pytest_testnodedown` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - workeroutput.get: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - node_worker_id: collaborator call used by this boundary
            - self.reporter._xdist_fragment_records.get: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_testnodedown`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `pytest_testnodedown`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_testnodedown`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `pytest_testnodedown`
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `pytest_testnodedown`

        State and side effects:
            mutates workeroutput, worker_id, existing_record, manifest_payload, manifest.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.pytest_testnodedown` keeps
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
        if self.reporter.is_disabled:
            return
        if not self.reporter.is_xdist_controller:
            return
        workeroutput = cast("dict[str, object]", getattr(node, "workeroutput", {}))
        worker_id = str(workeroutput.get("pytest_bdd_messages_fragment_worker_id") or node_worker_id(node))
        existing_record = self.reporter._xdist_fragment_records.get(  # noqa: SLF001
            worker_id,
            {
                "worker_id": worker_id,
                "role": "worker",
                "path": None,
                "complete": False,
                "manifest_received": False,
            },
        )
        manifest_payload = workeroutput.get("pytest_bdd_messages_manifest")
        if isinstance(manifest_payload, dict):
            manifest = WorkerCompletionManifest.from_dict(manifest_payload)
            if self.reporter.xdist_transport_session is not None:
                self.reporter.xdist_transport_session.record_manifest(manifest)
            existing_record["manifest_received"] = True
            existing_record["complete"] = manifest.complete and error is None
            existing_record["transferred_batch_count"] = manifest.transferred_batch_count
            existing_record["last_batch_sequence"] = manifest.last_batch_sequence
            existing_record["interruption_reason"] = manifest.interruption_reason
        else:
            existing_record["complete"] = False
            existing_record["manifest_received"] = False
            existing_record["interruption_reason"] = str(error) if error is not None else None
        self.reporter._xdist_fragment_records[worker_id] = existing_record  # noqa: SLF001

    def start_process_messages_thread(self) -> None:
        """
        Handle start process messages thread.

        Responsibility:
            Handle start process messages thread. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.start_process_messages_thread`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - Queue: collaborator call used by this boundary
            - Event: collaborator call used by this boundary
            - Thread: collaborator call used by this boundary
            - self.reporter.process_messages_thread.start: collaborator call used by this boundary
            - sleep: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `start_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `start_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `start_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `start_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `start_process_messages_thread`

        State and side effects:
            mutates self.reporter.process_messages_io_queue, self.reporter.process_messages_stop_event,
            self.reporter._process_messages_thread_error, self.reporter.process_messages_thread.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.start_process_messages_thread`
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
        self.reporter.process_messages_io_queue = Queue()
        self.reporter.process_messages_stop_event = Event()
        self.reporter._process_messages_thread_error = None  # noqa: SLF001
        self.reporter.process_messages_thread = Thread(
            target=self._run_process_messages_thread,
            kwargs={"force_transport_publish_failure": self.reporter._xdist_force_publish_failure},  # noqa: SLF001
            daemon=True,
        )
        self.reporter.process_messages_thread.start()
        sleep(0)

    def finish_process_messages_thread(self) -> None:
        """
        Handle finish process messages thread.

        Raises:
            RuntimeError: If the operation cannot be completed.

        Responsibility:
            Handle finish process messages thread. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.finish_process_messages_thread`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - RuntimeError: collaborator call used by this boundary
            - self.live_formatter_service._close_live_formatter_stream: collaborator call used by this boundary
            - monotonic: collaborator call used by this boundary
            - self.reporter.process_messages_thread.is_alive: collaborator call used by this boundary
            - sleep: collaborator call used by this boundary
            - self.reporter.process_messages_stop_event.set: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `finish_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `finish_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `finish_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `finish_process_messages_thread`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `finish_process_messages_thread`

        State and side effects:
            mutates msg, deadline, process, self.reporter._live_formatter_process,
            self.reporter._live_formatter_temp_dir.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.finish_process_messages_thread`
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
        deadline = monotonic() + 10
        while self.reporter.process_messages_io_queue.unfinished_tasks:
            if self.reporter._process_messages_thread_error is not None:  # noqa: SLF001
                msg = "Message writer thread crashed before queued envelopes were drained."
                raise RuntimeError(msg) from self.reporter._process_messages_thread_error  # noqa: SLF001
            if not self.reporter.process_messages_thread.is_alive():
                msg = "Message writer thread stopped before queued envelopes were drained."
                raise RuntimeError(msg)
            if monotonic() >= deadline:
                msg = "Timed out waiting for queued message envelopes to be drained."
                raise RuntimeError(msg)
            sleep(0.01)
        self.reporter.process_messages_stop_event.set()
        self.reporter.process_messages_thread.join(timeout=5)
        if self.reporter.process_messages_thread.is_alive():
            msg = "Message writer thread did not terminate after drain signal."
            raise RuntimeError(msg)
        if self.reporter._process_messages_thread_error is not None:  # noqa: SLF001
            msg = "Message writer thread crashed during shutdown."
            raise RuntimeError(msg) from self.reporter._process_messages_thread_error  # noqa: SLF001
        process = self.reporter._live_formatter_process  # noqa: SLF001
        if process is not None:
            self.live_formatter_service._finalize_live_formatter_process(process)  # noqa: SLF001
        self.live_formatter_service._join_live_formatter_threads()  # noqa: SLF001
        if process is not None:
            self.live_formatter_service._close_live_formatter_stream(process.stdin)  # noqa: SLF001
            self.live_formatter_service._close_live_formatter_stream(process.stdout)  # noqa: SLF001
            self.live_formatter_service._close_live_formatter_stream(process.stderr)  # noqa: SLF001
            self.reporter._live_formatter_process = None  # noqa: SLF001
        if self.reporter._live_formatter_temp_dir is not None:  # noqa: SLF001
            self.reporter._live_formatter_temp_dir.cleanup()  # noqa: SLF001
            self.reporter._live_formatter_temp_dir = None  # noqa: SLF001

    @staticmethod
    def process_messages(  # noqa: C901
        queue: Queue[str],
        stop_event: Event,
        messages_file_path: str | Path,
        transport_client: ReportingTransportClient | None = None,
        *,
        force_transport_publish_failure: bool = False,
    ) -> None:
        """
        Handle process messages.

        Responsibility:
            Handle process messages. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.process_messages` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - sleep: collaborator call used by this boundary
            - logger.exception: collaborator call used by this boundary
            - stop_event.is_set: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - messages_path.with_name: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `process_messages`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `process_messages`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `process_messages`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `process_messages`
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `process_messages`

        State and side effects:
            mutates last_enter, messages_path, lock_file, lines, batch_envelopes.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.process_messages` keeps its
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
        messages_path = Path(messages_file_path)
        lock_file = str(messages_path.with_name(f".{messages_path.name}.lock"))
        last_enter = False
        while not (stop_event.is_set() and last_enter):  # give one more enter to take all left messages
            if stop_event.is_set():
                last_enter = True

            lines = []
            batch_envelopes: list[JSONObject] = []
            while not queue.empty():
                try:
                    message_json = queue.get(timeout=1)
                except Empty:
                    sleep(0)
                    continue

                try:
                    envelope_dict = cast("JSONObject", json.loads(message_json))
                    envelope_from_dict(envelope_dict)
                except (TypeError, ValueError):
                    logger.exception("Failed to parse:\n%s\n", pformat(message_json))
                else:
                    lines.append(f"{message_json}\n")
                    batch_envelopes.append(envelope_dict)
                finally:
                    queue.task_done()
                sleep(0)

            if not lines:
                sleep(0)
                continue

            try:
                messages_path.parent.mkdir(parents=True, exist_ok=True)
                with FileLock(lock_file), messages_path.open(mode="at+", buffering=1, encoding="utf-8") as f:
                    f.writelines(lines)
                    f.flush()
            except OSError:
                logger.exception("Unable to write messages to '%s'", messages_path)

            if transport_client is not None and batch_envelopes:
                if force_transport_publish_failure:
                    transport_client.last_publish_error = "transport publication was disabled by test fixture"
                    logger.warning(
                        "Skipping remote transport batch publication for '%s' due to configured failure.",
                        transport_client.worker_id,
                    )
                    continue
                try:
                    transport_client.publish_envelopes(batch_envelopes)
                except RuntimeError:
                    logger.exception("Unable to publish remote transport batch for '%s'", transport_client.worker_id)

    @staticmethod
    def read_envelopes_from_path(messages_file_path: Path) -> list[Message]:
        """
        Read envelopes from path.

        Returns:
            List of messages.

        Responsibility:
            Read envelopes from path. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.read_envelopes_from_path`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - messages_file_path.exists: collaborator call used by this boundary
            - messages_file_path.read_text.splitlines: collaborator call used by this boundary
            - messages_file_path.read_text: collaborator call used by this boundary
            - line.strip: collaborator call used by this boundary
            - envelopes.append: collaborator call used by this boundary
            - envelope_from_dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `read_envelopes_from_path`

        State and side effects:
            mutates envelopes.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService.read_envelopes_from_path`
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
        envelopes: list[Message] = []
        if not messages_file_path.exists():
            return envelopes
        for line in messages_file_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            envelopes.append(envelope_from_dict(json.loads(line)))
        return envelopes

    def _write_final_messages_file(self, envelope_dicts: tuple[JSONObject, ...]) -> list[Message]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._write_final_messages_file`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._write_final_messages_file`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.reporter.final_messages_file_path.parent.mkdir: collaborator call used by this boundary
            - self.reporter.final_messages_file_path.write_text: collaborator call used by this boundary
            - join: collaborator call used by this boundary
            - json.dumps: collaborator call used by this boundary
            - self.read_envelopes_from_path: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_write_final_messages_file`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `_write_final_messages_file`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_write_final_messages_file`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `_write_final_messages_file`
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `_write_final_messages_file`

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
        self.reporter.final_messages_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.reporter.final_messages_file_path.write_text(
            "".join(f"{json.dumps(envelope_dict)}\n" for envelope_dict in envelope_dicts),
            encoding="utf-8",
        )
        return self.read_envelopes_from_path(self.reporter.final_messages_file_path)

    def _finalize_xdist_messages_file(self) -> list[Message]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._finalize_xdist_messages_file`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._finalize_xdist_messages_file`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - worker_ids.update: collaborator call used by this boundary
            - MessageFragment.from_path: collaborator call used by this boundary
            - self.reporter.xdist_transport_session.snapshot: collaborator call used by this boundary
            - set: collaborator call used by this boundary
            - transport_snapshot.batches_by_worker.keys: collaborator call used by this boundary
            - transport_snapshot.manifests_by_worker.keys: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_finalize_xdist_messages_file`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `_finalize_xdist_messages_file`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references
              `_finalize_xdist_messages_file`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `_finalize_xdist_messages_file`
            - src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py: imports or references
              `_finalize_xdist_messages_file`

        State and side effects:
            mutates controller_fragment, transport_snapshot, worker_ids, fragment_specs, batches.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.transport_runtime.TransportService._finalize_xdist_messages_file`
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
        controller_fragment = MessageFragment.from_path(
            worker_id="master",
            role="controller",
            path=self.reporter.messages_file_path,
            complete=True,
        )
        transport_snapshot = (
            self.reporter.xdist_transport_session.snapshot()
            if self.reporter.xdist_transport_session is not None
            else None
        )
        worker_ids: set[str] = set()
        if transport_snapshot is not None:
            worker_ids.update(transport_snapshot.expected_worker_ids)
            worker_ids.update(transport_snapshot.batches_by_worker.keys())
            worker_ids.update(transport_snapshot.manifests_by_worker.keys())
        worker_ids.update(worker_id for worker_id in self.reporter._xdist_fragment_records if worker_id != "master")  # noqa: SLF001
        fragment_specs = [controller_fragment]
        for worker_id in sorted(worker_ids):
            batches = () if transport_snapshot is None else transport_snapshot.batches_by_worker.get(worker_id, ())
            manifest = None if transport_snapshot is None else transport_snapshot.manifests_by_worker.get(worker_id)
            fragment_specs.append(
                MessageFragment.from_envelopes(
                    worker_id=worker_id,
                    role="worker",
                    envelopes=tuple(envelope_dict for batch in batches for envelope_dict in batch.envelopes),
                    complete=manifest.complete if manifest is not None else False,
                    manifest_received=manifest is not None,
                    transferred_batch_count=(
                        manifest.transferred_batch_count if manifest is not None else len(batches)
                    ),
                    last_batch_sequence=(
                        manifest.last_batch_sequence
                        if manifest is not None
                        else (batches[-1].batch_sequence if batches else None)
                    ),
                    interruption_reason=manifest.interruption_reason if manifest is not None else None,
                ),
            )
        consolidated_stream = consolidate_message_fragments(fragment_specs)
        for diagnostic in consolidated_stream.diagnostics:
            logger.warning("%s", diagnostic.message)
        return self._write_final_messages_file(consolidated_stream.envelope_dicts)
