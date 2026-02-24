<!-- markdownlint-disable MD013 -->

# Implementation Plan: Unified Test Run Context Model

**Branch**: `003-unify-run-context` | **Date**: 2026-02-24 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/003-unify-run-context/spec.md`
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/003-unify-run-context/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.
**Documentation Language Rule**: This plan and generated feature artifacts MUST be written in English.

## Summary

Introduce a session-root execution context hierarchy that is initialized at `pytest_sessionstart`, exposed as a session-scoped fixture, and stored canonically in `pytest.config.stash`. Hook parameter models must access `execution_context` as an embedded field/reference, while reporting paths must consume the same hierarchy when context is available. External API evolution remains additive-only and backward compatible.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: pytest, pluggy hook system, cucumber-messages models, pytest-bdd runtime/plugin layers
**Storage**: In-memory runtime context graph + canonical `pytest.config.stash` entry (no persistent storage)
**Testing**: pytest unit/feature/contract/compatibility/e2e suites, tox matrix, pre-commit
**Target Platform**: Linux/macOS/Windows CI matrix
**Project Type**: Single Python library + pytest plugin
**Performance Goals**: O(1) lookup for session context from fixture/stash/hook-parameter field access; no measurable regression in runtime test suites
**Constraints**: Additive-only external API changes; no public hook API removals/renames; deterministic lifecycle transitions; `SessionExecutionContext` initialized at `pytest_sessionstart`; fixture and stash references must remain identical for one session; reporting must rely on hierarchy with graceful fallback
**Scale/Scope**: Session-level lifecycle across hundreds to low-thousands of scenarios per run

**Cross-Platform Validation Rule**: Non-native platform test environments MUST use the Docker skill, except Windows targets which MAY use non-Docker execution paths.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | Spec exists at `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/003-unify-run-context/spec.md` with FR-001..FR-016 and SC-001..SC-006. |
| II. Independent Story Increments | PASS | Stories remain separable: hook context access, hierarchy lifecycle tracking, diagnostics/compatibility/reporting integration. |
| III. Validation-First Changes | PASS | Plan defines executable validation across contract, compatibility, feature, hook, and e2e suites. |
| IV. Deterministic Compatibility and Contracts | PASS | Contract and compatibility requirements explicitly enforce deterministic behavior and additive-only API evolution. |
| V. Task-Traceable Commits & Pre-Commit | PASS | Planning artifacts define validation evidence requirements; implementation workflow remains constrained by constitution rules. |
| Additional Constraint: English-only documentation | PASS | Plan and generated artifacts are written in English. |

**Gate Result (Pre-Design)**: PASS

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/003-unify-run-context/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── hook-execution-context.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/
├── src/pytest_bdd/
│   ├── model/
│   │   ├── execution_context.py
│   │   ├── hook_parameter_model.py
│   │   ├── gherkin_document/
│   │   │   ├── __init__.py
│   │   │   ├── core.py
│   │   │   ├── registry.py
│   │   │   └── lookup.py
│   ├── hook.py
│   └── plugin/scenario_runner/
│       ├── api_compatibility.py
│       ├── context_access.py
│       ├── context_store.py
│       ├── context_transitions.py
│       └── plugin.py
└── tests/
    ├── contract/
    ├── compatibility/
    ├── feature/
    ├── hook/
    ├── struct_bdd/
    └── e2e/
```

**Structure Decision**: Keep single-project structure and implement session-root context fixture/stash wiring in scenario-runner runtime modules, model contracts in `src/pytest_bdd/model/`, and validation coverage in existing test suites.

## Phase 0: Outline & Research

No `NEEDS CLARIFICATION` markers remain in Technical Context.

Research tasks generated from dependencies and integrations:

1. Research best practices for initializing session-scoped runtime context at `pytest_sessionstart`.
2. Research best practices for canonical session object sharing via `pytest.config.stash` and fixture access.
3. Research patterns for propagating context hierarchy into reporting without introducing breaking API changes.
4. Research compatibility guard strategy for additive-only API checks.

**Output**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/003-unify-run-context/research.md`

## Phase 1: Design & Contracts

1. Define entities and invariants for session fixture/stash binding and reporting snapshot consumption in `data-model.md`.
2. Extend design-time contract in `contracts/hook-execution-context.openapi.yaml` with fixture/stash/reporting hierarchy endpoints and schemas.
3. Define validation flow in `quickstart.md` for fixture injection timing, stash consistency, and reporting hierarchy usage.
4. Update agent context by running `.specify/scripts/bash/update-agent-context.sh codex`.

**Outputs**:

- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/003-unify-run-context/data-model.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/003-unify-run-context/contracts/hook-execution-context.openapi.yaml`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/003-unify-run-context/quickstart.md`

## Post-Design Constitution Check

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | Design artifacts map directly to FR-001..FR-016 and SC-001..SC-006, including fixture/stash/reporting requirements. |
| II. Independent Story Increments | PASS | Design keeps hook access, lifecycle tracking, and diagnostics/reporting compatibility independently testable. |
| III. Validation-First Changes | PASS | Quickstart includes executable validation scenarios for fixture initialization, stash linkage, contract, compatibility, and e2e checks. |
| IV. Deterministic Compatibility and Contracts | PASS | Contract explicitly models session-root hierarchy, stash access path, and additive compatibility constraints. |
| V. Task-Traceable Commits & Pre-Commit | PASS | No implementation commit in planning; downstream execution remains bound to task-traceable commits and pre-commit enforcement. |
| Additional Constraint: English-only documentation | PASS | All planning/design artifacts are in English. |

**Gate Result (Post-Design)**: PASS

## Complexity Tracking

No constitution violations detected. No exceptions required.
