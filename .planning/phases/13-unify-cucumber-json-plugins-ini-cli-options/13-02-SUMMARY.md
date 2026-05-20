---
phase: 13
plan: 13-02
subsystem: testing
tags:
  - cucumber-json
  - pytester
  - contract-tests
requires:
  - phase: 13-01
    provides: cucumber_json_dispatcher plugin package and pytest11 entry point
provides:
  - Dispatcher integration tests for INI-only, CLI-only, no-config, CLI-over-INI, xdist worker guard, and silent override behavior
  - Dispatcher contract tests for pyproject entry point, duplicated constants, required package files, and BLQ1002 cross-plugin import boundary
affects:
  - phase-13
  - cucumber-json-dispatcher
tech-stack:
  added: []
  patterns:
    - pytester subprocess-light integration tests
    - static contract checks over pyproject.toml and dispatcher source
key-files:
  created:
    - tests/cases/integration/cucumber_json/__init__.py
    - tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py
    - tests/cases/contract/contract/test_cucumber_json_dispatcher_contract.py
  modified: []
key-decisions:
  - "Use a local pytester node_modules stub for @cucumber/cucumber so CLI formatter tests do not depend on global npm state."
patterns-established:
  - "CLI formatter integration tests can provide local Node package stubs inside testdir tmpdir."
requirements-completed: []
metrics:
  duration: 23min
  completed: 2026-05-20
---

# Phase 13 Plan 02: Tests for cucumber_json_dispatcher Plugin Summary

**Dispatcher test coverage for INI/CLI cucumber JSON precedence, xdist no-op behavior, silent override, entry point registration, and BLQ1002 import isolation**

## Performance

- **Duration:** 23 min
- **Started:** 2026-05-20T05:53:50Z
- **Completed:** 2026-05-20T06:16:57Z
- **Tasks:** 7
- **Files modified:** 3

## Accomplishments

- Added 6 dispatcher integration tests under `tests/cases/integration/cucumber_json/`.
- Added 4 dispatcher contract tests under `tests/cases/contract/contract/`.
- Verified exact plan command passes with 10 green tests.

## Task Commits

1. **Tasks 13-02-T1 through 13-02-T7: dispatcher integration and contract tests** - `13886def` (test)

## Files Created/Modified

- `tests/cases/integration/cucumber_json/__init__.py` - Empty integration package marker.
- `tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py` - Six dispatcher integration tests covering INI/CLI activation, silence, precedence, xdist guard, and warning behavior.
- `tests/cases/contract/contract/test_cucumber_json_dispatcher_contract.py` - Four contract tests covering pyproject entry point, constants, required files, and cross-plugin import ban.

## Decisions Made

- Used a local pytester `node_modules` stub for `@cucumber/cucumber` and `@cucumber/cucumber-expressions` in CLI formatter tests. This verifies dispatcher CLI routing and output-path behavior without relying on global npm installs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added local Node formatter stub for CLI tests**
- **Found during:** Task 13-02-T2b and Task 13-02-T4
- **Issue:** The CLI formatter backend tried to auto-provision `@cucumber/cucumber`; global npm package availability is environment-dependent and produced no `cli_output.json`.
- **Fix:** Added a pytester-local `node_modules` stub that exposes the minimal formatter APIs needed by the bridge and writes deterministic JSON output.
- **Files modified:** `tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py`
- **Verification:** `uv run python -m pytest tests/cases/integration/cucumber_json/ tests/cases/contract/contract/test_cucumber_json_dispatcher_contract.py -v` passed with 10 tests.
- **Committed in:** `13886def`

---

**Total deviations:** 1 auto-fixed Rule 3 blocker.
**Impact on plan:** No scope change. Tests remain test-only and deterministic.

## Known Stubs

- `tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py:37` - Test fixture creates local stub `@cucumber/cucumber` and `@cucumber/cucumber-expressions` packages so CLI formatter tests do not require global npm package installation.
- `tests/cases/contract/contract/test_cucumber_json_dispatcher_contract.py:36` - Empty `violations` list is a contract-test accumulator, not product stub data.
- `tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py:194` - Empty warning list assertion verifies no warning was emitted.
- `tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py:195` - Empty string assertion verifies dispatcher zeroed INI cache when CLI wins.

## Threat Flags

None - tests only. No new runtime network endpoints, auth paths, file access trust boundaries, or schema changes.

## Issues Encountered

- Initial exact `uv run python -m pytest ...` failed before test execution because the local environment lacked the `test` extra that provides `pytest-order`. Running `uv run --extra test ...` synchronized test dependencies; the exact plan command then passed.

## User Setup Required

None - no external service configuration required.

## Verification

- `uv run python -m pytest tests/cases/integration/cucumber_json/ tests/cases/contract/contract/test_cucumber_json_dispatcher_contract.py -v` - 10 passed.
- `uv run --extra test ruff check tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py tests/cases/contract/contract/test_cucumber_json_dispatcher_contract.py` - passed.

## Self-Check: PASSED

- Created files exist.
- Commit `13886def` exists.
- No tracked files were deleted by the task commit.

## Next Phase Readiness

Plan 13-03 can proceed with documentation updates using tested dispatcher behavior as ground truth.

---
*Phase: 13-unify-cucumber-json-plugins-ini-cli-options*
*Completed: 2026-05-20*
