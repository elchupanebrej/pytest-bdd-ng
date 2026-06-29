# Quick Task: Refactor test classes to standalone functions

## Task Description
Refactor all `class Test*` in `src/pytest_bdd_testing/case/` to standalone pytest functions and remove `.*case.*` from pylint `ignore-paths`.

## Files to Modify
1. `pyproject.toml` — Remove `.*case.*` from `ignore-paths`
2. `src/pytest_bdd_testing/case/e2e/test_allure_pytest_coexistence.py` — Extract `TestAllurePytestIndependence` methods to module-level functions
3. `src/pytest_bdd_testing/case/e2e/test_allure_xdist_total_report.py` — Extract `TestAllureXdistTotalReport` methods to module-level functions
4. `src/pytest_bdd_testing/case/unit/test_dead_code.py` — Extract `TestDeadCode` methods to module-level functions (keep skipif decorator)

## Verification
- `uv run pytest src/pytest_bdd_testing/case/` passes
- `uv run pylint src/pytest_bdd/ src/pytest_bdd_testing/` passes with no BLQ903 errors
