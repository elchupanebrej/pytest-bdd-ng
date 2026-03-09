from __future__ import annotations

from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "011-merge-xdist-reporting"
    / "contracts"
    / "xdist-consolidated-stream.md"
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def test_xdist_consolidated_stream_contract_exists() -> None:
    assert CONTRACT_PATH.exists()


def test_xdist_consolidated_stream_contract_defines_payload_classes() -> None:
    contract_text = _contract_text()
    assert "### Controller-Singular Payloads" in contract_text
    assert "### Structural-Deduplicated Payloads" in contract_text
    assert "### Execution-Preserved Payloads" in contract_text
    assert "- `meta`" in contract_text
    assert "- `test_case`" in contract_text
    assert "- `test_case_started`" in contract_text


def test_xdist_consolidated_stream_contract_requires_deterministic_order_and_reference_rewrite() -> None:
    contract_text = _contract_text()
    assert "Worker-local structural IDs MUST NOT leak into the final stream" in contract_text
    assert "Runtime payloads MUST NOT reference structural records discarded during deduplication." in contract_text
    assert "The same set of transferred worker batches MUST produce the same final NDJSON order." in contract_text


def test_xdist_consolidated_stream_contract_requires_remote_safe_transport() -> None:
    contract_text = _contract_text()
    assert "remote worker topologies where participants do not share a filesystem" in contract_text
    assert (
        "The controller must be able to finalize the stream from transferred chunk data plus completion manifests alone."
        in contract_text
    )
    assert (
        "Docker acceptance tests verify that mixed worker outcomes survive consolidation across isolated containers."
        in contract_text
    )
