# Data Model: StepRun

## Entities

### `StepRun`

Represents the runtime execution context of a single Gherkin step.

**Attributes:**
- `step` (or similar metadata reference): Reference to the AST node or step definition representing the step being executed.
- `keyword`: The keyword used (e.g., "Given", "When", "Then").
- `text`: The text of the step.
- `parameters`: Parsed parameters from the step text.
- `status`: Execution status (e.g., pending, passed, failed, skipped).
- `duration`: Execution time (if applicable/tracked).
- `attachments`: List of attachments (if applicable).

### `ScenarioRun` (Existing)

Updates to existing entity:
- Add `step_run`: Optional[`StepRun`] - References the currently executing step, or `None` if no step is currently active within the scenario.

## Relationships

- A `ScenarioRun` has zero or one active `StepRun` at any given time during its execution.
- A `StepRun` is strictly scoped to a single `ScenarioRun`.

## State Transitions

- **Start of Step**: A new `StepRun` instance is created and assigned to `scenario_run.step_run`.
- **End of Step**: `scenario_run.step_run` may be set to `None` or preserved for reporting purposes until the next step begins, depending on the implementation pattern, but conceptually the active step has ended.

## Validation Rules

- `step_run` should be correctly populated before any step-level hooks or step functions are invoked.
- `step_run` should accurately reflect the parameters and text of the currently executing step.