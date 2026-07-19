---
phase: 30-add-a-new-phase-from-todo
subsystem: tooling
tags: [pylint, module-api, imports, __all__]
requires: []
provides:
  - Strict module API checker for BLQ1501-BLQ1513
  - Explicit __all__ declarations across pytest_bdd source modules
  - Enabled BLQ import-form policy across active pytest_bdd source
affects: [pylint, source-layout, import-style]
tech-stack:
  added: []
  patterns:
    - Pylint checker with static __all__ validation and cross-file import checks
    - Package __init__ APIs declared through direct imports and __all__
    - Local implementation privacy controlled by __all__, not leading-underscore module names
key-files:
  created:
    - src/pytest_bdd/_pylint/checkers/module_api_rules.py
    - .planning/phases/30-add-a-new-phase-from-todo/30-02-PLAN.md
    - .planning/phases/30-add-a-new-phase-from-todo/30-02-SUMMARY.md
  modified:
    - src/pytest_bdd/_pylint/__init__.py
    - pyproject.toml
    - src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py
    - src/pytest_bdd/
key-decisions:
  - "Renamed the custom BLQ1502 symbol to invalid-all-exports because invalid-all-format collides with Pylint E0605."
  - "Removed module-level __getattr__ facades after import-time validation showed no meaningful speedup."
  - "Renamed in-scope private implementation modules without leading underscores; API privacy is controlled through __all__."
  - "Migrated the codebase instead of keeping BLQ1506/1508/1509/1510/1511/1512 globally disabled."
patterns-established:
  - "Absolute sibling imports are checked using AST level None/0 compatibility and source package root matching."
  - "Conditional compatibility imports count as top-level names for __all__ validation."
  - "Type-checking-only local imports are exempt from runtime import-form policy after star/parent checks."
requirements-completed:
  - P30-MODAPI-01
  - P30-MODAPI-02
  - P30-MODAPI-03
  - P30-MODAPI-04
  - P30-MODAPI-05
  - P30-MODAPI-06
  - P30-MODAPI-07
  - P30-MODAPI-08
coverage:
  - id: D1
    description: "ModuleApiRulesChecker implements BLQ1501-BLQ1513 and is registered by the pytest_bdd Pylint plugin."
    requirement: P30-MODAPI-01
    verification:
      - kind: unit
        ref: "pytest src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py --basetemp=/tmp/pytest-bdd-ng-checkers"
        status: pass
      - kind: other
        ref: "pylint src/pytest_bdd/ --msg-template='{path}:{line}:{symbol}:{msg}' --reports=no"
        status: pass
    human_judgment: false
  - id: D2
    description: "Superseded init-rules references and BLQ140 IDs are removed from active source/config/test files."
    requirement: P30-MODAPI-02
    verification:
      - kind: other
        ref: "rg -n 'BLQ140[1-4]|init-code-required|empty-init|redundant-import-alias|all-defined' src pyproject.toml"
        status: pass
    human_judgment: false
  - id: D3
    description: "Checked source modules expose explicit APIs and no in-scope module-level __getattr__ remains."
    requirement: P30-MODAPI-03
    verification:
      - kind: other
        ref: "source export audit: 259 files checked, 0 missing non-init __all__, 0 bad non-root init __all__"
        status: pass
    human_judgment: false
  - id: D4
    description: "Existing package-level import compatibility remains available through direct package facade imports."
    requirement: P30-MODAPI-04
    verification:
      - kind: other
        ref: "public import smoke for pytest_bdd, scenario_locator, pickle_runner, lifecycle runtime, and struct BDD model"
        status: pass
    human_judgment: false
  - id: D5
    description: "Full custom Pylint checker unit file passes in a non-hidden temp directory."
    requirement: P30-MODAPI-05
    verification:
      - kind: unit
        ref: "pytest src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py --basetemp=/tmp/pytest-bdd-ng-checkers"
        status: pass
    human_judgment: false
  - id: D6
    description: "BLQ1506/1508/1509/1510/1511/1512 global disables were removed from pyproject.toml."
    requirement: P30-MODAPI-06
    verification:
      - kind: other
        ref: "pyproject.toml diff removes forbidden-star-import, sibling-import-form, prefer-module-import, import-name-not-in-all, attribute-not-in-all, same-hierarchy-import disables"
        status: pass
    human_judgment: false
  - id: D7
    description: "Active pytest_bdd source imports satisfy the enabled BLQ import-form rules."
    requirement: P30-MODAPI-07
    verification:
      - kind: other
        ref: "pylint src/pytest_bdd/ reports 10.00/10 with BLQ import-form rules enabled"
        status: pass
    human_judgment: false
  - id: D8
    description: "Full pre-commit passes with BLQ import-form rules enabled."
    requirement: P30-MODAPI-08
    verification:
      - kind: other
        ref: "pre-commit run --all-files"
        status: pass
    human_judgment: false
duration: 2 sessions
completed: 2026-07-03
status: complete
---

# Phase 30: Strict Module API & Import Rules Checker Summary

Phase 30 is complete. It introduced and enabled the BLQ15 module API checker family, made source module APIs explicit through `__all__`, removed module-level lazy facade machinery where it had no meaningful performance benefit, and migrated the active `src/pytest_bdd/` import surface so BLQ1506/1508/1509/1510/1511/1512 are enforced globally.

## Accomplishments

- Added `ModuleApiRulesChecker` with BLQ1501-BLQ1513 and registered it in the custom Pylint plugin.
- Removed active BLQ140/init-rules usage from source, tests, and config.
- Added explicit `__all__` declarations across the checked `src/pytest_bdd/` surface and made package facades static/direct.
- Removed package-level `__getattr__` machinery and stale wrapper modules after timing showed no large import-time speedup.
- Migrated star imports, same-package absolute imports, same-directory sibling imports, and local module attribute access to satisfy the enabled BLQ import-form rules.
- Removed the temporary global disables for `forbidden-star-import`, `sibling-import-form`, `prefer-module-import`, `import-name-not-in-all`, `attribute-not-in-all`, and `same-hierarchy-import`.

## Plan 02 Closure

Plan 02 was added after review identified that leaving BLQ1506/1508/1509/1510/1511/1512 disabled was not an acceptable Phase 30 endpoint. The implementation commit is `b07f82d4 refactor(30-02): migrate BLQ import-form rules`.

Initial violation inventory, with the rules enabled before migration:

- BLQ1506 `forbidden-star-import`: 1
- BLQ1508 `sibling-import-form`: 24
- BLQ1509 `prefer-module-import`: 52
- BLQ1510 `import-name-not-in-all`: 0
- BLQ1511 `attribute-not-in-all`: 68
- BLQ1512 `same-hierarchy-import`: 0

## Deviations

- BLQ1509 was refined to flag direct imports from actual sibling module files while allowing nested relative package imports.
- BLQ1511 now ignores type-checking-only local imports and shadowed module names when a non-import assignment owns the runtime name.
- BLQ1512 enforcement remains for disallowed `import pytest_bdd...` same-hierarchy imports; parent-relative `from ... import ...` forms remain aligned with Ruff TID252.
- The `pytest_bdd.scenario` module is loaded through `import_module()` in the few places where a direct package facade import would collide with the root `scenario` function export.

These changes were required to keep the rules precise enough to enable globally without adding broad suppressions.

## Verification

- `ruff check src/pytest_bdd src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py pyproject.toml` - passed.
- `python -m compileall -q src/pytest_bdd` - passed.
- Public import smoke for `pytest_bdd`, `scenario_locator`, pickle runner, lifecycle runtime, and struct BDD model - passed.
- `pylint src/pytest_bdd/ --msg-template='{path}:{line}:{symbol}:{msg}' --reports=no` - passed, rated 10.00/10.
- `pytest src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py --basetemp=/tmp/pytest-bdd-ng-checkers` - 38 passed.
- `pre-commit run mypy --all-files` - passed.
- `pre-commit run --all-files` - passed.

## User Setup Required

None.

---
*Phase: 30-add-a-new-phase-from-todo*
*Completed: 2026-07-03*
