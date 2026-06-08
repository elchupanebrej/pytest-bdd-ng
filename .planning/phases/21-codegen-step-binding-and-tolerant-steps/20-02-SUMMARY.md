---
phase: 20-codegen-step-binding-and-tolerant-steps
plan: 2
subsystem: code_generator
tags: [pytest, codegen, ast, rewrite, rollback]

requires:
  - 20-01
  - 20-03
provides:
  - idempotent --bind-feature target-file authoring
  - --generate-missing-steps skeleton authoring from gathered events
  - AST-aware existing scenarios and step decorator detection
  - transactional target-file formatting, syntax validation, rollback, and keep-on-error behavior
affects: [code_generator, generation-tests, phase-19]

tech-stack:
  added: []
  patterns:
    - stdlib ast detection for imports, scenarios calls, and step decorators
    - append-only target rewrites with ruff formatting and ast validation
    - target file ignored during wrapped pytest collection for generation commands

key-files:
  created:
    - src/pytest_bdd/plugin/code_generator/rewrite.py
    - tests/cases/integration/generation/test_bind_feature.py
    - tests/cases/integration/generation/test_generate_missing_steps.py
  modified:
    - src/pytest_bdd/plugin/code_generator/plugin.py
    - src/pytest_bdd/plugin/code_generator/rendering.py

key-decisions:
  - "Feature bindings are emitted as scenarios(relative_feature_path) and existing imported/qualified scenarios calls are detected by AST."
  - "Missing step skeletons always use def _() and @not_implemented, with duplicate function names intentionally accepted."
  - "Codegen target files are ignored during wrapped collection so invalid target syntax is handled by transactional validation."

patterns-established:
  - "Target rewrite helpers own read/propose/write/format/parse/rollback behavior."
  - "Generated skeleton rendering is snippet-level and does not reuse legacy full-module generation."

requirements-completed:
  - P20-BIND
  - P20-GENERATE
  - P20-ROLLBACK

duration: 52min
completed: 2026-06-03
---

# Phase 20 Plan 2: Target-File Code Generation Summary

**AST-aware bind-feature and missing-step skeleton authoring with transactional rollback**

## Performance

- **Duration:** 52 min
- **Started:** 2026-06-03T19:49:00Z
- **Completed:** 2026-06-03T20:41:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added `rewrite.py` for AST-aware pytest-bdd import, `scenarios(...)` binding, and step decorator detection.
- Wired `--bind-feature --target-file ...` to append formatted, idempotent feature bindings.
- Wired `--generate-missing-steps --target-file ...` to reuse gathered missing events and append inert step skeletons.
- Added skeleton rendering that imports public decorators, uses `@not_implemented`, defines `def _():`, and raises `NotImplementedError`.
- Added transactional target writes with `ruff format`, `ast.parse`, default rollback, and `--keep-generated-on-error` preservation.
- Fixed generated-code formatting to call `python -m ruff format`, avoiding unavailable private `ruff.find_ruff_bin`.

## Task Commits

1. **Task 1 and Task 2: Add target-file rewrite helpers, bind/generate wiring, and rollback tests** - `b937e364` (feat)

**Plan metadata:** pending docs commit

## Files Created/Modified

- `src/pytest_bdd/plugin/code_generator/rewrite.py` - AST detection, import insertion, append-only rewrites, and transactional writes.
- `src/pytest_bdd/plugin/code_generator/plugin.py` - bind/generate command dispatch and shared missing-event collection.
- `src/pytest_bdd/plugin/code_generator/rendering.py` - snippet rendering for missing-step skeletons and robust ruff invocation.
- `tests/cases/integration/generation/test_bind_feature.py` - binding, idempotency, AST detection, rollback, and keep tests.
- `tests/cases/integration/generation/test_generate_missing_steps.py` - skeleton generation, duplicate skipping, rollback, and keep tests.

## Decisions Made

- The target-file path is ignored during wrapped pytest collection for `--generate-missing-steps`, so invalid target syntax is validated by the rewrite transaction instead of failing pytest collection early.
- Existing invalid target files are treated as having no detectable imports/bindings/decorators; the proposed edit is still written and then validated, enabling both rollback and keep-generated-on-error behavior.
- `--generate-missing-steps` returns `100` when missing artifacts are found/generated, preserving the Plan 19 missing-artifact exit-code contract.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Avoided private ruff helper import**
- **Found during:** Focused test run
- **Issue:** The installed `ruff` package did not expose `find_ruff_bin`, and importing it at plugin load broke pytest startup.
- **Fix:** Switched formatting calls to `[sys.executable, "-m", "ruff", "format", ...]`.
- **Files modified:** `src/pytest_bdd/plugin/code_generator/rendering.py`, `src/pytest_bdd/plugin/code_generator/rewrite.py`
- **Verification:** Generation tests pass.
- **Committed in:** `b937e364`

**2. [Rule 3 - Blocking] Ignored target file during generation collection**
- **Found during:** Rollback tests
- **Issue:** An invalid `--target-file` named like a pytest module was collected before the rewrite transaction could validate or roll it back.
- **Fix:** Added target-file ignore entry during codegen wrapped collection.
- **Files modified:** `src/pytest_bdd/plugin/code_generator/plugin.py`
- **Verification:** Rollback and keep-generated-on-error tests pass.
- **Committed in:** `b937e364`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were required for D-07/D-08 and did not expand behavior beyond planned rollback semantics.

## Issues Encountered

- Pre-commit ruff moved type-only imports and required removing indirect exception docstrings; fixed before commit.
- Local Python imported a different checkout by default; verification commands used `PYTHONPATH=.../src` to exercise this worktree.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Wave 2 is complete. Plan 20-05 can now add end-to-end acceptance coverage across gather, bind, generate, mock-run, WIP, and tolerant behavior.

## Self-Check: PASSED

- `rtk cmd /C "set PYTHONPATH=C:\Users\bulky\Projects\hive\.codex\worktrees\a22c\pytest-bdd\src&& python -m pytest tests/cases/integration/generation/test_gather_missing_steps.py tests/cases/integration/generation/test_bind_feature.py tests/cases/integration/generation/test_generate_missing_steps.py -q"` -> 12 passed.
- Code commit `b937e364` exists for plan implementation.
- Key created files exist on disk.

---
*Phase: 20-codegen-step-binding-and-tolerant-steps*
*Completed: 2026-06-03*
