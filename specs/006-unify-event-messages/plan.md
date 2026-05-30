<!-- markdownlint-disable MD013 -->

# Implementation Plan: Unify Event Message Reporting

**Branch**: `006-unify-event-messages` | **Date**: 2026-02-25 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/006-unify-event-messages/spec.md`
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/006-unify-event-messages/spec.md`

**Documentation Language Rule**: This plan and generated feature artifacts MUST be written in English.

## Summary

Unify reporting around one canonical Cucumber message event stream, remove inconsistent parallel event-construction paths, keep legacy/user-facing outputs derived from canonical events, enforce attempt-level correlation identity, validate message construction via MyPy, and fix duplicate spec-prefix handling so prerequisite scripts resolve one active feature directory deterministically.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: pytest>=6.2.5, pluggy hook system, cucumber-messages models/converter, pytest-bdd reporter/runtime plugins, mypy, tox>=4.2, pre-commit
**Storage**: In-memory runtime state + NDJSON report artifacts + repository `specs/` directory metadata
**Testing**: pytest (messages/feature/hook/compatibility), mypy checks through tox matrix envs, pre-commit hooks
**Target Platform**: Linux/macOS/Windows local development and CI
**Project Type**: Single Python library + pytest plugin/reporting tooling
**Performance Goals**: No dropped lifecycle events in validated runs; targeted reporting validation suite runtime with reporting enabled stays within <=10% wall-clock overhead versus the same suite with reporting disabled in the same environment.
**Constraints**: Canonical message stream is the only source of truth; legacy and user-facing outputs must derive from canonical events; fail on emission/serialization only when message reporting is enabled; correlation IDs must be unique per execution attempt (including retries/parallel workers); latest message protocol version only; spec prefixes must be unique and monotonic for new features
**Scale/Scope**: Reporting and message-construction paths under `src/pytest_bdd/plugin/` and `src/pytest_bdd/model/`, validation coverage in `tests/messages/`, `tests/feature/`, `tests/hook/`, and spec-catalog hygiene for `specs/`

**Cross-Platform Validation Rule**: Non-native platform test environments MUST use the Docker skill, except Windows targets which MAY use non-Docker execution paths.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | Active feature spec exists at `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/006-unify-event-messages/spec.md` with accepted clarifications and FR-001..FR-017. |
| II. Independent Story Increments | PASS | Stories remain independently implementable: canonical lifecycle emission, consistency/ordering unification, and type-validation hardening. |
| III. Validation-First Changes | PASS | Plan includes explicit contract, data model, quickstart validation, and MyPy/reporting checks before implementation completion. |
| IV. Deterministic Compatibility and Contracts | PASS | Message protocol scope, lifecycle linkage rules, and deterministic prefix-resolution behavior are explicitly constrained. |
| V. Task-Traceable Commits & Pre-Commit | PASS | Plan preserves requirement for task-linked commits and pre-commit enforcement during implementation. |
| Additional Constraint: English-only documentation | PASS | Plan and generated planning artifacts are written in English. |

**Gate Result (Pre-Design)**: PASS

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/006-unify-event-messages/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── event-message-reporting.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/
├── src/pytest_bdd/
│   ├── model/
│   │   ├── message_converter.py
│   │   └── message_extension.py
│   └── plugin/
│       ├── gherkin_message_reporter/
│       ├── gherkin_terminal_reporter/
│       └── scenario_reporter/
├── tests/
│   ├── messages/
│   ├── feature/
│   ├── hook/
│   └── compatibility/
└── specs/
```

**Structure Decision**: Keep existing single-project pytest plugin structure; implement canonical message consistency in current reporter/model modules and validate through existing targeted test suites plus spec-prefix hygiene checks.

## Phase 0: Outline & Research

Research tasks generated from dependencies, integrations, and clarified constraints:

1. Research canonical event ownership boundaries between `gherkin_message_reporter`, `scenario_reporter`, and user-facing reporter outputs.
2. Research robust attempt-level correlation identifier strategy for retries and parallel workers.
3. Research best-practice failure policy for message emission/serialization when reporting is enabled versus disabled.
4. Research MyPy-hardening approach for message construction (minimizing `type: ignore` masking in message paths).
5. Research protocol-version policy implications for latest-only message compatibility validation.
6. Research deterministic spec-prefix conflict resolution workflow so plan/spec scripts select one active feature directory per prefix.

**Phase 0 Output**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/006-unify-event-messages/research.md`

## Phase 1: Design & Contracts

1. Model canonical reporting entities, lifecycle transitions, correlation/uniqueness rules, and spec-catalog prefix governance in `data-model.md`.
2. Define design-time contract in `contracts/event-message-reporting.openapi.yaml` for event stream validation, output derivation consistency, and prefix-conflict audit operations.
3. Define reproducible verification workflow in `quickstart.md` covering message stream tests, MyPy validation, and prerequisite/prefix conflict checks.
4. Update agent context via `SPECIFY_FEATURE=006-unify-event-messages /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.specify/scripts/bash/update-agent-context.sh codex`.

**Phase 1 Outputs**:

- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/006-unify-event-messages/data-model.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/006-unify-event-messages/contracts/event-message-reporting.openapi.yaml`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/006-unify-event-messages/quickstart.md`

## Post-Design Constitution Check

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | Research, data model, contract, and quickstart artifacts map directly to FR-001..FR-017 and SC-001..SC-008. |
| II. Independent Story Increments | PASS | Artifact boundaries preserve independent implementation/testing across lifecycle emission, consistency, and type-validation goals. |
| III. Validation-First Changes | PASS | Quickstart and contract define executable validation steps for reporting behavior and type checks. |
| IV. Deterministic Compatibility and Contracts | PASS | Contract captures deterministic lifecycle, correlation, protocol-version scope, and prefix-audit behavior. |
| V. Task-Traceable Commits & Pre-Commit | PASS | Plan artifacts preserve constitution requirements for task-ID commits and pre-commit gating in implementation. |
| Additional Constraint: English-only documentation | PASS | All generated planning artifacts remain in English. |

**Gate Result (Post-Design)**: PASS

## Complexity Tracking

No constitution violations detected. No exceptions required.
