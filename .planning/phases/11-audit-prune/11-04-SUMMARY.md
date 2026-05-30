---
phase: 11-audit-prune
plan: "04"
subsystem: code-architecture
tags: [module-split, package-refactor, attrs, enums]

# Dependency graph
requires:
  - phase: 11-audit-prune
    provides: dead code removal from 11-01
provides:
  - run.py split into 3 focused modules: stages.py, refs.py, lifecycle.py
  - Backward-compatible re-exports for all public classes and type aliases
  - Run class still inherits from StashBound with STASH_KEY preserved
affects: [future runtime feature development, scenario_run.py imports]

# Tech tracking
tech-stack:
  added: []
  patterns: [package re-exports, dependency ordering: stages -> refs -> lifecycle, per-file ruff ignores not needed (clean split)]

key-files:
  created:
    - src/pytest_bdd/model/run/__init__.py
    - src/pytest_bdd/model/run/stages.py
    - src/pytest_bdd/model/run/refs.py
    - src/pytest_bdd/model/run/lifecycle.py
  modified: []
  deleted:
    - src/pytest_bdd/model/run.py

key-decisions:
  - "Used explicit re-export pattern in __init__.py with __all__ for clear public API"
  - "Kept type aliases (LifecycleKind, NodeKind, ScenarioRunResult) in the sub-modules where they're used and re-exported from __init__.py"
  - "No per-file ruff ignores needed — split was clean with no intentional late imports"

patterns-established:
  - "Clean dependency ordering: stages.py (no internal deps) -> refs.py (no internal deps) -> lifecycle.py (imports stages + refs)"
  - "Type aliases defined alongside their primary consumers, re-exported from package root"

requirements-completed: [SIM-03]

# Metrics
duration: 20min
completed: 2026-05-16
---

# Phase 11 Plan 04: Split run.py Summary

Split 783-line monolithic model/run.py into 3 focused sub-modules (~100-350L each) with full backward compatibility for all imports.

## Performance

- **Duration:** 20min
- **Started:** 2026-05-16T23:24:00Z
- **Completed:** 2026-05-16T23:45:00Z
- **Tasks:** 1
- **Files modified:** 5 (4 created, 1 deleted)

## Accomplishments

- Split `run.py` (783L) into package with 4 modules: `stages.py`, `refs.py`, `lifecycle.py`, `__init__.py`
- Preserved all public API imports from `pytest_bdd.model.run` package path
- All 426 unit/hook tests pass, 207 message/contract tests pass
- ruff F401/F811/ERA001 passes clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Split run.py into model/run/ package** - `9ce41692` (refactor)

## Files Created/Modified

- `src/pytest_bdd/model/run/__init__.py` - Re-exports all public names + type aliases
- `src/pytest_bdd/model/run/stages.py` - HookPhase, RunStage, RunStatus StrEnum classes
- `src/pytest_bdd/model/run/refs.py` - LifecycleObjectRef, NoPreviousStep, 8 helper ref functions
- `src/pytest_bdd/model/run/lifecycle.py` - Run class (StashBound), state classes (ActiveObjectSet, ReportingLifecycleState, etc.)
- `src/pytest_bdd/model/run.py` - DELETED (original 783L file)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing type alias re-exports**
- **Found during:** Task 1 import verification
- **Issue:** `scenario_run.py` imports `LifecycleKind`, `NodeKind`, `ScenarioRunResult` from `pytest_bdd.model.run` but plan's `__init__.py` spec didn't include these type aliases
- **Fix:** Added re-exports for `LifecycleKind` (from refs.py), `NodeKind` and `ScenarioRunResult` (from lifecycle.py) to `__init__.py`
- **Files modified:** `src/pytest_bdd/model/run/__init__.py`
- **Commit:** `9ce41692`

**2. [Rule 1 - Bug] Unused imports in lifecycle.py**
- **Found during:** Task 1 pre-commit (ruff F401)
- **Issue:** `_finished_*_ref` functions imported in lifecycle.py but never used there (only needed by consumers via package re-export)
- **Fix:** Removed unused imports from lifecycle.py; they remain re-exported via `__init__.py`
- **Files modified:** `src/pytest_bdd/model/run/lifecycle.py`
- **Commit:** `9ce41692`

## Self-Check: PASSED

- All 4 new files exist and import correctly
- Original file deleted (Test-Path returns False)
- Import check exits 0 with "imports OK"
- 426 unit/hook tests pass, 207 message/contract tests pass
- ruff F401/F811/ERA001 passes clean
- Commit `9ce41692` exists in git log
