# 24-02-SUMMARY.md — Converter Core Pipeline

## What was built

Implemented the core NDJSON-to-Allure3 converter pipeline: reader, collector, step_tree, mapper, emitter, and wired `convert()` function.

## Changes made

### emitter.py
- Added `emit_container()` function that creates an AllureContainer referencing all result UUIDs and writes `*-container.json` files
- Updated `emit_results()` to return `list[Path]` (was `None`) for traceability
- Added `recurse=True` and `default=str` to `attrs.asdict()` for proper serialization

### mapper.py
- Made `map_unmappable_to_attachment()` public (was `_map_unmappable_to_attachment`)
- Updated internal call site to use public name

### converter.py
- Added `emit_container()` call to the convert() pipeline (result + container now both emitted)
- Added empty-input guard with `logger.warning` instead of silent pass

### test_converter.py
- Updated import to use public `map_unmappable_to_attachment`
- Added `test_emit_container_single` test for the new `emit_container()` function
- Fixed glob pattern in `test_emit_results_single` to match `*-result.json`

## Verification

- All 11 unit tests pass
- All 5 contract tests pass (schema validation)
- End-to-end smoke test: convert() produces both `*-result.json` and `*-container.json` from a valid NDJSON input
- All pre-commit hooks pass (ruff, vulture, mypy, etc.)

## Files modified

- `src/pytest_bdd/plugin/allure_cucumber/converter/emitter.py`
- `src/pytest_bdd/plugin/allure_cucumber/converter/mapper.py`
- `src/pytest_bdd/plugin/allure_cucumber/converter/converter.py`
- `tests/cases/unit/allure/test_converter.py`
