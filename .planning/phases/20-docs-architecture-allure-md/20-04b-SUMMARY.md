# Plan 20-04b: Contract, Integration, and Property-Based Tests

## Goal
Add contract tests (CLI registration, converter mapping, golden parity), hypothesis property-based invariants, and real pytest plugin integration tests for the allure-cucumber converter.

## Files Created
- `tests/cases/contract/allure/test_cli_contract.py`: 4 CLI contract tests
- `tests/cases/contract/allure/test_converter_contract.py`: 3 converter contract tests
- `tests/cases/contract/allure/test_golden_parity.py`: 2 golden parity tests
- `tests/cases/contract/allure/test_hypothesis.py`: 1 hypothesis property-based test
- `tests/cases/integration/allure/__init__.py`: Package marker
- `tests/cases/integration/allure/conftest.py`: Integration test config
- `tests/cases/integration/allure/test_plugin.py`: 2 plugin integration tests

## Bug Fixes During Execution
- **mapper.py**: Fixed event type matching to use snake_case (matching `payload_kind.value`) instead of PascalCase
- **mapper.py**: Fixed `test_step_finished` to read status from `projection.payload.test_step_result.status` instead of `projection.payload.status`
- **mapper.py**: Fixed `test_case_finished` to derive status from last step instead of non-existent `TestCaseFinished.status`
- **collector.py**: Fixed `_extract_test_case_id` to handle `TestCaseStarted` events (uses `id` field, not `testCaseStartedId`)
- **model.py**: Changed `statusDetails` defaults from `None` to `AllureStatusDetails()` to satisfy Allure3 JSON schema
- **emitter.py**: Replaced `default=str` serializer with proper `_convert_timestamps()` to emit timestamps as integers instead of `Timestamp(...)` objects
- **test_converter.py**: Updated mock_projection fixture to use snake_case event types
- **test_mapper.py**: Updated `_make_projection` calls and tests to use snake_case event types

## Test Summary
| File | Tests | Focus |
|------|-------|-------|
| test_cli_contract.py | 4 | pyproject.toml registration, --help, error handling, valid input |
| test_converter_contract.py | 3 | TestCase→TestResult mapping, unmappable→attachments, labels field |
| test_golden_parity.py | 2 | Known NDJSON→expected structure, container.children references |
| test_hypothesis.py | 1 | Any valid NDJSON→valid Allure JSON or documented error |
| test_plugin.py | 2 | pytest_sessionfinish emits results, INI config respected |

## Verification
All 64 tests pass: `uv run pytest tests/cases/unit/allure/ tests/cases/contract/allure/ tests/cases/integration/allure/ -v`

## Commits
- `test(20-04a): add factory-boy+hypothesis deps, unit tests for converter internals, extend schema validation`
- `test(20-04b): add contract, hypothesis, and integration tests; fix mapper/collector/emitter bugs`

## Status: ✅ COMPLETE
