---
description: "Task list for Maximize Messages Capability Coverage implementation"
---

# Tasks: Maximize Messages Capability Coverage

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are included because the specification defines independent test criteria for each story and requires validation-first delivery.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`)
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare feature artifacts and dedicated runtime-evidence harness.

- [X] T001 Refresh mandatory governance scope source in `specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt`
- [X] T002 [P] Refresh runtime-required scope source in `specs/008-maximize-messages-coverage/runtime-required-capability-ids.txt`
- [X] T003 [P] Refresh Non-Implementable clarification contract in `specs/008-maximize-messages-coverage/contracts/caps.yaml`
- [X] T004 [P] Refresh dedicated runtime coverage fixture in `tests/messages_coverage/fixtures/mandatory_coverage.feature`
- [X] T005 Wire dedicated audit helper command flow in `scripts/run_messages_coverage_audit.sh`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared governance/runtime primitives that must exist before user story work.

**⚠️ CRITICAL**: No user story work starts until this phase is complete.

- [X] T006 Implement `hard_limitation` and strict decision metadata model in `src/pytest_bdd/model/message_status_governance.py`
- [X] T007 [P] Implement extraction feasibility and runtime-scope reconciliation helpers in `src/pytest_bdd/model/message_capability_inventory.py`
- [X] T008 [P] Extend canonical observed-field extraction and path normalization in `src/pytest_bdd/model/message_validation.py`
- [X] T009 Implement deterministic governance gate pipeline (`I`, `R`, `O`, `D`) in `src/pytest_bdd/script/message_capability_governance.py`
- [X] T010 [P] Update governance report schema and OpenAPI components in `specs/008-maximize-messages-coverage/contracts/governance-report.schema.json` and `specs/008-maximize-messages-coverage/contracts/messages-capability-governance.openapi.yaml`
- [X] T011 [P] Add foundational status-governance tests in `tests/messages/test_message_status_governance.py`
- [X] T012 [P] Add foundational inventory/scope tests in `tests/messages/test_message_capability_inventory.py`
- [X] T013 [P] Add foundational CLI and contract schema tests in `tests/messages/test_governance_cli_contract.py` and `tests/contract/test_messages_capability_coverage_contract.py`

**Checkpoint**: Foundation complete, user stories can begin.

---

## Phase 3: User Story 1 - Complete capability inventory (Priority: P1) 🎯 MVP

**Goal**: Deliver canonical capability inventory with deterministic status governance and single active decision per capability per release.

**Independent Test**: Generate inventory and decision view and verify each relevant capability appears once with exactly one current status and required metadata for non-implemented statuses.

### Tests for User Story 1

- [X] T014 [P] [US1] Add inventory uniqueness and status vocabulary contract test in `tests/contract/test_messages_capability_coverage_contract.py`
- [X] T015 [P] [US1] Add duplicate-decision and release-cycle review recency tests in `tests/messages/test_governance.py`

### Implementation for User Story 1

- [X] T016 [US1] Implement canonical capability ID normalization and export consistency in `src/pytest_bdd/model/coverage/inventory.py`
- [X] T017 [US1] Enforce one active decision per (`capability_id`, `release_target`) in `src/pytest_bdd/model/message_status_governance.py`
- [X] T018 [US1] Implement runtime-required and mandatory-scope input loading in `src/pytest_bdd/script/message_capability_governance.py`
- [X] T019 [US1] Align decision records with required metadata fields in `specs/008-maximize-messages-coverage/contracts/capability-decisions.json`
- [X] T020 [US1] Document inventory and decision governance invariants in `specs/008-maximize-messages-coverage/research.md`

**Checkpoint**: US1 is independently testable with deterministic inventory and decision integrity.

---

## Phase 4: User Story 2 - Make coverage gaps visible (Priority: P2)

**Goal**: Emit only real runtime events while surfacing coverage gaps through deterministic post-factum NDJSON analysis.

**Independent Test**: Run dedicated runtime suite and verify emitted NDJSON contains real runtime/hook-derived fields, with deterministic mapping and no synthetic/test-only substitutions.

### Tests for User Story 2

- [X] T021 [P] [US2] Add reporter emission tests for hook metadata and test-case linkage in `tests/messages/test_messages.py`
- [X] T022 [P] [US2] Add attachment and externalAttachment field population tests in `tests/messages/test_message_attachments.py`
- [X] T023 [P] [US2] Add dedicated runtime-evidence assertions for parse/suggestion/undefined-parameter flows in `tests/messages_coverage/test_mandatory_attachments.py`

### Implementation for User Story 2

- [X] T024 [US2] Emit hook type and richer source reference fields in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T025 [US2] Emit test-case-to-run linkage fields in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T026 [US2] Implement parseError and undefinedParameterType message emission in `src/pytest_bdd/parser.py` and `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T027 [US2] Implement suggestion emission from step lookup errors in `src/pytest_bdd/plugin/scenario_runner/plugin.py` and `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T028 [US2] Remove synthetic/test-only substitution branches from normal runtime flow in `src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py` and `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T029 [US2] Extend observed-field tracking for newly emitted runtime paths in `src/pytest_bdd/model/message_validation.py`
- [X] T030 [US2] Add e2e deterministic mapping assertions for runtime-only flow in `tests/e2e/conftest.py`

**Checkpoint**: US2 is independently testable with runtime-pure emission and explicit coverage visibility.

---

## Phase 5: User Story 3 - Govern release readiness (Priority: P3)

**Goal**: Enforce release gates where runtime-required capabilities must be runtime-covered and all other capabilities must be covered or explicitly classified.

**Independent Test**: Build governance report from dedicated NDJSON evidence and verify strict pass/fail behavior for runtime-required misses, non-runtime classification gaps, and invalid Non-Implementable decisions.

### Tests for User Story 3

- [X] T031 [P] [US3] Add runtime-required gate behavior tests in `tests/messages/test_governance.py`
- [X] T032 [P] [US3] Add non-runtime classified-or-covered gate tests in `tests/messages/test_governance.py`
- [X] T033 [P] [US3] Add dedicated end-to-end governance gate test in `tests/messages_coverage/test_full_capability_governance.py`

### Implementation for User Story 3

- [X] T034 [US3] Implement runtime-required and non-runtime classification gate evaluation in `src/pytest_bdd/script/message_capability_governance.py`
- [X] T035 [US3] Enforce hard technical limitation policy for `Non-Implementable` in `src/pytest_bdd/model/message_status_governance.py`
- [X] T036 [US3] Implement conflict validation for runtime-observed capabilities marked `Non-Implementable` in `src/pytest_bdd/script/message_capability_governance.py`
- [X] T037 [US3] Emit governance report fields for `hard_limitation` and runtime/non-runtime counters in `src/pytest_bdd/script/message_capability_governance.py`
- [X] T038 [US3] Require `hard_limitation` for `Non-Implementable` in `specs/008-maximize-messages-coverage/contracts/governance-report.schema.json` and `specs/008-maximize-messages-coverage/contracts/messages-capability-governance.openapi.yaml`
- [X] T039 [US3] Align CLI report contract flags and strict requirements in `specs/008-maximize-messages-coverage/contracts/message-capability-governance-cli.schema.json`
- [X] T040 [US3] Refresh governed decision dataset with hard-issue-only exceptions in `specs/008-maximize-messages-coverage/contracts/capability-decisions.json`

**Checkpoint**: US3 is independently testable with strict, deterministic release-governance gates.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize documentation, CI wiring, and validation evidence.

- [X] T041 [P] Update user guide for runtime-pure coverage/governance workflow in `docs/messages-coverage-user-guide.md`
- [X] T042 [P] Update quickstart execution and validation instructions in `specs/008-maximize-messages-coverage/quickstart.md`
- [X] T043 [P] Update CI gate orchestration for dedicated audit runs in `.github/workflows/messages-baseline-drift.yml`
- [X] T044 Run contract and governance unit test slices in `tests/contract/test_messages_capability_coverage_contract.py`, `tests/messages/test_governance.py`, and `tests/messages/test_governance_cli_contract.py`
- [X] T045 Run dedicated messages coverage suite and full e2e suite with HTML report in `tests/messages_coverage/test_full_capability_governance.py` and `tests/e2e/`
- [X] T046 Run pre-commit hooks for touched files via `.pre-commit-config.yaml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2; consumes canonical scope outputs from US1.
- **Phase 5 (US3)**: Depends on Phase 2 and requires US1 + US2 outputs for final governance gates.
- **Phase 6 (Polish)**: Depends on completion of US1, US2, and US3.

### User Story Dependency Graph

```text
US1 (P1) -> US2 (P2) -> US3 (P3)
```

### Within Each User Story

- Tests are written before implementation tasks.
- Model/contract changes precede CLI/report integration.
- Each story must pass its independent test checkpoint before moving to the next priority.

## Parallel Execution Examples

### User Story 1

```bash
Task: "T014 [US1] Add inventory uniqueness contract test in tests/contract/test_messages_capability_coverage_contract.py"
Task: "T015 [US1] Add duplicate-decision and recency tests in tests/messages/test_governance.py"
```

### User Story 2

```bash
Task: "T021 [US2] Add reporter emission tests in tests/messages/test_messages.py"
Task: "T022 [US2] Add attachment field population tests in tests/messages/test_message_attachments.py"
Task: "T023 [US2] Add runtime-evidence assertions in tests/messages_coverage/test_mandatory_attachments.py"
```

### User Story 3

```bash
Task: "T031 [US3] Add runtime-required gate tests in tests/messages/test_governance.py"
Task: "T032 [US3] Add non-runtime classification gate tests in tests/messages/test_governance.py"
Task: "T033 [US3] Add full governance gate e2e test in tests/messages_coverage/test_full_capability_governance.py"
```

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate deterministic inventory and decision integrity.
4. Demo/review before runtime reporter expansion.

### Incremental Delivery

1. Deliver US1 for canonical inventory and status governance baseline.
2. Deliver US2 for runtime-pure event emission and coverage visibility.
3. Deliver US3 for strict release readiness gates.
4. Finish Polish phase for CI/docs/final validation.

### Parallel Team Strategy

1. Team completes Setup + Foundational together.
2. After Phase 2:
   - Engineer A drives US1 inventory and decision integrity.
   - Engineer B drives US2 runtime emission and coverage mapping.
3. Engineer C begins US3 gate logic after US1 and US2 checkpoints pass.

## Notes

- All tasks follow strict checklist format: checkbox + Task ID + optional `[P]` + optional `[US#]` + file path.
- `[P]` tasks are parallel-safe only when dependency ordering and file overlap allow.
- Suggested MVP scope: complete through **Phase 3 (US1)** first.
