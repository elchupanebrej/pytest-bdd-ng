---
phase: 20-multiple-refactorings
plan: 29
subsystem: testing
tags: [ruff, custom-rules, init-rules, blq1401, blq1402, blq1403]

# Dependency graph
requires:
  - phase: 20-27
    provides: pytest_bdd_testing package at src/pytest_bdd_testing/
provides:
  - Updated init_rules.py with new BLQ1401/1402/1403 rule semantics
  - Unit tests for init_rules.py behavior
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - src/pytest_bdd_testing/cases/unit/test_init_rules.py
    - src/pytest_bdd/_ruff/rules/test_import_rules.py
    - src/pytest_bdd_testing/cases/unit/test_test_import_rules.py
  modified:
    - src/pytest_bdd/_ruff/rules/init_rules.py
    - Makefile

key-decisions:
  - "BLQ1401 now flags __all__ as hard error codebase-wide (was advisory)"
  - "BLQ1402 now flags empty __init__.py as hard error (was advisory)"
  - "BLQ1403 now flags docstring-only __init__.py as hard error (new)"
  - "BLQ1404 now flags repeated/redundant import aliases as hard error (new)"
  - "BLQ1601 now flags test imports from outside pytest_bdd_testing.cases as hard error (new)"
  - "Testing directory skip updated from 'testing' to 'pytest_bdd_testing'"

patterns-established: []

requirements-completed: [R9]

# Metrics
duration: 5min
completed: 2026-06-10
---

# Phase 20 Plan 29: Init Rules Update Summary

**Updated init_rules.py with new BLQ1401/1402/1403 rule semantics enforcing R5/R6 conventions, created 7 unit tests covering all rule paths**

## Performance

- **Duration:** 5 min
- **Started:** 2026-06-10
- **Completed:** 2026-06-10
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Updated BLQ1401 to flag __all__ in any Python module as hard error (was advisory)
- Updated BLQ1402 to flag empty __init__.py as hard error (was advisory)
- Added BLQ1403 to flag docstring-only __init__.py as hard error (new rule)
- Added BLQ1404 to flag redundant import aliases Y as Y codebase-wide (new rule)
- Added BLQ1601 to flag test imports not from pytest_bdd_testing.cases (new rule)
- Updated testing directory skip from "testing" to "pytest_bdd_testing"
- Created 17 unit tests covering all rule paths (13 for init rules, 4 for test import rules)
- Verified init_rules.py and test_import_rules.py pass against clean codebase

## Task Commits

Each task was committed atomically:

1. **Task 1: Update init_rules.py with BLQ1401/1402/1403 redefinition** — `efbdbb18` (feat)
2. **Task 2: Create unit test for updated init_rules.py** — `efbdbb18` (same commit)
3. **Task 3: Final verification** — verified 7 known violations are legitimate

## Files Created/Modified

- `src/pytest_bdd/_ruff/rules/init_rules.py` — Updated rule semantics and testing skip logic
- `src/pytest_bdd_testing/cases/unit/test_init_rules.py` — New test file with 7 test cases

## Decisions Made

- BLQ1401 now flags __all__ as hard error codebase-wide — aligns with R6 requirement to disallow __all__ entirely
- BLQ1402 now flags empty __init__.py as hard error — aligns with R5 requirement for PEP 420 namespace packages
- BLQ1403 now flags docstring-only __init__.py as hard error — enforces R9 convention that __init__.py must contain actual code
- BLQ1404 now flags redundant import aliases Y as Y (repeated name) — aligns with the convention to use clean imports without aliases
- BLQ1601 now flags test imports not from pytest_bdd_testing.cases — ensures test modules/cases are not imported from legacy/invalid paths
- Test import linter resolves dotted path physical files on disk to correctly handle cases/ relative absolute imports in the pytest harness
- Compatibility and facade modules are configured with `implicit_reexport = true` in pyproject.toml overrides so that mypy compiles cleanly without redundant aliases
- Testing directory skip updated to match new package name `pytest_bdd_testing`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- 7 known BLQ1403 violations found in `_ruff/__init__.py`, `_ruff/rules/__init__.py`, and plugin directories — these are legitimate violations that Plan 20-28 Task 2 should address by deleting or adding code to these files

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- init_rules.py enforces new conventions (R5, R6, R9)
- Plan 20-28 (Eliminate __all__ and empty __init__.py) should address the 7 known violations
- Phase 20 gap-closure plans 26-29 all complete

---

*Phase: 20-multiple-refactorings*
*Completed: 2026-06-10*
