---
phase: 04-plugin-refactoring
status: complete
created: 2026-05-13
---

# Phase 04 Pattern Map

## Closest Existing Patterns

### Class-based plugin packages

- `src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py`
- `src/pytest_bdd/plugin/scenario_test_collector/plugin.py`
- `src/pytest_bdd/plugin/scenario_test_collector/hook.py`
- `src/pytest_bdd/plugin/pickle_runner/entrypoint.py`
- `src/pytest_bdd/plugin/pickle_runner/plugin.py`
- `src/pytest_bdd/plugin/pickle_runner/hook.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/hook.py`

Use these for Phase 4 package shape, hook spec registration, and plugin class placement.

### Service-style reporter runtime

- `src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/service_base.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py`

Use these for the `live_formatter_runtime.py` split. Keep `LiveFormatterService` as the coordinator and move responsibility clusters behind focused helpers/services.

### Model-level stable contracts

- `src/pytest_bdd/model/message_transport.py`
- `src/pytest_bdd/model/message_serialization.py`
- `src/pytest_bdd/model/cucumber_formatter_adapter.py`
- `src/pytest_bdd/model/message_outcome_mapping.py`
- `src/pytest_bdd/model/message_status_governance.py`

Use these as placement analogs for formatter request/result contracts and validation result contracts that are shared across plugin boundaries.

### Contract tests

- `tests/contract/test_cucumber_formatter_cli_contract.py`
- `tests/contract/test_standalone_rendering_boundary_contract.py`
- `tests/contract/test_xdist_worker_controller_boundary_contract.py`
- `tests/model/test_scenario_run_returns_contract.py`
- `tests/messages/test_message_validation.py`

Use these for source-level contracts, plugin boundary contracts, and validation split characterization.

## Files Expected To Change

- `pyproject.toml`
- `src/pytest_bdd/plugin/code_generator/entrypoint.py`
- `src/pytest_bdd/plugin/code_generator/plugin.py`
- `src/pytest_bdd/plugin/code_generator/*.py`
- `src/pytest_bdd/plugin/cucumber_*`
- `src/pytest_bdd/plugin/cucumber_formatter_support/*.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/*.py`
- `src/pytest_bdd/model/message_validation.py`
- `src/pytest_bdd/model/message_validation_*.py`
- `tests/contract/*.py`
- `tests/messages/test_message_validation.py`
- `tests/compatibility/test_render_cucumber_formatters.py`
- `tests/e2e/test_cucumber_formatters.py`

## Constraints

- Preserve CLI flags and `pytest11` plugin names.
- No private-path compatibility shims.
- Keep imports direct from owning modules.
- Keep `steps.py` out of scope unless an executor proves a direct dependency blocks Phase 4 success criteria.
