# Plan 24-04a: Unit Tests for Converter Internals

## Goal
Add comprehensive unit tests for each internal module of the allure converter (reader, collector, step_tree, mapper, emitter) plus end-to-end converter tests.

## Files Modified
- `pyproject.toml`: Added `factory-boy` and `hypothesis` to `[project.optional-dependencies] test`
- `tests/cases/unit/allure/conftest.py`: Empty (reserved for shared fixtures)
- `tests/cases/unit/allure/test_reader.py`: 5 tests for `read_envelopes()`
- `tests/cases/unit/allure/test_collector.py`: 6 tests for `collect_cases()`
- `tests/cases/unit/allure/test_step_tree.py`: 6 tests for `build_step_tree()`
- `tests/cases/unit/allure/test_mapper.py`: 7 tests for `map_status()`, `map_test_case_to_result()`, `map_unmappable_to_attachment()`
- `tests/cases/unit/allure/test_emitter.py`: 7 tests for `emit_results()` and `emit_container()`
- `tests/cases/unit/allure/test_converter_e2e.py`: 3 end-to-end tests
- `tests/cases/contract/allure/conftest.py`: Updated `sample_ndjson` fixture with full Cucumber Messages event chain; added `converter_output_dir` fixture
- `tests/cases/contract/allure/test_schema_validation.py`: Added `test_converter_output_validates`

## Test Summary
| Module | Tests | Focus |
|--------|-------|-------|
| reader | 5 | JSON parsing, multi-envelope, empty lines, malformed input, empty file |
| collector | 6 | Case grouping, multi-case, no-id skipping, camelCase IDs, order preservation |
| step_tree | 6 | Empty projections, single step, sibling steps, status mapping, markers, unknown events |
| mapper | 7 | Status mapping (all statuses + case-insensitive), testCase→result, unmappable→attachment |
| emitter | 7 | Empty results, single result, JSON validity, container creation, container references |
| e2e | 3 | Full pipeline produces files, empty input no error, output JSON structure |
| contract | 1 | Converter output validates against Allure schema |

## Verification
All 52 tests pass: `uv run pytest tests/cases/unit/allure/ tests/cases/contract/allure/test_schema_validation.py -v`

## Commits
- `test(24-04a): add factory-boy+hypothesis deps, unit tests for converter internals, extend schema validation` (allure-integration)

## Status: ✅ COMPLETE
