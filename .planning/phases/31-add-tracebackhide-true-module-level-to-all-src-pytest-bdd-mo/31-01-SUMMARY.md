---
phase: 31-add-tracebackhide-true-module-level-to-all-src-pytest-bdd-mo
plan: "01"
subsystem: testing
tags: [pytest, tracebackhide, integration-test]

requires: []
provides:
  - Integration test for pytest-bdd module-level traceback hiding
affects:
  - 31-02-PLAN.md
  - 31-03-PLAN.md

tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - src/pytest_bdd_toolchain/case/integration/test_tracebackhide.py
  modified: []

key-decisions:
  - "Use pytester/testdir to run a scenario that fails, verifying that internal frames are hidden by default and visible with --full-trace"

patterns-established: []

requirements-completed: []

coverage:
  - id: D31-01
    description: "Integration test for traceback hiding created"
    verification:
      - kind: integration
        ref: "src/pytest_bdd_toolchain/case/integration/test_tracebackhide.py"
        status: fail
    human_judgment: false

duration: 10min
completed: 2026-07-08
status: complete
---

# Plan 31-01: Scaffold the integration test for traceback hiding

**Create the integration test to verify module-level traceback hiding for pytest-bdd**

## Performance

- **Duration:** 10 min
- **Started:** 2026-07-08T05:14:46Z
- **Completed:** 2026-07-08T05:19:50Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created integration test at `src/pytest_bdd_toolchain/case/integration/test_tracebackhide.py` to check that traceback hiding is active under normal runs and disabled under `--full-trace` runs.

## Task Commits

1. **Task 1: Create the integration test for traceback hiding** - `pending` (test)

## Files Created/Modified
- `src/pytest_bdd_toolchain/case/integration/test_tracebackhide.py` - Created integration test.

## Decisions Made
- None - followed plan as specified.

## Deviations from Plan
- None - plan executed exactly as written.

## Issues Encountered
- None.

## Next Phase Readiness
- Test is ready. It currently fails as expected because the traceback hiding implementation is not yet done.

---
*Phase: 31-add-tracebackhide-true-module-level-to-all-src-pytest-bdd-mo*
*Completed: 2026-07-08*
