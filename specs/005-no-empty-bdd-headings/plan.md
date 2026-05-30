<!-- markdownlint-disable MD013 -->

# Implementation Plan: Enforce Non-empty BDD Headings

**Branch**: `005-no-empty-bdd-headings` | **Date**: 2026-02-25 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/005-no-empty-bdd-headings/spec.md`
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/005-no-empty-bdd-headings/spec.md`

**Documentation Language Rule**: This plan and generated feature artifacts MUST be written in English.

## Summary

Prevent empty parsed BDD titles in repository feature documents by enforcing validation over `features/` for `Feature`, `Scenario`, and `Scenario Outline` headings, normalizing existing repository files to comply, and preserving scope so only parsed headings are enforced (not literal snippet content).

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: pytest>=6.2.5, pytest-bdd parser/runtime layers, gherkin markdown token matcher, pre-commit, tox>=4.2
**Storage**: N/A (in-repo text files and validation diagnostics only)
**Testing**: pytest unit/feature/contract/doc suites, pre-commit hooks, targeted tox matrix slice
**Target Platform**: Linux/macOS/Windows development and CI environments
**Project Type**: Single Python library + CLI/plugin tooling
**Performance Goals**: Repository-wide heading validation completes within standard contributor feedback loop and emits deterministic diagnostics in one pass
**Constraints**: Detect only parsed headings, treat whitespace-only titles as empty, report file+line+heading type, fail validation on violations, avoid false positives from non-parsed code/literal snippets
**Scale/Scope**: All documents under `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/` (current baseline plus future additions)

**Cross-Platform Validation Rule**: Non-native platform test environments MUST use the Docker skill, except Windows targets which MAY use non-Docker execution paths.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | Spec exists at `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/005-no-empty-bdd-headings/spec.md` with FR-001..FR-007 and SC-001..SC-004. |
| II. Independent Story Increments | PASS | Stories remain independent: validation enforcement, baseline cleanup, and false-positive boundary protection. |
| III. Validation-First Changes | PASS | Plan includes contract, parser-focused, and repository-baseline validation steps before implementation completion. |
| IV. Deterministic Compatibility and Contracts | PASS | Validation policy and diagnostics contract are explicit and deterministic. |
| V. Task-Traceable Commits & Pre-Commit | PASS | Planning preserves mandatory task-ID commit linkage and pre-commit enforcement for implementation phase. |
| Additional Constraint: English-only documentation | PASS | Plan and generated planning artifacts are written in English. |

**Gate Result (Pre-Design)**: PASS

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/005-no-empty-bdd-headings/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── empty-heading-validation.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/
├── src/pytest_bdd/
│   ├── script/
│   ├── model/
│   ├── plugin/
│   └── util/
├── features/
└── tests/
    ├── contract/
    ├── feature/
    ├── hook/
    └── doc/
```

**Structure Decision**: Keep existing single-project layout, implementing heading validation in existing parser/validation paths and enforcing behavior via focused tests plus repository baseline updates under `features/`.

## Phase 0: Outline & Research

Research tasks generated from dependencies and integration scope:

1. Research the parser-level source of truth for heading detection (markdown and non-markdown gherkin modes).
2. Research robust empty-title detection rules (missing text vs whitespace-only text) that preserve existing parse compatibility.
3. Research diagnostics contract shape to keep failures actionable and deterministic (file, line, heading type, message).
4. Research false-positive prevention strategy for literal/non-parsed snippets.
5. Research where to enforce the check for contributor workflow consistency (pre-commit/test path).

**Phase 0 Output**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/005-no-empty-bdd-headings/research.md`

## Phase 1: Design & Contracts

1. Model feature documents, parsed heading records, validation policy, and violation diagnostics in `data-model.md`.
2. Define design-time contract in `contracts/empty-heading-validation.openapi.yaml` for validation invocation and deterministic diagnostics payload.
3. Define reproducible validation scenarios in `quickstart.md` including repository-baseline checks and false-positive boundaries.
4. Update agent context via `.specify/scripts/bash/update-agent-context.sh codex`.

**Phase 1 Outputs**:

- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/005-no-empty-bdd-headings/data-model.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/005-no-empty-bdd-headings/contracts/empty-heading-validation.openapi.yaml`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/005-no-empty-bdd-headings/quickstart.md`

## Post-Design Constitution Check

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | Research/design artifacts map directly to FR-001..FR-007 and SC-001..SC-004. |
| II. Independent Story Increments | PASS | Artifact boundaries preserve independent implementation and testing for each story. |
| III. Validation-First Changes | PASS | Quickstart and contract define executable validation before merge. |
| IV. Deterministic Compatibility and Contracts | PASS | Validation output contract defines deterministic fields and failure policy. |
| V. Task-Traceable Commits & Pre-Commit | PASS | Planning artifacts preserve constitution obligations for task-linked commits and pre-commit gating. |
| Additional Constraint: English-only documentation | PASS | All generated plan-phase artifacts remain in English. |

**Gate Result (Post-Design)**: PASS

## Complexity Tracking

No constitution violations detected. No exceptions required.
