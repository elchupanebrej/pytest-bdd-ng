# ADR-010: Pickle Runner Isolation with Per-Scenario State Machine

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** pytest-bdd-ng core team

## Context

Each Gherkin scenario execution must be fully isolated — step failures, fixture teardowns, or state mutations in one scenario must never affect another scenario within the same test module. pytest-bdd-ng's `pickle_runner` plugin orchestrates scenario execution by dispatching pickle steps through pytest's hook system and managing execution state transitions (setup → step_dispatch → teardown → complete).

The original implementation stored scenario execution state in a shared `Run` object, with individual scenarios tracked via nested dictionaries indexed by pickle ID. This created several problems:

- **State leakage:** A failing step in scenario A could leave the `Run` object in a stale state, causing scenario B to skip setup or execute with incorrect context.
- **Weak isolation guarantees:** Teardown hooks for scenario A could observe or mutate state from scenario B when scenarios share the same `Run` container.
- **Debugging complexity:** Tracing individual scenario state required navigating deeply nested dictionary structures with implicit lifecycle transitions.

## Decision

Adopt a **per-scenario state machine** using `ScenarioRun` with explicit `RunStage` transitions, and delegate step dispatch to `pickle_runner`:

1. **`ScenarioRun`** (in `model/scenario_run.py`) is a stateful object representing exactly one scenario execution attempt. It holds:
   - `stage: RunStage` — current lifecycle stage (Active, BeforeStep, AfterStep, Teardown, Complete)
   - `feature: FeatureRuntimeBinding` — resolved feature binding for the scenario
   - `pickle: Pickle` — the Gherkin pickle being executed
   - `step_run: StepRun | None` — the currently executing step (None between steps)
   - `result: ScenarioRunResult | None` — execution outcome (populated at Complete)

2. **`Run`** (in `model/run/lifecycle.py`) manages the collection of `ScenarioRun` instances:
   - `scenario_runs: dict[str, ScenarioRun]` — keyed by pickle ID
   - `create_scenario_run(pickle, feature_binding) -> ScenarioRun` — factory method
   - `pop_scenario_run(pickle_id) -> ScenarioRun` — cleanup and retrieval
   - `active_run -> ScenarioRun | None` — the currently executing scenario

3. **`pickle_runner/plugin.py`** owns step dispatch:
   - `_dispatch_step(scenario_run, step, hook_context)` — resolves step definition, executes via pytest hook, records outcome
   - `apply_transition(scenario_run, transition)` — state machine transition logic (from `run_transitions.py`, already extracted)
   - Hook implementations (`pytest_runtest_setup`, `pytest_runtest_call`) delegate to the dispatch layer

4. **Isolation guarantees:**
   - `ScenarioRun` objects never share mutable state — each is independently created and destroyed
   - `Run.pop_scenario_run()` ensures complete cleanup (including `RunStage.Complete` transition) before the next scenario begins
   - Step dispatch always reads from `/` writes to the current `ScenarioRun`, never the parent `Run`

## Consequences

### Positive

- **Guaranteed isolation:** Each `ScenarioRun` is a self-contained unit of execution. Step failure in scenario A cannot corrupt scenario B's state.
- **Clean teardown:** `pop_scenario_run()` enforces a complete lifecycle (setup → dispatch → teardown → complete) before the object is removed, preventing resource leaks.
- **Traceable execution:** `ScenarioRun.stage` + `scenario_runs` dict provide a clear audit trail. Tools can dump the entire `Run` state at any point for debugging.
- **Testable in isolation:** `ScenarioRun` can be unit-tested independently — create a `ScenarioRun`, dispatch steps, assert stage transitions.

### Negative

- **Explicit state management:** Every scenario lifecycle transition requires an explicit call. Missing a transition (e.g., forgetting to call `pop_scenario_run()`) leaves orphaned state.
- **Memory overhead:** Each `ScenarioRun` holds a full copy of the `Pickle`, `FeatureRuntimeBinding`, and hook context — this is bounded (one active scenario at a time via `active_run`) but larger than the previous shared-dict approach.
- **Lock-stepping risk:** If `pickle_runner` fails to complete a `ScenarioRun` (e.g., due to an unhandled exception in teardown), subsequent scenarios in the same test module may be skipped. The `Run.pop_scenario_run()` provides a `force` parameter for emergency cleanup.

### Neutral

- **`pickle_runner/plugin.py` remains the dispatch owner:** The plugin is already structured for this role; the decision formalizes existing implicit ownership.
- **`run_transitions.py` already extracted:** The transition logic is already in its own module (Phase 11 refactoring). This ADR does not require creating new modules — it formalizes the existing architecture.
- **No user-visible API change:** `scenario()` and `scenarios()` continue to work identically. The state machine is internal to the pickle runner.

## References

- `src/pytest_bdd/model/scenario_run.py` — `ScenarioRun` and `StepRun` classes
- `src/pytest_bdd/model/run/lifecycle.py` — `Run` with `create_scenario_run()` and `pop_scenario_run()`
- `src/pytest_bdd/plugin/pickle_runner/plugin.py` — step dispatch and hook implementations
- `src/pytest_bdd/plugin/pickle_runner/run_transitions.py` — `apply_transition()` state machine
- ADR-008 — pytest config stash state pattern (used by `Run` for session-level state)
