---
phase: 03-core-runtime-refactor
plan: "01"
subsystem: runtime-characterization
tags: [characterization, tdd, import-contracts]
requires: []
provides:
  - "Runtime serialization characterization tests"
  - "RunStage transition characterization across PHASE_TO_STAGE"
  - "Source contract for moved scenario_run symbols"
affects: [phase-03, runtime-model-tests]
key-files:
  created:
    - tests/hook/test_scenario_run_characterization.py
  modified:
    - tests/model/test_scenario_run_returns_contract.py
requirements-completed: [REF-01]
completed: 2026-05-12
---

# Phase 03 Plan 01: Characterization Safety Net Summary

## Accomplishments

- Added runtime characterization tests for `LifecycleObjectRef`, `ActiveObjectSet`, `Run`, `ScenarioRun`, `ContextErrorState`, and `ReportingContextSnapshot` serialization.
- Added transition characterization across every `HookPhase` in `PHASE_TO_STAGE`.
- Added RED import contract tests for the target split modules:
  - `pytest_bdd.model.run`
  - `pytest_bdd.model.feature_binding`
  - `pytest_bdd.model.scenario_run`
- Extended `tests/model/test_scenario_run_returns_contract.py` with a source-level stale import guard.

## Verification

- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/hook/test_scenario_run_characterization.py tests/model/test_scenario_run_returns_contract.py -q` — RED as expected:
  - `pytest_bdd.model.feature_binding` missing until Plan 02.
  - Moved symbols still imported from `pytest_bdd.model.scenario_run` until Plan 02.

## Commits

| Commit | Description |
|--------|-------------|
| `61bf755d` | `test(03-01): characterize runtime split contract` |

## Deviations from Plan

- Verification used `UV_PROJECT_ENVIRONMENT=.venv-linux` and `-s -o addopts=''` because the default `.venv/Scripts` path and pytest capture hit known Windows/WSL filesystem errors.
- Plan 01 intentionally leaves RED split-module/import tests for Plan 02 to satisfy. Existing behavior characterization tests pass.

**Total deviations:** 1 environmental workaround, 1 intentional TDD RED state.
**Impact:** Expected and bounded; Plan 02 is the GREEN step.

## Self-Check: PASSED

Plan 01 created the requested test-first characterization and import contract. The remaining failures are the intended RED assertions for the upcoming module split.
