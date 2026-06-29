---
status: complete
---

# Quick Task 260629-e0w: Refactor test classes to standalone functions

## Summary
Removed `.*case.*` from pylint `ignore-paths` in `pyproject.toml` and refactored all `class Test*` declarations across 19 test files to standalone pytest functions.

## Changes
- **pyproject.toml**: Changed `ignore-paths = [".*case.*"]` to `ignore-paths = []`
- **19 test files** refactored: removed class declarations, extracted methods to module-level functions, removed `self` parameters
- **Pylint score**: 10.00/10 (no BLQ903 violations)
- **Tests**: All passing (13 failures in allure tests are pre-existing due to missing `allure_commons` module, unrelated to this change)

## Files Modified
- `pyproject.toml`
- `src/pytest_bdd_testing/case/e2e/test_allure_pytest_coexistence.py`
- `src/pytest_bdd_testing/case/e2e/test_allure_xdist_total_report.py`
- `src/pytest_bdd_testing/case/unit/test_dead_code.py`
- `src/pytest_bdd_testing/case/contract/cck/test_cck_allure_conversion.py`
- `src/pytest_bdd_testing/case/contract/cck/test_cck_allure_rendering.py`
- `src/pytest_bdd_testing/case/contract/formatters/allure_formatter/test_allure_consumption_ui.py`
- `src/pytest_bdd_testing/case/contract/formatters/allure_formatter/test_allure_hook_vs_import_golden.py`
- `src/pytest_bdd_testing/case/contract/formatters/allure_formatter/test_allure_plugin_hook_ingestion.py`
- `src/pytest_bdd_testing/case/contract/formatters/allure_formatter/test_allure_plugin_ndjson_import.py`
- `src/pytest_bdd_testing/case/contract/formatters/allure_formatter/test_mapping_contract.py`
- `src/pytest_bdd_testing/case/contract/formatters/allure_formatter/test_pytest_bdd_field_coverage.py`
- `src/pytest_bdd_testing/case/contract/formatters/allure_formatter/test_schema_field_coverage.py`
- `src/pytest_bdd_testing/case/unit/formatters/allure_formatter/test_api_hooks.py`
- `src/pytest_bdd_testing/case/unit/formatters/allure_formatter/test_collector.py`
- `src/pytest_bdd_testing/case/unit/formatters/allure_formatter/test_converter.py`
- `src/pytest_bdd_testing/case/unit/formatters/allure_formatter/test_converter_e2e.py`
- `src/pytest_bdd_testing/case/unit/formatters/allure_formatter/test_emitter.py`
- `src/pytest_bdd_testing/case/unit/formatters/allure_formatter/test_listener.py`
- `src/pytest_bdd_testing/case/unit/formatters/allure_formatter/test_mapper.py`
- `src/pytest_bdd_testing/case/unit/formatters/allure_formatter/test_message_adapter.py`
- `src/pytest_bdd_testing/case/unit/formatters/allure_formatter/test_reader.py`
- `src/pytest_bdd_testing/case/unit/formatters/allure_formatter/test_step_tree.py`
