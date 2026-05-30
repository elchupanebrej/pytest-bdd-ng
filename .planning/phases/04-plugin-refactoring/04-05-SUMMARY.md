---
phase: 04-plugin-refactoring
plan: "05"
subsystem: plugin-refactoring
tags: [live-formatter, cucumber-formatters, runtime-split, refactor]
requires:
  - phase: 04-04
    provides: formatter plugin packages and plugin boundary contracts
provides:
  - live formatter process lifecycle module
  - live formatter node package resolution module
  - live formatter payload module
  - live formatter runner module
affects: [plugin-refactoring, cucumber-formatters, reporting]
tech-stack:
  added: []
  patterns:
    - mixin-based responsibility split for reporter runtime services
    - thin coordinator module preserving public service import path
key-files:
  created:
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_process.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_payload.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py
  modified:
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py
key-decisions:
  - "LiveFormatterService remains importable from live_formatter_runtime.py as a thin coordinator."
  - "Process, Node package, payload, and runner responsibilities are split into focused modules."
patterns-established:
  - "Large reporter service splits can keep public service imports stable while moving private implementation methods to responsibility modules."
requirements-completed: []
duration: 19 min
completed: 2026-05-14
---

# Phase 04 Plan 05: Live Formatter Runtime Split Summary

Live formatter runtime is now a thin coordinator backed by process, Node resolution, payload, and runner modules while preserving formatter output.

## Performance

- **Duration:** 19 min
- **Started:** 2026-05-14T06:04:00Z
- **Completed:** 2026-05-14T06:23:24Z
- **Tasks:** 4
- **Files modified:** 5

## Accomplishments

- Reduced `live_formatter_runtime.py` from 900 physical lines to 25.
- Added `live_formatter_process.py` for stream delivery, flush, wait/kill, thread joining, and failure recording behavior.
- Added `live_formatter_node.py` for Node/npm package discovery, installation, environment construction, and missing-package warnings.
- Added `live_formatter_payload.py` for formatter support-code payload construction.
- Added `live_formatter_runner.py` for runtime asset rendering, live formatter startup, requested formatter execution, and HTML report generation.

## Task Commits

1. **Tasks 1-4: Live formatter responsibility split and focused verification** - `f54d1f88` (refactor)

**Plan metadata:** this docs commit

## Files Created/Modified

- `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py` - thin coordinator defining `LiveFormatterService`.
- `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_process.py` - process lifecycle and live stream delivery.
- `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py` - Node package availability and environment handling.
- `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_payload.py` - formatter payload/support-code construction.
- `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py` - live/deferred formatter execution and HTML report orchestration.

## Decisions Made

- Used mixins to keep existing method names available on `LiveFormatterService` without re-exporting private helpers from old paths.
- Kept runtime behavior in the reporter plugin package because it is still plugin runtime behavior, not a stable model contract.

## Deviations from Plan

### Auto-fixed Issues

**1. [Execution Granularity] Combined tightly coupled split tasks into one commit**

- **Found during:** Tasks 1-4
- **Issue:** Process, Node, payload, and runner extraction share method calls on one service object; splitting commits would create transient broken imports.
- **Fix:** Performed the mechanical responsibility split in one atomic refactor commit.
- **Files modified:** live formatter runtime modules.
- **Verification:** formatter contracts and focused formatter suite passed.
- **Committed in:** `f54d1f88`

**2. [Rule 3 - Blocking] Plan-level large-file contract includes the next plan's target**

- **Found during:** Task 3 verification
- **Issue:** `tests/contract/test_large_file_contract.py` also checks `src/pytest_bdd/model/message_validation.py`, which is owned by 04-06 and remains 791 lines.
- **Fix:** Verified the 04-05 target directly (`live_formatter_runtime.py` is 25 lines) and carried the remaining large-file contract failure forward to 04-06.
- **Files modified:** none beyond the live formatter split.
- **Verification:** golden formatter parity passed; large-file contract fails only on `message_validation.py`.
- **Committed in:** `f54d1f88`

---

**Total deviations:** 2 auto-fixed / carried forward.
**Impact on plan:** 04-05 live formatter target is complete. Cross-plan large-file contract remains intentionally pending for 04-06.

## Issues Encountered

- The formatter e2e command with `-o addopts=''` removes the repository's `-p pytester` addopts, so `testdir` fixture is unavailable. The same focused suite passed with project addopts intact.
- `tests/contract/test_large_file_contract.py` still fails on `message_validation.py`; this is the explicit 04-06 target.

## Verification

- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -c "from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process import LiveFormatterProcess; print('process ok')"` - passed, printed `process ok`.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_standalone_rendering_boundary_contract.py -q` - 4 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_formatter_golden_parity.py tests/contract/test_large_file_contract.py -q` - golden parity passed; large-file contract failed only for `message_validation.py`.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_plugin_boundary_contract.py -q` - 1 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest tests/contract/test_formatter_golden_parity.py tests/compatibility/test_render_cucumber_formatters.py tests/e2e/test_cucumber_formatters.py -q` - 39 passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for 04-06. Live formatter runtime is below the large-file threshold; the remaining large-file failure is isolated to `message_validation.py`.

---
*Phase: 04-plugin-refactoring*
*Completed: 2026-05-14*
