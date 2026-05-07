from __future__ import annotations

from pathlib import Path

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "tests" / "contract" / "fixtures" / "xdist_consolidated_stream.md"
LIVE_CONTRACT_PATH = (
    Path(__file__).resolve().parents[2] / "tests" / "contract" / "fixtures" / "xdist_live_reporting_boundary.md"
)


def _contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _live_contract_text() -> str:
    return LIVE_CONTRACT_PATH.read_text(encoding="utf-8")


def test_xdist_consolidated_stream_contract_exists() -> None:
    assert CONTRACT_PATH.exists()


def test_live_formatter_boundary_contract_exists_for_stream_ordering() -> None:
    assert LIVE_CONTRACT_PATH.exists()


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
        "The controller must be able to finalize the stream from transferred chunk data "
        "plus completion manifests alone." in contract_text
    )
    assert (
        "Docker acceptance tests verify that mixed worker outcomes survive consolidation across isolated containers."
        in contract_text
    )


def test_live_formatter_boundary_contract_requires_per_source_order_and_arrival_interleaving() -> None:
    contract_text = _live_contract_text()

    assert "Message order must be preserved within each `source_id`." in contract_text
    assert "Cross-source live interleaving follows controller arrival order" in contract_text
    assert "The controller may terminate the live formatter session as failed" in contract_text


def test_live_formatter_boundary_contract_keeps_canonical_ndjson_as_final_artifact() -> None:
    contract_text = _live_contract_text()

    assert "Canonical NDJSON remains the final validation and replay artifact" in contract_text
