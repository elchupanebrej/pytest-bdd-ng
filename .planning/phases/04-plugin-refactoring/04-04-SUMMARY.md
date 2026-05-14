---
phase: 04-plugin-refactoring
plan: "04"
subsystem: plugin-refactoring
tags: [formatter-plugins, plugin-boundaries, contracts, refactor]
requires:
  - phase: 04-02
    provides: plugin structure and boundary contract tests
provides:
  - package-shaped cucumber formatter plugins
  - model-level formatter request/result contracts
  - model-level scenario report and run access contracts
  - util-owned cucumber formatter support helpers
affects: [plugin-refactoring, cucumber-formatters, reporting]
tech-stack:
  added: []
  patterns:
    - package entrypoint/plugin/hook structure for pytest11 plugins
    - plugin boundary dependencies through model and util modules
key-files:
  created:
    - src/pytest_bdd/model/cucumber_formatter_contract.py
    - src/pytest_bdd/model/run_access.py
    - src/pytest_bdd/model/scenario_collection.py
    - src/pytest_bdd/model/scenario_report.py
    - src/pytest_bdd/util/cucumber_formatter_support/
    - src/pytest_bdd/plugin/cucumber_json_formatter/
    - src/pytest_bdd/plugin/cucumber_junit/
    - src/pytest_bdd/plugin/cucumber_pretty/
    - src/pytest_bdd/plugin/cucumber_progress/
    - src/pytest_bdd/plugin/cucumber_progress_bar/
    - src/pytest_bdd/plugin/cucumber_snippets/
    - src/pytest_bdd/plugin/cucumber_summary/
    - src/pytest_bdd/plugin/cucumber_usage/
    - src/pytest_bdd/plugin/cucumber_usage_json/
  modified:
    - pyproject.toml
    - src/pytest_bdd/plugin/gherkin_message_reporter/session.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py
    - src/pytest_bdd/plugin/scenario_reporter/plugin.py
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py
    - src/pytest_bdd/plugin/pickle_runner/plugin.py
key-decisions:
  - "Formatter plugin entrypoints now resolve through package entrypoint modules."
  - "Shared formatter support moved to util so formatter plugins do not import peer plugin internals."
  - "Scenario report, scenario collection markers, and run access helpers moved to model-level contracts."
patterns-established:
  - "Formatter plugins define Plugin classes in plugin.py and expose plugin instances from entrypoint.py."
  - "Plugin packages depend on model/util contracts for cross-package data and helper access."
requirements-completed: [REF-02]
duration: 8h 33m
completed: 2026-05-14
---

# Phase 04 Plan 04: Plugin Package and Boundary Normalization Summary

Formatter plugins now use package entrypoints with model/util-owned shared contracts and no plugin-to-plugin internal imports.

## Performance

- **Duration:** 8h 33m
- **Started:** 2026-05-13T21:26:49Z
- **Completed:** 2026-05-14T05:59:49Z
- **Tasks:** 3
- **Files modified:** 72

## Accomplishments

- Moved stable formatter request/result types to `pytest_bdd.model.cucumber_formatter_contract`.
- Converted nine single-file cucumber formatter plugins into package directories with `entrypoint.py`, `plugin.py`, and `hook.py`.
- Updated all formatter pytest11 entrypoints to package entrypoint modules.
- Removed plugin-to-plugin internal imports from plugin code by moving shared formatter support to `util/` and shared scenario/run contracts to `model/`.
- Added canonical `*Plugin` class names for older plugin packages so all 17 pytest11 plugins satisfy the structure contract.

## Task Commits

1. **Task 1: Move stable formatter contracts to model layer** - `a4abf59e` (refactor)
2. **Task 2: Convert single-file formatter plugins into packages** - `12257b5a` (refactor)
3. **Task 3: Remove plugin-to-plugin internal imports** - `7d2a8652` (refactor)

**Plan metadata:** this docs commit

## Files Created/Modified

- `src/pytest_bdd/model/cucumber_formatter_contract.py` - stable formatter request/result/runtime contract types.
- `src/pytest_bdd/util/cucumber_formatter_support/` - formatter plugin base, registry, and standalone request helpers.
- `src/pytest_bdd/model/run_access.py` - shared run access helpers used by reporting and collection plugins.
- `src/pytest_bdd/model/scenario_collection.py` - scenario collection marker and option contracts.
- `src/pytest_bdd/model/scenario_report.py` - scenario report data and normalization contracts.
- `src/pytest_bdd/plugin/cucumber_*_formatter/` and formatter package directories - canonical formatter plugin packages.
- `pyproject.toml` - pytest11 formatter entrypoints now target package entrypoints.

## Decisions Made

- Kept formatter plugin behavior in plugin packages, but moved reusable support helpers out of the plugin tree to avoid cross-plugin imports.
- Used model-level modules only for stable value contracts and run/report access helpers; plugin runtime behavior stayed in plugin packages.
- Added direct `*Plugin` subclasses for existing package plugins instead of rewriting their runtime behavior.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Existing package plugins lacked canonical `*Plugin` class names**

- **Found during:** Task 2 (Convert single-file formatter plugins into packages)
- **Issue:** The structure contract applies to all 17 pytest11 plugins, but several existing package plugins had classes such as `PickleRunner` and `ScenarioReporter` that did not end in `Plugin`.
- **Fix:** Added thin canonical subclasses and updated entrypoints to instantiate them.
- **Files modified:** existing plugin package `plugin.py` and `entrypoint.py` files.
- **Verification:** `tests/contract/test_plugin_structure_contract.py` passed.
- **Committed in:** `12257b5a`

**2. [Rule 2 - Missing Critical] Formatter support package was itself a plugin-tree boundary dependency**

- **Found during:** Task 3 (Remove plugin-to-plugin internal imports)
- **Issue:** Formatter plugins still imported `pytest_bdd.plugin.cucumber_formatter_support.*`, which violated the strict boundary contract after package migration.
- **Fix:** Moved formatter support helpers to `pytest_bdd.util.cucumber_formatter_support` and updated source/tests.
- **Files modified:** formatter plugins, reporter session/standalone renderer, formatter scripts, contract tests.
- **Verification:** `tests/contract/test_plugin_boundary_contract.py` passed.
- **Committed in:** `7d2a8652`

---

**Total deviations:** 2 auto-fixed.
**Impact on plan:** Required to satisfy the phase contract. No compatibility alias modules were added for removed private imports.

## Issues Encountered

None.

## Verification

- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -c "import pytest_bdd.model.cucumber_formatter_contract; print('formatter contract ok')"` - passed during Task 1.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_plugin_structure_contract.py tests/contract/test_cucumber_formatter_cli_contract.py -q` - 15 passed during Task 2.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_plugin_boundary_contract.py -q` - 1 passed during Task 3.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/contract/test_plugin_structure_contract.py tests/contract/test_plugin_boundary_contract.py tests/contract/test_cucumber_formatter_cli_contract.py -q` - 16 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -q tests/contract/test_standalone_rendering_boundary_contract.py tests/contract/test_formatter_golden_parity.py tests/feature/test_report.py tests/hook/test_reporting_context_snapshot_unit.py tests/hook/test_scenario_reference_resolution.py` - 28 passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for 04-05. Formatter plugin structure and boundary contracts are green; large-file targets remain for live formatter runtime and message validation follow-up plans.

---
*Phase: 04-plugin-refactoring*
*Completed: 2026-05-14*
