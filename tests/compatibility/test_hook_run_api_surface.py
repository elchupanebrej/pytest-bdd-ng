from __future__ import annotations

from pathlib import Path

from pytest_bdd import scenario
from pytest_bdd.plugin.pickle_runner.api_compatibility import (
    build_external_api_compatibility_record,
    collect_hook_public_symbols,
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


def test_current_hook_public_symbols_cover_the_saved_baseline() -> None:
    baseline_path = Path(__file__).with_name("hook_public_api_baseline.json")
    baseline = load_api_baseline(baseline_path)

    current_symbols = collect_hook_public_symbols()

    assert set(baseline["symbols"]).issubset(current_symbols)


def test_current_hook_public_symbols_are_sorted_and_unique() -> None:
    current_symbols = collect_hook_public_symbols()

    assert current_symbols == sorted(current_symbols)
    assert len(current_symbols) == len(set(current_symbols))


def test_scenario_decorator_uses_pickle_fixture_for_runtime_binding() -> None:
    decorator = scenario("test.feature", "Scenario", return_test_decorator=True)

    @decorator
    def test_case():
        return None

    usefixtures_marks = [mark for mark in test_case.pytestmark if mark.name == "usefixtures"]

    assert any(mark.args == ("gherkin_document", "pickle", "feature_source") for mark in usefixtures_marks)
