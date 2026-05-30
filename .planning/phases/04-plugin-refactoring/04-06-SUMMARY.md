---
phase: 04-plugin-refactoring
plan: "06"
subsystem: plugin-refactoring
tags: [message-validation, large-file-split, final-verification, refactor]
requires:
  - phase: 04-03
    provides: code generator plugin class pattern
  - phase: 04-04
    provides: plugin package and boundary contracts
  - phase: 04-05
    provides: live formatter runtime split
provides:
  - message schema validation module
  - message stream validation module
  - message validation result module
  - message xdist compatibility module
  - final Phase 4 verification evidence
affects: [plugin-refactoring, messages, xdist, reporting]
tech-stack:
  added: []
  patterns:
    - thin public facade for stable validation imports
    - model-owned responsibility modules for schema, stream, result, and xdist validation
key-files:
  created:
    - src/pytest_bdd/model/message_schema_validation.py
    - src/pytest_bdd/model/message_stream_validation.py
    - src/pytest_bdd/model/message_validation_result.py
    - src/pytest_bdd/model/message_validation_xdist.py
  modified:
    - src/pytest_bdd/model/message_validation.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py
    - src/pytest_bdd/script/message_capability_governance.py
    - tests/hook/test_gherkin_reporter_context_lifecycle.py
key-decisions:
  - "message_validation.py remains a public facade and parse helper only."
  - "Source internals import moved helpers from owning modules, not the facade."
  - "Existing hook tests were updated to patch post-split owning symbols instead of adding private compatibility shims."
patterns-established:
  - "Large model modules can keep stable public import facades while moving implementation to owning modules."
requirements-completed: [REF-02, REF-03]
duration: 2h 8m
completed: 2026-05-14
---

# Phase 04 Plan 06: Message Validation Split Summary

Message validation is split by responsibility and Phase 4 contracts are green in the available environment.

## Performance

- **Duration:** 2h 8m
- **Started:** 2026-05-14T06:25:20Z
- **Completed:** 2026-05-14T08:33:11Z
- **Tasks:** 4
- **Files modified:** 9

## Accomplishments

- Reduced `message_validation.py` from 791 physical lines to 72.
- Added `message_schema_validation.py` for schema validator loading, schema cleanup, and envelope schema checks.
- Added `message_stream_validation.py` for stream lifecycle validation, outcome collection, and capability coverage collection.
- Added `message_validation_result.py` for validation result, violation, and code types.
- Added `message_validation_xdist.py` for xdist compatibility and execnet payload checks.
- Updated source internals to import moved helpers from owning modules.
- Updated reporter lifecycle tests to patch post-split owning symbols.

## Task Commits

1. **Tasks 1-3: Message validation responsibility split** - `f69b7d69` (refactor)
2. **Regression test compatibility after reporter/runtime split** - `220619c7` (test)

**Plan metadata:** this docs commit

## Files Created/Modified

- `src/pytest_bdd/model/message_validation.py` - thin public facade plus `parse_message_dict`.
- `src/pytest_bdd/model/message_schema_validation.py` - schema validator cache and envelope schema validation.
- `src/pytest_bdd/model/message_stream_validation.py` - stream validation, outcome mapping, and coverage helpers.
- `src/pytest_bdd/model/message_validation_result.py` - validation result and violation types.
- `src/pytest_bdd/model/message_validation_xdist.py` - distributed reporting compatibility checks.
- `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py` - imports direct owning validation modules.
- `src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py` - imports outcome mapping defaults from owning module.
- `src/pytest_bdd/script/message_capability_governance.py` - imports stream validation helpers from owning module.
- `tests/hook/test_gherkin_reporter_context_lifecycle.py` - patches post-split owning symbols.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Exact `-o addopts=''` message-suite command removes pytester**

- **Found during:** Task 3 verification.
- **Issue:** The exact plan command removes repository addopts, including `-p pytester`; tests using `testdir` fail before exercising project code.
- **Fix:** Ran the exact focused commands where valid, and ran message/full suites with project addopts intact.
- **Verification:** message-focused suite passed with project addopts intact; exact focused non-pytester validation passed.
- **Committed in:** none; environment/test invocation issue only.

**2. [Rule 2 - Missing Critical] Existing tests patched pre-split private symbols**

- **Found during:** final full-suite verification.
- **Issue:** Two hook tests patched `entrypoint.GherkinMessageReporter` and `live_formatter_runtime.shutil.which`, but owning symbols moved during 04-04/04-05.
- **Fix:** Updated tests to patch `entrypoint.GherkinMessageReporterPlugin` and `live_formatter_node.shutil.which`.
- **Files modified:** `tests/hook/test_gherkin_reporter_context_lifecycle.py`.
- **Verification:** targeted tests passed; non-Docker full suite passed.
- **Committed in:** `220619c7`

**3. [Environment] Docker-backed remote xdist tests cannot run locally**

- **Found during:** full-suite verification.
- **Issue:** Exact full suite failed three Docker-marked ssh remote xdist tests because Docker Desktop is not installed.
- **Fix:** Recorded the environment blocker and ran the full suite with `-m "not docker"` plus a local xdist smoke.
- **Verification:** non-Docker full suite and local xdist smoke passed.
- **Committed in:** none; environment issue only.

---

**Total deviations:** 2 auto-fixed, 1 environment-gated.
**Impact on plan:** Phase 4 source and behavior contracts are satisfied in the available environment. Docker-backed verification remains external-environment gated.

## Issues Encountered

- `-o addopts=''` is incompatible with pytester-dependent tests in this repo because it removes `-p pytester`.
- Docker Desktop is not installed, so Docker-marked remote ssh xdist tests fail at environment setup.

## Verification

- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/messages/test_message_validation.py -q` - 10 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/messages/test_message_validation.py tests/messages/test_xdist_message_consolidation.py tests/messages/test_xdist_remote_transport.py -q` - 23 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest tests/contract/test_large_file_contract.py tests/contract/test_plugin_structure_contract.py tests/contract/test_plugin_boundary_contract.py tests/messages -q` - 110 passed, 2 skipped.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest tests/hook/test_gherkin_reporter_context_lifecycle.py::test_entrypoint_does_not_quiet_terminal_reporter_before_live_formatter_startup tests/hook/test_gherkin_reporter_context_lifecycle.py::test_reporter_warns_when_node_is_missing_for_requested_cucumber_formatter -q` - 2 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest tests/ -q` - 858 passed, 14 skipped, 5 failed. Failures: 2 stale test monkeypatch targets fixed in `220619c7`; 3 Docker-marked ssh tests blocked by missing Docker Desktop.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest tests/ -q -m "not docker"` - 850 passed, 14 skipped, 13 deselected.
- `env UV_PROJECT_ENVIRONMENT=.venv-linux timeout 120s uv run --extra test python -m pytest tests/messages/test_xdist_message_consolidation.py tests/messages/test_xdist_remote_transport.py tests/e2e/test_xdist_message_aggregation.py -q -n 2` - 16 passed.
- `uvx pre-commit run --all-files` - passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest tests/contract/test_large_file_contract.py tests/contract/test_plugin_structure_contract.py tests/contract/test_plugin_boundary_contract.py tests/contract/test_formatter_golden_parity.py tests/compatibility/test_render_cucumber_formatters.py tests/e2e/test_cucumber_formatters.py -q` - 42 passed.

## User Setup Required

- Docker Desktop is required to run Docker-marked remote ssh xdist tests locally.

## Phase 4 Self-Check

- `CodeGeneratorPlugin` class pattern: complete.
- `live_formatter_runtime.py` below 400 lines: complete, 25 physical lines.
- `message_validation.py` below 400 lines: complete, 72 physical lines.
- All pytest11 plugins class + entrypoint + hook structure: contract passed.
- No plugin-to-plugin internal imports: boundary contract passed.
- Formatter parity: passed.
- Full available suite: non-Docker suite passed.

## Next Phase Readiness

Ready for Phase 5. Phase 4 is complete; Docker-backed remote verification remains blocked only by local Docker availability.

---
*Phase: 04-plugin-refactoring*
*Completed: 2026-05-14*
