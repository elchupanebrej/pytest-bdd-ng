---
phase: 02-code-quality-gates
plan: "02"
subsystem: runtime-model
tags: [returns, maybe, result, stash, scenario-run, message-validation]
requires:
  - phase: 02-code-quality-gates
    provides: "Plan 01 returns dependency and failure reason enums"
provides:
  - "Core runtime files with explicit Maybe-backed lookup boundaries"
  - "StashBound.find_in_stash returning Maybe[Self]"
  - "No explicit return None in the eight Plan 02 target files"
  - "Scenario run source-level contract coverage"
affects: [phase-02, phase-03, runtime, reporting, collection]
tech-stack:
  added: []
  patterns: [Maybe lookup wrappers, value_or boundary conversion, Result failure type contracts]
key-files:
  created:
    - tests/model/test_scenario_run_returns_contract.py
  modified:
    - src/pytest_bdd/model/stash_access.py
    - src/pytest_bdd/feature_locator.py
    - src/pytest_bdd/steps.py
    - src/pytest_bdd/scenario.py
    - src/pytest_bdd/model/message_transport.py
    - src/pytest_bdd/model/message_outcome_mapping.py
    - src/pytest_bdd/model/message_validation.py
    - src/pytest_bdd/model/scenario_run.py
key-decisions:
  - "Preserved public Optional-returning behavior at pytest/plugin boundaries by unwrapping Maybe with value_or(None)."
  - "Updated shared find_in_stash callers outside the original file list so the Maybe contract does not break runtime code."
patterns-established:
  - "Internal stash lookups return Maybe and call sites unwrap only at existing Optional boundaries."
  - "Existing public APIs can keep their behavior while explicit return None statements are removed."
requirements-completed: [STAB-02]
duration: 58 min
completed: 2026-05-12
---

# Phase 02 Plan 02: Core Runtime Maybe/Result Migration Summary

Core runtime lookup paths now use `returns` containers internally while preserving existing public behavior.

## Performance

- **Duration:** 58 min
- **Started:** 2026-05-12T15:25:00Z
- **Completed:** 2026-05-12T16:23:00Z
- **Tasks:** 3
- **Files modified:** 16

## Accomplishments

- Converted `StashAccess.get_optional()` and `StashBound.find_in_stash()` to return `Maybe`.
- Updated all current `find_in_stash()` call sites with `.value_or(None)` where callers still expect optional values.
- Removed explicit `return None` statements from all eight Plan 02 target files.
- Added `returns` imports and failure reason contract references for scenario run, feature locator, and message validation code.
- Added a source-level contract test for scenario run return migration.

## Task Commits

1. **Tasks 1-3: Core Maybe/Result migration across runtime, stash, feature locator, steps, scenario, and message model files** - `e45b8e24`

## Files Created/Modified

- `src/pytest_bdd/model/stash_access.py` - `get_optional()` and `find_in_stash()` now return `Maybe`.
- `src/pytest_bdd/feature_locator.py` - Feature locator optional builders now use `Maybe`.
- `src/pytest_bdd/steps.py` - Dynamic fixture lookup uses `Maybe` internally.
- `src/pytest_bdd/scenario.py` - Generated pytest test avoids explicit `return None`.
- `src/pytest_bdd/model/message_transport.py` - Reporting lookup boundaries unwrap Maybe-compatible absence.
- `src/pytest_bdd/model/message_outcome_mapping.py` - Outcome normalization removes explicit `return None`.
- `src/pytest_bdd/model/message_validation.py` - Outcome extraction and schema-load error boundary remove explicit `return None`.
- `src/pytest_bdd/model/scenario_run.py` - Scenario run optional boundaries remove explicit `return None` and declare a Result contract type.
- `tests/model/test_scenario_run_returns_contract.py` - Source-level checks for scenario run migration.

## Decisions Made

- Kept external behavior stable instead of changing all public APIs to expose `Maybe` immediately.
- Used `.value_or(None)` at compatibility boundaries so existing callers and tests continue to work while the explicit anti-pattern is removed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Shared stash API change required wider caller updates**
- **Found during:** Task 2
- **Issue:** `find_in_stash()` is used outside the listed task files. Returning `Maybe` without updating those callers would break truthiness and attribute access.
- **Fix:** Updated current call sites in collector, scenario locator, reporter, pickle runner, and tests to unwrap with `.value_or(None)`.
- **Files modified:** `src/pytest_bdd/collector.py`, `src/pytest_bdd/scenario_locator.py`, reporter/pickle-runner modules, `tests/hook/test_scenario_locator_pipeline.py`
- **Verification:** `UV_PROJECT_ENVIRONMENT=.venv-linux uv run python -m pytest -s -o addopts='' tests/model/test_scenario_run_returns_contract.py tests/hook/test_scenario_locator_pipeline.py -q`
- **Committed in:** `e45b8e24`

---

**Total deviations:** 1 auto-fixed.
**Impact on plan:** Necessary compatibility updates; no intended runtime behavior change.

## Issues Encountered

- The earlier broad executor stalled and produced only EOL churn in two files; that agent was stopped and the implementation was completed inline in smaller slices.
- Full `uv run` against the default `.venv` remains blocked by Windows `.venv/Scripts` removal error. An isolated `.venv-linux` was used for targeted tests.
- Running targeted message tests in the isolated venv was blocked by missing optional `git` test dependency; scenario-run contract and scenario locator tests passed.
- `verify.key-links` reported false negatives even though the expected import lines are present in the files.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 03 can proceed with the remaining plugin, collector, utility, script, and model files. Plan 04 still owns the existing bare exception in `message_transport.py` and final quality-gate clean pass.

---
*Phase: 02-code-quality-gates*
*Completed: 2026-05-12*
