"""Coordinate two xdist gateway threads around a shared live pickle."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from pytest_cuke.message_plugin import MessagePlugin
from pytest_cuke.model.message_consolidation import LiveMessageAdapter
from pytest_cuke.native_allure import NativeAllureReporter

_first_batches = threading.Barrier(2, timeout=30)
_state_lock = threading.Lock()
_worker_cases: dict[str, str] = {}
_owner: list[str] = []
_pickle_registered = threading.Event()
_contender_finished = threading.Event()
_receive = MessagePlugin._receive_worker_message_batch
_adapt = LiveMessageAdapter.worker_envelope
_start_case = NativeAllureReporter._start_case


def _coordinate_batch(self: MessagePlugin, payload: dict[str, Any]) -> None:
    worker_id = payload["worker_id"]
    with _state_lock:
        first = worker_id not in _worker_cases
        if first:
            _worker_cases[worker_id] = next(
                envelope["testCase"]["pickleId"] for envelope in payload["envelopes"] if "testCase" in envelope
            )
    if first:
        _first_batches.wait()
    _receive(self, payload)


def _coordinate_pickle(self: LiveMessageAdapter, envelope: dict[str, Any], *, worker_id: str) -> dict[str, Any] | None:
    with _state_lock:
        if not _owner:
            _owner.append(worker_id)
        owner = _owner[0]
        other_case = next(case for worker, case in _worker_cases.items() if worker != owner)
    if worker_id != owner and not _pickle_registered.wait(30):
        raise TimeoutError("the first worker did not register the shared pickle")
    result = _adapt(self, envelope, worker_id=worker_id)
    if worker_id == owner and result is not None and result.get("pickle", {}).get("id") == f"{owner}:{other_case}":
        Path("native-allure-xdist-race-probe.json").write_text(
            json.dumps({"owner": owner, "workers": sorted(_worker_cases)}), encoding="utf-8"
        )
        _pickle_registered.set()
        _contender_finished.wait(8)
    return result


def _observe_start(self: NativeAllureReporter, started: Any) -> None:
    try:
        _start_case(self, started)
    finally:
        if started.worker_id != _owner[0]:
            _contender_finished.set()


MessagePlugin._receive_worker_message_batch = _coordinate_batch
LiveMessageAdapter.worker_envelope = _coordinate_pickle
NativeAllureReporter._start_case = _observe_start
