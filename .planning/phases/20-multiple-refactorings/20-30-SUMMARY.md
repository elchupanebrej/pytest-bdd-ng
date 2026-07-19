---
phase: 20-multiple-refactorings
plan: 30
status: complete
completed: 2026-06-13
requirements: [A5]
---

# Plan 20-30 Summary: Unified Pylint Checker Plugin

## Completed

- Added `pylint` and `astroid` development dependencies.
- Added Pylint configuration that loads `pytest_bdd._pylint`.
- Created `src/pytest_bdd/_pylint/` plugin entrypoint.
- Created checker adapters that expose existing BLQ rule implementations through Pylint messages:
  - BLQ9xx quality gates
  - BLQ10xx plugin pattern rules
  - BLQ11xx typing rules
  - BLQ12xx file size rules
  - BLQ13xx layer rules
  - BLQ14xx namespace package rules
  - BLQ15xx layout rules
  - BLQ16xx test import rules
- Added targeted unit tests for custom Pylint checker detection behavior.
- Updated `.pre-commit-config.yaml` and `Makefile` to route custom static rules through Pylint.

## Verification

- `uv run pytest src/pytest_bdd_testing/cases/unit/test_pylint_checkers.py`
  - Blocked by existing pytest addopts requiring `pytest-order` option in this environment.
- `uv run pytest -o addopts= src/pytest_bdd_testing/cases/unit/test_pylint_checkers.py`
  - Passed: 9 tests.
- `uv run pylint --version`
  - Passed: pylint 4.0.5, astroid 4.0.4.
- `make custom-rules`
  - Blocked by repository Makefile Windows shell guard when invoked from PowerShell.
- `uv run --python 3.14 pylint src/pytest_bdd/ src/pytest_bdd_testing/cases/unit/`
  - Plugin loaded and emitted BLQ diagnostics successfully.
  - Failed because migrated rules expose existing repository violations, including file-size, layer, namespace-package, and quality-gate findings.

## Known Follow-up

Plan 31 must narrow or resolve the remaining Pylint gate failures so `custom-rules` can pass cleanly with cyclic-import and duplicate-code enabled.
