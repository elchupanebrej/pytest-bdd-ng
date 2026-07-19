---
phase: 02-code-quality-gates
fixed_at: 2026-05-19T00:00:00Z
review_path: .planning/phases/02-code-quality-gates/02-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-05-19T00:00:00Z
**Source review:** .planning/phases/02-code-quality-gates/02-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (all Warning-level)
- Fixed: 5
- Skipped: 0

## Fixed Issues

### WR-01: Event loop not closed on exception in _fetch_feature_responses

**Files modified:** `src/pytest_bdd/scenario_locator.py`
**Commit:** f6e15053
**Applied fix:** Wrapped `run_until_complete()` and `sleep()` in try/finally block so `loop.close()` is guaranteed to run even if `fetch_all()` raises an exception.

### WR-02: Duplicate docstring on arguments property

**Files modified:** `src/pytest_bdd/parsers.py`
**Commit:** abfa4f87
**Applied fix:** Removed duplicate `"""Initialize the cucumber regular expression."""` docstring on `cucumber_regular_expression.arguments` property. Replaced with `"""Get argument names from the compiled regular expression."""`.

### WR-03: Potential KeyError on missing worker_id in transport payloads

**Files modified:** `src/pytest_bdd/model/message_transport.py`
**Commit:** 15e7dcf3
**Applied fix:** Changed both `WorkerChunkBatch.from_dict` (line 125) and `WorkerCompletionManifest.from_dict` (line 176) to use `payload.get("worker_id")` with an explicit `ValueError` when the key is missing. Docstrings updated to document the raised exception. Extracted error messages to variables to satisfy ruff EM101/TRY003 rules.

### WR-04: rmdir in finally block can mask original exceptions

**Files modified:** `src/pytest_bdd/util/tests_group_ordering.py`
**Commit:** 96c43830
**Applied fix:** Wrapped `lock_path.rmdir()` in `contextlib.suppress(FileNotFoundError)` inside the `_barrier_lock` finally block. Added `suppress` to the `contextlib` import. This prevents `FileNotFoundError` from masking exceptions raised in the `yield` body.

### WR-05: Module-level mutable state for test name generation

**Files modified:** `src/pytest_bdd/scenario.py`
**Commit:** 9e57924e
**Applied fix:** Removed module-level `test_names = get_python_name_generator("")` and replaced its single usage at line 462 with `test.__name__ = next(get_python_name_generator(""))`. Each `scenarios()` call with `return_test_decorator=False` now creates a fresh generator, making name assignment deterministic regardless of import order. **Requires human verification** — this is a logic change to how test names are generated across multiple modules.

## Skipped Issues

None — all in-scope findings were fixed.

---

_Fixed: 2026-05-19T00:00:00Z_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 1_
