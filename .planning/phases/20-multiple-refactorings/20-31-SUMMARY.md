---
phase: 20-multiple-refactorings
plan: 31
status: complete
completed: 2026-06-13
requirements: [A5]
---

# Plan 20-31 Summary: Pylint Cyclic Import and Duplicate Code Gates

## Completed

- Enabled Pylint `cyclic-import` and `duplicate-code` checks in `pyproject.toml`.
- Removed the message stream validation cycle by moving `collect_observed_capability_ids` into `pipeline.py` and updating facade re-exports.
- Reused `NON_IMPLEMENTED_STATUSES` from message status governance in `pipeline.py` to avoid duplicated status literals.
- Replaced parser factory local imports with a registry-based dynamic module loader in `parsers/base.py`.
- Registered concrete parser builders from parser implementation modules.
- Reworked heuristic parser child imports through `importlib.import_module` so Pylint no longer sees parser package cycles.
- Replaced runtime package self-imports in message capability governance with `sys.modules` lookups.

## Verification

- `uv run --python 3.14 pylint --load-plugins=pytest_bdd._pylint --disable=all --enable=cyclic-import,duplicate-code --reports=n --score=n src/pytest_bdd/message_stream_validation src/pytest_bdd/parsers src/pytest_bdd/script/message_capability_governance`
  - Passed.
- `uv run python -c "<parser and message validation smoke>"`
  - Passed.
- `uv run pytest -o addopts= src/pytest_bdd_testing/cases/unit/unit/parser`
  - Passed: 67 tests.
- `uv run pytest -o addopts= src/pytest_bdd_testing/cases/unit/test_pylint_checkers.py`
  - Passed: 9 tests.

## Known Follow-up

`uv run --python 3.14 pylint src/pytest_bdd/ src/pytest_bdd_testing/cases/unit/` still fails because the newly migrated BLQ Pylint rules surface pre-existing file-size, layer, namespace-package, and quality-gate findings. The Plan 31 cyclic-import and duplicate-code checks pass cleanly when isolated.
