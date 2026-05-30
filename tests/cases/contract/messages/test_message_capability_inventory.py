"""Provide test message capability inventory helpers."""

from __future__ import annotations

from pathlib import Path

from pytest_bdd.model import message_capability_inventory
from pytest_bdd.model.coverage.inventory import SCHEMA_DIR, generate_inventory, iter_capability_ids
from pytest_bdd.model.message_capability import capability_is_relevant, classify_capability_relevance
from pytest_bdd.model.message_capability_inventory import (
    reconcile_inventory_with_mandatory_scope,
    reconcile_runtime_scope_coverage,
    resolve_messages_schema_dir,
    sync_capability_inventory,
)

from .message_capability_fixtures import make_capability


def test_sync_capability_inventory_counts_relevant_and_detects_duplicates() -> None:
    """Verify sync capability inventory counts relevant and detects duplicates."""
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
    """Verify sync capability inventory rewrites baseline release."""
    entries = [make_capability("cap-1", baseline_release="legacy")]

    result = sync_capability_inventory("v32.0.1", entries)

    assert result.capabilities[0].baseline_release == "v32.0.1"


def test_relevance_classifier_uses_supported_impact_domains() -> None:
    """Verify relevance classifier uses supported impact domains."""
    relevant_capability = make_capability("cap-1", affects=("lifecycle_linkage",))
    out_of_scope_capability = make_capability("cap-2", affects=())

    assert classify_capability_relevance(relevant_capability) == "relevant"
    assert capability_is_relevant(relevant_capability) is True

    assert classify_capability_relevance(out_of_scope_capability) == "out_of_scope"
    assert capability_is_relevant(out_of_scope_capability) is False


def test_resolve_messages_schema_dir_finds_envelope_schema() -> None:
    """Verify resolve messages schema dir finds envelope schema."""
    schema_dir = resolve_messages_schema_dir()
    assert (schema_dir / "Envelope.json").exists() or (schema_dir / "Envelope.schema.json").exists()


def test_resolve_messages_schema_dir_falls_back_to_bundled_package_schema(tmp_path, monkeypatch) -> None:
    """Verify resolve messages schema dir falls back to bundled package schema."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(message_capability_inventory, "_schema_dir_from_git_root", lambda: None)

    schema_dir = resolve_messages_schema_dir()

    assert schema_dir.name == "message_jsonschema"
    assert (schema_dir / "Envelope.schema.json").exists()


def test_coverage_inventory_schema_dir_points_to_bundled_package_schema() -> None:
    """Verify coverage inventory schema dir points to bundled package schema."""
    assert SCHEMA_DIR.name == "message_jsonschema"
    assert (SCHEMA_DIR / "Envelope.schema.json").exists()


def test_generated_inventory_capability_ids_are_unique_and_canonical() -> None:
    """Verify generated inventory capability ids are unique and canonical."""
    inventory = generate_inventory(resolve_messages_schema_dir())
    capability_ids = iter_capability_ids(inventory)

    assert capability_ids == tuple(sorted(capability_ids))
    assert len(capability_ids) == len(set(capability_ids))
    assert all("_" not in capability_id.split(".", 1)[0] for capability_id in capability_ids)


def test_reconcile_inventory_with_runtime_required_scope_has_zero_missing() -> None:
    """Verify reconcile inventory with runtime required scope has zero missing."""
    inventory = generate_inventory(resolve_messages_schema_dir())
    inventory_capability_ids = iter_capability_ids(inventory)
    runtime_required_scope_path = (
        Path(__file__).resolve().parents[4]
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
    """Verify reconcile runtime scope coverage tracks unclassified non runtime gaps."""
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
