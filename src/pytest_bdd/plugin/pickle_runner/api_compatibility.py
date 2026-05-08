"""Provide api compatibility helpers."""

from __future__ import annotations

import json
from inspect import isfunction
from pathlib import Path
from typing import cast

from pytest_bdd.hook import after_mark, after_tag, around_mark, around_tag, before_mark, before_tag
from pytest_bdd.model.scenario_run import ExternalApiCompatibilityRecord
from pytest_bdd.types.json import JSONObject

from .hook import PickleRunnerHookSpec

DECORATOR_PUBLIC_SYMBOLS = {
    "decorator:after_mark": after_mark,
    "decorator:after_tag": after_tag,
    "decorator:around_mark": around_mark,
    "decorator:around_tag": around_tag,
    "decorator:before_mark": before_mark,
    "decorator:before_tag": before_tag,
}


def normalize_public_symbols(symbols: list[str]) -> list[str]:
    """Normalize public symbols."""
    return sorted(dict.fromkeys(symbols))


def collect_hook_public_symbols() -> list[str]:
    """Collect hook public symbols."""
    symbols: list[str] = []
    for attr_name, attr_value in vars(PickleRunnerHookSpec).items():
        if attr_name.startswith("_"):
            continue
        if isfunction(attr_value):
            symbols.append(f"hook:{attr_name}")
    symbols.extend(DECORATOR_PUBLIC_SYMBOLS)
    return normalize_public_symbols(symbols)


def load_api_baseline(path: str | Path) -> JSONObject:
    """Load api baseline."""
    baseline_path = Path(path)
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    return cast(JSONObject, payload)


def build_external_api_compatibility_record(
    *,
    baseline_reference: str,
    baseline_symbols: list[str],
    current_symbols: list[str] | None = None,
) -> ExternalApiCompatibilityRecord:
    """Build external api compatibility record."""
    effective_current_symbols = normalize_public_symbols(current_symbols or collect_hook_public_symbols())
    normalized_baseline_symbols = normalize_public_symbols(baseline_symbols)
    baseline_set = set(normalized_baseline_symbols)
    current_set = set(effective_current_symbols)

    removed_symbols = sorted(baseline_set - current_set)
    additive_symbols = sorted(current_set - baseline_set)

    # Renames are intentionally conservative: explicit rename detection is deferred.
    renamed_symbols: list[str] = []

    return ExternalApiCompatibilityRecord(
        api_surface_id="hook-plugin-public-api",
        baseline_reference=baseline_reference,
        changed_symbols=normalize_public_symbols(additive_symbols),
        removed_symbols=removed_symbols,
        renamed_symbols=renamed_symbols,
        additive_symbols=additive_symbols,
        consumer_migration_required=bool(removed_symbols or renamed_symbols),
    )
