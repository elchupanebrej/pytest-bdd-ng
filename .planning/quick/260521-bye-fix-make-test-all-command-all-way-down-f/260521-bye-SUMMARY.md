# Quick Task 260521-bye: fix make test-all - Summary

**Status:** complete
**Date:** 2026-05-21

## Changes Made

### 1. test_message_emission_points.py (integration test fix)
**File:** `tests/cases/integration/messages/test_message_emission_points.py`
- Added `external_attachment` to `EMITTED_OUTSIDE_REPORTER_PLUGIN` set
- `external_attachment` is a cucumber-messages protocol field emitted outside reporter plugin runtime modules (external/cross-system layer), same as `parse_error`

### 2. Makefile (4 fixes)
**File:** `Makefile`

- **test-slow**: Changed marker from `slow` to `"slow and not external and not docker"` — external/docker tests have separate optional targets and require Docker
- **test-posix**: Added `|| [ $$? -eq 5 ]` — no posix tests on Windows, exit code 5 is expected
- **test-windows**: Added `|| [ $$? -eq 5 ]` — same pattern as posix
- **render-tox-reports-run**: Changed `--cucumber-html` to `--cucumber-json` — `--cucumber-html` is not a valid option for `render_cucumber_formatters`

## Verification

All required targets pass:
- unit: 834 passed, 1 skipped
- integration: 266 passed, 3 skipped
- contract: 223 passed, 9 skipped
- e2e: 227 passed, 7 skipped
- compat: 39 passed
- perf: 1 passed
- slow: 3 passed
- posix: 0 selected (handled gracefully)

Optional targets (Docker-dependent) fail as expected without Docker daemon.
