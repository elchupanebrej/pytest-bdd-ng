# Implementation Plan: Maximize Messages Capability Coverage

**Branch**: `008-maximize-messages-coverage` | **Date**: 2026-03-02 | **Spec**: [spec.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/spec.md)
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/spec.md`

## Summary

Implement mandatory hook-populated coverage for the full stakeholder-defined capability list in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt` (323 IDs), while preserving deterministic status vocabulary and governance report contracts. The delivery approach is: normalize inventory/runtime capability key matching, extend reporting formation points for missing message payload fields, enforce mandatory-scope governance gates, and validate using a dedicated audit suite separated from the main test suite.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: `pytest>=6.2.5`, `cucumber-messages`, `pluggy`, `jsonschema`, `tox>=4.2`, `pre-commit`
**Storage**: In-memory runtime state + NDJSON artifacts + repository governance artifacts under `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/`
**Testing**: `pytest` unit/contract/messages suites, dedicated `tests/messages_coverage` audit suite, `tox`, `pre-commit`
**Target Platform**: Local development and CI for Python plugin execution (macOS/Linux runners; Windows compatibility unchanged)
**Project Type**: Python library + pytest plugin + CLI governance tooling
**Performance Goals**: Default test runs remain fast (no audit-only tracing cost when audit flag/suite is not enabled); dedicated audit suite may pay full tracing cost to enforce 100% mandatory coverage.
**Constraints**: Must enforce canonical statuses (`Implemented`, `Pending`, `Non-Implementable`, `Not-Applicable`, `Not-Acceptable`); mandatory list IDs cannot be deferred for release readiness; weekly baseline drift reporting remains required; compatibility contracts remain deterministic and versioned.
**Scale/Scope**: 349 schema-derived capabilities total, 323 mandatory hook-populated IDs in scope for implementation, 0 allowed unresolved mandatory IDs at release gate.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Gate

- [x] **I. Spec-Driven Delivery**: Spec exists and clarifications are integrated in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/spec.md`.
- [x] **II. Independent Story Increments**: Work remains partitioned by inventory, coverage mapping, and governance readiness stories.
- [x] **III. Validation-First Changes**: Plan includes executable validation via messages tests, contract checks, and dedicated coverage audit suite.
- [x] **IV. Deterministic Compatibility and Contracts**: Contracts are explicit and versioned under `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/contracts/`.
- [x] **V. Task-Traceable Commits and Pre-Commit Enforcement**: Implementation phase will require task-tagged commits and pre-commit clean status before each commit.

**Gate Status**: PASS

### Post-Phase 1 Re-Check

- [x] **I. Spec-Driven Delivery**: `research.md`, `data-model.md`, `quickstart.md`, and contract artifacts were updated to match FR-011/FR-014/FR-015 and SC-006.
- [x] **II. Independent Story Increments**: Design separates formation-point work, governance enforcement, and audit-suite validation to keep increments testable.
- [x] **III. Validation-First Changes**: Design defines dedicated validation gates for mandatory IDs and contract-level schema checks.
- [x] **IV. Deterministic Compatibility and Contracts**: Design keeps canonical status vocabulary and deterministic mapping with explicit contract updates.
- [x] **V. Task-Traceable Commits and Pre-Commit Enforcement**: No implementation tasks executed in this phase; commit policy remains enforceable for `/speckit.implement`.

**Gate Status**: PASS

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── mandatory-hook-capability-ids.txt
├── contracts/
│   ├── governance-report.schema.json
│   ├── messages-capability-governance.openapi.yaml
│   └── message-capability-governance-cli.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/
├── model/
│   ├── coverage/
│   │   ├── inventory.py
│   │   └── tracker.py
│   ├── message_extension.py
│   ├── message_validation.py
│   └── message_status_governance.py
├── plugin/
│   └── gherkin_message_reporter/
│       └── plugin.py
└── script/
    └── message_capability_governance.py

/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/
├── contract/
├── messages/
├── messages_coverage/
└── e2e/
```

**Structure Decision**: Keep a single-project Python plugin/library layout. Extend existing message model, reporter plugin, and governance CLI modules in place; validate via message-focused suites and a dedicated coverage-audit suite.

## Phase 0: Research Plan

Research tasks were derived from technical context dependencies and integration risks:

1. Research mandatory capability enforcement at governance-report generation and decision-merge boundaries.
2. Research formation points for currently uncovered `attachment`, `externalAttachment`, and deep `gherkinDocument` fields.
3. Research performance-safe exhaustive coverage strategy that keeps default runs lightweight and audit suite strict.

Consolidated findings are captured in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/research.md` with decisions, rationale, and alternatives.

## Phase 1: Design & Contracts Plan

1. Refresh data model to include explicit `MandatoryCapabilityScope` and release-gate invariants for mandatory IDs.
2. Extend contracts with governance-report and CLI-level mandatory coverage enforcement semantics.
3. Update quickstart flow to show dedicated audit execution and mandatory-ID pass criteria.
4. Update agent context via `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.specify/scripts/bash/update-agent-context.sh codex`.

## Phase 2 Planning Preview (stops here)

Implementation will follow `/speckit.tasks` output and enforce this order:

1. Foundation: capability matching normalization and governance mandatory-ID gates.
2. Core formation work: reporter hook payload completion for mandatory field set.
3. Validation expansion: dedicated audit fixtures and contract assertions for mandatory list.
4. Polish: performance checks and documentation refinements.

## Complexity Tracking

No constitution violations require exception handling at planning time.
