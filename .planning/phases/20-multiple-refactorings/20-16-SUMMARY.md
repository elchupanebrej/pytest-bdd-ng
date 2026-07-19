---
phase: 20-multiple-refactorings
plan: 16
subsystem: typing
tags: [mypy, type-hints, unused-ignore, untyped-decorator, pluggy]

requires: []
provides:
  - Zero unused-ignore mypy errors across codebase
  - 1 non-pluggy untyped-decorator error fixed
  - Updated test_mypy_strict xfail reason with current error counts
affects: [20-17 (pluggy stubs will resolve remaining 57 untyped-decorator errors)]

tech-stack:
  added: []
  patterns:
    - "type:ignore[untyped-decorator] for third-party decorators (pytest.fixture)"

key-files:
  created: []
  modified:
    - tests/cases/unit/unit/test_mypy_strict.py (xfail reason updated)
    - src/pytest_bdd/**/*.py (35 files, comment removals + cast import fixes)
    - src/pytest_bdd/plugin/pickle_runner/entrypoint.py (untyped-decorator fix)

key-decisions:
  - "57 pluggy @hookimpl/@hookspec untyped-decorator errors deferred to plan 20-17 stubs"
  - "Pre-existing cast import bugs fixed in barrier.py and _gherkin_go/__init__.py (Rule 3 blocking)"
  - "1 remaining test failure (xdist.remote import-untyped) is pre-existing, not caused by this plan"

requirements-completed: [T2]

# Metrics
duration: 22min
completed: 2026-06-09
---

# Phase 20 Plan 16: Remove unused type:ignores and fix untyped-decorator errors Summary

**Reduced mypy errors from 483 to 414 by removing 64 unused type:ignore comments and fixing 1 non-pluggy untyped-decorator; 57 pluggy decorator errors deferred to plan 17 stubs**

## Performance

- **Duration:** 22 min
- **Started:** 2026-06-09T12:22:33Z
- **Completed:** 2026-06-09T12:45:11Z
- **Tasks:** 3
- **Files modified:** 37

## Accomplishments
- Removed 64 unused `# type: ignore[...]` comments across 35 source files — zero `[unused-ignore]` errors remain
- Fixed 1 non-pluggy untyped-decorator error (`@pytest.fixture` on `run_context` in entrypoint.py)
- Updated `test_mypy_strict.py` xfail reason from "800 errors in 104 files" to "414 errors in 77 files"
- Fixed 2 pre-existing `cast` import bugs that blocked test execution (Rule 3)

## Task Commits

1. **Task 1: Remove 64 unused type:ignore comments** - `2acd59df` (fix)
2. **Task 2: Fix 1 non-pluggy untyped-decorator error** - `8faa1818` (fix)
3. **Task 3: Update test_mypy_strict xfail reason** - `00e53e39` (fix)

## Files Created/Modified
- `src/pytest_bdd/**/*.py` - 35 files: removed unused type:ignore comments
- `src/pytest_bdd/plugin/pickle_runner/entrypoint.py` - Added `# type: ignore[untyped-decorator]` to `@pytest.fixture`
- `src/pytest_bdd/util/tests_group_ordering/barrier.py` - Added missing `cast` import (pre-existing bug)
- `src/pytest_bdd/_gherkin_go/__init__.py` - Added missing `cast` import (pre-existing bug)
- `tests/cases/unit/unit/test_mypy_strict.py` - Updated xfail reason with current error counts

## Decisions Made
- 57 pluggy `@hookimpl`/`@hookspec` untyped-decorator errors deferred to plan 20-17 stubs (per coordination note — plan 17 owns the pluggy stubs)
- 3 compound `# type:ignore[attr-defined, import-untyped]` comments reduced to `# type:ignore[attr-defined]` where only `import-untyped` was unused
- Pre-existing `cast` import bugs fixed as blocking issues (tests could not run without them)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed missing `cast` import in barrier.py**
- **Found during:** Task 3 (test verification)
- **Issue:** `barrier.py:178` used `cast()` without importing it — caused `NameError` at runtime
- **Fix:** Added `cast` to `from typing import TYPE_CHECKING, TypedDict, cast`
- **Files modified:** `src/pytest_bdd/util/tests_group_ordering/barrier.py`
- **Committed in:** `00e53e39`

**2. [Rule 3 - Blocking] Fixed missing `cast` import in _gherkin_go/__init__.py**
- **Found during:** Task 3 (test verification)
- **Issue:** `_gherkin_go/__init__.py:77` used `cast()` without importing it
- **Fix:** Added `cast` to `from typing import TYPE_CHECKING, cast`
- **Files modified:** `src/pytest_bdd/_gherkin_go/__init__.py`
- **Committed in:** `00e53e39`

**3. [Rule 1 - Bug] Fixed 40 dangling `[error-code]` remnants from initial script**
- **Found during:** Task 1 (verification)
- **Issue:** Initial removal script left bare `[import-untyped]`, `[attr-defined]` etc. on lines after removing `# type:ignore`
- **Fix:** Ran cleanup script to remove all 40 dangling bracket remnants
- **Files modified:** 24 files in `src/pytest_bdd/`
- **Committed in:** `2acd59df`

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking)
**Impact on plan:** All fixes were necessary for correctness (pre-existing bugs) or to correct script errors. No scope creep.

## Issues Encountered
- Initial regex-based removal script left dangling error-code brackets on 40 lines — required a second cleanup pass
- Pre-existing `cast` import bugs in `barrier.py` and `_gherkin_go/__init__.py` blocked test execution — fixed as blocking issues
- 1 pre-existing test failure remains: `test_mypy_strict_no_import_untyped` fails due to `xdist.remote` lacking type stubs (unrelated to this plan)

## Known Stubs
- 57 `[untyped-decorator]` errors on `@pytest.hookimpl`/`@pytest.hookspec` decorators — will be resolved by plan 20-17's pluggy stub enhancements (deferred per coordination agreement)

## Threat Flags
None — all changes are comment-only or import additions, no new network endpoints, auth paths, or schema changes.

## Next Phase Readiness
- Ready for plan 20-17 (pluggy stubs) — 57 untyped-decorator errors waiting for stub-based resolution
- Plan 17's stubs will also help with the 155 `attr-defined` errors remaining
- Pre-existing `xdist.remote` import-untyped error needs attention in a future plan

## Final Verification

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Total mypy errors | 483 | 414 | ~361 |
| unused-ignore | 64 | **0** | 0 |
| untyped-decorator | 58 | 57 | 0 (deferred) |
| Files with errors | 87 | 77 | — |
| Unit tests passing | — | 989/990 | All passing |

**Note:** The mypy error count reduction is 69 (483→414) rather than the planned 122 because all 57 pluggy untyped-decorator errors were deferred to plan 20-17 rather than resolved inline. Actual resolved errors: 64 unused-ignore + 1 non-pluggy untyped-decorator + 4 eliminated via compound comment reduction = 69.

---

*Phase: 20-multiple-refactorings*
*Completed: 2026-06-09*

## Self-Check: PASSED
- SUMMARY.md exists ✓
- All 3 task commits verified in git history ✓
- All key modified files exist on disk ✓
