---
phase: 30
plan: 01
type: feature
wave: 1
depends_on: []
files_modified:
  - src/pytest_bdd/_pylint/checkers/module_api_rules.py
  - src/pytest_bdd/_pylint/__init__.py
  - src/pytest_bdd/_pylint/checkers/init_rules.py
  - pyproject.toml
  - src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py
  - src/pytest_bdd/__init__.py
  - "~55-80+ source modules in src/pytest_bdd/"
autonomous: true
requirements:
  - P30-MODAPI-01
  - P30-MODAPI-02
  - P30-MODAPI-03
  - P30-MODAPI-04
  - P30-MODAPI-05
---

# Phase 30 Plan 01: Strict Module API & Import Rules Checker

## Objective
Implement 12 custom Pylint rules (BLQ1501-BLQ1512) as a single `ModuleApiRulesChecker` class that enforces strict module export discipline and import boundaries across `src/pytest_bdd/`. Remove the superseded `InitRulesChecker` (BLQ1401-BLQ1404), add `__all__` to all ~55-80+ source modules in one coordinated sweep, and ensure pre-commit passes after all fixes.

## Tasks

### Task 1: Write the ModuleApiRulesChecker (12 rules, BLQ1501-BLQ1512)
**Type:** feature
**Files:** src/pytest_bdd/_pylint/checkers/module_api_rules.py
**read_first:**
  - src/pytest_bdd/_pylint/checkers/init_rules.py
  - src/pytest_bdd/_pylint/checkers/import_rules.py (for cross-file patterns)
  - src/pytest_bdd/_pylint/checkers/test_import_rules.py (for test patterns)
  - .planning/phases/30-add-a-new-phase-from-todo/30-RESEARCH.md (§Rule Analysis)
**Action:** Create `src/pytest_bdd/_pylint/checkers/module_api_rules.py` with a single `ModuleApiRulesChecker(BaseChecker)` class implementing all 12 rules. Follow the exact BaseChecker, msgs dict (E9101-E9112 message IDs), and visit_*/leave_* pattern from init_rules.py. Include a module docstring with Responsibility, Delegates, Cohesion, and Separation sections per project convention. Each rule message must use the symbolic name format `BLQ1501: ...`. Rules BLQ1510/BLQ1511 require cross-file AST analysis via astroid file loading — implement with error handling and caching to avoid circular imports. Include a filepath guard that skips case/, cases/, script/, _gherkin_go/, _pylint/ paths and pytest_bdd_toolchain/. The _pylint/ exclusion prevents the checker from self-reporting BLQ1501 violations against itself and other checker modules.

**12 Rules to implement:**
  - BLQ1501: Every non-`__init__.py` module must define top-level `__all__`
  - BLQ1502: `__all__` must be a static list or tuple of unique string names
  - BLQ1503: Every name in `__all__` must exist in the defining module
  - BLQ1504: Every `__init__.py` must define exactly `__all__ = []`
  - BLQ1505: `__init__.py` must not re-export names from submodules
  - BLQ1506: Star imports (`from x import *`) are forbidden
  - BLQ1507: Parent-relative imports using `..` are forbidden
  - BLQ1508: Sibling modules must be imported with explicit one-dot relative imports
  - BLQ1509: Prefer `from . import module` over `from .module import name`
  - BLQ1510: Imported names from local modules must exist in source module's `__all__`
  - BLQ1511: Attribute access through imported local modules must target `__all__` names
  - BLQ1512: Same-hierarchy modules must use sibling/local import form, not absolute

**acceptance_criteria:**
  - File exists at src/pytest_bdd/_pylint/checkers/module_api_rules.py
  - Module docstring has Responsibility, Delegates, Cohesion, Separation sections
  - All 12 message definitions use BLQ1501-BLQ1512 symbolic names with descriptive text
- Filepath guard excludes case/, cases/, script/, _gherkin_go/, _pylint/, pytest_bdd_toolchain/
- Follows existing checker pattern (BaseChecker subclass, msgs dict, visit_* methods)
- Docstring or code comment documents why each rule is needed despite built-in Pylint/Ruff equivalents (per RESEARCH.md §Overlap Analysis and CONTEXT.md D-25)

### Task 2: Update Pylint plugin registration
**Type:** refactor
**Files:** src/pytest_bdd/_pylint/__init__.py
**read_first:** src/pytest_bdd/_pylint/__init__.py
**Action:** In `src/pytest_bdd/_pylint/__init__.py`, import `ModuleApiRulesChecker` from the new module and call `linter.register_checker(ModuleApiRulesChecker(linter))`. Remove the `InitRulesChecker` import and its `register_checker()` call.
**acceptance_criteria:**
  - ModuleApiRulesChecker is imported and registered
  - InitRulesChecker import and registration are removed
  - Total checker count remains at 10

### Task 3: Delete superseded InitRulesChecker
**Type:** cleanup
**Files:** src/pytest_bdd/_pylint/checkers/init_rules.py
**read_first:** src/pytest_bdd/_pylint/checkers/init_rules.py
**Action:** Delete `src/pytest_bdd/_pylint/checkers/init_rules.py` entirely.
**acceptance_criteria:**
  - File no longer exists
  - No imports reference init_rules.py anywhere in the codebase

### Task 4: Update pyproject.toml Pylint configuration
**Type:** config
**Files:** pyproject.toml
**read_first:** pyproject.toml (focus on [tool.pylint] sections)
**Action:** In `pyproject.toml`, remove references to BLQ1401-BLQ1404 (init_rules checker messages) from the pylint enable list or per-file ignore sections. Add the 12 new BLQ1501-BLQ1512 message codes to the enable list. Ensure the ignore-paths pattern for case/ covers the new checker's scope exclusions.
**acceptance_criteria:**
  - BLQ1401-BLQ1404 no longer appear in pyproject.toml
  - BLQ1501-BLQ1512 appear in the pylint enable list
  - pre-commit pylint runs with ModuleApiRulesChecker active

### Task 5: Add __all__ to all non-__init__.py source modules
**Depends on:** Task 1 (checker must exist to validate), Task 4 (pylint config must enable BLQ15xx rules)
**Type:** feature
**Files:** ~55-80+ source modules under src/pytest_bdd/ (excluding case/, cases/, script/, _gherkin_go/)
**read_first:**
  - src/pytest_bdd/checkers/pickle_runner/plugin.py (only existing __all__ example — note: correct path is src/pytest_bdd/plugin/pickle_runner/plugin.py)
  - .planning/phases/30-add-a-new-phase-from-todo/30-RESEARCH.md (§Module Inventory)
**Action:** Add `__all__ = [...]` to every non-`__init__.py` module under `src/pytest_bdd/` that currently lacks one. Each `__all__` must list all public names (functions, classes, constants) exported by the module. Use a static list or tuple of unique string names. Write an automated script first to generate initial `__all__` lists by extracting top-level def/class names, then manually curate for accuracy.
**acceptance_criteria:**
  - Every non-__init__.py module under src/pytest_bdd/ (excl. exclusions) has __all__
  - All __all__ entries are valid (names exist in module)
  - No duplicate entries in any __all__
  - Root src/pytest_bdd/__init__.py has __all__ = [] (no re-exports)

### Task 6: Fix root __init__.py conflict with BLQ1504
**Type:** refactor
**Files:** src/pytest_bdd/__init__.py
**read_first:** src/pytest_bdd/__init__.py
**Action:** Resolve the conflict between BLQ1504 (all __init__.py must have __all__ = []) and the root __init__.py which serves as the public API facade. Based on RESEARCH.md recommendations, exempt the root __init__.py from BLQ1504 by adding a filepath guard in the checker, OR restructure the root __init__.py to use only `from . import X` re-exports with BLQ1504 satisfied by __all__ = [] if feasible. Document the decision in the checker docstring.
**acceptance_criteria:**
  - Decision is documented in module_api_rules.py docstring
  - No checker violation on root __init__.py after resolution
  - Public API remains importable from pytest_bdd

### Task 7: Write comprehensive unit tests for ModuleApiRulesChecker
**Type:** test
**Files:** src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py
**read_first:**
  - src/pytest_bdd_toolchain/case/unit/ (list existing test files, read test patterns)
  - .planning/phases/30-add-a-new-phase-from-todo/30-RESEARCH.md (§Test Patterns)
**Action:** Add comprehensive tests for all 12 BLQ1501-BLQ1512 rules to the existing test suite. For each rule, provide both passing and failing examples using Pylint's testutils. Delete any existing `test_init_checker_*` functions that test the removed InitRulesChecker. Follow the project's test style (pyhamcrest assertions, module-level test functions). Include tests for the filepath guard exclusions.
**acceptance_criteria:**
  - At least one passing and one failing test case per rule (24+ test functions)
  - Filepath guard exclusion tests for case/, script/, _gherkin_go/ paths
  - All InitRulesChecker tests removed
  - Tests pass: pytest src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py
  - Test style follows project conventions (pyhamcrest assertions)

### Task 8: Run pre-commit and fix all violations
**Type:** verify
**Files:** all modified files
**read_first:** .pre-commit-config.yaml
**Action:** Run `pre-commit run --all-files` and fix any violations reported by the new checker. Ensure pylint with ModuleApiRulesChecker reports zero BLQ15xx errors. Fix any other pre-commit violations introduced by the massive __all__ additions.
**acceptance_criteria:**
  - pre-commit run --all-files exits 0 (BLQ15xx rules pass)
  - No BLQ1501-BLQ1512 violations in src/pytest_bdd/ (excl. exclusions)
  - Existing pre-commit hooks still pass (ruff, mypy, etc.)

### Task 9: Run full test suite
**Type:** verify
**Files:** all
**read_first:** .planning/DEVELOPMENT.rst
**Action:** Run the full test suite to ensure no regressions from the massive module changes. Verify pytest passes, ruff passes, mypy passes, and all custom lint rules pass.
**acceptance_criteria:**
  - Full pytest suite passes with zero new failures
  - ruff check exits 0
  - mypy --strict src/ exits 0
  - All pre-commit hooks pass

## Verification

1. `pre-commit run --all-files` — BLQ15xx rules active, zero violations
2. `pytest src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py` — all 12 rule tests pass
3. `pytest` — full test suite, zero regressions
4. `ruff check` — no new lint violations
5. `mypy --strict src/` — no type errors
6. Verify init_rules.py has been removed
7. Verify ~55-80+ modules now have __all__
8. Verify root __init__.py public API still works

## must_haves

### truths
- File src/pytest_bdd/_pylint/checkers/module_api_rules.py exists with a ModuleApiRulesChecker class
- ModuleApiRulesChecker is registered in src/pytest_bdd/_pylint/__init__.py
- InitRulesChecker is completely removed (file deleted, import removed, registration removed, tests removed)
- All 12 BLQ1501-BLQ1512 message definitions exist with symbolic names and remediation text
- Every non-__init__.py module under src/pytest_bdd/ (excluding case/, cases/, script/, _gherkin_go/, _pylint/, pytest_bdd_toolchain/) defines __all__
- Every __init__.py under src/pytest_bdd/ (excluding root __init__.py per documented decision) has __all__ = []
- All __all__ entries reference names that actually exist in their defining modules
- No star imports exist in src/pytest_bdd/
- No parent-relative imports (..) exist in src/pytest_bdd/
- Sibling imports use explicit one-dot relative form (from . import module or from .module import name)
- Cross-file validation rules (BLQ1510, BLQ1511) handle missing/invalid modules gracefully
- pyproject.toml pylint config references BLQ15xx, not BLQ14xx
- Test suite has passing AND failing examples for all 12 rules
- pre-commit run --all-files exits 0
- Full test suite passes with zero regressions

### prohibitions
- BLQ1401-BLQ1404 message IDs must not appear in any source file, test, or config
- No module under src/pytest_bdd/ (excl. documented exclusions) may lack __all__
- No __init__.py (excl. root per documented decision) may have __all__ containing non-empty values

## Artifacts this phase produces

**New files:**
- src/pytest_bdd/_pylint/checkers/module_api_rules.py

**New classes:**
- ModuleApiRulesChecker(BaseChecker) — implements all 12 rules

**New message IDs:**
- E9101 (BLQ1501: missing-all), E9102 (BLQ1502: invalid-all-type), E9103 (BLQ1503: name-not-in-module)
- E9104 (BLQ1504: init-all-not-empty), E9105 (BLQ1505: init-re-exports), E9106 (BLQ1506: star-import)
- E9107 (BLQ1507: parent-relative-import), E9108 (BLQ1508: implicit-sibling-import)
- E9109 (BLQ1509: prefer-module-import), E9110 (BLQ1510: imported-name-not-in-all)
- E9111 (BLQ1511: attribute-not-in-all), E9112 (BLQ1512: same-hierarchy-absolute-import)

**Deleted files:**
- src/pytest_bdd/_pylint/checkers/init_rules.py

**Deleted classes:**
- InitRulesChecker

**Deleted message IDs:**
- E9051 (BLQ1401), E9052 (BLQ1402), E9053 (BLQ1403), E9054 (BLQ1404)

**Modified files:**
- src/pytest_bdd/_pylint/__init__.py
- pyproject.toml
- src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py
- ~55-80+ source modules in src/pytest_bdd/ (__all__ additions)

**New test functions:**
- test_blq1501_missing_all, test_blq1501_has_all, test_blq1502_invalid_all_type, test_blq1502_valid_all, ...
- (2 test functions per rule × 12 rules = 24+ test functions)
- test_filepath_guard_case, test_filepath_guard_script, test_filepath_guard_gherkin_go
