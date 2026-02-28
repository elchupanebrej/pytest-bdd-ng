from __future__ import annotations

from pytest_bdd.model.message_capability import capability_is_relevant, classify_capability_relevance
from pytest_bdd.model.message_capability_inventory import sync_capability_inventory

from .message_capability_fixtures import make_capability


def test_sync_capability_inventory_counts_relevant_and_detects_duplicates() -> None:
    entries = [
        make_capability("cap-1", affects=("emitted_envelope_payload",)),
        make_capability("cap-2", affects=()),
        make_capability("cap-1", affects=("status_mapping",)),
    ]

    result = sync_capability_inventory("v32.0.1", entries)

    assert result.total_relevant == 1
    assert result.total_out_of_scope == 1
    assert result.duplicate_capability_ids == ("cap-1",)
    assert len(result.capabilities) == 2


def test_sync_capability_inventory_rewrites_baseline_release() -> None:
    entries = [make_capability("cap-1", baseline_release="legacy")]

    result = sync_capability_inventory("v32.0.1", entries)

    assert result.capabilities[0].baseline_release == "v32.0.1"


def test_relevance_classifier_uses_supported_impact_domains() -> None:
    relevant_capability = make_capability("cap-1", affects=("lifecycle_linkage",))
    out_of_scope_capability = make_capability("cap-2", affects=())

    assert classify_capability_relevance(relevant_capability) == "relevant"
    assert capability_is_relevant(relevant_capability) is True

    assert classify_capability_relevance(out_of_scope_capability) == "out_of_scope"
    assert capability_is_relevant(out_of_scope_capability) is False
