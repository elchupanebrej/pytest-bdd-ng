---
phase: 20-codegen-step-binding-and-tolerant-steps
plan: 5
subsystem: atdd
tags: [pytest, bdd, e2e, docs, codegen]

requires:
  - 21-01
  - 21-02
  - 21-03
  - 21-04
provides:
  - executable ATDD coverage for Phase 21 codegen authoring loop
  - generated feature documentation for updated code generator behavior
  - focused final verification across generation, mock-run, WIP, tolerant, messages, and E2E slices
affects: [features, e2e-tests, docs, phase-19]

tech-stack:
  added: []
  patterns:
    - executable feature scenarios backed by deterministic pytester projects
    - NDJSON output parsed as JSON objects in E2E steps
    - generated docs refreshed from feature source

key-files:
  modified:
    - features/13 Code Generator/01 Code generation.feature.md
    - tests/cases/e2e/steps_code_generator.py
    - tests/cases/integration/generation/test_generate_missing.py
    - docs/features/13 Code Generator/01 Code generation.feature.rst

key-decisions:
  - "Executable docs use only spec flags; old --generate, --generate-missing, and --feature behavior is not preserved."
  - "E2E codegen assertions inspect parsed NDJSON and target-file bytes/content rather than loose stdout snippets."
  - "Legacy generation integration tests were aligned to --gather-missing-steps so the full generation directory verifies new behavior."

patterns-established:
  - "Code generator E2E steps create isolated pytester modules and assert concrete files/results."
  - "Feature docs are regenerated through bdd_tree_to_rst, not hand-edited."

requirements-completed:
  - P20-ATDD
  - P20-CLI
  - P20-NDJSON
  - P20-BIND
  - P20-GENERATE
  - P20-ROLLBACK
  - P20-MOCK
  - P20-WIP
  - P20-TOLERANT

duration: 44min
completed: 2026-06-03
---

# Phase 21 Plan 5: ATDD and Final Verification Summary

**Executable Code Generator feature docs and final focused verification**

## Performance

- **Duration:** 44 min
- **Started:** 2026-06-03T20:42:00Z
- **Completed:** 2026-06-03T21:26:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Replaced legacy Code Generator feature scenarios with concrete Phase 21 workflows.
- Added E2E step definitions for NDJSON gather, idempotent bind-feature, missing-step skeleton generation, mock-run, WIP, and tolerant ignored behavior.
- Regenerated `docs/features/13 Code Generator/01 Code generation.feature.rst` from the executable feature source.
- Updated stale generation integration tests to use `--gather-missing-steps` instead of removed legacy flags.
- Ran focused final verification across generation, runtime feature modes, tolerant message reporting, E2E, ruff, and source-audit grep.

## Task Commits

1. **Task 1 and Task 2: Add executable codegen authoring coverage and regenerated docs** - `d2113ae8` (test)

**Plan metadata:** pending docs commit

## Files Created/Modified

- `features/13 Code Generator/01 Code generation.feature.md` - new executable scenarios for the Phase 21 workflow.
- `tests/cases/e2e/steps_code_generator.py` - deterministic pytester-backed E2E steps.
- `tests/cases/integration/generation/test_generate_missing.py` - legacy tests aligned to the gather-missing contract.
- `docs/features/13 Code Generator/01 Code generation.feature.rst` - generated feature documentation.

## Decisions Made

- `--generate-missing` and `--feature` are treated as removed legacy flags; coverage now verifies the replacement spec flow.
- E2E tolerant coverage asserts user-visible continuation, while message-level failed-step evidence remains covered by `test_tolerant_step_reporting.py`.
- The docs generator was allowed to rewrite only the Code Generator RST file; `docs/features/features.rst` did not change.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Disabled feature autoload in E2E subprocess fixtures**
- **Found during:** E2E feature verification
- **Issue:** Temp `.feature` files were collected directly outside the Python module owning step definitions, causing missing-step failures.
- **Fix:** Added fixture-local pytest ini disabling feature autoload for mock-run, WIP, and tolerant subprocess projects where explicit `@scenario` bindings own execution.
- **Files modified:** `tests/cases/e2e/steps_code_generator.py`
- **Verification:** `test_feature_058_code_generator.py` passed.
- **Committed in:** `d2113ae8`

**2. [Rule 3 - Blocking] Updated stale legacy generation integration tests**
- **Found during:** Final focused verification
- **Issue:** `test_generate_missing.py` still invoked removed `--generate-missing --feature` flags.
- **Fix:** Rewrote those tests around `--gather-missing-steps`, parsed NDJSON, and corrected fixture bindings/parser coverage.
- **Files modified:** `tests/cases/integration/generation/test_generate_missing.py`
- **Verification:** Final focused verification passed.
- **Committed in:** `d2113ae8`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes kept D-01 intact and made the requested verification slice meaningful against the new spec behavior.

## Issues Encountered

- `bdd_tree_to_rst` exits nonzero when it rewrites docs; the expected "Documentation is generated and overwritten" signal occurred and produced the updated RST.
- Windows shell quoting made one source-audit regex command brittle; reran the audit as simpler `rg` checks for D-01, D-12, and implemented coverage keywords.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 21 implementation and focused verification are complete. Roadmap state can be marked complete for all five plans.

## Self-Check: PASSED

- `rtk cmd /C "set PYTHONPATH=C:\Users\bulky\Projects\hive\.codex\worktrees\a22c\pytest-bdd\src&& python -m pytest tests/cases/integration/generation tests/cases/integration/feature/test_mock_run.py tests/cases/integration/feature/test_wip_steps.py tests/cases/integration/feature/test_tolerant_steps.py tests/cases/integration/messages/test_tolerant_step_reporting.py tests/cases/e2e/e2e/test_feature_058_code_generator.py -q"` -> 39 passed, 3 skipped.
- `rtk cmd /C "set PYTHONPATH=C:\Users\bulky\Projects\hive\.codex\worktrees\a22c\pytest-bdd\src&& python -m ruff check src/pytest_bdd/plugin/code_generator src/pytest_bdd/plugin/pickle_runner src/pytest_bdd/steps tests/cases/integration/generation tests/cases/integration/feature/test_mock_run.py tests/cases/integration/feature/test_wip_steps.py tests/cases/integration/feature/test_tolerant_steps.py tests/cases/integration/messages/test_tolerant_step_reporting.py tests/cases/e2e/steps_code_generator.py"` -> All checks passed.
- Source-audit `rg` checks confirmed D-01/D-12 planning references and implementation coverage keywords across E2E/integration/message tests.
- Code/test/docs commit `d2113ae8` exists for plan implementation.

---
*Phase: 20-codegen-step-binding-and-tolerant-steps*
*Completed: 2026-06-03*
