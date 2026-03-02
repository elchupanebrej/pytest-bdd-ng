---
description: "Task list for Maximize Messages Capability Coverage implementation"
---

# Tasks: Maximize Messages Capability Coverage

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are included because the specification defines explicit
independent tests per story and constitution requires validation-first changes.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and shared implementation scaffolding

- [X] T001 Create feature workflow scaffold for scheduled drift checks in `.github/workflows/messages-baseline-drift.yml`
- [X] T002 Add feature-level contract fixture bootstrap in `tests/contract/test_messages_capability_coverage_contract.py`
- [X] T003 [P] Add shared message governance fixture data for new scenarios in `tests/messages/message_capability_fixtures.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement canonical schema resolver policy (importlib resources + git fallback) in `src/pytest_bdd/model/message_capability_inventory.py`
- [X] T005 [P] Implement shared capability status vocabulary and mandatory evidence-field guardrails in `src/pytest_bdd/model/message_status_governance.py`
- [X] T006 [P] Implement structured validation diagnostic model in `src/pytest_bdd/model/message_validation.py`
- [X] T007 Implement deterministic outcome normalization primitives in `src/pytest_bdd/model/message_outcome_mapping.py`
- [X] T008 Implement governance-report schema loading/validation utilities in `src/pytest_bdd/script/message_capability_governance.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Complete capability inventory (Priority: P1) 🎯 MVP

**Goal**: Provide a canonical inventory of relevant capabilities with one status and evidence-ready governance decisions.

**Independent Test**: A maintainer can generate the inventory and verify every
relevant capability appears exactly once, and any non-implemented capability
includes rationale, owner, evidence reference, and review date.

### Tests for User Story 1

- [X] T009 [P] [US1] Add contract tests for capability sync semantics (`/coverage/capabilities/sync`) in `tests/contract/test_messages_capability_coverage_contract.py`
- [X] T010 [P] [US1] Add inventory generation and uniqueness tests in `tests/messages/test_message_capability_inventory.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement capability inventory sync and relevance filtering flow in `src/pytest_bdd/model/message_capability_inventory.py`
- [X] T012 [US1] Implement capability decision evidence enforcement rules in `src/pytest_bdd/model/message_status_governance.py`
- [X] T013 [US1] Implement inventory sync summary output (totals + duplicate IDs) in `src/pytest_bdd/script/message_capability_governance.py`
- [X] T014 [US1] Implement inventory CLI generation path aligned with approved baseline source in `src/pytest_bdd/model/coverage/inventory.py`

**Checkpoint**: User Story 1 is independently functional and ready for MVP validation

---

## Phase 4: User Story 2 - Make coverage gaps visible (Priority: P2)

**Goal**: Ensure runtime outcomes map deterministically to capabilities and expose missing/ambiguous coverage.

**Independent Test**: Running the fixed readiness matrix produces deterministic
mappings and consistent status terminology across reporting entry points.

### Tests for User Story 2

- [X] T015 [P] [US2] Add contract tests for mapping validation semantics (`/coverage/mappings/validate`) in `tests/contract/test_messages_capability_coverage_contract.py`
- [X] T016 [P] [US2] Add fixed-readiness matrix mapping consistency tests in `tests/messages/test_message_outcome_mapping.py`
- [X] T017 [P] [US2] Add state-dependent evidence traceability tests in `tests/messages/test_coverage.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement canonical outcome mapping resolution with explicit priority handling in `src/pytest_bdd/model/message_outcome_mapping.py`
- [X] T019 [US2] Integrate canonical mapping reuse across message reporting entry points in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T020 [US2] Implement opt-in runtime coverage tracing and evidence capture in `src/pytest_bdd/model/coverage/tracker.py`
- [X] T021 [US2] Integrate fail-fast schema validation with structured diagnostics in `src/pytest_bdd/model/message_validation.py`

**Checkpoint**: User Stories 1 and 2 are independently testable and provide deterministic coverage visibility

---

## Phase 5: User Story 3 - Govern release readiness (Priority: P3)

**Goal**: Publish governance checklist output that supports release go/no-go decisions and scheduled baseline drift review.

**Independent Test**: A reviewer uses only governance artifacts to identify
supported capabilities, deferred items, blockers, and weekly capability deltas.

### Tests for User Story 3

- [X] T022 [P] [US3] Add contract tests for checklist rendering semantics (`/coverage/checklist/render`) in `tests/contract/test_messages_capability_coverage_contract.py`
- [X] T023 [P] [US3] Add governance checklist disposition tests in `tests/messages/test_message_governance_checklist.py`
- [X] T024 [P] [US3] Add weekly baseline diff delta tests in `tests/messages/test_message_baseline_diff.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement governance checklist rendering and blocker/deferred disposition rules in `src/pytest_bdd/model/message_governance_checklist.py`
- [X] T026 [US3] Implement governance report generation and schema-conformance validation in `src/pytest_bdd/script/message_capability_governance.py`
- [X] T027 [US3] Implement baseline diff generation for added/changed/removed capability IDs in `src/pytest_bdd/model/message_baseline_diff.py`
- [X] T028 [US3] Implement scheduled weekly drift workflow execution and artifact publication in `.github/workflows/messages-baseline-drift.yml`

**Checkpoint**: All user stories are independently functional with release governance visibility

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Update user documentation and governance terminology references in `docs/messages-coverage.md`
- [X] T030 Validate quickstart end-to-end commands and expected outputs in `specs/008-maximize-messages-coverage/quickstart.md`
- [X] T031 Execute full message/governance regression slice and capture outcomes in `tests/messages/`
- [X] T032 Run formatting/lint hooks for touched files via configuration in `.pre-commit-config.yaml`

---

## Dependencies & Execution Order

### Dependency Graph

```text
Phase 1 (Setup)
  -> Phase 2 (Foundational)
      -> US1 (P1)
      -> US2 (P2; depends on foundational primitives + US1 status vocabulary)
      -> US3 (P3; depends on governance inputs from US1 + US2 outputs)
          -> Phase 6 (Polish)
```

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational completion and reuses
  canonical status/mapping primitives from US1 outputs
- **User Story 3 (Phase 5)**: Depends on Foundational completion and consumes US1 inventory + US2 mapping/evidence outputs
- **Polish (Phase 6)**: Depends on completion of all targeted user stories

### Within Each User Story

- Tests MUST be written first and fail before implementation
- Core model/rule logic before plugin or CLI integration
- Integration wiring before story completion checkpoint

### Parallel Opportunities

- Setup: `T003` can run in parallel with `T001-T002`
- Foundational: `T005` and `T006` can run in parallel after `T004`
- US1: `T009` and `T010` can run in parallel; `T011` and `T012` can proceed in parallel after tests are in place
- US2: `T015-T017` can run in parallel; `T020` can proceed in parallel with `T018` before `T019`/`T021` wiring
- US3: `T022-T024` can run in parallel; `T027` can run in parallel with `T025` before `T026`
- Polish: `T029` and `T032` can run in parallel

---

## Parallel Execution Examples

### User Story 1

```bash
# Parallel tests
Task: "T009 [US1] contract sync tests in tests/contract/test_messages_capability_coverage_contract.py"
Task: "T010 [US1] inventory tests in tests/messages/test_message_capability_inventory.py"

# Parallel implementation
Task: "T011 [US1] inventory sync in src/pytest_bdd/model/message_capability_inventory.py"
Task: "T012 [US1] evidence enforcement in src/pytest_bdd/model/message_status_governance.py"
```

### User Story 2

```bash
# Parallel tests
Task: "T015 [US2] mapping contract tests in tests/contract/test_messages_capability_coverage_contract.py"
Task: "T016 [US2] readiness matrix tests in tests/messages/test_message_outcome_mapping.py"
Task: "T017 [US2] evidence traceability tests in tests/messages/test_coverage.py"

# Parallel implementation
Task: "T018 [US2] deterministic mapping in src/pytest_bdd/model/message_outcome_mapping.py"
Task: "T020 [US2] opt-in tracing in src/pytest_bdd/model/coverage/tracker.py"
```

### User Story 3

```bash
# Parallel tests
Task: "T022 [US3] checklist contract tests in tests/contract/test_messages_capability_coverage_contract.py"
Task: "T023 [US3] checklist disposition tests in tests/messages/test_message_governance_checklist.py"
Task: "T024 [US3] weekly diff tests in tests/messages/test_message_baseline_diff.py"

# Parallel implementation
Task: "T025 [US3] checklist rendering in src/pytest_bdd/model/message_governance_checklist.py"
Task: "T027 [US3] baseline diff generation in src/pytest_bdd/model/message_baseline_diff.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm canonical inventory generation and evidence-required non-implemented decisions

### Incremental Delivery

1. Deliver US1 inventory and status governance foundation
2. Add US2 deterministic runtime mapping + coverage evidence flow
3. Add US3 release governance checklist + weekly baseline drift automation
4. Run Phase 6 polish and quickstart validation before release

---

## Notes

- All tasks use strict checklist format with task ID, optional `[P]`, optional `[US#]`, and explicit file path.
- Story phases are organized for independent testability and incremental delivery.
- Suggested MVP scope: complete through Phase 3 (US1) before expanding to later stories.
