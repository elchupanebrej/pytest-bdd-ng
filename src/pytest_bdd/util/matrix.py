"""CI and tox matrix helpers for compatibility inspection."""

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
    Extract Python and pytest factors from tox.ini file.

    Returns:
        Tuple of (python_factors, pytest_factors) lists.

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
    Expand tox env names from compatibility entries.

    Returns:
        List of tox environment names for compatible entries.

    """
    return [entry.tox_env_name for entry in entries if entry.is_compatible and entry.tox_env_name]


def _normalize_scenario_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def discover_feature_scenario_ids(features_root: Path) -> set[str]:
    """
    Discover feature scenario IDs from feature files.

    Returns:
        Set of normalized scenario IDs.

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
    Discover user-facing test scenario IDs from test files.

    Returns:
        Set of normalized test scenario IDs.

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
    Build migration coverage summary.

    Returns:
        Migration coverage summary with statistics.

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
    Build compatibility matrix for Python/pytest combinations.

    Args:
        python_factors: Python version factors.
        pytest_factors: Pytest version factors.
        execution_targets: Target platforms.

    Returns:
        List of compatibility matrix entries.

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
    Format Python factor as version string.

    Args:
        python_factor: Python factor string.

    Returns:
        Formatted version string.

    """
    if not python_factor.isdigit():
        return python_factor
    if len(python_factor) == 2:  # noqa: PLR2004
        return f"3.{python_factor[1]}"
    if len(python_factor) == 3:  # noqa: PLR2004
        return f"{python_factor[0]}.{python_factor[1:]}"
    return python_factor


def _format_pytest_version(pytest_factor: str) -> str:
    """
    Format pytest factor as version string.

    Args:
        pytest_factor: Pytest factor string.

    Returns:
        Formatted version string.

    """
    if pytest_factor == "latest":
        return "latest"
    if len(pytest_factor) == 2:  # noqa: PLR2004
        return f"{pytest_factor[0]}.{pytest_factor[1]}"
    if len(pytest_factor) == 3:  # noqa: PLR2004
        return f"{pytest_factor[0]}.{pytest_factor[1]}.{pytest_factor[2]}"
    return pytest_factor
