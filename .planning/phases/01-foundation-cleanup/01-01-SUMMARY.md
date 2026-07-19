---
phase: 01-foundation-cleanup
plan: 01
subsystem: cleanup
tags: [allure, pyproject.toml, dead-code, plugin]
requires: []
provides:
  - Clean pyproject.toml with zero allure references (entrypoint, extras, mypy, ruff, test groups)
  - Deleted dead allure_logger plugin directory (289 unreachable lines)
  - Deleted compatibility/allure.py shim (7 lines, ALLURE_INSTALLED=False)
  - Deleted allure test directories (tests/allure_/, tests/e2e/allure/)
affects: [02-code-quality-gates]

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - pyproject.toml
  deleted:
    - src/pytest_bdd/plugin/allure_logger/
    - src/pytest_bdd/compatibility/allure.py
    - tests/allure_/
    - tests/e2e/allure/

key-decisions:
  - "Direct removal per D-10 precedent — no deprecation warnings, no transitional code"

patterns-established: []

requirements-completed:
  - STAB-01

duration: 5min
completed: 2026-05-12
---

# Phase 01 Plan 01: Remove Dead Allure Plugin Summary

**Stripped every trace of the dead Allure logger plugin: entrypoint, source directories, compatibility shim, optional dependency group, mypy overrides, test group config, and ruff suppressions.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-05-12
- **Completed:** 2026-05-12
- **Tasks:** 2
- **Files modified:** 1 (pyproject.toml)
- **Files deleted:** 4 directories, 1 file

## Accomplishments
- pyproject.toml has zero allure references: removed entrypoint, [allure] extras block, full-extra reference, test dependency, mypy override, test group path, and 2 ruff per-file-ignores
- Deleted dead allure_logger plugin (3 files, entrypoint registered at runtime but all 289 lines unreachable)
- Deleted compatibility/allure.py shim (only set ALLURE_INSTALLED=False)
- Deleted allure test directories (tests/allure_/, tests/e2e/allure/)

## Task Commits

1. **Task 1: Strip allure from pyproject.toml** - `6d4de6c3` (fix)
2. **Task 2: Delete Allure plugin source, compat shim, and test directories** - `755dac41` (fix)

## Files Deleted
- `src/pytest_bdd/plugin/allure_logger/` — dead plugin directory
- `src/pytest_bdd/compatibility/allure.py` — compatibility shim
- `tests/allure_/` — allure unit tests
- `tests/e2e/allure/` — allure E2E tests

## Decisions Made
- Direct removal without deprecation warnings (D-10 precedent from CONTEXT.md)
- No transitional code or comments — all allure references removed entirely

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Stale `.pyc` cache files in `src/pytest_bdd/compatibility/__pycache__/` contained allure bytecode — cleaned during execution
- Stale `src/UNKNOWN.egg-info/SOURCES.txt` listed deleted allure files — removed stale egg-info directory

## Next Phase Readiness
- Plan 01-02 (--cucumberjson removal) ready to execute
- All verifications pass: pytest-bdd imports cleanly, allure_logger import raises ImportError

---
*Phase: 01-foundation-cleanup*
*Completed: 2026-05-12*
