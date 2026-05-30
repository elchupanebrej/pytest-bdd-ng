---
phase: 11-audit-prune
plan: "02"
subsystem: code-cleanup
tags: [module-split, refactoring, steps, backward-compat]

# Dependency graph
requires:
  - phase: 11-audit-prune
    plan: "01"
    provides: dead code removal (runner.py deleted)
provides:
  - steps.py (971L) split into 5 focused modules (~100-200L each)
  - Backward-compatible public API preserved
  - StepDefinitionManager.Registry/Matcher/Definition nested class access preserved
affects: [11-03, 11-04, 11-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [module split with re-export __init__.py, namespace class for backward compat]

key-files:
  created:
    - src/pytest_bdd/steps/__init__.py
    - src/pytest_bdd/steps/definition.py
    - src/pytest_bdd/steps/registry.py
    - src/pytest_bdd/steps/matcher.py
    - src/pytest_bdd/steps/decorators.py
    - src/pytest_bdd/steps/manager.py
  modified:
    - src/pytest_bdd/steps.py (DELETED)

key-decisions:
  - "Used namespace class (StepDefinitionManager) instead of attrs for backward compat with nested class access"
  - "Separated decorator_builder into manager.py to avoid RUF067 __init__ lint violation"
  - "Matcher class uses manual __init__ (not @define) to avoid attrs field initialization complexity"

patterns-established:
  - "Module split pattern: sub-modules + __init__.py re-exports + namespace class for nested access"

requirements-completed: [SIM-03]

# Metrics
duration: 45min
completed: 2026-05-16
---

# Phase 11 Plan 02: Steps Module Split Summary

**Split steps.py (971L) into 5 focused modules with full backward compatibility**

## Performance

- **Duration:** 45 min
- **Started:** 2026-05-16T22:00:00Z
- **Completed:** 2026-05-16T22:44:17Z
- **Tasks:** 2 of 2 completed
- **Files modified:** 6 created, 1 deleted (steps.py)

## Accomplishments

- Split 971L god module into 5 focused modules (definition.py, registry.py, matcher.py, decorators.py, manager.py)
- Full backward compatibility: `from pytest_bdd.steps import given, when, then, step, StepDefinitionManager` works
- Nested class access preserved: `StepDefinitionManager.Registry`, `.Matcher`, `.Definition` resolve correctly
- `Step` and `StepFunc` re-exported for pickle_runner plugin compatibility
- ruff F401/F811/ERA001 passes clean
- 441 unit tests pass, 49 step-specific tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create steps/ package with sub-modules** - `cf7fb992` (refactor)
   - Created definition.py, registry.py, matcher.py, manager.py, __init__.py
   - Extracted Definition, Registry, Matcher classes
   - Original steps.py preserved

2. **Task 2: Move decorators, delete steps.py** - `7e50b4d1` (refactor)
   - Created decorators.py with given/when/then/step
   - Moved decorator_builder to manager.py
   - Deleted original steps.py (971L)

## Files Created/Modified

- `src/pytest_bdd/steps/__init__.py` - Re-exports all public API
- `src/pytest_bdd/steps/definition.py` - Definition attrs class, type aliases, helper functions
- `src/pytest_bdd/steps/registry.py` - Registry class with fixture injection
- `src/pytest_bdd/steps/matcher.py` - Matcher class with three-pass matching
- `src/pytest_bdd/steps/decorators.py` - given/when/then/step decorator functions
- `src/pytest_bdd/steps/manager.py` - StepDefinitionManager namespace class + decorator_builder
- `src/pytest_bdd/steps.py` - DELETED (was 971L)

## Decisions Made

- **Used namespace class for StepDefinitionManager** instead of keeping it as an attrs class — allows clean separation of sub-modules while preserving `StepDefinitionManager.Registry` etc. access pattern
- **Separated decorator_builder into manager.py** to avoid RUF067 lint violation (__init__ should only contain re-exports)
- **Matcher uses manual __init__** accepting `config` parameter — matches original attrs `@define` behavior where `config: Config = field()` was the first init arg

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **Matcher __init__ signature mismatch** — initial rewrite used no-arg `__init__` but original attrs class accepted `config` as first arg. Fixed by adding `config: Config` parameter to `__init__`.
- **Missing Step/StepFunc re-exports** — pickle_runner plugin imports `Step` and `StepFunc` from `pytest_bdd.steps`. Added to __init__.py re-exports.
- **RUF067 lint violation** — __init__.py cannot contain class definitions. Moved StepDefinitionManager to separate manager.py file.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- steps.py successfully split into 5 focused modules
- All public API preserved, no breaking changes
- Ready for next phase plan

---
*Phase: 11-audit-prune*
*Completed: 2026-05-16*

## Self-Check: PASSED

- steps.py deleted: confirmed
- steps/ package exists with 6 files: confirmed
- `from pytest_bdd.steps import given, when, then, step, StepDefinitionManager`: confirmed
- `StepDefinitionManager.Registry/Matcher/Definition` accessible: confirmed
- ruff F401/F811 passes: confirmed
- 441 unit tests pass: confirmed
- Commits cf7fb992, 7e50b4d1: confirmed
