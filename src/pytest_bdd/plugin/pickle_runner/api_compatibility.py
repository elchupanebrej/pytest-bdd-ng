"""
Provide api compatibility helpers.

Responsibility:
    Provide api compatibility helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.pickle_runner.api_compatibility` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - normalize_public_symbols: owns nested behavior below this boundary
    - collect_hook_public_symbols: owns nested behavior below this boundary
    - load_api_baseline: owns nested behavior below this boundary
    - build_external_api_compatibility_record: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates DECORATOR_PUBLIC_SYMBOLS, symbols, baseline_path, payload, effective_current_symbols; depends on
    __future__.annotations, json, inspect.isfunction, pathlib.Path, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.plugin.pickle_runner.api_compatibility` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

import json
from inspect import isfunction
from pathlib import Path
from typing import TYPE_CHECKING, cast

from pytest_bdd.hook import after_mark, after_tag, around_mark, around_tag, before_mark, before_tag
from pytest_bdd.model.run import ExternalApiCompatibilityRecord

from .hook import PickleRunnerHookSpec

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject

DECORATOR_PUBLIC_SYMBOLS = {
    "decorator:after_mark": after_mark,
    "decorator:after_tag": after_tag,
    "decorator:around_mark": around_mark,
    "decorator:around_tag": around_tag,
    "decorator:before_mark": before_mark,
    "decorator:before_tag": before_tag,
}


def normalize_public_symbols(symbols: list[str]) -> list[str]:
    """
    Normalize public symbols.

    Returns:
        Sorted list of unique symbols.

    Responsibility:
        Normalize public symbols. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.api_compatibility.normalize_public_symbols` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - sorted: collaborator call used by this boundary
        - dict.fromkeys: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    return sorted(dict.fromkeys(symbols))


def collect_hook_public_symbols() -> list[str]:
    """
    Collect hook public symbols.

    Returns:
        List of public hook symbols.

    Responsibility:
        Collect hook public symbols. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.api_compatibility.collect_hook_public_symbols` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - vars.items: collaborator call used by this boundary
        - vars: collaborator call used by this boundary
        - attr_name.startswith: collaborator call used by this boundary
        - isfunction: collaborator call used by this boundary
        - symbols.append: collaborator call used by this boundary
        - symbols.extend: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/__init__.py: imports or references `collect_hook_public_symbols`

    State and side effects:
        mutates symbols.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.api_compatibility.collect_hook_public_symbols` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    symbols: list[str] = []
    for attr_name, attr_value in vars(PickleRunnerHookSpec).items():
        if attr_name.startswith("_"):
            continue
        if isfunction(attr_value):
            symbols.append(f"hook:{attr_name}")
    symbols.extend(DECORATOR_PUBLIC_SYMBOLS)
    return normalize_public_symbols(symbols)


def load_api_baseline(path: str | Path) -> JSONObject:
    """
    Load api baseline.

    Returns:
        Parsed JSON baseline.

    Responsibility:
        Load api baseline. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.api_compatibility.load_api_baseline`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Path: collaborator call used by this boundary
        - json.loads: collaborator call used by this boundary
        - baseline_path.read_text: collaborator call used by this boundary
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates baseline_path, payload.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.api_compatibility.load_api_baseline` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    baseline_path = Path(path)
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    return cast("JSONObject", payload)


def build_external_api_compatibility_record(
    *,
    baseline_reference: str,
    baseline_symbols: list[str],
    current_symbols: list[str] | None = None,
) -> ExternalApiCompatibilityRecord:
    """
    Build external api compatibility record.

    Returns:
        External API compatibility record.

    Responsibility:
        Build external api compatibility record. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.api_compatibility.build_external_api_compatibility_record` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - normalize_public_symbols: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - sorted: collaborator call used by this boundary
        - collect_hook_public_symbols: collaborator call used by this boundary
        - ExternalApiCompatibilityRecord: collaborator call used by this boundary
        - bool: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/__init__.py: imports or references
          `build_external_api_compatibility_record`

    State and side effects:
        mutates effective_current_symbols, normalized_baseline_symbols, baseline_set, current_set, removed_symbols.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.api_compatibility.build_external_api_compatibility_record` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
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
