from __future__ import annotations

from pathlib import Path

from pytest_bdd.plugin.scenario_runner.api_compatibility import (
    build_external_api_compatibility_record,
    load_api_baseline,
)


def test_external_api_surface_remains_additive_only() -> None:
    baseline_path = Path(__file__).with_name("hook_public_api_baseline.json")
    baseline = load_api_baseline(baseline_path)

    record = build_external_api_compatibility_record(
        baseline_reference=baseline["baseline_reference"],
        baseline_symbols=baseline["symbols"],
    )

    assert record.removed_symbols == []
    assert record.renamed_symbols == []
    assert record.consumer_migration_required is False


def test_external_api_compatibility_record_is_serializable() -> None:
    baseline_path = Path(__file__).with_name("hook_public_api_baseline.json")
    baseline = load_api_baseline(baseline_path)

    record = build_external_api_compatibility_record(
        baseline_reference=baseline["baseline_reference"],
        baseline_symbols=baseline["symbols"],
    )

    payload = record.as_dict()
    assert payload["api_surface_id"] == "hook-plugin-public-api"
    assert payload["baseline_reference"] == baseline["baseline_reference"]
    assert isinstance(payload["additive_symbols"], list)
