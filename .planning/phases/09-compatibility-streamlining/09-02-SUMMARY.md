---
phase: "09-compatibility-streamlining"
plan: "02"
subsystem: compatibility
tags: [module-split, refactoring, matrix, runtime-compat, tox]

# Dependency graph
requires:
  - phase: "09-compatibility-streamlining"
    provides: "09-01: dead deps removed, clean baseline for refactoring"
provides:
  - "compatibility/runtime_compat.py: runtime compatibility rules (is_pair_compatible, bounds, constants)"
  - "util/matrix.py: CI/tox helpers (build_matrix, discovery, coverage summary)"
  - "Old compatibility/matrix.py deleted (352 lines split into two focused modules)"
  - "All 11 consumers updated to new import paths"
affects: ["10-pattern-unification", "11-dependency-upgrades"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One-way dependency: util/matrix imports from runtime_compat, never the reverse"
    - "Private version formatting helpers duplicated in util/matrix to avoid cross-module coupling"

key-files:
  created:
    - "src/pytest_bdd/compatibility/runtime_compat.py"
    - "src/pytest_bdd/util/matrix.py"
  modified:
    - "src/pytest_bdd/runner.py"
    - "src/pytest_bdd/script/compatibility_matrix.py"
    - "tests/compatibility/test_matrix_rules.py"
    - "tests/compatibility/test_matrix_expansion.py"
    - "tests/compatibility/test_tox_env_stability.py"
    - "tests/compatibility/test_existing_support_regression.py"
    - "tests/compatibility/test_ci_matrix_completeness.py"
    - "tests/compatibility/test_e2e_inventory.py"
    - "tests/compatibility/test_e2e_classification.py"
    - "tests/compatibility/test_e2e_no_duplicates.py"
    - "tests/compatibility/test_e2e_migration_threshold.py"

key-decisions:
  - "Duplicated _format_python_version and _format_pytest_version in util/matrix to avoid runtime_compat importing from util (circular import prevention)"
  - "MigrationCoverageSummary stays in runtime_compat (per D-10); util/matrix imports it"

patterns-established:
  - "Runtime rules (version checking) separated from CI helpers (matrix generation, tox parsing)"
  - "Single-direction import dependency: util/matrix → runtime_compat, never reverse"

requirements-completed: ["SIM-01"]

# Metrics
duration: 10min
completed: 2026-05-16
---

# Phase 09 Plan 02: Split compatibility/matrix.py Summary

**Split 352-line matrix.py into runtime_compat.py (runtime version rules) and util/matrix.py (CI/tox helpers), updated 11 consumers, deleted old module.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-05-16T11:50:00Z
- **Completed:** 2026-05-16T12:00:00Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments

- Created compatibility/runtime_compat.py with is_pair_compatible, bounds, constants, data classes
- Created util/matrix.py with build_matrix, CI/tox helpers, scenario discovery functions
- Updated all 11 consumer files to import from correct new module paths
- Deleted old compatibility/matrix.py (352 lines)
- All 39 compatibility tests pass, no circular imports

## Task Commits

Each task was committed atomically:

1. **Task 1: Create runtime_compat.py** - `7ba57900` (feat)
2. **Task 2: Create util/matrix.py** - `e0a4e03d` (feat)
3. **Task 3: Update consumers, delete matrix.py** - `eabc3c30` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified

- `src/pytest_bdd/compatibility/runtime_compat.py` - Runtime compatibility rules (173 lines)
- `src/pytest_bdd/util/matrix.py` - CI/tox matrix helpers (228 lines)
- `src/pytest_bdd/runner.py` - Updated import to runtime_compat
- `src/pytest_bdd/script/compatibility_matrix.py` - Split imports across both new modules
- `tests/compatibility/test_matrix_rules.py` - Import from runtime_compat
- `tests/compatibility/test_matrix_expansion.py` - Import from util.matrix
- `tests/compatibility/test_tox_env_stability.py` - Import from util.matrix
- `tests/compatibility/test_existing_support_regression.py` - Import from util.matrix
- `tests/compatibility/test_ci_matrix_completeness.py` - Import from util.matrix
- `tests/compatibility/test_e2e_inventory.py` - Import from util.matrix
- `tests/compatibility/test_e2e_classification.py` - Import from util.matrix
- `tests/compatibility/test_e2e_no_duplicates.py` - Import from util.matrix
- `tests/compatibility/test_e2e_migration_threshold.py` - Import from util.matrix
- `src/pytest_bdd/compatibility/matrix.py` - DELETED

## Decisions Made

- Duplicated `_format_python_version` and `_format_pytest_version` in util/matrix.py rather than importing from runtime_compat. These are private helpers used only by build_matrix. Importing them from runtime_compat would create unnecessary coupling. The duplication is minimal (6 lines each) and keeps modules truly independent.
- MigrationCoverageSummary stays in runtime_compat (per D-10 in plan). util/matrix imports it for build_migration_coverage_summary return type.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 09 complete (both plans done)
- SIM-01 requirement fully satisfied: dead deps removed (09-01), matrix split complete (09-02)
- Ready for Phase 10 (pattern unification)

---
*Phase: 09-compatibility-streamlining*
*Completed: 2026-05-16*
