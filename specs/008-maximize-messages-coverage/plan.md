# Implementation Plan: Maximize Messages Capability Coverage

**Branch**: `[008-maximize-messages-coverage]` | **Date**: 2026-03-03 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/spec.md`
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/spec.md`

## Summary

Deliver a runtime-pure reporting model where the reporter emits only real events, then evaluate capability coverage and governance post-factum from NDJSON. Expand runtime reporting to extract all fields realistically available from Python runtime and pytest-bdd hook surfaces (including hook metadata, testcase/run linkage, parse/lookup error signals, and source references), and allow `Non-Implementable` only for objectively unreachable capabilities with hard technical proof and explicit recheck triggers.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: `pytest>=6.2.5`, `pluggy`, `cucumber-messages`, `jsonschema`, `PyYAML`
**Storage**: N/A (in-memory runtime state + file artifacts: NDJSON/JSON/YAML under repository and temporary paths)
**Testing**: `pytest`, `tox>=4.2`, contract tests, dedicated `tests/messages_coverage` suite, end-to-end tests in `tests/e2e`
**Target Platform**: Linux/macOS CI and local developer environments (Windows compatibility remains supported by project matrix)
**Project Type**: Python library + pytest plugin + CLI tooling
**Performance Goals**: Dedicated coverage/governance audit completes within standard CI job budgets and produces deterministic governance output for one release target in a single run
**Constraints**: Reporter MUST not inject synthetic/test-only payloads; runtime-required set MUST include all capabilities extractable via real Python runtime/hook surfaces; `Non-Implementable` is valid only with hard technical impossibility proof
**Scale/Scope**: 323 mandatory-governance capability IDs for release scope; runtime-required subset maintained per release cycle; weekly baseline drift comparison

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Delivery | PASS | Spec exists with clarified requirements and acceptance criteria in `spec.md`. |
| II. Independent Story Increments | PASS | Scope remains separable into inventory, runtime mapping visibility, and governance readiness increments. |
| III. Validation-First Changes | PASS | Plan includes executable validation in unit/contract/messages coverage/e2e suites. |
| IV. Deterministic Compatibility and Contracts | PASS | Governance contracts are versioned in `contracts/` and validated by tests. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | PASS | Implementation phase will enforce task-linked commits and pre-commit clean state per constitution. |

### Post-Design Gate (Re-check)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Delivery | PASS | `research.md`, `data-model.md`, `contracts/`, and `quickstart.md` implement clarified spec constraints. |
| II. Independent Story Increments | PASS | Runtime extraction, governance analysis, and release gating remain independently testable slices. |
| III. Validation-First Changes | PASS | Contracts and quickstart define executable verification flow and fail-fast gates. |
| IV. Deterministic Compatibility and Contracts | PASS | Deterministic set-based gate model and schemas are explicitly documented. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | PASS | No design-level exceptions required; implementation remains bound to commit/pre-commit policy. |

No constitution violations requiring complexity exceptions were identified.

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/
├── model/
│   ├── coverage/
│   ├── message_capability_inventory.py
│   ├── message_status_governance.py
│   └── message_validation.py
├── plugin/
│   └── gherkin_message_reporter/
└── script/
    └── message_capability_governance.py

/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/
├── contract/
├── e2e/
├── messages/
└── messages_coverage/
```

**Structure Decision**: Keep the existing single-package library/plugin layout and implement feature behavior by extending current model, reporter plugin, governance CLI, and dedicated coverage suites; no new top-level project split is needed.

## Complexity Tracking

No constitution exceptions or additional complexity justifications are required for this feature.
