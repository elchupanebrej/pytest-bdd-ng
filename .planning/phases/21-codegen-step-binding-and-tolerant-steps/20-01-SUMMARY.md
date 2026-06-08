---
phase: 20-codegen-step-binding-and-tolerant-steps
plan: 1
subsystem: testing
tags: [pytest, codegen, ndjson, cli]

requires: []
provides:
  - spec codegen CLI flags for gather/bind/generate workflows
  - deterministic NDJSON event model for missing scenario bindings and missing step definitions
  - collection-backed gather-missing command path
affects: [code_generator, generation-tests, phase-19]

tech-stack:
  added: []
  patterns:
    - attrs event value objects serialized with sorted-key JSON
    - positional feature path capture isolated from pytest collection targets

key-files:
  created:
    - src/pytest_bdd/plugin/code_generator/events.py
    - tests/cases/integration/generation/test_gather_missing_steps.py
  modified:
    - src/pytest_bdd/plugin/code_generator/collection.py
    - src/pytest_bdd/plugin/code_generator/const.py
    - src/pytest_bdd/plugin/code_generator/entrypoint.py
    - src/pytest_bdd/plugin/code_generator/plugin.py
    - src/pytest_bdd/plugin/code_generator/request.py

key-decisions:
  - "Gather mode disables feature autoload during the wrapped session so unbound feature scenarios remain discoverable as missing bindings."
  - "Gather mode captures original positional feature paths before resetting pytest collection args to Python tests."

patterns-established:
  - "Code-generation events live in attrs value objects and serialize through a single to_ndjson helper."
  - "Machine-readable codegen modes suppress pytest terminal prose before wrapped-session output."

requirements-completed:
  - P20-CLI
  - P20-NDJSON

duration: 55min
completed: 2026-06-03
---

# Phase 20 Plan 1: Gather Missing Steps Summary

**Spec codegen gather CLI with deterministic NDJSON events backed by pytest collection and step matching**

## Performance

- **Duration:** 55 min
- **Started:** 2026-06-03T18:24:00Z
- **Completed:** 2026-06-03T19:19:21Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Replaced legacy registered codegen options with spec flags: `--gather-missing-steps`, `--bind-feature`, `--target-file`, `--generate-missing-steps`, and `--keep-generated-on-error`.
- Added attrs-backed missing scenario binding and missing step definition event models with sorted-key NDJSON serialization.
- Wired `--gather-missing-steps` through existing pytest collection and step matching helpers, with NDJSON-only command output and codegen exit status `100` when missing artifacts exist.
- Added integration coverage for legacy flag rejection, missing feature validation, missing scenario binding events, and missing step definition events.

## Task Commits

1. **Task 1 and Task 2: Add spec CLI flags, NDJSON event contract, and gather command wiring** - `c18cad5c` (feat)

**Plan metadata:** pending docs commit

## Files Created/Modified

- `src/pytest_bdd/plugin/code_generator/events.py` - attrs event objects and `to_ndjson` serializer.
- `src/pytest_bdd/plugin/code_generator/entrypoint.py` - spec option registration, with legacy option registration removed.
- `src/pytest_bdd/plugin/code_generator/plugin.py` - gather command orchestration, feature-path capture, terminal suppression, event building, and exit-code handling.
- `src/pytest_bdd/plugin/code_generator/request.py` - positional feature path parsing and validation.
- `src/pytest_bdd/plugin/code_generator/collection.py` - feature locator now reads captured codegen feature paths.
- `src/pytest_bdd/plugin/code_generator/const.py` - spec option destination constants.
- `tests/cases/integration/generation/test_gather_missing_steps.py` - integration tests for D-01 and D-02.

## Decisions Made

- Gather mode sets `feature_autoload` false while collecting Python tests so feature-file autoload does not incorrectly mark every scenario as bound.
- Gather mode resets pytest collection args to `.` after capturing feature paths, avoiding direct collection of feature paths while still collecting local Python test files.
- The NDJSON schema uses `type`, `feature`, `scenario`, `line`, `keyword`, and `text` fields, with path strings normalized through existing feature binding filenames.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Captured positional feature paths before pytest collection**
- **Found during:** Task 2 (Wire gather command)
- **Issue:** Passing a feature path positionally made pytest collect the feature file as a test target, which hid missing binding events.
- **Fix:** Captured original invocation feature paths into `config.option.codegen_feature_paths`, reset collection args to `.`, and disabled feature autoload in gather mode.
- **Files modified:** `src/pytest_bdd/plugin/code_generator/plugin.py`, `src/pytest_bdd/plugin/code_generator/request.py`
- **Verification:** `test_gather_missing_steps_emits_ndjson_events` reports both missing binding and missing step events.
- **Committed in:** `c18cad5c`

**2. [Rule 3 - Blocking] Preserved codegen exit code after wrapped pytest session**
- **Found during:** Task 2 (Wire gather command)
- **Issue:** `wrap_session` normalized the command result to `0` even when missing events were found.
- **Fix:** Stored `codegen_missing_events_found` on config and returned `100` from the outer command path.
- **Files modified:** `src/pytest_bdd/plugin/code_generator/plugin.py`
- **Verification:** `test_gather_missing_steps_emits_ndjson_events` asserts return code `100`.
- **Committed in:** `c18cad5c`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were required to satisfy the planned CLI and NDJSON contract. No scope expansion.

## Issues Encountered

- Local Python imported a different checkout by default; verification commands used `PYTHONPATH=.../src` to exercise this worktree.
- Pre-commit ruff hook required explicit `Returns` sections in new public helper docstrings; fixed before commit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 20-02 can consume `events.py` and the captured feature-path request model for target-file generation. Wave 1 can continue with Plan 20-03 runtime metadata and mock-run behavior.

## Self-Check: PASSED

- `rtk cmd /C "set PYTHONPATH=C:\Users\bulky\Projects\hive\.codex\worktrees\a22c\pytest-bdd\src&& python -m pytest tests/cases/integration/generation/test_gather_missing_steps.py tests/cases/integration/generation/test_generate_missing.py::test_process_single_item_tears_down_after_fixture_error -q"` -> 4 passed.
- Code commit `c18cad5c` exists for plan implementation.
- Key created files exist on disk.

---
*Phase: 20-codegen-step-binding-and-tolerant-steps*
*Completed: 2026-06-03*
