---
phase: 14-gap-closure
plan: 01
subsystem: testing
tags: [coverage, bdd, triage, pytest]
requires: []
provides:
  - "Coverage gap report for Phase 14 test allocation"
  - "BDD collection triage report for Phase 14 failure resolution"
affects: [14-gap-closure, TEST-01, TEST-02]
tech-stack:
  added: []
  patterns: ["Analysis-only plan artifacts generated from pytest-cov JSON and E2E collection output"]
key-files:
  created:
    - ".planning/phases/14-gap-closure/coverage-gap-report.md"
    - ".planning/phases/14-gap-closure/bdd-triage-report.md"
  modified: []
key-decisions:
  - "Use Makefile-equivalent uv extras for test commands because runtime-only uv sync lacks pytest-order."
  - "Treat current BDD result as collection infrastructure blocker: 61 feature bindings skip as NOTSET before scenario execution."
patterns-established:
  - "Coverage triage maps coverage.py missing lines and branches to AST function spans."
  - "BDD triage must first prove scenario collection yields pickles before categorizing StepNotFound or AssertionError failures."
requirements-completed: [TEST-01, TEST-02]
duration: 35min
completed: 2026-05-20
---

# Phase 14 Plan 01: Analysis Sweep Summary

**Coverage and BDD triage reports that expose current test allocation targets and the E2E collection blocker**

## Performance

- **Duration:** 35 min
- **Started:** 2026-05-20T10:48:00Z
- **Completed:** 2026-05-20T11:23:31Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `coverage-gap-report.md` from `coverage.json`, including aggregate coverage, non-exempt modules below 70%, top uncovered functions/branches, and prioritized test targets.
- Created `bdd-triage-report.md` from an all-scenarios temporary loader run.
- Identified that the historical 27 BDD failures are currently masked: the E2E loader resolves 61 feature bindings as empty parameter sets before any scenario body executes.

## Task Commits

1. **Task 1: Run coverage gap scan and produce report** - `723b68b5` (docs)
2. **Task 2: Run BDD failure triage and produce categorized report** - `723b68b5` (docs)

**Plan metadata:** this summary commit.

## Files Created/Modified

- `.planning/phases/14-gap-closure/coverage-gap-report.md` - Per-module coverage table and prioritized test-writing hit-list.
- `.planning/phases/14-gap-closure/bdd-triage-report.md` - Current BDD collection result and next fix strategy.

## Decisions Made

- Used `uv run --extra test --extra testtypes --extra doc-gen --extra struct-bdd` because plain `uv run` rebuilt `.venv` without `pytest-order`, causing `--order-scope=session` to be unrecognized.
- Reported the actual BDD triage result instead of forcing the stale expected 27-failure shape. Current result is `61 skipped, 3 passed`, with skips caused by empty scenario parameter sets.

## Deviations from Plan

### Auto-fixed Issues

None.

---

**Total deviations:** 0 auto-fixed.
**Impact on plan:** Reports were produced. BDD failure categorization is blocked until collection yields concrete pickles.

## Issues Encountered

- Coverage command produced usable JSON but exited non-zero: total coverage is 37.83%, below 70%, and baseline run has 21 failures.
- BDD all-scenarios run did not surface StepNotFound/AssertionError categories because all 61 feature bindings skipped with `got empty parameter set for (gherkin_document, pickle, feature_source)`.

## User Setup Required

None.

## Next Phase Readiness

Ready for 14-02 coverage augmentation using `coverage-gap-report.md`.

14-03 should start by fixing E2E scenario collection/binding, then rerun all-scenarios triage to expose the real failure categories.

---
*Phase: 14-gap-closure*
*Completed: 2026-05-20*
