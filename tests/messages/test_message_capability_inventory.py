from __future__ import annotations

from pathlib import Path

from pytest_bdd.model.coverage.inventory import generate_inventory, iter_capability_ids
from pytest_bdd.model.message_capability import capability_is_relevant, classify_capability_relevance
from pytest_bdd.model.message_capability_inventory import (
    reconcile_inventory_with_mandatory_scope,
    reconcile_runtime_scope_coverage,
    resolve_messages_schema_dir,
    sync_capability_inventory,
)

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


def test_resolve_messages_schema_dir_finds_envelope_schema() -> None:
    schema_dir = resolve_messages_schema_dir()
    assert (schema_dir / "Envelope.json").exists()


def test_generated_inventory_capability_ids_are_unique_and_canonical() -> None:
    inventory = generate_inventory(resolve_messages_schema_dir())
    capability_ids = iter_capability_ids(inventory)

    assert capability_ids == tuple(sorted(capability_ids))
    assert len(capability_ids) == len(set(capability_ids))
    assert all("_" not in capability_id.split(".", 1)[0] for capability_id in capability_ids)


def test_reconcile_inventory_with_runtime_required_scope_has_zero_missing() -> None:
    inventory = generate_inventory(resolve_messages_schema_dir())
    inventory_capability_ids = iter_capability_ids(inventory)
    runtime_required_scope_path = (
        Path(__file__).resolve().parents[2]
        / "specs"
        / "008-maximize-messages-coverage"
        / "runtime-required-capability-ids.txt"
    )
    runtime_required_scope_ids = [
        line.strip()
        for line in runtime_required_scope_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    reconciliation = reconcile_inventory_with_mandatory_scope(
        inventory_capability_ids=inventory_capability_ids,
        mandatory_capability_ids=runtime_required_scope_ids,
    )

    assert reconciliation.mandatory_total > 0
    assert reconciliation.has_missing_mandatory_capabilities is False
    assert reconciliation.missing_mandatory_capability_ids == ()


def test_reconcile_runtime_scope_coverage_tracks_unclassified_non_runtime_gaps() -> None:
    reconciliation = reconcile_runtime_scope_coverage(
        inventory_capability_ids=("cap.a", "cap.b", "cap.c"),
        runtime_required_capability_ids=("cap.a",),
        observed_capability_ids=("cap.a",),
        classified_capability_ids=("cap.b",),
    )

    assert reconciliation.runtime_required_total == 1
    assert reconciliation.runtime_required_covered == 1
    assert reconciliation.runtime_required_missing == 0
    assert reconciliation.non_runtime_required_total == 2
    assert reconciliation.non_runtime_covered == 0
    assert reconciliation.non_runtime_classified == 1
    assert reconciliation.uncovered_non_runtime_unclassified_capability_ids == ("cap.c",)
