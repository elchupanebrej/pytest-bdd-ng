from __future__ import annotations

from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "011-merge-xdist-reporting"
    / "contracts"
    / "xdist-worker-controller-boundary.md"
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def test_xdist_worker_controller_boundary_contract_exists() -> None:
    assert CONTRACT_PATH.exists()


def test_xdist_worker_controller_boundary_contract_assigns_transport_ownership() -> None:
    contract_text = _contract_text()
    assert "pytest_xdist_getremotemodule" in contract_text
    assert "emit reporting payloads into execnet-serializable chunk batches" in contract_text
    assert "write directly to the final canonical `--messages-ndjson` artifact in xdist mode" in contract_text
    assert "require the controller to open worker-local-only files" in contract_text
    assert "own the canonical structural identity table" in contract_text
    assert "emit exactly one canonical final stream for the logical run" in contract_text


def test_xdist_worker_controller_boundary_contract_covers_partial_run_behavior() -> None:
    contract_text = _contract_text()
    assert "popen" in contract_text
    assert "ssh" in contract_text
    assert "socket" in contract_text
    assert "via" in contract_text
    assert "If a worker transfer is interrupted after some batches were received" in contract_text
    assert "Partial-stream diagnostics must identify the missing or incomplete participant" in contract_text
    assert "Xdist-only hook registration remains conditional" in contract_text
    assert "fail-fast diagnostics" in contract_text
