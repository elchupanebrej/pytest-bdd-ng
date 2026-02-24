from __future__ import annotations

import json
from inspect import isfunction
from pathlib import Path
from typing import Any

from pytest_bdd.hook import after_mark, after_tag, around_mark, around_tag, before_mark, before_tag
from pytest_bdd.model.execution_context import ExternalApiCompatibilityRecord

from .hook import ScenarioRunnerHookSpec

DECORATOR_PUBLIC_SYMBOLS = {
    "decorator:after_mark": after_mark,
    "decorator:after_tag": after_tag,
    "decorator:around_mark": around_mark,
    "decorator:around_tag": around_tag,
    "decorator:before_mark": before_mark,
    "decorator:before_tag": before_tag,
}


def collect_hook_public_symbols() -> list[str]:
    symbols: list[str] = []
    for attr_name, attr_value in vars(ScenarioRunnerHookSpec).items():
        if attr_name.startswith("_"):
            continue
        if isfunction(attr_value):
            symbols.append(f"hook:{attr_name}")
    symbols.extend(DECORATOR_PUBLIC_SYMBOLS)
    return sorted(symbols)


def load_api_baseline(path: str | Path) -> dict[str, Any]:
    baseline_path = Path(path)
    return json.loads(baseline_path.read_text())


def build_external_api_compatibility_record(
    *,
    baseline_reference: str,
    baseline_symbols: list[str],
    current_symbols: list[str] | None = None,
) -> ExternalApiCompatibilityRecord:
    effective_current_symbols = current_symbols or collect_hook_public_symbols()
    baseline_set = set(baseline_symbols)
    current_set = set(effective_current_symbols)

    removed_symbols = sorted(baseline_set - current_set)
    additive_symbols = sorted(current_set - baseline_set)

    # Renames are intentionally conservative: explicit rename detection is deferred.
    renamed_symbols: list[str] = []

    return ExternalApiCompatibilityRecord(
        api_surface_id="hook-plugin-public-api",
        baseline_reference=baseline_reference,
        changed_symbols=sorted(additive_symbols),
        removed_symbols=removed_symbols,
        renamed_symbols=renamed_symbols,
        additive_symbols=additive_symbols,
        consumer_migration_required=bool(removed_symbols or renamed_symbols),
    )
