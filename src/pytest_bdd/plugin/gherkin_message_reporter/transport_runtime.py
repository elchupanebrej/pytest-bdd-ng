"""Provide transport runtime helpers."""

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
    raw_value = str(getattr(config, "getini", lambda _name: "")("pytest_bdd_transport_fail_workers") or "").strip()
    if not raw_value:
        return set()
    return {worker_id.strip() for worker_id in raw_value.split(",") if worker_id.strip()}


class TransportService(ReporterServiceBase):
    """
    Represent transport service state.

    Raises:
        RuntimeError: If the operation cannot be completed.

    """

    plugin_suffix = "transport"

    def __init__(self, reporter: GherkinMessageReporter, *, live_formatter_service: LiveFormatterService) -> None:
        """Initialize the transport service."""
        super().__init__(reporter)
        self.live_formatter_service = live_formatter_service

    def _run_process_messages_thread(self, *, force_transport_publish_failure: bool) -> None:
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
        worker_id, gateway_mode = _resolve_reporting_worker_identity(config)
        return _format_reporting_worker_id(worker_id, gateway_mode)

    def _activate_xdist_controller_mode(self) -> None:
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
        """Handle the pytest configure node pytest hook."""
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
        """Handle the pytest bdd xdist message batch pytest hook."""
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
        """Handle the pytest testnodedown pytest hook."""
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
        """Handle start process messages thread."""
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
        """Handle process messages."""
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
        self.reporter.final_messages_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.reporter.final_messages_file_path.write_text(
            "".join(f"{json.dumps(envelope_dict)}\n" for envelope_dict in envelope_dicts),
            encoding="utf-8",
        )
        return self.read_envelopes_from_path(self.reporter.final_messages_file_path)

    def _finalize_xdist_messages_file(self) -> list[Message]:
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
