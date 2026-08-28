from __future__ import annotations

from pytest_bdd.compatibility.runtime_compat import (
    MIN_SUPPORTED_PYTEST,
    MIN_SUPPORTED_PYTHON,
    PYTEST_COMPATIBILITY_BOUNDS,
    CompatibilityMatrixEntry,
    MigrationCoverageSummary,
)


def test_matrix_bounds_and_constants() -> None:
    assert MIN_SUPPORTED_PYTHON == (3, 10)
    assert MIN_SUPPORTED_PYTEST == (7, 0, 0)
    assert "80" in PYTEST_COMPATIBILITY_BOUNDS


def test_matrix_entry_and_migration_summary() -> None:
    entry = CompatibilityMatrixEntry(
        python_version="3.10", pytest_version="8.0", is_compatible=True, is_supported=True, reason_code="compatible"
    )
    assert entry.is_compatible is True

    summary = MigrationCoverageSummary(
        total_user_facing_scenarios=10,
        user_facing_in_features=10,
        coverage_percent=100.0,
        threshold_percent=80,
        threshold_met=True,
        duplicates_in_tests=0,
    )
    assert summary.threshold_met is True
