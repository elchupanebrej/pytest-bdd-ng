# Feature Specification: Replace extended_step_context with StepRun

**Feature Branch**: `015-replace-step-context`
**Created**: 2026-03-18
**Status**: Draft
**Input**: User description: "extended_step_context не должен быть больше использован, вместо него должно появиться и использоваться поле run.scenario_run.step_run и новый класс StepRun - по сути контекст выполнения шага"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Expose Step Execution Context via StepRun (Priority: P1)

As a framework user writing step definitions or plugins, I need to access the current step's execution context through a dedicated `StepRun` object available at `run.scenario_run.step_run`, rather than the old `extended_step_context`.

**Why this priority**: It establishes a clear, unified, and predictable way to access the runtime state of a step, improving the extension capabilities and reliability.

**Independent Test**: Can be tested by executing a suite with multiple steps and verifying that a hook or fixture accessing `run.scenario_run.step_run` receives an object that accurately reflects the properties of the currently executing step, and that `extended_step_context` is no longer available.

**Acceptance Scenarios**:

1. **Given** a scenario with multiple steps is executing, **When** a step is currently running, **Then** `run.scenario_run.step_run` provides an instance representing that specific step's context.
2. **Given** a step has completed execution, **When** the next step begins, **Then** `run.scenario_run.step_run` is updated to reflect the new step's context.
3. **Given** a plugin attempts to use `extended_step_context`, **When** accessing it, **Then** the context should not be available, ensuring the complete removal of the legacy context.

---

### Edge Cases

- What happens when accessing `run.scenario_run.step_run` outside of a step execution (e.g., in a before/after scenario hook)? The system should clearly define its state (e.g., as `None` or an empty state).
- How does `StepRun` behave if a step fails or is skipped? The context should remain available and accurately reflect the step's details and status up to the point of failure or skip.
- Does `StepRun` properly encapsulate data for steps executed in parallel? It should ensure thread/process safety and isolation per scenario run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define a new conceptual entity `StepRun` that encapsulates the execution context of a single step.
- **FR-002**: System MUST provide access to the current `StepRun` instance via `run.scenario_run.step_run` during step execution.
- **FR-003**: System MUST sequentially update `run.scenario_run.step_run` as execution transitions from one step to the next within a scenario.
- **FR-004**: System MUST completely remove the usage of `extended_step_context` across all execution paths.
- **FR-005**: System MUST ensure that `StepRun` provides access to necessary step details (e.g., step text, keyword, parsed parameters, attachments).
- **FR-006**: System MUST handle the state of `run.scenario_run.step_run` gracefully when no step is executing.

### Key Entities *(include if feature involves data)*

- **StepRun**: Represents the runtime context of a specific step being executed. Contains step metadata, parameter values, execution status, and any step-scoped state.
- **ScenarioRun**: The existing entity representing a scenario's execution, updated to hold a reference to the currently executing `StepRun`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of internal codebase references to `extended_step_context` are removed.
- **SC-002**: All existing test suites pass with the new `StepRun` implementation, ensuring zero regressions in core capabilities.
- **SC-003**: System provides step context to hooks/plugins successfully without relying on any deprecated workarounds.
