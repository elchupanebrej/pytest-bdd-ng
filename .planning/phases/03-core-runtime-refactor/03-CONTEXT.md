# Phase 3: Core Runtime Refactor - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Split the 1156-line `scenario_run.py` god module into three focused model modules: `model/run.py`, `model/scenario_run.py`, and `model/feature_binding.py`. Zero behavior change — pure structural refactoring.

The file contains 16 classes, 18 external importers, and implements the `RunStage` state machine that drives scenario lifecycle tracking for reporters, hooks, and diagnostics.

</domain>

<decisions>
## Implementation Decisions

## Module Boundary Placement
- The planner determines optimal class→module grouping based on dependency analysis
- ROADMAP names the target modules: `model/run.py`, `model/scenario_run.py`, `model/feature_binding.py`
- The planner MAY adjust which classes land in which module to minimize cross-module coupling
- Current class inventory (16 classes): `HookPhase`, `RunStage`, `RunStatus`, `LifecycleObjectRef`, `NoPreviousStep`, `ActiveObjectSet`, `ReportingLifecycleState`, `ReferenceResolverState`, `ContextErrorState`, `FeatureRuntimeBinding`, `Run`, `RunNode`, `StepRun`, `ScenarioRun`, `ReportingContextSnapshot`, `ExternalApiCompatibilityRecord`

## Import Migration Strategy
- Update all 18 importing files to use new module paths directly
- No backward-compatibility re-exports from old path
- `model/__init__.py` already re-exports — update its imports to pull from the 3 new submodules
- Importers: `scenario_locator.py`, `parser.py`, `hook.py`, `model/__init__.py`, `plugin/pickle_runner/{plugin,hook,entrypoint,run_transitions,run_access,api_compatibility}.py`, `plugin/scenario_test_collector/plugin.py`, `plugin/scenario_reporter/{plugin,report}.py`, `plugin/gherkin_message_reporter/{lifecycle_runtime,scenario_runtime,step_catalog_runtime,attachment_runtime}.py`, `plugin/code_generator/plugin.py`

## Characterization Test Strategy
- Write explicit characterization tests BEFORE the split (Option B — safer approach)
- Tests must snapshot specific behaviors:
  - `RunStage` transitions produce exact `ActiveObjectSet` states
  - `as_dict()` serialization output is byte-identical before/after
  - `Run.initialize_for_session()` → `apply_transition()` chain produces specific node trees
  - Import resolution: all 16 classes importable from their new paths
- Existing 6 hook/model tests + e2e suite serve as secondary verification gate
- Existing tests: `test_run_transitions.py`, `test_scenario_run_model.py`, `test_gherkin_reporter_context_lifecycle.py`, `test_reporting_context_snapshot_unit.py`, `test_run_diagnostics.py`, `test_scenario_reference_resolution.py`

## Circular Import Resolution
- Restructure class references to eliminate `Run` ↔ `FeatureRuntimeBinding` ↔ `ScenarioRun` dependency triangle
- Do NOT use `TYPE_CHECKING`-only imports as the fix — restructure the actual runtime references
- The planner determines the specific restructuring approach (protocol classes, dependency inversion, etc.)

## The Agent's Discretion
- Specific helper functions placement (e.g., `_inactive_feature_ref()`, `_finished_step_ref()`) — co-locate with the class they construct
- Type alias placement (`ScenarioRunResult`, `LifecycleKind`, `NodeKind`)
- Test file organization for characterization tests
- Order of operations: characterization tests first, then split, then import updates

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source Module
- `src/pytest_bdd/model/scenario_run.py` — The 1156-line file being split (16 classes, all state machine logic)

### State Machine Implementation
- `src/pytest_bdd/plugin/pickle_runner/run_transitions.py` — `apply_transition()` + `PHASE_TO_STAGE` mapping; primary consumer of RunStage
- `src/pytest_bdd/plugin/pickle_runner/run_access.py` — Runtime access patterns for Run/ScenarioRun

### Existing Model Tests
- `tests/hook/test_run_transitions.py` — State transition tests
- `tests/hook/test_scenario_run_model.py` — ScenarioRun construction tests
- `tests/hook/test_gherkin_reporter_context_lifecycle.py` — Lifecycle state tests
- `tests/hook/test_reporting_context_snapshot_unit.py` — Snapshot serialization tests
- `tests/hook/test_run_diagnostics.py` — Error state diagnostics
- `tests/hook/test_scenario_reference_resolution.py` — Reference resolver tests

### Module Registry
- `src/pytest_bdd/model/__init__.py` — Re-exports all model classes; must be updated to import from new submodules

### Project Patterns
- `src/pytest_bdd/model/stash_access.py` — `StashBound` base class pattern used by `Run`
- `DEVELOPMENT.rst` — Project conventions (attrs, StashBound, testing patterns)

</canonical_refs>

<specifics>
## Specific Ideas

- The `RunStage` state machine is a linear flow: `idle → scenario_setup → scenario_running ⇄ step_running → scenario_teardown → finished`
- `HookPhase` enum maps pytest-bdd hook names to stages via `PHASE_TO_STAGE` dict in `run_transitions.py`
- `FeatureRuntimeBinding` is the heaviest class (~280 lines) — handles Gherkin document binding, pickle compilation, AST node resolution
- `Run` is the second heaviest (~200 lines) — session-level state, stash binding, scenario run management
- `ScenarioRun` + `StepRun` + `RunNode` form the per-test execution tracking

</specifics>

<deferred>
## Deferred Ideas

None — scope is well-defined by REF-01.

</deferred>

---

*Phase: 03-core-runtime-refactor*
*Context gathered: 2026-05-12 via discuss-phase*
