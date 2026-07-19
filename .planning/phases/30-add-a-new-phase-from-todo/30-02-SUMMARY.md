---
phase: 30
plan: 02
status: complete
completed: 2026-07-03
commit: b07f82d4
requirements:
  - P30-MODAPI-06
  - P30-MODAPI-07
  - P30-MODAPI-08
---

# Phase 30 Plan 02 Summary: BLQ Import-Form Migration

## Outcome

Plan 02 completed the Phase 30 gap identified after Plan 01: the BLQ import-form rules are no longer implemented-but-disabled. The codebase was migrated and `pyproject.toml` now enforces BLQ1506, BLQ1508, BLQ1509, BLQ1510, BLQ1511, and BLQ1512 globally.

Implementation commit: `b07f82d4 refactor(30-02): migrate BLQ import-form rules`.

## Work Completed

- Removed global disables for `forbidden-star-import`, `sibling-import-form`, `prefer-module-import`, `import-name-not-in-all`, `attribute-not-in-all`, and `same-hierarchy-import`.
- Replaced the remaining checked star import with explicit dynamic cucumber message aliases.
- Migrated same-package and sibling imports to the local/module import forms required by the BLQ rules.
- Restored facade `__init__.py` files to direct imports with meaningful `__all__` declarations.
- Refined checker behavior for nested relative imports, type-checking-only imports, and shadowed imported module names.
- Added checker regression tests for the refined BLQ1509/BLQ1512 behavior.

## Verification

- Initial inventory before migration: BLQ1506=1, BLQ1508=24, BLQ1509=52, BLQ1510=0, BLQ1511=68, BLQ1512=0.
- `ruff check src/pytest_bdd src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py pyproject.toml` - passed.
- `python -m compileall -q src/pytest_bdd` - passed.
- Public import smoke for affected public facades - passed.
- `pylint src/pytest_bdd/ --msg-template='{path}:{line}:{symbol}:{msg}' --reports=no` - passed, rated 10.00/10.
- `pytest src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py --basetemp=/tmp/pytest-bdd-ng-checkers` - 38 passed.
- `pre-commit run mypy --all-files` - passed.
- `pre-commit run --all-files` - passed.

## Notes

No broad rule disables or directory exclusions were added. Remaining local suppressions are limited to specific dynamic typing or private protocol cases with inline explanations.
