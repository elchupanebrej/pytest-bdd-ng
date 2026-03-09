from __future__ import annotations

from typing import Any

from cucumber_messages import TestCaseStarted as CucumberTestCaseStarted  # type:ignore[attr-defined]

from pytest_bdd.model.message_consolidation import MessageFragment, consolidate_message_fragments
from pytest_bdd.model.message_transport import (
    REPORTING_BATCH_EVENT,
    ReportingTransportClient,
    ReportingTransportSession,
)
from pytest_bdd.model.message_validation import validate_message_stream, validate_xdist_reporting_compatibility
from tests.messages.message_stream_assertions import worker_ids_for_payloads
from tests.messages.test_xdist_message_consolidation import _controller_fragment, _worker_fragment


def _session_sender(session: ReportingTransportSession):
    def sender(event_name: str, **kwargs: Any) -> None:
        assert event_name == REPORTING_BATCH_EVENT
        session.receive_remote_event(event_name, kwargs)

    return sender


def test_remote_transport_batches_finalize_without_shared_filesystem() -> None:
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


def test_remote_transport_missing_manifest_and_interruption_are_diagnosed() -> None:
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
    assert worker_result.reason is not None and "worker channel sender" in worker_result.reason
    assert controller_result.is_valid is False
    assert controller_result.reason is not None and "controller support" in controller_result.reason
