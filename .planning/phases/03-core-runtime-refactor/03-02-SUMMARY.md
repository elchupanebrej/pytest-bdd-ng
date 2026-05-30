---
phase: 03-core-runtime-refactor
plan: "02"
subsystem: runtime-model-split
tags: [refactor, runtime-model, imports]
requires:
  - 03-01
provides:
  - "Focused Run, FeatureRuntimeBinding, and ScenarioRun runtime modules"
  - "Direct owning-module imports for moved runtime symbols"
  - "Stable package-level model re-exports"
affects: [phase-03, runtime-model, reporter-runtime, pickle-runner]
key-files:
  created:
    - src/pytest_bdd/model/run.py
    - src/pytest_bdd/model/feature_binding.py
  modified:
    - src/pytest_bdd/model/scenario_run.py
    - src/pytest_bdd/model/__init__.py
    - src/pytest_bdd/plugin/pickle_runner/run_access.py
    - src/pytest_bdd/plugin/pickle_runner/run_transitions.py
    - tests/model/test_scenario_run_returns_contract.py
requirements-completed: [REF-01]
completed: 2026-05-12
---

# Phase 03 Plan 02: Runtime Module Split Summary

## Accomplishments

- Split the runtime model into three focused modules:
  - `src/pytest_bdd/model/run.py` owns `Run`, lifecycle state, reporting snapshots, and compatibility records.
  - `src/pytest_bdd/model/feature_binding.py` owns `FeatureRuntimeBinding`.
  - `src/pytest_bdd/model/scenario_run.py` owns `RunNode`, `StepRun`, and `ScenarioRun`.
- Rewrote production and test imports so moved symbols use direct owning paths.
- Updated `src/pytest_bdd/model/__init__.py` to preserve package-level imports for `Run`, `FeatureRuntimeBinding`, and `ScenarioRun`.
- Kept the only runtime circular edge lazy inside `Run.create_scenario_run()`.

## Verification

- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -c "from pytest_bdd.model.run import Run, RunStage, HookPhase, LifecycleObjectRef, ActiveObjectSet, ReportingContextSnapshot; from pytest_bdd.model.feature_binding import FeatureRuntimeBinding; from pytest_bdd.model.scenario_run import ScenarioRun, RunNode, StepRun; from pytest_bdd.model import Run as PackageRun, FeatureRuntimeBinding as PackageFeatureRuntimeBinding, ScenarioRun as PackageScenarioRun; print('imports ok')"` — passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/hook/test_scenario_run_characterization.py tests/model/test_scenario_run_returns_contract.py -q` — 19 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test python -m pytest -s -o addopts='' tests/hook/test_scenario_run_characterization.py tests/hook/test_run_transitions.py tests/hook/test_scenario_run_model.py tests/hook/test_run_scenario_runtime_unit.py tests/hook/test_reporting_context_snapshot_unit.py tests/hook/test_run_diagnostics.py tests/hook/test_scenario_reference_resolution.py tests/model/test_scenario_run_returns_contract.py -q` — 53 passed.
- `UV_PROJECT_ENVIRONMENT=.venv-linux uv run --extra test ruff check <changed runtime/import files>` — passed.

## Commits

| Commit | Description |
|--------|-------------|
| `c5853b1e` | `refactor(03-02): split runtime model modules` |

## Deviations from Plan

- Verification used `UV_PROJECT_ENVIRONMENT=.venv-linux` and `-s -o addopts=''` because the default `.venv/Scripts` path and pytest capture hit known Windows/WSL filesystem errors.
- Commit used `SKIP=generate-feature-doc` because that hook still resolves the broken default `.venv/Scripts` environment.

**Total deviations:** 2 environmental workarounds.
**Impact:** No product behavior change; target tests and changed-file lint passed.

## Self-Check: PASSED

Plan 02 produced the three target runtime modules, removed moved-symbol imports from `pytest_bdd.model.scenario_run`, preserved public model re-exports, and satisfied the Plan 01 RED import contract.
