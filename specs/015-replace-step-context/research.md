# Research: Replace extended_step_context with StepRun

## Decisions

### 1. Introduction of `StepRun` class

- **Decision**: Introduce a `StepRun` dataclass or attr class to encapsulate step execution state.
- **Rationale**: `extended_step_context` was previously used as a global or thread-local dict/object to hold step context. Moving to `run.scenario_run.step_run` provides a clearer, strongly typed, and hierarchical representation of execution state (`Run` -> `ScenarioRun` -> `StepRun`).
- **Alternatives considered**: Modifying `extended_step_context` in place, but that wouldn't fix the architectural disconnect from `Run`/`ScenarioRun`.

### 2. Location of `step_run` attribute

- **Decision**: Add `step_run` field to the existing `ScenarioRun` context.
- **Rationale**: The execution model currently tracks the active scenario in `run.scenario_run`. Since steps are children of scenarios, tracking the active step inside the active scenario run makes logical sense and ensures proper lifecycle management (isolation per scenario run).
- **Alternatives considered**: Attaching it directly to `pytest` config stash, but that bypasses the existing `ScenarioRun` hierarchy.

### 3. Removal of `extended_step_context`

- **Decision**: Completely remove `extended_step_context` and replace all internal references with `request.stash.get(RUN_KEY).scenario_run.step_run` (or similar depending on how `run` is accessed).
- **Rationale**: Prevents having two sources of truth for the step context, simplifying the codebase and reducing potential bugs.
- **Alternatives considered**: Keeping it as an alias for backwards compatibility. However, the requirement explicitly states "completely remove the usage", so it must be removed.