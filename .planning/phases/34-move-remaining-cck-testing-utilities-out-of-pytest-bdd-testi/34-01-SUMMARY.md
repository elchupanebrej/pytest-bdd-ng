---
phase: 34-move-remaining-cck-testing-utilities-out-of-pytest-bdd-testi
plan: "01"
subsystem: testing
tags: [pytest, cck, refactoring]

requires:
  - phase: 33-gather-failed-ci-logs-into-workflow-artifact
    provides: "CI logging integration"
provides:
  - "CCK utility module migrated to pytest_bdd_toolchain"
  - "Direct construction error of UnboundFeatureItem resolved using from_parent"
affects: [pytest_bdd_toolchain, cck]

tech-stack:
  added: []
  patterns: [import CCK from toolchain packages instead of library package]

key-files:
  created:
    - src/pytest_bdd_toolchain/case/contract/cck/cck.py
  modified:
    - src/pytest_bdd/plugin/scenario_test_collector/unbound.py
    - src/pytest_bdd_toolchain/case/contract/cck/conftest.py
    - src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_conversion.py
    - src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_rendering.py
    - src/pytest_bdd_toolchain/step/steps_cck_allure.py

key-decisions:
  - "Migrated cck.py testing utilities from public pytest_bdd package to local-only toolchain package to prevent public API contamination."
  - "Switched UnboundFeatureItem to from_parent construction to align with pytest 9.x API contracts."

patterns-established:
  - "Import CCK test fixtures/utilities locally within the toolchain instead of exporting via pytest_bdd.testing."

requirements-completed: []

coverage:
  - id: D1
    description: "Move cck.py to pytest_bdd_toolchain and update consumer imports"
    verification:
      - kind: integration
        ref: "src/pytest_bdd_toolchain/case/contract/cck/#all cck allure tests"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fix UnboundFeatureItem instantiation under pytest 9.x"
    verification:
      - kind: unit
        ref: "src/pytest_bdd_toolchain/case/unit/test_unbound_features.py#TestUnboundFeatureItem"
        status: pass
    human_judgment: false

duration: 26min
completed: 2026-07-12
status: complete
---

# Phase 34: Move remaining CCK testing utilities out of pytest_bdd/testing Summary

**Migrated cck.py Cucumber Compatibility Kit utilities to the local toolchain package and resolved UnboundFeatureItem direct instantiation crash under pytest 9.x**

## Performance

- **Duration:** 26 min
- **Started:** 2026-07-12T14:35:00Z
- **Completed:** 2026-07-12T15:01:00Z
- **Tasks:** 5 completed
- **Files modified:** 6

## Accomplishments
- Moved `cck.py` from `src/pytest_bdd/testing/cck.py` to `src/pytest_bdd_toolchain/case/contract/cck/cck.py` to prevent library code contamination.
- Updated all 4 toolchain consumer modules to import `cck.py` locally.
- Fully removed the now-empty `src/pytest_bdd/testing/` package directory.
- Resolved `UnboundFeatureItem` direct instantiation collection crash by migrating to `from_parent` as mandated by pytest 9.x.

## Task Commits

Each task was committed atomically:

1. **Task: Fix UnboundFeatureItem direct instantiation crash** - `6c5e8fb7` (fix)
2. **Task: Migrate CCK testing utilities to toolchain** - `99479953` (feat)

## Files Created/Modified
- `src/pytest_bdd_toolchain/case/contract/cck/cck.py` - Migrated CCK helper utilities
- `src/pytest_bdd_toolchain/case/contract/cck/conftest.py` - Updated imports
- `src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_conversion.py` - Updated imports
- `src/pytest_bdd_toolchain/case/contract/cck/test_cck_allure_rendering.py` - Updated imports
- `src/pytest_bdd_toolchain/step/steps_cck_allure.py` - Updated imports
- `src/pytest_bdd/plugin/scenario_test_collector/unbound.py` - Switched to from_parent construction

## Decisions Made
- Migrated `cck.py` testing utilities from public `pytest_bdd` package to local-only toolchain package to prevent public API contamination.
- Switched `UnboundFeatureItem` to `from_parent` construction to align with pytest 9.x API contracts.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CCK testing utilities are fully local to the toolchain.
- Pytest 9.x collection issue is resolved.
- Ready to proceed to next planned phases.

---
*Phase: 34-move-remaining-cck-testing-utilities-out-of-pytest-bdd-testi*
*Completed: 2026-07-12*

## Self-Check: PASSED
