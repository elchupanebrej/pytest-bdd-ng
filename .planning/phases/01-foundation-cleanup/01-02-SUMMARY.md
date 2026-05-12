---
phase: 01-foundation-cleanup
plan: 02
subsystem: cleanup
tags: [cucumber-json, cli, legacy, entrypoint]
requires: []
provides:
  - Clean cucumber_json entrypoint without legacy --cucumberjson flag
  - Running pytest --cucumberjson produces standard "unrecognized arguments" error
affects: []

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - src/pytest_bdd/plugin/cucumber_json/entrypoint.py

key-decisions:
  - "Direct removal per D-10 — no deprecation, no transitional period"
  - "Removed unused `group` variable to satisfy ruff F841 (deviation from plan which said to keep it)"

patterns-established: []

requirements-completed:
  - STAB-04

duration: 3min
completed: 2026-05-12
---

# Phase 01 Plan 02: Remove Legacy --cucumberjson CLI Flag Summary

**Removed the deprecated `--cucumberjson` flag from cucumber_json entrypoint. Users now get standard pytest "unrecognized arguments" error; `--cucumber-json` continues working via cucumber_json_formatter.py.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-05-12
- **Completed:** 2026-05-12
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Deleted `group.addoption(--cucumberjson)` call and TODO comment from `pytest_addoption()`
- `parser.addini(cucumber_json_path)` preserved — ini option still works
- `--cucumber-json` (defined in cucumber_json_formatter.py) unaffected
- Running `pytest --cucumberjson` produces `error: unrecognized arguments: --cucumberjson`

## Task Commits

1. **Task 1: Remove --cucumberjson addoption from entrypoint** - `6ae8abc6` (fix)

## Files Modified
- `src/pytest_bdd/plugin/cucumber_json/entrypoint.py` — removed 10 lines (TODO + addoption block), cleaned unused `group` variable

## Decisions Made
- Direct removal without deprecation warnings (D-10 precedent)
- No transitional code or error hints

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Unused `group` variable violated ruff F841**
- **Found during:** Task 1 (commit pre-commit hook)
- **Issue:** Plan said to keep `group = parser.getgroup(...)` but without the `addoption()` call, `group` was unused
- **Fix:** Changed to `parser.getgroup("bdd", "Cucumber JSON")` — preserves help group registration without unused variable
- **Files modified:** src/pytest_bdd/plugin/cucumber_json/entrypoint.py
- **Verification:** Ruff pre-commit hook passed
- **Committed in:** 6ae8abc6

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minimal — preserves help group in CLI output while satisfying ruff lint.

## Issues Encountered
None

## Next Phase Readiness
- Phase 01 Foundation Cleanup complete
- Ready for Phase 02: Code Quality Gates

---
*Phase: 01-foundation-cleanup*
*Completed: 2026-05-12*
