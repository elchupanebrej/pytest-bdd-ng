---
phase: 11-audit-prune
plan: "01"
subsystem: code-cleanup
tags: [dead-code, vulture, ruff, pruning]

# Dependency graph
requires:
  - phase: 10-pattern-unification
    provides: plugin structure verified, cross-plugin imports eliminated
provides:
  - runner.py dead module removed (validate_requested_pair unused)
  - feature_locator.py and temp_root.py retained (found active consumers)
affects: [11-02, 11-03, 11-04, 11-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [verify imports before deletion, not just static analysis]

key-files:
  created: []
  modified:
    - src/pytest_bdd/runner.py (DELETED)

key-decisions:
  - "Retained feature_locator.py — active consumer in code_generator/collection.py"
  - "Retained util/temp_root.py — active consumer in scenario_test_collector/entrypoint.py"
  - "Deleted runner.py — only truly dead module (zero imports)"

patterns-established:
  - "Static analysis (vulture) alone insufficient — must verify with runtime import check"

requirements-completed: [SIM-03]

# Metrics
duration: 15min
completed: 2026-05-16
---

# Phase 11 Plan 01: Audit Prune Summary

**Removed 1 dead module (runner.py); retained 2 falsely-flagged modules with active consumers**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-16T18:53:45Z
- **Completed:** 2026-05-16T22:15:24Z
- **Tasks:** 1 of 2 completed (Task 1 skipped — false positives)
- **Files modified:** 1 deleted (runner.py)

## Accomplishments

- Deleted runner.py (20L) — contained only unused validate_requested_pair function
- Verified feature_locator.py has active consumer (code_generator plugin)
- Verified temp_root.py has active consumer (scenario_test_collector plugin)
- ruff F401/F811/ERA001 passes clean
- Unit test suite passes (441 passed, 0 failures from changes)

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove confirmed dead modules** — SKIPPED (false positives)
   - feature_locator.py: retained — imported by `plugin/code_generator/collection.py`
   - util/temp_root.py: retained — imported by `plugin/scenario_test_collector/entrypoint.py`

2. **Task 2: Remove unused validate_requested_pair** - `bf1924c4` (chore)
   - Deleted runner.py entirely (only contained the unused function + its import)

## Files Created/Modified

- `src/pytest_bdd/runner.py` — DELETED (dead code, zero imports)

## Decisions Made

- **Retained feature_locator.py** despite plan claiming "zero imports" — found active import in `src/pytest_bdd/plugin/code_generator/collection.py` (line 10: `from pytest_bdd.feature_locator import FeatureLocatorArgs, ScenarioLocatorBuilder`)
- **Retained util/temp_root.py** despite plan claiming "zero imports" — found active import in `src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py` (line 12: `from pytest_bdd.util.temp_root import prefer_posix_temp_root`)
- **Deleted runner.py** — confirmed zero imports; entire file was single unused function wrapping `is_pair_compatible`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan incorrectly flagged feature_locator.py as dead code**
- **Found during:** Task 1
- **Issue:** Plan/RESEARCH.md claimed "zero imports in src or tests" but `plugin/code_generator/collection.py` imports `FeatureLocatorArgs` and `ScenarioLocatorBuilder`
- **Fix:** Restored feature_locator.py from git; excluded from deletion
- **Files modified:** src/pytest_bdd/feature_locator.py (restored)
- **Verification:** `uv run python -c "from pytest_bdd.feature_locator import FeatureLocatorArgs, ScenarioLocatorBuilder"` succeeds; test suite passes
- **Committed in:** N/A (restored before commit)

**2. [Rule 1 - Bug] Plan incorrectly flagged util/temp_root.py as dead code**
- **Found during:** Task 1
- **Issue:** Plan/RESEARCH.md claimed "zero imports" but `plugin/scenario_test_collector/entrypoint.py` imports and calls `prefer_posix_temp_root()`
- **Fix:** Restored temp_root.py from git; excluded from deletion
- **Files modified:** src/pytest_bdd/util/temp_root.py (restored)
- **Verification:** Import succeeds; test suite passes
- **Committed in:** N/A (restored before commit)

---

**Total deviations:** 2 auto-fixed (2 false-positive dead code flags in plan)
**Impact on plan:** Plan's vulture/import analysis missed 2 active consumers. Only runner.py was truly dead. Scope reduced from 3 deletions to 1.

## Issues Encountered

- `tests/feature/test_report.py::test_step_trace` — pre-existing failure (confirmed on original code)
- `tests/e2e/test_xdist_remote_message_aggregation.py::test_remote_xdist_run_aggregates_into_one_ndjson[ssh]` — pre-existing failure (confirmed on original code, Docker/SSH env issue)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- runner.py removal complete — no regressions introduced
- feature_locator.py and temp_root.py retained with confirmed consumers
- ruff gates pass clean
- Ready for next phase plan (11-02 or subsequent)

---
*Phase: 11-audit-prune*
*Completed: 2026-05-16*

## Self-Check: PASSED

- runner.py deleted: confirmed
- feature_locator.py retained: confirmed
- temp_root.py retained: confirmed
- SUMMARY.md exists: confirmed
- Commits bf1924c4, 25d8ffae: confirmed
