---
phase: 20-docs-architecture-allure-md
plan: 01
subsystem: testing
tags: [allure, jsonschema, attrs, converter, cucumber-messages]

# Dependency graph
requires: []
provides:
  - "Canonical Allure3 Events JSONSchema at docs/allure3-events.schema.json"
  - "attrs-based model types: AllureTestResult, AllureStepResult, AllureContainer, etc."
  - "Converter package scaffold with convert() entry point and 5 module stubs"
  - "Contract test suite validating schema compliance"
affects: [20-02, 20-03, 20-04a, 20-04b, 20-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [schema-driven-development, attrs-model, contract-first-testing]

key-files:
  created:
    - docs/allure3-events.schema.json
    - src/pytest_bdd/plugin/allure_cucumber/__init__.py
    - src/pytest_bdd/plugin/allure_cucumber/converter/__init__.py
    - src/pytest_bdd/plugin/allure_cucumber/converter/converter.py
    - src/pytest_bdd/plugin/allure_cucumber/converter/model.py
    - src/pytest_bdd/plugin/allure_cucumber/converter/reader.py
    - src/pytest_bdd/plugin/allure_cucumber/converter/collector.py
    - src/pytest_bdd/plugin/allure_cucumber/converter/step_tree.py
    - src/pytest_bdd/plugin/allure_cucumber/converter/mapper.py
    - src/pytest_bdd/plugin/allure_cucumber/converter/emitter.py
    - tests/cases/contract/allure/conftest.py
    - tests/cases/contract/allure/test_schema_validation.py
    - tests/cases/unit/allure/__init__.py
  modified:
    - pyproject.toml

key-decisions:
  - "Schema derived from allure-js-commons TypeScript types (no official JSONSchema exists)"
  - "N815 per-file-ignore for camelCase attrs matching Allure3 external schema contract"
  - "convert() lives in converter.py module (RUF067 forbids functions in __init__.py)"

patterns-established:
  - "Schema-driven development: JSONSchema committed first, model types match schema"
  - "Contract-first testing: schema validation tests run before implementation"

requirements-completed: [REQ-05, REQ-01]

# Metrics
duration: 45min
completed: 2026-06-10
---

# Phase 20 Plan 01: Schema Foundation Summary

**Allure3 Events JSONSchema extracted from TypeScript types, attrs model types defined, converter package scaffolded with contract tests**

## Performance

- **Duration:** 45 min
- **Started:** 2026-06-10T10:00:00Z
- **Completed:** 2026-06-10T10:45:00Z
- **Tasks:** 3
- **Files created:** 13

## Accomplishments
- Canonical Allure3 Events JSONSchema (draft-2020-12) committed covering TestResult, TestResultContainer, and all shared types
- 9 attrs model types defined matching the schema (AllureTestResult, AllureStepResult, AllureContainer, AllureFixtureResult, AllureStatusDetails, AllureLabel, AllureLink, AllureAttachment, AllureParameter)
- Converter package scaffold with convert() entry point and 5 module stubs ready for Plan 02
- 5 contract tests passing: schema validity, minimal result/container validation, malformed input rejection

## Task Commits

Each task was committed atomically:

1. **Task 1: Extract canonical Allure3 Events JSONSchema** - `0bf2b55c` (feat)
2. **Task 2: Define converter model types with attrs** - `53564f9c` (feat)
3. **Task 3: Create converter package init and test scaffold** - `027f2a4c` (feat)

## Files Created/Modified
- `docs/allure3-events.schema.json` - Canonical Allure3 Events JSONSchema (215 lines)
- `src/pytest_bdd/plugin/allure_cucumber/converter/model.py` - attrs model types
- `src/pytest_bdd/plugin/allure_cucumber/converter/converter.py` - convert() entry point
- `src/pytest_bdd/plugin/allure_cucumber/converter/__init__.py` - Package re-exports
- `src/pytest_bdd/plugin/allure_cucumber/converter/{reader,collector,step_tree,mapper,emitter}.py` - Module stubs
- `tests/cases/contract/allure/test_schema_validation.py` - 5 contract tests
- `pyproject.toml` - N815 per-file-ignore for allure model

## Decisions Made
- Schema derived from allure-js-commons TypeScript types (allure-js/packages/allure-js-commons/src/model.ts) since no official JSONSchema exists in the allure ecosystem
- N815 ruff rule ignored for model.py because camelCase field names match the external Allure3 JSON schema contract
- convert() function placed in converter.py module rather than __init__.py due to RUF067

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Schema and model types ready for Plan 20-02 (Converter Core)
- Contract test infrastructure in place for ongoing validation
- All 5 converter module stubs define the function signatures Plan 02 will implement

## Self-Check: PASSED

---
*Phase: 20-docs-architecture-allure-md*
*Completed: 2026-06-10*
