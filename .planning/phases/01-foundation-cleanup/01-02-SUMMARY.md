---
phase: 01-foundation-cleanup
plan: 02
subsystem: cleanup
tags: [cucumber-json, cli, legacy, entrypoint]
requires: []
provides:
  - Clean cucumber_json entrypoint without legacy --cucumberjson flag
  - Running pytest --cucumberjson produces standard "unrecognized arguments" error
affects: []

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - src/pytest_bdd/plugin/cucumber_json/entrypoint.py

key-decisions:
  - "Direct removal per D-10 — no deprecation, no transitional period"
  - "Removed unused `group` variable to satisfy ruff F841 (deviation from plan which said to keep it)"
  - "Added config.getini() fallback in pytest_configure because --cucumberjson was the only CLI flag setting cucumber_json_path"

patterns-established: []

requirements-completed:
  - STAB-04

duration: 15min
completed: 2026-05-12
---

# Phase 01 Plan 02: Remove Legacy --cucumberjson CLI Flag Summary

**Removed the deprecated `--cucumberjson` flag from cucumber_json entrypoint. Users now get standard pytest "unrecognized arguments" error; `--cucumber-json` continues working via cucumber_json_formatter.py.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-12
- **Completed:** 2026-05-12
- **Tasks:** 1
- **Files modified:** 2 (entrypoint.py + test file)

## Accomplishments
- Deleted `group.addoption(--cucumberjson)` call and TODO comment from `pytest_addoption()`
- `parser.addini(cucumber_json_path)` preserved — ini option still works
- `--cucumber-json` (defined in cucumber_json_formatter.py) unaffected
- Running `pytest --cucumberjson` produces `error: unrecognized arguments: --cucumberjson`

## Task Commits

1. **Task 1: Remove --cucumberjson addoption from entrypoint** - `6ae8abc6` (fix)
2. **Guard against missing cucumber_json_path option** - `53dacfee` (fix)
3. **Read cucumber_json_path from INI config + test updates** - `1936ae8f` (fix)

## Files Modified
- `src/pytest_bdd/plugin/cucumber_json/entrypoint.py` — removed 10 lines (TODO + addoption block), cleaned unused `group` variable, added `config.getini()` fallback
- `tests/feature/test_cucumber_json.py` — updated `runandparse()` to set `cucumber_json_path` via `pytest.ini` instead of removed `--cucumberjson` flag

## Decisions Made
- Direct removal without deprecation warnings (D-10 precedent)
- No transitional code or error hints

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Unused `group` variable violated ruff F841**
- **Found during:** Task 1 (commit pre-commit hook)
- **Issue:** Plan said to keep `group = parser.getgroup(...)` but without the `addoption()` call, `group` was unused
- **Fix:** Changed to `parser.getgroup("bdd", "Cucumber JSON")` — preserves help group registration without unused variable
- **Files modified:** src/pytest_bdd/plugin/cucumber_json/entrypoint.py
- **Verification:** Ruff pre-commit hook passed
- **Committed in:** 6ae8abc6

**2. [Rule 2 - Missing Critical] `pytest_configure` crashed after removal of `--cucumberjson` option**
- **Found during:** Post-merge test gate (plan incorrectly assumed no tests used legacy flag)
- **Issue:** Removing `group.addoption("--cucumberjson", dest="cucumber_json_path")` removed the only `config.option.cucumber_json_path` registration. `pytest_configure` accessed `config.option.cucumber_json_path` directly, causing `AttributeError`
- **Fix:** Changed to `getattr(config.option, ..., None)` + `config.getini(...)` fallback so old reporter works via INI config. Updated `pytest_configure` to read from both CLI option (getattr) and INI option (config.getini)
- **Files modified:** src/pytest_bdd/plugin/cucumber_json/entrypoint.py
- **Verification:** Debug confirmed `ini_val` properly resolves from INI file; old reporter produces cucumber.json
- **Committed in:** 53dacfee, 1936ae8f

**3. [Rule 1 - Bug] Test file `test_cucumber_json.py` used removed `--cucumberjson` flag**
- **Found during:** Task verification (plan incorrectly assumed "no tests test the legacy alias directly")
- **Issue:** Two test sites in `tests/feature/test_cucumber_json.py` passed `--cucumberjson` flag, now unrecognized
- **Fix:** `runandparse()` writes `cucumber_json_path` to `pytest.ini` instead (preserves same old-reporter output format). Second test (`test_cucumber_json_step_status_parity_with_canonical_messages`) creates fresh INI.
- **Files modified:** tests/feature/test_cucumber_json.py
- **Verification:** Reporter activates and produces cucumber.json; test assertions face pre-existing format mismatch (unrelated to this change)
- **Committed in:** 1936ae8f

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 missing critical)
**Impact on plan:** Medium — plan incorrectly assumed no test usage. Required INI-based fallback + test updates. Core goal achieved: `--cucumberjson` removed, plugin still functional via INI.

## Issues Encountered
- `tests/feature/test_cucumber_json.py::test_step_trace` has pre-existing AssertionError (IDs and keywords mismatch) — confirmed on pre-Phase-1 code. Not caused by this change.
- Plan had incorrect assumption: "no tests test the legacy alias directly" — 2 test sites used `--cucumberjson`

## Next Phase Readiness
- Phase 01 Foundation Cleanup complete
- Ready for Phase 02: Code Quality Gates

---
*Phase: 01-foundation-cleanup*
*Completed: 2026-05-12*
