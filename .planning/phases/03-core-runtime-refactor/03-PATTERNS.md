# Phase 03: Pattern Map

**Phase:** 03 - Core Runtime Refactor
**Date:** 2026-05-12

## Target Files And Closest Analogs

| Target | Role | Closest Existing Analog | Pattern To Preserve |
|--------|------|-------------------------|---------------------|
| `src/pytest_bdd/model/run.py` | Session/root runtime model and shared lifecycle values | `src/pytest_bdd/model/scenario_run.py`, `src/pytest_bdd/model/stash_access.py` | `@define(slots=True)`, `StashBound`, `ClassVar STASH_KEY`, `Nothing.value_or(None)` at optional boundaries |
| `src/pytest_bdd/model/feature_binding.py` | Feature document/pickle runtime binding | `FeatureRuntimeBinding` in `src/pytest_bdd/model/scenario_run.py` | Runtime registry owned by `Run`; no `Feature` adapter; compile pickles via `PicklesCompiler` |
| `src/pytest_bdd/model/scenario_run.py` | Scenario-only runtime model | Existing `ScenarioRun`, `RunNode`, `StepRun` classes | Per-scenario active refs, `set_active_set()`, `record_context_error()`, `as_dict()` shape |
| `tests/hook/test_scenario_run_characterization.py` | Pre-split behavior lock | `tests/hook/test_run_transitions.py`, `tests/hook/test_run_scenario_runtime_unit.py` | Inline `_Dummy`/`SimpleNamespace` factories, exact assertions, no heavy mocking |
| `src/pytest_bdd/model/__init__.py` | Package re-export registry | Existing `model/__init__.py` | Import concrete symbols from owning modules, keep `__all__` stable |

## Data Flow

1. `plugin/pickle_runner/plugin.py` initializes `Run` and creates `ScenarioRun`.
2. `Run.create_scenario_run()` creates feature/scenario nodes and calls `Run.ensure_feature_binding()` when a `GherkinDocument` exists.
3. `FeatureRuntimeBinding.ensure_pickles()` compiles pickles and indexes objects through `Run.index_identifiable_tree()`.
4. `plugin/pickle_runner/run_transitions.py` mutates `ScenarioRun` through `apply_transition()`.
5. `plugin/pickle_runner/run_access.py` and reporters read `Run`, `ScenarioRun`, `ActiveObjectSet`, and `ReportingContextSnapshot`.

## Concrete Code Patterns

### StashBound Root

Use the existing `Run` pattern unchanged:

```python
@define(slots=True)
class Run(StashBound):
    STASH_KEY: ClassVar[str] = "_pytest_bdd_run"
```

Keep stash access through `initialize_in_stash()`, `set_in_stash()`, `from_stash()`, and `find_in_stash()`.

### attrs Model Classes

All moved classes must keep `attrs`:

```python
@define(slots=True)
class LifecycleObjectRef:
    kind: LifecycleKind
    object_id: str
```

Do not introduce stdlib `dataclass`.

### Optional Boundary

Phase 02 established `returns` usage. Preserve public optional boundaries by returning `Nothing.value_or(None)` where the current behavior returns `None`:

```python
if uri is None:
    return Nothing.value_or(None)
```

Do not convert additional APIs to new `Maybe`/`Result` surfaces in this refactor unless required by existing behavior.

### Lazy Transition Import

Preserve the existing lazy import in `Run.create_scenario_run()`:

```python
from pytest_bdd.plugin.pickle_runner.run_transitions import (
    build_lifecycle_ref,
    initial_scenario_run_id,
    runtime_object_id,
)
```

This prevents the model split from creating an eager import cycle with transition helpers.

## Import Rewrite Map

| Symbol Group | New Import |
|--------------|------------|
| `Run`, `HookPhase`, `RunStage`, `RunStatus`, `LifecycleObjectRef`, `ActiveObjectSet`, `ReportingContextSnapshot`, `ContextErrorState`, `ExternalApiCompatibilityRecord` | `pytest_bdd.model.run` |
| `FeatureRuntimeBinding` | `pytest_bdd.model.feature_binding` |
| `RunNode`, `StepRun`, `ScenarioRun` | `pytest_bdd.model.scenario_run` |

## Landmines

- Do not keep `Run` or `FeatureRuntimeBinding` re-exported from `pytest_bdd.model.scenario_run`; Phase 03 explicitly wants direct new paths.
- Do not move `apply_transition()` into model modules; that would expand scope and risk lifecycle behavior changes.
- Do not remove `Nothing.value_or(None)` public boundary conversions inherited from Phase 02.
- Do not touch parser behavior; parser changes are outside Phase 03.
- Run xdist smoke because `Run` state is session/worker scoped.

## PATTERN MAPPING COMPLETE
