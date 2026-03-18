# Implementation Plan: Replace extended_step_context with StepRun

**Branch**: `015-replace-step-context` | **Date**: 2026-03-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/015-replace-step-context/spec.md`

## Summary

The feature introduces a new `StepRun` class to encapsulate the execution context of a step and exposes it via `run.scenario_run.step_run`. All usages of the legacy `extended_step_context` will be completely removed. This establishes a unified, predictable way to access runtime state.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: `pytest>=7`, `pytest-bdd-ng` internal core
**Testing**: `pytest`, `tox>=4.2`
**Target Platform**: Linux, macOS, Windows
**Project Type**: Python library/plugin
**Constraints**: Must maintain compatibility with existing `pytest-bdd` workflows (excluding the explicit removal of `extended_step_context`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec-Driven Delivery**: Yes, spec is defined.
- **Independent Story Increments**: Yes, this is a single, cohesive architectural change.
- **Validation-First Changes**: Yes, changes will be covered by existing test suites ensuring context works properly.
- **Deterministic Compatibility and Contracts**: `extended_step_context` is explicitly removed as a breaking internal API change in favor of the new contract `run.scenario_run.step_run`.
- **Task-Traceable Commits**: Will follow this protocol during implementation.

## Project Structure

### Documentation (this feature)

```text
specs/015-replace-step-context/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/pytest_bdd/
├── context.py / models.py   # Where StepRun and ScenarioRun are defined
├── plugin.py                # Where hooks manage the execution context
├── steps.py                 # Where steps access their context
└── ...

tests/
├── ...                      # Existing tests updated to use the new context
```

**Structure Decision**: Standard Python library structure within the `pytest-bdd-ng` codebase. The modifications will mostly target the runtime context and step execution components.

## Complexity Tracking

None.