from __future__ import annotations

from attrs import frozen

PYTEST_COMPATIBILITY_BOUNDS: dict[str, tuple[tuple[int, int], tuple[int, int] | None]] = {
    "70": ((3, 7), (3, 11)),
    "71": ((3, 7), (3, 11)),
    "72": ((3, 7), (3, 11)),
    "73": ((3, 7), (3, 11)),
    "74": ((3, 7), (3, 11)),
    "80": ((3, 8), (3, 13)),
    "81": ((3, 8), (3, 13)),
    "82": ((3, 8), (3, 13)),
    "83": ((3, 8), (3, 13)),
    "84": ((3, 8), (3, 13)),
    "90": ((3, 9), (3, 14)),
    "latest": ((3, 9), (3, 14)),
}

MIN_SUPPORTED_PYTHON: tuple[int, int] = (3, 10)
MIN_SUPPORTED_PYTEST: tuple[int, int, int] = (7, 0, 0)

REASON_COMPATIBLE = "compatible"
REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST = "python_not_supported_by_pytest"
REASON_PYTEST_UNAVAILABLE = "pytest_unavailable"
REASON_PYTHON_UNAVAILABLE = "python_unavailable"
REASON_EOL_PYTHON = "eol_python"
REASON_EOL_PYTEST = "eol_pytest"


@frozen
class CompatibilityMatrixEntry:
    python_version: str
    pytest_version: str
    is_compatible: bool
    is_supported: bool
    reason_code: str
    execution_targets: tuple[str, ...] = ("lin", "mac", "win")
    compatibility_source: str = "pytest-metadata"
    tox_env_name: str | None = None


@frozen
class MigrationCoverageSummary:
    total_user_facing_scenarios: int
    user_facing_in_features: int
    coverage_percent: float
    threshold_percent: int
    threshold_met: bool
    duplicates_in_tests: int


__all__ = [
    "MIN_SUPPORTED_PYTEST",
    "MIN_SUPPORTED_PYTHON",
    "PYTEST_COMPATIBILITY_BOUNDS",
    "REASON_COMPATIBLE",
    "REASON_EOL_PYTEST",
    "REASON_EOL_PYTHON",
    "REASON_PYTEST_UNAVAILABLE",
    "REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST",
    "REASON_PYTHON_UNAVAILABLE",
    "CompatibilityMatrixEntry",
    "MigrationCoverageSummary",
]
