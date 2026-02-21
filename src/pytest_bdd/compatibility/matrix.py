"""Compatibility matrix helpers for Python/pytest version selection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import product
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

PYTEST_COMPATIBILITY_BOUNDS: dict[str, tuple[tuple[int, int], tuple[int, int] | None]] = {
    # pytest 6.x
    "625": ((3, 6), (3, 10)),
    # pytest 7.x
    "70": ((3, 7), (3, 11)),
    "71": ((3, 7), (3, 11)),
    "72": ((3, 7), (3, 11)),
    "73": ((3, 7), (3, 11)),
    "74": ((3, 7), (3, 11)),
    # pytest 8.x
    "80": ((3, 8), (3, 13)),
    "81": ((3, 8), (3, 13)),
    "82": ((3, 8), (3, 13)),
    "83": ((3, 8), (3, 13)),
    "84": ((3, 8), (3, 13)),
    # pytest 9.x
    "90": ((3, 9), (3, 14)),
    # latest follows newest known major guardrails to avoid project-specific caps.
    "latest": ((3, 9), (3, 14)),
}

MIN_SUPPORTED_PYTHON: tuple[int, int] = (3, 10)
MIN_SUPPORTED_PYTEST: tuple[int, int, int] = (6, 2, 5)

REASON_COMPATIBLE = "compatible"
REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST = "python_not_supported_by_pytest"
REASON_PYTEST_UNAVAILABLE = "pytest_unavailable"
REASON_PYTHON_UNAVAILABLE = "python_unavailable"
REASON_EOL_PYTHON = "eol_python"
REASON_EOL_PYTEST = "eol_pytest"


@dataclass(frozen=True)
class CompatibilityMatrixEntry:
    python_version: str
    pytest_version: str
    is_compatible: bool
    is_supported: bool
    reason_code: str
    execution_targets: tuple[str, ...] = ("lin", "mac", "win")
    compatibility_source: str = "pytest-metadata"
    tox_env_name: str | None = None


@dataclass(frozen=True)
class MigrationCoverageSummary:
    total_user_facing_scenarios: int
    user_facing_in_features: int
    coverage_percent: float
    threshold_percent: int
    threshold_met: bool
    duplicates_in_tests: int


def _parse_python_factor(python_factor: str) -> tuple[int, int] | None:
    if not python_factor.isdigit():
        return None
    if len(python_factor) == 2:
        return (3, int(python_factor[1]))
    if len(python_factor) == 3:
        return (int(python_factor[0]), int(python_factor[1:]))
    return None


def _format_python_version(python_factor: str) -> str:
    parsed = _parse_python_factor(python_factor)
    return f"{parsed[0]}.{parsed[1]}" if parsed else python_factor


def _format_pytest_version(pytest_factor: str) -> str:
    if pytest_factor == "latest":
        return "latest"
    if len(pytest_factor) == 2:
        return f"{pytest_factor[0]}.{pytest_factor[1]}"
    if len(pytest_factor) == 3:
        return f"{pytest_factor[0]}.{pytest_factor[1]}.{pytest_factor[2]}"
    return pytest_factor


def _parse_pytest_factor(pytest_factor: str) -> tuple[int, int, int] | None:
    if pytest_factor == "latest":
        # Keep "latest" above current known floor.
        return (99, 0, 0)
    if not pytest_factor.isdigit():
        return None
    if len(pytest_factor) == 2:
        return (int(pytest_factor[0]), int(pytest_factor[1]), 0)
    if len(pytest_factor) == 3:
        return (int(pytest_factor[0]), int(pytest_factor[1]), int(pytest_factor[2]))
    return None


def is_pair_compatible(python_factor: str, pytest_factor: str) -> tuple[bool, str]:
    py = _parse_python_factor(python_factor)
    if py is None:
        return False, REASON_PYTHON_UNAVAILABLE
    if py < MIN_SUPPORTED_PYTHON:
        return False, REASON_EOL_PYTHON

    pytest_version = _parse_pytest_factor(pytest_factor)
    if pytest_version is not None and pytest_version < MIN_SUPPORTED_PYTEST:
        return False, REASON_EOL_PYTEST

    bounds = PYTEST_COMPATIBILITY_BOUNDS.get(pytest_factor)
    if bounds is None:
        return False, REASON_PYTEST_UNAVAILABLE

    min_version, max_version = bounds
    if py < min_version:
        return False, REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST
    if max_version is not None and py > max_version:
        return False, REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST
    return True, REASON_COMPATIBLE


def build_matrix(
    python_factors: Iterable[str],
    pytest_factors: Iterable[str],
    execution_targets: tuple[str, ...] = ("lin", "mac", "win"),
) -> list[CompatibilityMatrixEntry]:
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


def extract_factors_from_tox_ini(tox_ini_path: Path) -> tuple[list[str], list[str]]:
    text = tox_ini_path.read_text(encoding="utf-8")
    python_factors = sorted(set(re.findall(r"py(?:py)?(\d{2,3})", text)))
    pytest_factors = sorted(set(re.findall(r"pytest(latest|\d{2,3})", text)))
    return python_factors, pytest_factors


def expand_tox_env_names(entries: Iterable[CompatibilityMatrixEntry]) -> list[str]:
    return [entry.tox_env_name for entry in entries if entry.is_compatible and entry.tox_env_name]


def _normalize_scenario_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def discover_feature_scenario_ids(features_root: Path) -> set[str]:
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
