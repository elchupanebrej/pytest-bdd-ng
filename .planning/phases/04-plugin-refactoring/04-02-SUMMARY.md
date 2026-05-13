---
phase: 04-plugin-refactoring
plan: "02"
subsystem: testing
tags: [contract-tests, plugin-boundaries, formatter-golden, large-file-contracts]
requires:
  - phase: 04-01
    provides: local verification environment unblocked enough to run focused contract gates
provides:
  - plugin package structure contract for pytest11 entrypoints
  - plugin-to-plugin import boundary contract
  - formatter golden parity snapshot contract
  - large-file split contract for Phase 4 refactor targets
affects: [plugin-refactoring, formatter-refactoring, message-validation]
tech-stack:
  added: []
  patterns:
    - AST-backed source contracts
    - committed formatter output snapshots with normalization
key-files:
  created:
    - tests/contract/test_plugin_structure_contract.py
    - tests/contract/test_plugin_boundary_contract.py
    - tests/contract/test_formatter_golden_parity.py
    - tests/contract/test_large_file_contract.py
    - tests/fixtures/cucumber_formatter_golden.json
  modified: []
key-decisions:
  - "Structure, boundary, and line-count contracts are intentionally red until later Phase 4 migration plans satisfy them."
  - "Formatter parity is green before refactor and uses fake Node outputs to avoid external formatter drift."
patterns-established:
  - "Phase 4 source contracts collect all violations before asserting so later plans get complete failure inventories."
requirements-completed: [REF-02, REF-03]
duration: 41 min
completed: 2026-05-13
---

# Phase 04 Plan 02: Source Contracts and Formatter Golden Baselines Summary

Plugin refactor safety net with source contracts for package shape, boundary imports, formatter parity, and large-file targets.

## Performance

- **Duration:** 41 min
- **Started:** 2026-05-13T19:40:00Z
- **Completed:** 2026-05-13T20:21:28Z
- **Tasks:** 4
- **Files modified:** 5

## Accomplishments

- Added a pytest11 plugin structure contract that parses `pyproject.toml`, asserts 17 plugin entrypoints, requires package-style `.entrypoint` modules, and explicitly checks for `CodeGeneratorPlugin`.
- Added an AST-based plugin boundary contract that reports the source file and imported plugin module for cross-plugin internal imports.
- Added a formatter golden parity contract covering `summary`, `progress`, `progress-bar`, `snippets`, `pretty`, `usage`, `json`, `junit`, and `usage-json`.
- Added a large-file contract for `live_formatter_runtime.py` and `message_validation.py`, while keeping `steps.py` out of scope per D-05.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add pytest11 plugin structure source contract** - `c698f913` (test)
2. **Task 2: Add plugin boundary import contract** - `2963ac6a` (test)
3. **Task 3: Add formatter golden parity contract** - `c1cecf74` (test)
4. **Task 4: Add large-file line-count contract** - `69b33087` (test)

**Plan metadata:** this docs commit

## Files Created/Modified

- `tests/contract/test_plugin_structure_contract.py` - pytest11 entrypoint and canonical package-shape contract.
- `tests/contract/test_plugin_boundary_contract.py` - AST import walker that blocks peer plugin implementation imports.
- `tests/contract/test_formatter_golden_parity.py` - formatter golden parity checks using fake Node runtime.
- `tests/contract/test_large_file_contract.py` - line-count threshold checks for Phase 4 split targets.
- `tests/fixtures/cucumber_formatter_golden.json` - stable expected formatter outputs.

## Decisions Made

- Kept red source contracts as real failing tests instead of marking them xfail, because the plan explicitly requires contracts that fail before later migration plans and pass after those plans.
- Stored formatter snapshots under `tests/fixtures/` and normalized only temp paths, ANSI sequences, and duration text.

## Deviations from Plan

None - plan executed exactly as written.

---

**Total deviations:** 0 auto-fixed.
**Impact on plan:** None.

## Issues Encountered

- Task 1 and Task 3 commits initially hit style hooks. The test code was reformatted/fixed and the commits were retried successfully.

## Verification

- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_plugin_structure_contract.py -q` — expected red, 1 failed. Current failures identify missing canonical hook modules, formatter single-file entrypoints, and missing `CodeGeneratorPlugin`.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_plugin_boundary_contract.py -q` — expected red, 1 failed. Current failures identify 24 cross-plugin imports.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_formatter_golden_parity.py -q` — passed, 11 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_large_file_contract.py -q` — expected red, 1 failed. Current counts: `live_formatter_runtime.py` 900 lines and `message_validation.py` 791 lines.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_plugin_structure_contract.py tests/contract/test_plugin_boundary_contract.py tests/contract/test_formatter_golden_parity.py tests/contract/test_large_file_contract.py -q` — expected red, 3 failed and 11 passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for 04-03. Later plans must make the red structure, boundary, and large-file contracts green while preserving the formatter golden parity contract.

---
*Phase: 04-plugin-refactoring*
*Completed: 2026-05-13*
