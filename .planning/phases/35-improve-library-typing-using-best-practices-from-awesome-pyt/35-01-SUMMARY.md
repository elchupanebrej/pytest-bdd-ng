---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: "01"
subsystem: typing
tags: [mypy, pyright, stubs, allure]
requires:
  - phase: 34
    provides: completed preceding refactoring phase
provides:
  - strict no-bypass mypy baseline evidence
  - Python 3.10/all-platform Pyright discovery configuration
  - local Allure dependency-boundary stubs
affects: [35-02-PLAN.md, 35-139-PLAN.md, 35-140-PLAN.md]
tech-stack:
  added: [pyright]
  patterns: [narrow third-party stubs, immutable typing baseline]
key-files:
  created:
    - pyright.strict.json
    - stubs/allure_commons/__init__.pyi
    - stubs/allure_commons/lifecycle.pyi
    - stubs/allure_commons/logger.pyi
    - stubs/allure_commons/model2.pyi
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-BASELINE.md
  modified: [pyproject.toml]
key-decisions:
  - "Keep strict mypy no-bypass and record its nonzero baseline for later source slices."
  - "Use upstream Pyright strict configuration as discovery evidence, not a source gate."
requirements-completed: []
coverage: []
completed: 2026-07-13
status: complete
---

# Phase 35 Plan 01: Typing Foundation Summary

**Strict mypy baseline evidence, Python-3.10/all-platform Pyright discovery configuration, and narrow Allure typing boundary stubs are ready for source remediation.**

## Performance

- **Tasks:** 3 completed
- **Files modified:** 8

## Accomplishments

- Removed mypy source exclusions and module-wide `ignore_errors`, while preserving the 2,709-error expanded baseline as evidence rather than a bypass.
- Added upstream Pyright to the `testtypes` extra and a strict discovery configuration for both source packages.
- Added concrete local stubs for the Allure lifecycle, logger, plugin manager, and model symbols used by the formatter.

## Task Commits

1. **Task 1: Remove broad mypy bypasses and record the expanded baseline** — `74e8d80d`
2. **Task 2: Add an executable upstream-Pyright strict discovery configuration** — `c351abf3`
3. **Task 3: Add exact Allure dependency-boundary stubs** — `5940c345`

## Verification

- Passed: `uv sync --all-extras`.
- Passed: Python assertions confirming no mypy `exclude` or `ignore_errors` override and that `pyright` is in `testtypes`.
- Passed: Python assertions confirming the strict Pyright configuration targets Python 3.10 and platform `All`.
- Passed: stub-boundary file and no-`Any` assertions.
- Passed: normal pre-commit hooks for all task commits; the Task 3 first attempt autoformatted the stubs and the restaged retry passed.
- Environment issue: the literal `uv run --all-extras pyright --project pyright.strict.json --version` could not spawn because the local Pyright installation had package metadata but no console launcher or Python wrapper files. Reinstalling the plan-declared package did not repair that pre-existing WSL virtualenv state. The checked-in configuration remains valid; rerun this command in a repaired environment before Plan 139 discovery.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Completed lifecycle and model attributes in the Allure boundary stubs**

- **Found during:** Task 3
- **Issue:** The initial stub boundary did not model lifecycle methods and model attributes referenced by the formatter message adapter.
- **Fix:** Added concrete schedule/update lifecycle methods and used result/step model attributes without `Any` or suppressions.
- **Files modified:** `stubs/allure_commons/lifecycle.pyi`, `stubs/allure_commons/model2.pyi`
- **Verification:** Stub-boundary file and no-`Any` assertions; normal pre-commit hooks.
- **Committed in:** `5940c345`

**Total deviations:** 1 auto-fixed (Rule 3). **Impact:** Necessary boundary completeness only; no source remediation was pulled into this plan.

## Issues Encountered

- The linked worktree’s common Git metadata lies outside the sandbox root, so normal commits required scoped permission to create its index lock. Hooks were never bypassed.
- Local Pyright launcher files were absent despite installed metadata; this is recorded above as an environment issue rather than hidden by a configuration bypass.

## Next Phase Readiness

Plans 02–137 can remediate isolated source slices against the recorded strict-mypy baseline. Plan 139 should rerun upstream Pyright discovery after repairing the local virtualenv launcher installation.

## Self-Check: PASSED
