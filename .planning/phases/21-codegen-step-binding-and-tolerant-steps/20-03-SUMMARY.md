---
phase: 20-codegen-step-binding-and-tolerant-steps
plan: 3
subsystem: runtime
tags: [pytest, bdd, mock-run, wip, steps]

requires: []
provides:
  - public not_implemented decorator with order-independent Definition metadata
  - mock-run mode that validates bindings without scenario or step lifecycle execution
  - WIP status policy using pytest marker, Gherkin tag, CLI, default priority
affects: [pickle_runner, steps, phase-19]

tech-stack:
  added: []
  patterns:
    - central status resolver for WIP policy priority
    - function-level pending metadata propagated into Definition objects

key-files:
  created:
    - src/pytest_bdd/plugin/pickle_runner/status_policy.py
    - tests/cases/unit/unit/test_step_policy_decorators.py
    - tests/cases/integration/feature/test_mock_run.py
    - tests/cases/integration/feature/test_wip_steps.py
  modified:
    - src/pytest_bdd/steps/definition.py
    - src/pytest_bdd/steps/manager.py
    - src/pytest_bdd/steps/decorators.py
    - src/pytest_bdd/steps/__init__.py
    - src/pytest_bdd/__init__.py
    - src/pytest_bdd/plugin/pickle_runner/const.py
    - src/pytest_bdd/plugin/pickle_runner/entrypoint.py
    - src/pytest_bdd/plugin/pickle_runner/plugin.py

key-decisions:
  - "Mock-run validates matched step definitions before pytest_bdd_before_scenario, so hook and body execution stay skipped."
  - "WIP tag priority is implemented through collected pytest marks named wip-status-*."

patterns-established:
  - "Step policy decorators update both function-level metadata and already-created Definition objects."
  - "Runtime status policy helpers return a value and source, keeping priority behavior testable."

requirements-completed:
  - P20-MOCK
  - P20-WIP

duration: 17min
completed: 2026-06-03
---

# Phase 20 Plan 3: Mock Run and WIP Steps Summary

**Mock-run binding validation plus public not_implemented step metadata and WIP status priority**

## Performance

- **Duration:** 17 min
- **Started:** 2026-06-03T19:20:00Z
- **Completed:** 2026-06-03T19:36:47Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- Added public `not_implemented` decorator exported from `pytest_bdd` and `pytest_bdd.steps`.
- Added `Definition.not_implemented` metadata and propagation for both decorator orders.
- Added `--mock-run`, branching before scenario hooks and step lifecycle execution while still validating step bindings.
- Added `--wip-status` and a central resolver for pytest marker > Gherkin tag > CLI > default priority.
- Added focused unit and integration coverage for decorator order, mock-run lifecycle suppression, missing-step failure, WIP pass/skip/fail, and priority ordering.

## Task Commits

1. **Task 1 and Task 2: Add not_implemented metadata, mock-run, and WIP priority** - `2d42eaf6` (feat)

**Plan metadata:** pending docs commit

## Files Created/Modified

- `src/pytest_bdd/plugin/pickle_runner/status_policy.py` - WIP status normalization and priority resolution.
- `src/pytest_bdd/plugin/pickle_runner/entrypoint.py` - `--mock-run`, `--wip-status`, and WIP marker registration.
- `src/pytest_bdd/plugin/pickle_runner/plugin.py` - early mock-run branch and not-implemented step handling.
- `src/pytest_bdd/steps/definition.py` - `Definition.not_implemented` field.
- `src/pytest_bdd/steps/manager.py` - pending function metadata propagation into definitions.
- `src/pytest_bdd/steps/decorators.py` - public `not_implemented` decorator.
- `src/pytest_bdd/steps/__init__.py` and `src/pytest_bdd/__init__.py` - public exports.
- `tests/cases/unit/unit/test_step_policy_decorators.py` - decorator metadata tests.
- `tests/cases/integration/feature/test_mock_run.py` - mock-run lifecycle tests.
- `tests/cases/integration/feature/test_wip_steps.py` - WIP runtime priority tests.

## Decisions Made

- Mock-run performs matcher validation directly from the active scenario run, then returns before `pytest_bdd_before_scenario`.
- WIP `passed` returns from step body handling before `pytest_bdd_before_step`, so not-implemented bodies and step hooks are not executed for synthetic pass behavior.
- WIP `skipped` uses `pytest.skip`, preserving pytest-native skip reporting.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Registered WIP marks and tag-derived marker names**
- **Found during:** Task 2 (WIP status priority tests)
- **Issue:** Strict warning handling turned unknown `wip_status` and `wip-status-*` marks into collection errors.
- **Fix:** Registered the marker and allowed tag-derived marker names for all WIP statuses.
- **Files modified:** `src/pytest_bdd/plugin/pickle_runner/entrypoint.py`
- **Verification:** `test_pytest_marker_wins_over_cli` and `test_gherkin_tag_wins_over_cli` pass.
- **Committed in:** `2d42eaf6`

**2. [Rule 3 - Blocking] Adjusted mock-run missing-step assertion to collection gate behavior**
- **Found during:** Task 2 (mock-run tests)
- **Issue:** Existing zero-match collection validation fails before runtime mock-run when no step definitions exist.
- **Fix:** Kept the existing fail-fast collection behavior and asserted nonzero failure with the existing diagnostic.
- **Files modified:** `tests/cases/integration/feature/test_mock_run.py`
- **Verification:** `test_mock_run_still_fails_missing_step_definitions` passes.
- **Committed in:** `2d42eaf6`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Behavior still satisfies D-09 and D-12. Existing collection validation remains intact.

## Issues Encountered

- Pre-commit required type-only `Item` import, dynamic attribute casting for `StepFunc`, and explicit raised-exception docs for mock-run binding verification; fixed before commit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 20-04 can build tolerant step behavior on top of the new status policy pattern and `Definition` metadata propagation approach.

## Self-Check: PASSED

- `rtk cmd /C "set PYTHONPATH=C:\Users\bulky\Projects\hive\.codex\worktrees\a22c\pytest-bdd\src&& python -m pytest tests/cases/unit/unit/test_step_policy_decorators.py tests/cases/integration/feature/test_mock_run.py tests/cases/integration/feature/test_wip_steps.py -q"` -> 11 passed.
- Code commit `2d42eaf6` exists for plan implementation.
- Key created files exist on disk.

---
*Phase: 20-codegen-step-binding-and-tolerant-steps*
*Completed: 2026-06-03*
