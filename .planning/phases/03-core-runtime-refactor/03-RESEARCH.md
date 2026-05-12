# Phase 03: Core Runtime Refactor - Research

**Phase:** 03 - Core Runtime Refactor
**Date:** 2026-05-12
**Requirement:** REF-01
**Question:** What must be known to plan a zero-behavior split of `src/pytest_bdd/model/scenario_run.py`?

## Executive Summary

Phase 03 is a pure structural refactor of the runtime context model. The safe path is characterization-first, then a three-module extraction with direct importer migration and no compatibility shim from `pytest_bdd.model.scenario_run`.

The current module is the canonical runtime state boundary for `Run`, `FeatureRuntimeBinding`, and `ScenarioRun`. Existing SpecKit contracts from `003-unify-run-context`, `009-execution-context-reporting`, and `016-strict-non-null` establish that `Run` owns session/root state and registries, `FeatureRuntimeBinding` owns feature document/pickle lookup, and `ScenarioRun` owns per-scenario active lifecycle state. The phase should preserve that ownership while moving code into focused modules.

## Current Runtime Shape

`src/pytest_bdd/model/scenario_run.py` currently defines:

- Core aliases: `ScenarioRunResult`, `LifecycleKind`, `NodeKind`
- Enums: `HookPhase`, `RunStage`, `RunStatus`
- Lifecycle value objects: `LifecycleObjectRef`, `NoPreviousStep`, `ActiveObjectSet`
- Shared state objects: `ReportingLifecycleState`, `ReferenceResolverState`, `ContextErrorState`
- Feature binding: `FeatureRuntimeBinding`
- Session root: `Run`
- Scenario tracking: `RunNode`, `StepRun`, `ScenarioRun`
- Snapshot/API records: `ReportingContextSnapshot`, `ExternalApiCompatibilityRecord`

High-risk dependencies:

- `Run.create_scenario_run()` imports `build_lifecycle_ref`, `initial_scenario_run_id`, and `runtime_object_id` lazily from `plugin/pickle_runner/run_transitions.py`.
- `run_transitions.py` imports `ActiveObjectSet`, `HookPhase`, `LifecycleKind`, `LifecycleObjectRef`, `NoPreviousStep`, `RunNode`, `RunStage`, `RunStatus`, and `ScenarioRun`.
- `run_access.py` imports both session/root and scenario/snapshot symbols.
- `FeatureRuntimeBinding` stores `run: Run` and calls `Run.index_identifiable_tree()`.
- `Run` stores `feature_bindings_by_uri: dict[str, FeatureRuntimeBinding]` and creates `ScenarioRun`.
- `ScenarioRun.feature_binding` resolves through `Run.feature_binding_for_uri()` / `Run.feature_binding_for_document()`.

## Recommended Module Boundaries

### `src/pytest_bdd/model/run.py`

Own session/root runtime state and shared value objects used by root and reporting.

Place here:

- `HookPhase`
- `RunStage`
- `RunStatus`
- `ScenarioRunResult`
- `LifecycleKind`
- `NodeKind`
- `LifecycleObjectRef`
- `NoPreviousStep`
- inactive/finished lifecycle ref factories
- `ActiveObjectSet`
- `ReportingLifecycleState`
- `ReferenceResolverState`
- `ContextErrorState`
- `Run`
- `ReportingContextSnapshot`
- `ExternalApiCompatibilityRecord`

Rationale: `run_transitions.py`, reporters, and `run_access.py` need these symbols. Keeping shared lifecycle values with `Run` avoids a fourth module that ROADMAP does not name.

### `src/pytest_bdd/model/feature_binding.py`

Own feature document, pickle compilation, and AST/reference lookup.

Place here:

- `FeatureRuntimeBinding`

Dependencies:

- Runtime import of `Run` only for attrs type annotation can be avoided with `from __future__ import annotations` and `TYPE_CHECKING`.
- Methods that call `self.run.index_identifiable_tree()` can rely on duck-typed method presence; no runtime import of `Run` is needed.

Rationale: SpecKit `009-execution-context-reporting` requires feature-level registry/lookup state to live in `Run`/`ScenarioRun`, not in the removed `Feature` adapter. `FeatureRuntimeBinding` is the focused runtime carrier for that feature-level state.

### `src/pytest_bdd/model/scenario_run.py`

Own per-scenario execution state only.

Place here:

- `RunNode`
- `StepRun`
- `ScenarioRun`

Dependencies:

- Import shared lifecycle symbols from `pytest_bdd.model.run`.
- Import `FeatureRuntimeBinding` from `pytest_bdd.model.feature_binding`.
- Use `TYPE_CHECKING` for `Run` annotation where possible, but keep runtime behavior unchanged where attrs needs real classes.

Rationale: Keeps existing filename as the scenario-specific module, not a compatibility barrel. Importers must move to specific module paths.

## Import Migration Findings

Direct production importers of `pytest_bdd.model.scenario_run`:

- `src/pytest_bdd/hook.py`
- `src/pytest_bdd/parser.py`
- `src/pytest_bdd/scenario_locator.py`
- `src/pytest_bdd/plugin/code_generator/plugin.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/attachment_runtime.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py`
- `src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py`
- `src/pytest_bdd/plugin/pickle_runner/api_compatibility.py`
- `src/pytest_bdd/plugin/pickle_runner/entrypoint.py`
- `src/pytest_bdd/plugin/pickle_runner/hook.py`
- `src/pytest_bdd/plugin/pickle_runner/plugin.py`
- `src/pytest_bdd/plugin/pickle_runner/run_access.py`
- `src/pytest_bdd/plugin/pickle_runner/run_transitions.py`
- `src/pytest_bdd/plugin/scenario_reporter/plugin.py`
- `src/pytest_bdd/plugin/scenario_reporter/report.py`
- `src/pytest_bdd/plugin/scenario_test_collector/plugin.py`

Test importers should be migrated too so they prove the new direct import paths:

- `tests/hook/test_*.py` runtime/context tests
- `tests/messages/test_messages_feature_suite.py`
- `tests/model/gherkin_document/test_feature_context_lookup.py`

`src/pytest_bdd/model/__init__.py` must continue package-level re-exports, but it should import each symbol from its owning new module. `pytest_bdd.model.scenario_run` must not re-export `Run` or `FeatureRuntimeBinding`, per Phase 03 context decision.

## Characterization Strategy

Existing tests cover important fragments but do not fully lock byte-level `as_dict()` behavior or all hook transitions. Add tests before extraction.

Recommended new file:

- `tests/hook/test_scenario_run_characterization.py`

Minimum characterization cases:

1. `LifecycleObjectRef.as_dict()` and `ActiveObjectSet.as_dict()` include exact keys and values for active and inactive lifecycle slots.
2. `Run.initialize_for_session()` stores `Run` and `EnvelopeRegistry` in `config.stash`, with exact `Run.as_dict()` output for idle state.
3. `Run.create_scenario_run()` creates feature/scenario nodes, active refs, feature binding, and request mapping with exact serialized shape.
4. `apply_transition()` covers every `HookPhase` in `PHASE_TO_STAGE` and asserts exact `RunStage`, `RunStatus`, active slot `empty_state_reason`, transition counters, and step-node open/close behavior.
5. `apply_transition(... HookPhase.after_scenario ...)` preserves existing reporting state behavior, closes scenario/feature nodes, and marks active set `finished`.
6. `ScenarioRun.record_context_error()` writes identical `ContextErrorState.as_dict()` values to scenario and run.
7. New import paths work:
   - `from pytest_bdd.model.run import Run, RunStage, HookPhase`
   - `from pytest_bdd.model.scenario_run import ScenarioRun, RunNode, StepRun`
   - `from pytest_bdd.model.feature_binding import FeatureRuntimeBinding`

## Extraction Sequence

1. Add characterization tests while imports still use old path only where necessary.
2. Extract shared lifecycle and `Run` code to `model/run.py`.
3. Extract `FeatureRuntimeBinding` to `model/feature_binding.py`.
4. Reduce `model/scenario_run.py` to `RunNode`, `StepRun`, and `ScenarioRun`.
5. Update production importers to direct owning modules.
6. Update tests to direct owning modules.
7. Update `model/__init__.py` re-exports from new modules.
8. Run import-cycle check before broader tests.

## Circular Import Risks And Mitigations

Risk: `Run` imports `ScenarioRun` and `FeatureRuntimeBinding`, while those classes need a `Run` reference.

Mitigation:

- In `run.py`, import `FeatureRuntimeBinding` and `ScenarioRun` at runtime only if needed for object construction.
- In `feature_binding.py` and `scenario_run.py`, guard `Run` imports with `TYPE_CHECKING`.
- Keep `from __future__ import annotations` in all new modules.
- Preserve existing lazy import from `Run.create_scenario_run()` to `plugin.pickle_runner.run_transitions`; do not move transition functions into model modules during this phase.

Risk: tests and plugins still importing moved symbols from `pytest_bdd.model.scenario_run`.

Mitigation:

- Use `rg "pytest_bdd\\.model\\.scenario_run"` as a migration checklist.
- Assert old-path imports of moved symbols are gone from `src/` and `tests/`.

## Security Threat Model

<threat_model>

### Assets

- Deterministic pytest lifecycle state in `Run` and `ScenarioRun`
- Cucumber message/reporting correlation IDs
- `pytest.config.stash` session state
- Feature document and pickle object registries

### Threats

- **T-03-01: State leak across scenarios or workers.** A bad split could make `scenario_runs_by_request`, `active_scenario_run`, or feature bindings shared incorrectly.
  - Severity: high
  - Mitigation: characterization tests for request mapping, pop cleanup, xdist `-n 2` verification.
- **T-03-02: Silent reporting corruption.** Import-cycle workarounds could cause reporters to resolve fallback snapshots instead of active context.
  - Severity: high
  - Mitigation: reporter lifecycle tests plus `ReportingContextSnapshot.as_dict()` characterization.
- **T-03-03: Import shim masks missed migration.** Re-exporting moved symbols from `model/scenario_run.py` could hide stale imports and undercut maintainability.
  - Severity: medium
  - Mitigation: source-level test banning moved symbol imports from old module.
- **T-03-04: Registry reference drift.** Moving `FeatureRuntimeBinding` could lose indexing of `GherkinDocument`, `Pickle`, `Scenario`, or `Step` IDs.
  - Severity: high
  - Mitigation: reference resolver tests and new feature binding characterization with real cucumber message objects.

</threat_model>

## Validation Architecture

Use a narrow-to-wide validation ladder:

1. Fast characterization loop:
   - `uv run python -m pytest tests/hook/test_scenario_run_characterization.py -q`
2. Runtime model loop:
   - `uv run python -m pytest tests/hook/test_run_transitions.py tests/hook/test_scenario_run_model.py tests/hook/test_run_scenario_runtime_unit.py tests/hook/test_reporting_context_snapshot_unit.py tests/hook/test_run_diagnostics.py tests/hook/test_scenario_reference_resolution.py -q`
3. Import and source contract loop:
   - `uv run python -m pytest tests/model/test_scenario_run_returns_contract.py tests/compatibility/test_public_api_exports.py -q`
4. Integration loop:
   - `uv run python -m pytest tests/feature/test_run_lifecycle.py tests/feature/test_run_hooks.py tests/hook/test_scenario_locator_pipeline.py tests/hook/test_scenario_collection_read_hooks.py -q`
5. Full suite:
   - `uv run python -m pytest tests/ -q`
6. xdist smoke:
   - `uv run python -m pytest tests/ -q -n 2`
7. Quality gate:
   - `uv run pre-commit run --all-files`

Nyquist sampling rule: after each extraction task, run the fastest relevant loop that exercises the touched module. No two module-extraction tasks should occur without a model loop run.

## Planning Implications

Plan split should be:

- Wave 1: characterization tests and source-level import contract.
- Wave 2: extract modules and update direct imports.
- Wave 3: full validation and cleanup of old module assumptions.

REF-01 is covered when all three target modules exist, moved-symbol imports use direct paths, characterization tests pass, full tests pass, xdist passes, and no import cycle appears from `python -c` direct imports of the three new modules.

## RESEARCH COMPLETE
