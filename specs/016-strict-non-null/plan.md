<!-- markdownlint-disable MD013 -->

# Implementation Plan: Strict Non-Null Lifecycle Refactoring

**Branch**: `016-strict-non-null` | **Date**: 2026-03-19 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/spec.md`
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/spec.md`

**Note**: This plan is filled by the `/speckit.plan` workflow and must remain in English.

## Summary

Refactor the internal runtime lifecycle so every in-scope lifecycle accessor returns either a populated object or a dedicated Empty-State Object, never `None`, and so lifecycle invariant enforcement happens through centralized lifecycle guards rather than repeated inline absence checks. The change focuses on `Run`/`ScenarioRun`, lifecycle access helpers, reporter-facing snapshots, and parse-error emission boundaries while preserving the public pytest hook and plugin surface.

## Technical Context

**Language/Version**: Python 3.10-3.14  
**Primary Dependencies**: `attrs`, `pytest>=7`, pluggy hook system, `cucumber-messages`, `gherkin`, internal `pickle_runner` and `gherkin_message_reporter` runtime layers  
**Storage**: In-memory `Run`/`ScenarioRun`/binding state in `pytest.config.stash` plus transient reporting and parse-error payloads; no new persistent storage  
**Testing**: pytest hook/feature/contract/compatibility suites, targeted runtime unit tests, `tox`, `mypy`, `pre-commit`  
**Target Platform**: Linux/macOS/Windows CI matrix  
**Project Type**: Single Python library plus pytest plugin  
**Performance Goals**: O(1) access to active lifecycle objects at hook time; no measurable regression in targeted runtime, reporting, and contract suites; fewer normal-path conditional branches around lifecycle access  
**Constraints**: Preserve the public `run` hook argument, `run_context` fixture/stash identity, and hook/decorator symbol surface; do not use `None` as the in-scope lifecycle contract outside pytest hook implementations; define dedicated Empty-State Objects for inactive-by-design lifecycle slots; centralize lifecycle invariant enforcement through reusable guards rather than inline per-method checks  
**Scale/Scope**: Internal run/scenario/step lifecycle across `scenario_run`, `stash_access`, `run_access`, `run_transitions`, parser error emission, and reporter consumers; external schema or transport optionals remain out of primary scope unless promoted into lifecycle-managed runtime state

**Cross-Platform Validation Rule**: Non-native platform test environments MUST use the Docker skill, except Windows targets which MAY use non-Docker execution paths.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | Spec exists at `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/spec.md` with lifecycle-focused stories, explicit clarifications, FR-001..FR-013, and SC-001..SC-005. |
| II. Independent Story Increments | PASS | Stories remain separable: direct lifecycle access, explicit Empty-State Objects, and centralized invariant enforcement can be validated independently. |
| III. Validation-First Changes | PASS | Plan defines targeted runtime, feature, reporting, contract, and compatibility validation before implementation. |
| IV. Deterministic Compatibility and Contracts | PASS | Plan preserves public hook/plugin contracts while tightening internal lifecycle guarantees through dedicated design artifacts. |
| V. Task-Traceable Commits & Pre-Commit | PASS | Planning only; downstream implementation remains governed by task-traceable commits and mandatory pre-commit execution. |
| Additional Constraint: English-only documentation | PASS | Plan and generated design artifacts are written in English. |
| Additional Constraint: No routine `None` returns outside hooks | PASS | Design explicitly replaces in-scope lifecycle `None` returns with populated objects, dedicated Empty-State Objects, or deterministic boundary failures. |

**Gate Result (Pre-Design)**: PASS

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── hook-lifecycle-non-null.openapi.yaml
│   ├── reporting-lifecycle-boundary.md
│   └── hook-plugin-public-api-compatibility.md
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/
├── src/pytest_bdd/
│   ├── parser.py
│   ├── model/
│   │   ├── scenario_run.py
│   │   └── stash_access.py
│   └── plugin/
│       ├── pickle_runner/
│       │   ├── api_compatibility.py
│       │   ├── hook.py
│       │   ├── plugin.py
│       │   ├── run_access.py
│       │   └── run_transitions.py
│       ├── scenario_reporter/
│       │   └── plugin.py
│       ├── allure_logger/
│       │   └── plugin.py
│       ├── scenario_test_collector/
│       │   └── plugin.py
│       └── gherkin_message_reporter/
│           ├── hook.py
│           ├── lifecycle_runtime.py
│           └── scenario_runtime.py
└── tests/
    ├── compatibility/
    ├── contract/
    ├── feature/
    └── hook/
```

**Structure Decision**: Keep the existing single-project layout. Implement the strict non-null rules in the core runtime model and lifecycle access layer first, then align parser/reporting consumers and preserve the public hook/plugin contract through explicit contract artifacts and targeted regression suites.

## Phase 0: Outline & Research

No `NEEDS CLARIFICATION` markers remain in the technical context.

Research tasks generated from dependencies and integrations:

1. Research how to model dedicated Empty-State Objects for inactive-by-design lifecycle slots without widening public hook contracts.
2. Research centralized lifecycle guard patterns for enforcing non-null invariants at runtime boundaries rather than inside consumer methods.
3. Research reporting and parse-error boundary patterns that keep lifecycle contracts deterministic without `None`-driven fallback logic.
4. Research compatibility-safe strategies for tightening `Run`/`ScenarioRun` invariants while keeping public hook and decorator symbols stable.

**Output**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/research.md`

## Phase 1: Design & Contracts

1. Define runtime entities, dedicated Empty-State Objects, lifecycle guards, validation rules, and stage transitions in `data-model.md`.
2. Define design-time contracts for hook-visible lifecycle guarantees, reporter-facing lifecycle boundaries, and public hook/plugin compatibility under `contracts/`.
3. Define a validation quickstart covering stash identity, lifecycle transitions, Empty-State Object behavior, centralized guard enforcement, and compatibility checks in `quickstart.md`.
4. Update agent context by running `.specify/scripts/bash/update-agent-context.sh codex`.

**Outputs**:

- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/data-model.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/contracts/hook-lifecycle-non-null.openapi.yaml`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/contracts/reporting-lifecycle-boundary.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/contracts/hook-plugin-public-api-compatibility.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/quickstart.md`

## Post-Design Constitution Check

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | Research and design artifacts map directly to the clarified spec requirements for populated lifecycle access, dedicated Empty-State Objects, and centralized lifecycle guards. |
| II. Independent Story Increments | PASS | Data model and contracts isolate runtime access, exceptional empty-state behavior, and invariant enforcement into independently testable areas. |
| III. Validation-First Changes | PASS | Quickstart defines executable runtime, feature, reporting, contract, and compatibility validation before implementation. |
| IV. Deterministic Compatibility and Contracts | PASS | Contract artifacts keep public hook/plugin guarantees explicit while documenting internal lifecycle guard and Empty-State Object rules. |
| V. Task-Traceable Commits & Pre-Commit | PASS | Planning artifacts are complete; downstream implementation remains governed by tasks, validation evidence, and pre-commit enforcement. |
| Additional Constraint: English-only documentation | PASS | All generated planning/design artifacts remain in English. |
| Additional Constraint: No routine `None` returns outside hooks | PASS | Data model and contracts define dedicated Empty-State Objects and deterministic lifecycle guards instead of nullable steady-state access. |

**Gate Result (Post-Design)**: PASS

## Complexity Tracking

No constitution violations detected. No exceptions required.
