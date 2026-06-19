---
phase: 20-codegen-step-binding-and-tolerant-steps
plan: 4
subsystem: runtime
tags: [pytest, bdd, tolerant, reporting, steps]

requires:
  - 21-03
provides:
  - public tolerant decorator with order-independent Definition metadata
  - tolerant status policy using pytest marker, Gherkin tag, CLI, default priority
  - runner behavior that can ignore tolerant failures at scenario outcome level
  - message coverage proving ignored tolerant failures still report failed step results
affects: [pickle_runner, steps, messages, phase-19]

tech-stack:
  added: []
  patterns:
    - central status resolver extended for tolerant policy priority
    - function-level tolerant metadata propagated into Definition objects
    - failure hook emission kept before scenario-level suppression

key-files:
  created:
    - tests/cases/integration/feature/test_tolerant_steps.py
    - tests/cases/integration/messages/test_tolerant_step_reporting.py
  modified:
    - src/pytest_bdd/steps/definition.py
    - src/pytest_bdd/steps/manager.py
    - src/pytest_bdd/steps/decorators.py
    - src/pytest_bdd/steps/__init__.py
    - src/pytest_bdd/__init__.py
    - src/pytest_bdd/plugin/pickle_runner/const.py
    - src/pytest_bdd/plugin/pickle_runner/status_policy.py
    - src/pytest_bdd/plugin/pickle_runner/entrypoint.py
    - src/pytest_bdd/plugin/pickle_runner/plugin.py
    - tests/cases/unit/unit/test_step_policy_decorators.py

key-decisions:
  - "Tolerant failures always set the step run to failed and invoke pytest_bdd_step_error before optional suppression."
  - "Ignored tolerant failures reset active run/scenario status to ok and continue dispatching later steps."
  - "Tolerant tag priority is implemented through collected pytest marks named tolerant-status-*."

patterns-established:
  - "Step policy decorators update both function-level metadata and already-created Definition objects."
  - "Runtime policy helpers return a value and source for marker > tag > CLI > default priority."

requirements-completed:
  - P20-TOLERANT

duration: 30min
completed: 2026-06-03
---

# Phase 21 Plan 4: Tolerant Steps Summary

**Public tolerant step decorator with reporting-preserving ignored failure behavior**

## Performance

- **Duration:** 30 min
- **Started:** 2026-06-03T19:37:00Z
- **Completed:** 2026-06-03T19:48:47Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments

- Added public `tolerant` decorator exported from `pytest_bdd` and `pytest_bdd.steps`.
- Added `Definition.tolerant` metadata and propagation for both decorator orders.
- Added `--tolerant-status` with `failed` and `ignored` values, defaulting to `failed`.
- Extended status policy resolution for pytest marker > Gherkin tag > CLI > default priority.
- Updated runner failure handling so ignored tolerant failures keep failed step evidence while allowing scenario continuation.
- Added unit, feature integration, and message integration coverage for tolerant behavior and reporting.

## Task Commits

1. **Task 1 and Task 2: Add tolerant metadata, policy resolution, runner behavior, and reporting tests** - `ca3a616b` (feat)

**Plan metadata:** pending docs commit

## Files Created/Modified

- `src/pytest_bdd/plugin/pickle_runner/status_policy.py` - tolerant status normalization and priority resolution.
- `src/pytest_bdd/plugin/pickle_runner/entrypoint.py` - `--tolerant-status` and tolerant marker registration.
- `src/pytest_bdd/plugin/pickle_runner/plugin.py` - tolerant failure suppression after failed step hook/report emission.
- `src/pytest_bdd/steps/definition.py` - `Definition.tolerant` field.
- `src/pytest_bdd/steps/manager.py` - tolerant function metadata propagation into definitions.
- `src/pytest_bdd/steps/decorators.py` - public `tolerant` decorator.
- `src/pytest_bdd/steps/__init__.py` and `src/pytest_bdd/__init__.py` - public exports.
- `tests/cases/unit/unit/test_step_policy_decorators.py` - tolerant decorator metadata and export tests.
- `tests/cases/integration/feature/test_tolerant_steps.py` - tolerant default fail, ignored pass, and priority tests.
- `tests/cases/integration/messages/test_tolerant_step_reporting.py` - NDJSON message assertion for failed step result with passing scenario outcome.

## Decisions Made

- Ignored tolerant failures do not bypass `pytest_bdd_step_error`; this preserves reporter-visible failed step results per D-11.
- Default tolerant status remains strict failure, so adding `@tolerant` alone does not change outcomes without an explicit policy.
- Gherkin tags reuse pytest marker collection and normalize underscores to hyphens, matching the WIP policy pattern.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Avoided mypy policy type collision**
- **Found during:** Pre-commit
- **Issue:** Reusing the local name `policy` for both WIP and tolerant policy objects caused mypy to infer an incompatible assignment.
- **Fix:** Renamed the tolerant local to `tolerant_policy`.
- **Files modified:** `src/pytest_bdd/plugin/pickle_runner/plugin.py`
- **Verification:** Focused tests pass and pre-commit commit hook passed.
- **Committed in:** `ca3a616b`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** No scope change. The fix preserves planned behavior and satisfies type checking.

## Issues Encountered

- Pre-commit ruff hooks reformatted one message assertion and updated staged files before the final successful commit.
- Local Python imported a different checkout by default; verification commands used `PYTHONPATH=.../src` to exercise this worktree.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 21-02 can proceed in Wave 2 independently. Plan 21-05 can later combine gather/bind/generate, mock-run, WIP, and tolerant behavior in end-to-end acceptance coverage.

## Self-Check: PASSED

- `rtk cmd /C "set PYTHONPATH=C:\Users\bulky\Projects\hive\.codex\worktrees\a22c\pytest-bdd\src&& python -m pytest tests/cases/unit/unit/test_step_policy_decorators.py tests/cases/integration/feature/test_tolerant_steps.py tests/cases/integration/messages/test_tolerant_step_reporting.py -q"` -> 13 passed.
- Code commit `ca3a616b` exists for plan implementation.
- Key created files exist on disk.

---
*Phase: 20-codegen-step-binding-and-tolerant-steps*
*Completed: 2026-06-03*
