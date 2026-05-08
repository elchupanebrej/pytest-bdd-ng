"""Provide test xdist remote transport helpers."""

from __future__ import annotations

import json
from queue import Empty, Queue
from threading import Event
from types import SimpleNamespace
from typing import Any

import pytest
from cucumber_messages import TestCaseStarted as CucumberTestCaseStarted  # type:ignore[attr-defined]

from pytest_bdd.model.message_consolidation import MessageFragment, consolidate_message_fragments
from pytest_bdd.model.message_transport import (
    REPORTING_BATCH_EVENT,
    REPORTING_TRANSPORT_BINDING_STASH_KEY,
    ReportingTransportClient,
    ReportingTransportSession,
    install_reporting_event_sender,
    resolve_reporting_event_sender,
    resolve_reporting_gateway_mode,
)
from pytest_bdd.model.message_validation import validate_message_stream, validate_xdist_reporting_compatibility
from pytest_bdd.plugin.gherkin_message_reporter import transport_runtime
from pytest_bdd.plugin.gherkin_message_reporter.runtime_support import _resolve_reporting_worker_identity
from pytest_bdd.plugin.gherkin_message_reporter.transport_runtime import TransportService
from tests.messages.message_stream_assertions import worker_ids_for_payloads
from tests.messages.test_xdist_message_consolidation import _controller_fragment, _worker_fragment


def _session_sender(session: ReportingTransportSession):
    def sender(event_name: str, **kwargs: Any) -> None:
        assert event_name == REPORTING_BATCH_EVENT
        session.receive_remote_event(event_name, kwargs)

    return sender


def _build_dummy_transport_service(
    *,
    messages_file_path,
    force_transport_publish_failure: bool,
    process_messages,
):
    class DummyTransportService(TransportService):
        is_xdist_worker = False
        xdist_transport_client = None
        _live_formatter_process = None
        _live_formatter_temp_dir = None
        _live_formatter_stdout_thread = None
        _live_formatter_stderr_thread = None

        def __init__(self):
            live_formatter_service = SimpleNamespace(
                _finalize_live_formatter_process=lambda _process: None,
                _join_live_formatter_threads=lambda: None,
                _close_live_formatter_stream=lambda _stream: None,
            )
            reporter = SimpleNamespace(
                services=(),
                messages_file_path=messages_file_path,
                _xdist_force_publish_failure=force_transport_publish_failure,
                _process_messages_thread_error=None,
                is_xdist_worker=False,
                xdist_transport_client=None,
                _live_formatter_process=None,
                _live_formatter_temp_dir=None,
                _live_formatter_stdout_thread=None,
                _live_formatter_stderr_thread=None,
                live_formatter_service=live_formatter_service,
            )
            super().__init__(reporter, live_formatter_service=live_formatter_service)
            reporter.services = (self,)

        @staticmethod
        def process_messages(
            queue,
            stop_event,
            messages_file_path,
            transport_client=None,
            *,
            force_transport_publish_failure=False,
        ):
            return process_messages(
                queue,
                stop_event,
                messages_file_path,
                transport_client=transport_client,
                force_transport_publish_failure=force_transport_publish_failure,
            )

    return DummyTransportService()


def test_remote_transport_batches_finalize_without_shared_filesystem() -> None:
    """Verify remote transport batches finalize without shared filesystem."""
    session = ReportingTransportSession()
    session.register_expected_worker("gw0")
    worker_fragment = _worker_fragment("gw0", "remote scenario")
    client = ReportingTransportClient(
        worker_id="gw0",
        sender=_session_sender(session),
        gateway_mode="socket",
    )

    client.publish_envelopes(list(worker_fragment.envelopes))
    session.record_manifest(client.build_manifest(complete=True))
    batches = session.wait_for_batches("gw0")
    snapshot = session.snapshot()

    remote_fragment = MessageFragment.from_envelopes(
        worker_id="gw0",
        role="worker",
        envelopes=tuple(envelope_dict for batch in batches for envelope_dict in batch.envelopes),
        complete=snapshot.manifests_by_worker["gw0"].complete,
        manifest_received=True,
        transferred_batch_count=snapshot.manifests_by_worker["gw0"].transferred_batch_count,
        last_batch_sequence=snapshot.manifests_by_worker["gw0"].last_batch_sequence,
    )
    consolidated = consolidate_message_fragments([_controller_fragment(), remote_fragment])
    validation_result = validate_message_stream(list(consolidated.envelopes), track_coverage=False)

    assert validation_result.status == "pass"
    assert worker_ids_for_payloads(consolidated.envelopes, CucumberTestCaseStarted) == {"gw0"}
    assert snapshot.manifests_by_worker["gw0"].gateway_mode == "socket"
    assert not any(
        diagnostic.code == "missing_worker_fragment" and diagnostic.worker_id == "gw0"
        for diagnostic in consolidated.diagnostics
    )


def test_reporting_identity_ignores_inherited_xdist_environment(monkeypatch) -> None:
    """Verify reporting identity ignores inherited xdist environment."""
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw7")
    monkeypatch.setenv("PYTEST_XDIST_WORKER_COUNT", "2")
    worker_id, gateway_mode = _resolve_reporting_worker_identity(SimpleNamespace())

    assert worker_id == "master"
    assert gateway_mode is None


def test_remote_transport_missing_manifest_and_interruption_are_diagnosed() -> None:
    """Verify remote transport missing manifest and interruption are diagnosed."""
    worker_fragment = _worker_fragment("gw1", "interrupted scenario")
    interrupted_fragment = MessageFragment.from_envelopes(
        worker_id="gw1",
        role="worker",
        envelopes=worker_fragment.envelopes[:4],
        complete=False,
        manifest_received=False,
        transferred_batch_count=1,
        last_batch_sequence=0,
        interruption_reason="connection reset",
    )

    consolidated = consolidate_message_fragments([_controller_fragment(), interrupted_fragment])
    diagnostic_codes = {(diagnostic.code, diagnostic.worker_id) for diagnostic in consolidated.diagnostics}

    assert ("missing_worker_manifest", "gw1") in diagnostic_codes
    assert ("interrupted_worker_transfer", "gw1") in diagnostic_codes
    assert ("partial_stream", "gw1") in diagnostic_codes


def test_remote_transport_client_manifest_marks_publish_failures() -> None:
    """
    Verify remote transport client manifest marks publish failures.

    Raises:
        AssertionError: If the manifest does not record the publish failure.

    """

    def failing_sender(event_name: str, **kwargs: Any) -> None:
        _ = event_name, kwargs
        msg = "simulated sender failure"
        raise RuntimeError(msg)

    client = ReportingTransportClient(
        worker_id="gw2",
        sender=failing_sender,
        gateway_mode="ssh",
    )

    try:
        client.publish_envelopes([{"meta": {"protocolVersion": "1.0.0"}}])
    except RuntimeError:
        pass
    else:
        msg = "Expected remote transport publish to fail."
        raise AssertionError(msg)

    manifest = client.build_manifest(complete=False)

    assert manifest.complete is False
    assert manifest.transferred_batch_count == 0
    assert manifest.gateway_mode == "ssh"
    assert manifest.interruption_reason is not None


def test_remote_transport_zero_batch_interruption_still_emits_partial_diagnostics() -> None:
    """Verify remote transport zero batch interruption still emits partial diagnostics."""
    interrupted_fragment = MessageFragment.from_envelopes(
        worker_id="gw3",
        role="worker",
        envelopes=(),
        complete=False,
        manifest_received=True,
        transferred_batch_count=0,
        last_batch_sequence=None,
        interruption_reason="connection refused",
    )

    consolidated = consolidate_message_fragments([_controller_fragment(), interrupted_fragment])
    diagnostic_codes = {(diagnostic.code, diagnostic.worker_id) for diagnostic in consolidated.diagnostics}

    assert ("missing_worker_fragment", "gw3") in diagnostic_codes
    assert ("interrupted_worker_transfer", "gw3") in diagnostic_codes
    assert ("partial_stream", "gw3") in diagnostic_codes


def test_remote_transport_compatibility_requires_worker_sender_and_controller_patch() -> None:
    """Verify remote transport compatibility requires worker sender and controller patch."""
    worker_result = validate_xdist_reporting_compatibility(
        xdist_active=True,
        is_worker=True,
        is_controller=False,
        remote_module_available=True,
        controller_event_patch_installed=True,
        worker_sender_available=False,
    )
    controller_result = validate_xdist_reporting_compatibility(
        xdist_active=True,
        is_worker=False,
        is_controller=True,
        remote_module_available=True,
        controller_event_patch_installed=False,
        worker_sender_available=True,
    )

    assert worker_result.is_valid is False
    assert worker_result.reason is not None
    assert "worker channel sender" in worker_result.reason
    assert controller_result.is_valid is False
    assert controller_result.reason is not None
    assert "controller support" in controller_result.reason


def test_install_reporting_event_sender_stores_binding_in_config_stash() -> None:
    """Verify install reporting event sender stores binding in config stash."""
    config = SimpleNamespace(stash={})

    def sender(event_name: str, **kwargs: Any) -> None:
        _ = event_name, kwargs

    install_reporting_event_sender(config, sender, gateway_mode="socket")

    assert resolve_reporting_event_sender(config) is sender
    assert resolve_reporting_gateway_mode(config) == "socket"
    assert REPORTING_TRANSPORT_BINDING_STASH_KEY in config.stash
    assert getattr(config, REPORTING_TRANSPORT_BINDING_STASH_KEY, None) is None


def test_install_reporting_event_sender_initializes_missing_config_stash() -> None:
    """Verify install reporting event sender initializes missing config stash."""
    config = SimpleNamespace()

    def sender(event_name: str, **kwargs: Any) -> None:
        _ = event_name, kwargs

    install_reporting_event_sender(config, sender)

    assert hasattr(config, "stash")
    assert resolve_reporting_event_sender(config) is sender
    assert resolve_reporting_gateway_mode(config) is None


def test_process_messages_thread_passes_force_failure_flag(tmp_path) -> None:
    """Verify process messages thread passes force failure flag."""
    observed: dict[str, object] = {}

    def process_messages(
        queue,
        stop_event,
        messages_file_path,
        transport_client=None,
        *,
        force_transport_publish_failure=False,
    ):
        observed["messages_file_path"] = messages_file_path
        observed["transport_client"] = transport_client
        observed["force_transport_publish_failure"] = force_transport_publish_failure
        while not (stop_event.is_set() and queue.unfinished_tasks == 0):
            try:
                queue.get(timeout=0.1)
            except Empty:
                continue
            queue.task_done()

    runtime = _build_dummy_transport_service(
        messages_file_path=tmp_path / "messages.ndjson",
        force_transport_publish_failure=True,
        process_messages=process_messages,
    )

    runtime.start_process_messages_thread()
    runtime.reporter.process_messages_io_queue.put_nowait("{}")
    runtime.finish_process_messages_thread()

    assert observed["messages_file_path"] == tmp_path / "messages.ndjson"
    assert observed["transport_client"] is None
    assert observed["force_transport_publish_failure"] is True
    assert runtime.reporter._process_messages_thread_error is None


def test_process_messages_writes_without_temporary_directory(monkeypatch, tmp_path) -> None:
    """Verify process messages writes without temporary directory."""

    def fail_temporary_directory():
        msg = "message writer lock must not depend on a temporary directory"
        raise AssertionError(msg)

    if hasattr(transport_runtime, "tempfile"):
        monkeypatch.setattr(transport_runtime.tempfile, "TemporaryDirectory", fail_temporary_directory)
    queue = Queue()
    stop_event = Event()
    queue.put_nowait(
        json.dumps(
            {
                "testRunStarted": {
                    "id": "run-1",
                    "timestamp": {"seconds": 0, "nanos": 0},
                }
            }
        )
    )
    stop_event.set()
    messages_path = tmp_path / "messages.ndjson"

    TransportService.process_messages(queue, stop_event, messages_path)

    assert messages_path.read_text(encoding="utf-8").splitlines() == [
        '{"testRunStarted": {"id": "run-1", "timestamp": {"seconds": 0, "nanos": 0}}}'
    ]


def test_finish_process_messages_thread_fails_fast_when_writer_thread_crashes(tmp_path) -> None:
    """Verify finish process messages thread fails fast when writer thread crashes."""

    def process_messages(
        queue,
        stop_event,
        messages_file_path,
        transport_client=None,
        *,
        force_transport_publish_failure=False,
    ):
        _ = queue, stop_event, messages_file_path, transport_client, force_transport_publish_failure
        msg = "boom"
        raise RuntimeError(msg)

    runtime = _build_dummy_transport_service(
        messages_file_path=tmp_path / "messages.ndjson",
        force_transport_publish_failure=False,
        process_messages=process_messages,
    )

    runtime.start_process_messages_thread()
    runtime.reporter.process_messages_io_queue.put_nowait("{}")

    with pytest.raises(RuntimeError, match="crashed before queued envelopes were drained"):
        runtime.finish_process_messages_thread()
