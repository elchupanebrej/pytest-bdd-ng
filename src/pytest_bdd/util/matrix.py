"""
Provides focused utility functions for the `matrix` concern within pytest-bdd utility layer,
offering helper operatio.

Responsibility:
    Provides focused utility functions for the `matrix` concern within pytest-bdd utility layer,
    offering helper operations consumed by higher layers (collection, runtime, reporting) without
    pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `matrix` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `matrix`-related helper operations within the
    utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `matrix` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `matrix` utilities for reporting, collection, and runtime operations

State and side effects:
    None, this module keeps no persistent state and performs no file or network I/O.

Invariants:
    - The public API surface (exported names) remains stable across internal refactors.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import re
from itertools import product
from typing import TYPE_CHECKING

from pytest_bdd.compatibility.runtime_compat import (
    CompatibilityMatrixEntry,
    MigrationCoverageSummary,
    is_pair_compatible,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def _extract_brace_factor_values(*, text: str, prefix: str) -> set[str]:
    """
    Perform the `_extract_brace_factor_values` operation within its module boundary, implementing.
    a focused helper funct.

    Responsibility:
        Performs the `_extract_brace_factor_values` operation within its module boundary, implementing
        a focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_extract_brace_factor_values` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _extract_brace_factor_values operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _extract_brace_factor_values for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _extract_brace_factor_values function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    factors: set[str] = set()
    for raw_group in re.findall(rf"{prefix}\{{([^}}]+)\}}", text):
        for raw_factor in raw_group.split(","):
            factor = raw_factor.strip()
            if factor.startswith("py") and factor[2:].isdigit():
                factor = factor[2:]
            if factor == "latest" or factor.isdigit():
                factors.add(factor)
    return factors


def extract_factors_from_tox_ini(tox_ini_path: Path) -> tuple[list[str], list[str]]:
    """
    Perform the `extract_factors_from_tox_ini` operation within its module boundary, implementing.
    a focused helper funct.

    Responsibility:
        Performs the `extract_factors_from_tox_ini` operation within its module boundary, implementing
        a focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `extract_factors_from_tox_ini` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the extract_factors_from_tox_ini operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke extract_factors_from_tox_ini for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The extract_factors_from_tox_ini function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    text = tox_ini_path.read_text(encoding="utf-8")
    python_factors = sorted(
        set(re.findall(r"py(?:py)?(\d{2,3})", text)) | _extract_brace_factor_values(text=text, prefix="py"),
    )
    pytest_factors = sorted(
        set(re.findall(r"pytest(latest|\d{2,3})", text)) | _extract_brace_factor_values(text=text, prefix="pytest"),
    )
    return python_factors, pytest_factors


def expand_tox_env_names(entries: Iterable[CompatibilityMatrixEntry]) -> list[str]:
    """
    Perform the `expand_tox_env_names` operation within its module boundary, implementing a.
    focused helper function that.

    Responsibility:
        Performs the `expand_tox_env_names` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `expand_tox_env_names` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the expand_tox_env_names operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke expand_tox_env_names for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The expand_tox_env_names function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return [entry.tox_env_name for entry in entries if entry.is_compatible and entry.tox_env_name]


def _normalize_scenario_id(value: str) -> str:
    """
    Perform the `_normalize_scenario_id` operation within its module boundary, implementing a.
    focused helper function th.

    Responsibility:
        Performs the `_normalize_scenario_id` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_normalize_scenario_id` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _normalize_scenario_id operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _normalize_scenario_id for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _normalize_scenario_id function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def discover_feature_scenario_ids(features_root: Path) -> set[str]:
    """
    Perform the `discover_feature_scenario_ids` operation within its module boundary, implementing.
    a focused helper func.

    Responsibility:
        Performs the `discover_feature_scenario_ids` operation within its module boundary, implementing
        a focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `discover_feature_scenario_ids` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the discover_feature_scenario_ids operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke discover_feature_scenario_ids for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The discover_feature_scenario_ids function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if not features_root.exists():
        return set()

    ids: set[str] = set()
    for file_path in features_root.rglob("*"):
        if not file_path.is_file():
            continue
        suffix = "".join(file_path.suffixes).lower()
        if suffix not in {".feature", ".feature.md", ".md"}:
            continue
        if ".feature" not in file_path.name.lower():
            continue
        ids.add(_normalize_scenario_id(file_path.stem.replace(".feature", "")))
    return ids


def discover_user_facing_test_scenario_ids(tests_root: Path) -> set[str]:
    """
    Perform the `discover_user_facing_test_scenario_ids` operation within its module boundary,.
    implementing a focused he.

    Responsibility:
        Performs the `discover_user_facing_test_scenario_ids` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `discover_user_facing_test_scenario_ids` exists as a standalone function because it
        encapsulates an operation that does not require shared instance state and benefits from being
        independently callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the discover_user_facing_test_scenario_ids operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke discover_user_facing_test_scenario_ids for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The discover_user_facing_test_scenario_ids function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if not tests_root.exists():
        return set()

    # Migration scope for user-facing scenarios is intentionally constrained to the
    # explicit documentation-oriented E2E tests selected for migration.
    migrated_candidates = {
        "test_no_scenario.py",
        "test_feature_base_dir.py",
    }

    # `tests/feature/` is treated as the source of user-facing E2E tests to migrate.
    user_facing_dir = tests_root / "feature"
    if not user_facing_dir.exists():
        return set()

    ids: set[str] = set()
    for file_path in user_facing_dir.rglob("test_*.py"):
        if file_path.name == "__init__.py":
            continue
        if file_path.name not in migrated_candidates:
            continue
        ids.add(_normalize_scenario_id(file_path.stem.replace("test_", "")))
    return ids


def build_migration_coverage_summary(
    tests_root: Path,
    features_root: Path,
    threshold_percent: int = 80,
) -> MigrationCoverageSummary:
    """
    Perform the `build_migration_coverage_summary` operation within its module boundary,.
    implementing a focused helper f.

    Responsibility:
        Performs the `build_migration_coverage_summary` operation within its module boundary,
        implementing a focused helper function that is consumed by higher layers for its specific
        utility purpose within the pytest-bdd architecture.

    Reason for existence:
        `build_migration_coverage_summary` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the build_migration_coverage_summary operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke build_migration_coverage_summary for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The build_migration_coverage_summary function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    feature_ids = discover_feature_scenario_ids(features_root)
    user_facing_test_ids = discover_user_facing_test_scenario_ids(tests_root)

    total_ids = feature_ids | user_facing_test_ids
    in_features = len(feature_ids)
    total = len(total_ids)
    coverage = 100.0 if total == 0 else (in_features / total) * 100
    duplicates_in_tests = len(feature_ids & user_facing_test_ids)
    threshold_met = coverage >= threshold_percent and duplicates_in_tests == 0

    return MigrationCoverageSummary(
        total_user_facing_scenarios=total,
        user_facing_in_features=in_features,
        coverage_percent=round(coverage, 2),
        threshold_percent=threshold_percent,
        threshold_met=threshold_met,
        duplicates_in_tests=duplicates_in_tests,
    )


def build_matrix(
    python_factors: Iterable[str],
    pytest_factors: Iterable[str],
    execution_targets: tuple[str, ...] = ("lin", "mac", "win"),
) -> list[CompatibilityMatrixEntry]:
    """
    Perform the `build_matrix` operation within its module boundary, implementing a focused helper.
    function that is cons.

    Responsibility:
        Performs the `build_matrix` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `build_matrix` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the build_matrix operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke build_matrix for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The build_matrix function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    entries: list[CompatibilityMatrixEntry] = []
    for python_factor, pytest_factor in product(sorted(set(python_factors)), sorted(set(pytest_factors))):
        compatible, reason = is_pair_compatible(python_factor, pytest_factor)
        tox_env = None
        if compatible:
            tox_env = f"py{python_factor}-pytest{pytest_factor}-coverage-lin"
        entries.append(
            CompatibilityMatrixEntry(
                python_version=_format_python_version(python_factor),
                pytest_version=_format_pytest_version(pytest_factor),
                is_compatible=compatible,
                is_supported=compatible,
                reason_code=reason,
                execution_targets=execution_targets,
                tox_env_name=tox_env,
            ),
        )
    return entries


def _format_python_version(python_factor: str) -> str:
    """
    Perform the `_format_python_version` operation within its module boundary, implementing a.
    focused helper function th.

    Responsibility:
        Performs the `_format_python_version` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_format_python_version` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _format_python_version operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _format_python_version for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _format_python_version function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if not python_factor.isdigit():
        return python_factor
    if len(python_factor) == 2:  # noqa: PLR2004  -- suppressed warning
        return f"3.{python_factor[1]}"
    if len(python_factor) == 3:  # noqa: PLR2004  -- suppressed warning
        return f"{python_factor[0]}.{python_factor[1:]}"
    return python_factor


def _format_pytest_version(pytest_factor: str) -> str:
    """
    Perform the `_format_pytest_version` operation within its module boundary, implementing a.
    focused helper function th.

    Responsibility:
        Performs the `_format_pytest_version` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_format_pytest_version` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _format_pytest_version operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _format_pytest_version for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _format_pytest_version function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if pytest_factor == "latest":
        return "latest"
    if len(pytest_factor) == 2:  # noqa: PLR2004  -- suppressed warning
        return f"{pytest_factor[0]}.{pytest_factor[1]}"
    if len(pytest_factor) == 3:  # noqa: PLR2004  -- suppressed warning
        return f"{pytest_factor[0]}.{pytest_factor[1]}.{pytest_factor[2]}"
    return pytest_factor
