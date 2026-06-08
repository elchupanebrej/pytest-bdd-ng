---
phase: 20-multiple-refactorings
plan: 28
status: done
commit: ed46f711
---

# Plan 20-28: Eliminate __all__, delete backward-compat shim, delete _ruff __init__.py

## Summary

Eliminated all `__all__` lists from `__init__.py` files by replacing with clean imports (no repeated as-aliases) and configuring mypy overrides with `implicit_reexport = true`. Deleted backward-compat shim and empty `_ruff` `__init__.py` files. Added INP001 suppressions for new namespace directories.

## What Was Done

### Task 1: Replace __all__ with as-imports (R6)

Converted 10 `__init__.py` files from `__all__` lists to clean imports and mypy overrides:

- `src/pytest_bdd/__init__.py` — TYPE_CHECKING block + as-aliases for lazy-loaded names
- `src/pytest_bdd/model/__init__.py` — ~60 symbols converted
- `src/pytest_bdd/model/run/__init__.py` — ~25 symbols converted
- `src/pytest_bdd/parsers/__init__.py` — ~10 symbols converted
- `src/pytest_bdd/scenario_locator/__init__.py` — ~7 symbols converted
- `src/pytest_bdd/steps/__init__.py` — ~15 symbols converted
- `src/pytest_bdd/types/__init__.py` — ~7 symbols converted
- `src/pytest_bdd/script/__init__.py` — 1 symbol converted
- `src/pytest_bdd/script/message_capability_governance/__init__.py` — ~15 symbols converted
- `src/pytest_bdd/compatibility/pytest/__init__.py` — ~25 symbols converted

### Task 2: Delete backward-compat shim and _ruff __init__.py (R5, R7, R8)

- Deleted `src/pytest_bdd_testing/cucumber_formatters.py` — backward-compat stub per R7
- Deleted `src/pytest_bdd/_ruff/__init__.py` — docstring-only, PEP 420 namespace
- Deleted `src/pytest_bdd/_ruff/rules/__init__.py` — docstring-only, PEP 420 namespace
- Added INP001 suppressions for `src/pytest_bdd/_ruff/**` and `src/pytest_bdd_testing/**`
- Removed INP001 from `src/pytest_bdd_testing/cases/*` (covered by `**` pattern)
- Removed `cucumber_formatters.py` per-file-ignore entry

### Task 2 (aborted): PEP 420 namespace __init__.py deletion

Attempted to delete 71 empty `__init__.py` files in `pytest_bdd_testing/` subdirectories. This caused `ImportPathMismatchError` because pytest's default import mode can't distinguish between modules with the same name in different directories without `__init__.py` files. All files were restored. PEP 420 namespace package deletion is deferred — requires `importmode = "importlib"` which causes other internal errors.

### Task 3: Final verification

- mypy --strict src/pytest_bdd/ — passes (zero new errors)
- ruff check src/ --select INP001 — passes (zero violations)
- Import smoke test — all public API imports work
- Unit test suite — 819 passed, 2 skipped, 1 xfailed

## Issues Encountered

1. **mypy `no_implicit_reexport` with third-party packages**: `from cucumber_messages import PickleStep as Step` wasn't recognized as explicit re-export. Fixed by importing `Step` directly from `cucumber_messages` in consumer file.

2. **Unused `type: ignore` after `__all__` removal**: `_static_helpers.py` had `# type: ignore[attr-defined]` for `_CucumberExpression` import that became valid after adding `as _CucumberExpression`. Removed the comment.

3. **pytest `ImportPathMismatchError`**: Deleting `__init__.py` files broke pytest's module resolution. All `pytest_bdd_testing/` `__init__.py` files restored.

4. **Test references to `__all__`**: Two test files referenced `pytest_bdd.__all__`. Updated to use `hasattr()` and hardcoded public API list.

## Verification

| Check | Result |
|-------|--------|
| mypy --strict src/pytest_bdd/ | Pass |
| ruff check src/ --select INP001 | Pass |
| pytest src/pytest_bdd_testing/cases/unit -m unit | 819 passed |
| `from pytest_bdd import given, when, then` | OK |
| `import pytest_bdd_testing` | OK |
| `__all__` in __init__.py | Zero |
