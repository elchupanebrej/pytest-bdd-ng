# Plan: Run pylint architecture injector on src/pytest_bdd_testing (excluding cases/)

**Quick ID:** 260615-kzf
**Description:** Run pylint architecture injector on src/pytest_bdd_testing excluding src/pytest_bdd_testing/cases

## Context

The project has a custom pylint plugin (`pytest_bdd._pylint`) that includes architecture-related checkers:
- `layer_rules.py` - BLQ1301/BLQ1302/BLQ1303: import layer boundary enforcement
- `responsibility_docs.py` - BLQ910/BLQ911/BLQ913/BLQ914/BLQ915: architecture score and responsibility doc checks
- `test_responsibility_docs.py` - BLQ920/BLQ921/BLQ922/BLQ923: test responsibility doc checks

Currently, pre-commit runs pylint on `src/pytest_bdd/` and `src/pytest_bdd_testing/cases/unit/`. The user wants to extend coverage to `src/pytest_bdd_testing/` excluding the `cases/` subdirectory.

## Task 1: Run pylint on non-case files in src/pytest_bdd_testing/

**Files:** All .py files in `src/pytest_bdd_testing/` excluding `src/pytest_bdd_testing/cases/`

**Action:**
1. Collect all Python files in `src/pytest_bdd_testing/` that are NOT inside `cases/`
2. Run `uv run pylint <files>` with the project's custom pylint plugin loaded
3. Capture and report the output

**Verify:** Pylint runs to completion and reports any violations found

**Done:** Results reported to user

## Task 2: Create SUMMARY.md

**Action:** Write summary of findings

**Done:** Summary created
