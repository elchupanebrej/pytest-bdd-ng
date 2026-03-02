---
description: "Task list for Maximize Messages Capability Coverage implementation"
---

# Tasks: Maximize Messages Capability Coverage

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Test tasks are included because the specification defines
independent test criteria for each story and requires validation-first delivery.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`)
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare dedicated audit inputs and shared scaffolding before core implementation.

- [X] T001 Create dedicated audit fixture package in `tests/messages_coverage/__init__.py`
- [X] T002 Create mandatory Gherkin fixture with comments/background/rule/examples/docstring/datatable in `tests/messages_coverage/fixtures/mandatory_coverage.feature`
- [X] T003 [P] Create attachment-driven audit scenarios in `tests/messages_coverage/test_mandatory_attachments.py`
- [X] T004 [P] Add shared mandatory-scope fixtures in `tests/messages_coverage/conftest.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared primitives required by all user stories.

**⚠️ CRITICAL**: No user story work starts until this phase is complete.

- [X] T005 Implement canonical capability ID normalization helpers in `src/pytest_bdd/model/coverage/inventory.py`
- [X] T006 [P] Integrate normalized capability IDs in coverage tracking outputs in `src/pytest_bdd/model/coverage/tracker.py`
- [X] T007 [P] Integrate normalized capability IDs in message validation coverage extraction in `src/pytest_bdd/model/message_validation.py`
- [X] T008 Implement mandatory capability list loader and parser in `src/pytest_bdd/script/message_capability_governance.py`
- [X] T009 Implement mandatory summary metric aggregation scaffolding in `src/pytest_bdd/script/message_capability_governance.py`
- [X] T010 [P] Add normalization unit tests in `tests/messages/test_capability_id_normalization.py`
- [X] T011 Add mandatory list loading and uniqueness tests in `tests/messages/test_governance.py`

**Checkpoint**: Foundation complete, user stories can proceed.

---

## Phase 3: User Story 1 - Complete capability inventory (Priority: P1) 🎯 MVP

**Goal**: Ensure canonical inventory and decision model are deterministic and mandatory-scope aware.

**Independent Test**: Generate inventory and verify each relevant capability
appears once with one status, and non-implemented non-mandatory entries require
evidence fields.

### Tests for User Story 1

- [X] T012 [P] [US1] Add contract assertions for canonical inventory uniqueness in `tests/contract/test_messages_capability_coverage_contract.py`
- [X] T013 [P] [US1] Add inventory cardinality and mandatory-scope inclusion tests in `tests/messages/test_message_capability_inventory.py`
- [X] T014 [P] [US1] Add decision lifecycle invariants tests for one-decision-per-release-cycle in `tests/messages/test_message_status_governance.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement canonical inventory export and stable capability ID generation in `src/pytest_bdd/model/coverage/inventory.py`
- [X] T016 [US1] Implement inventory reconciliation against mandatory scope in `src/pytest_bdd/model/message_capability_inventory.py`
- [X] T017 [US1] Enforce exactly one active decision per capability and release target in `src/pytest_bdd/model/message_status_governance.py`
- [X] T018 [US1] Update mandatory scope source artifact for deterministic ordering and comments in `specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt`

**Checkpoint**: US1 delivers canonical, deterministic capability inventory for MVP governance.

---

## Phase 4: User Story 2 - Make coverage gaps visible (Priority: P2)

**Goal**: Populate mandatory hook fields at runtime and expose any coverage gap deterministically.

**Independent Test**: Dedicated readiness matrix emits mandatory payload paths
and maps all observed outcomes to canonical capability IDs with no ambiguity.

### Tests for User Story 2

- [X] T019 [P] [US2] Add attachment mandatory-field formation tests in `tests/messages/test_message_attachments.py`
- [X] T020 [P] [US2] Add deep gherkin document branch coverage tests in `tests/messages/test_messages.py`
- [X] T021 [P] [US2] Add external attachment payload coverage tests in `tests/messages/test_message_validation.py`
- [X] T022 [P] [US2] Upgrade dedicated audit assertions for mandatory observed IDs in `tests/messages_coverage/test_full_capability_governance.py`

### Implementation for User Story 2

- [X] T023 [US2] Extend reporter attachment emission to populate timestamp/url/source/linkage fields in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T024 [US2] Extend scenario runner attach hook contract for source/url metadata in `src/pytest_bdd/plugin/scenario_runner/hook.py`
- [X] T025 [US2] Pass attachment metadata through attach fixture entrypoint in `src/pytest_bdd/plugin/scenario_runner/entrypoint.py`
- [X] T026 [US2] Add external attachment payload-kind support and envelope unfolding in `src/pytest_bdd/model/message_extension.py`
- [X] T027 [US2] Extend message validation payload-kind recognition for external attachments in `src/pytest_bdd/model/message_validation.py`
- [X] T028 [US2] Expand struct-bdd and parser AST formation for rule/background/comments depth in `src/pytest_bdd/plugin/struct_bdd/model_builder.py`
- [X] T029 [US2] Complete parser-driven gherkin document field propagation for mandatory nested paths in `src/pytest_bdd/parser.py`
- [X] T030 [US2] Add mandatory audit feature inputs invoking attachment and gherkin branches in `tests/messages_coverage/fixtures/mandatory_coverage.feature`

**Checkpoint**: US2 provides deterministic runtime coverage visibility for mandatory hook-populated fields.

---

## Phase 5: User Story 3 - Govern release readiness (Priority: P3)

**Goal**: Enforce release-governance gates so mandatory IDs cannot be deferred and readiness fails on violations.

**Independent Test**: Governance report alone shows all mandatory IDs as
`Implemented`, zero mandatory-scope violations, and deterministic
blocker/deferred/approved disposition.

### Tests for User Story 3

- [X] T031 [P] [US3] Add contract tests for governance report mandatory flags and failure modes in `tests/contract/test_messages_capability_coverage_contract.py`
- [X] T032 [P] [US3] Add governance report mandatory-scope enforcement tests in `tests/messages/test_governance.py`
- [X] T033 [P] [US3] Add CLI contract schema validation tests for report command in `tests/messages/test_governance_cli_contract.py`

### Implementation for User Story 3

- [X] T034 [US3] Implement `--mandatory-capabilities-file` and `--require-mandatory-implemented` report options in `src/pytest_bdd/script/message_capability_governance.py`
- [X] T035 [US3] Enforce mandatory-scope status restrictions during decision merge in `src/pytest_bdd/model/message_status_governance.py`
- [X] T036 [US3] Add mandatory summary fields and capability-level scope marker in `specs/008-maximize-messages-coverage/contracts/governance-report.schema.json`
- [X] T037 [US3] Update governance OpenAPI report contract for mandatory enforcement semantics in `specs/008-maximize-messages-coverage/contracts/messages-capability-governance.openapi.yaml`
- [X] T038 [US3] Implement CLI command contract for mandatory enforcement options in `specs/008-maximize-messages-coverage/contracts/message-capability-governance-cli.schema.json`
- [X] T039 [US3] Replace non-implemented mandatory decisions with compliant governance baseline in `specs/008-maximize-messages-coverage/contracts/capability-decisions.json`

**Checkpoint**: US3 enables release go/no-go governance with mandatory-scope enforcement.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gates, docs, and release-ready validation.

- [X] T040 [P] Update user-facing 007/008 guide with mandatory audit flow in `docs/messages-coverage-user-guide.md`
- [X] T041 Update command walkthrough and expected strict outcomes in `specs/008-maximize-messages-coverage/quickstart.md`
- [X] T042 [P] Add explicit CI gate for dedicated mandatory coverage audit in `.github/workflows/messages-baseline-drift.yml`
- [X] T043 Execute mandatory coverage regression slice and document commands in `specs/008-maximize-messages-coverage/quickstart.md`
- [X] T044 Run pre-commit for touched files and resolve all hook issues via `.pre-commit-config.yaml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2 and reuses US1 canonical inventory/ID normalization.
- **Phase 5 (US3)**: Depends on Phase 2 and consumes US1+US2 outputs for readiness enforcement.
- **Phase 6 (Polish)**: Depends on completion of US1, US2, US3.

### User Story Dependency Graph

```text
US1 (P1) -> US2 (P2) -> US3 (P3)
```

Rationale:
- US1 establishes deterministic inventory and decision constraints.
- US2 depends on canonical IDs and inventory semantics from US1.
- US3 enforces governance using runtime evidence produced by US2.

### Within Each User Story

- Test tasks precede implementation tasks.
- Model/rule updates precede plugin/CLI wiring.
- Story checkpoint must pass before moving to next priority.

## Parallel Execution Examples

### User Story 1

```bash
Task: "T012 [US1] Add contract assertions in tests/contract/test_messages_capability_coverage_contract.py"
Task: "T013 [US1] Add inventory tests in tests/messages/test_message_capability_inventory.py"
Task: "T014 [US1] Add decision lifecycle tests in tests/messages/test_message_status_governance.py"
```

### User Story 2

```bash
Task: "T019 [US2] Add attachment formation tests in tests/messages/test_message_attachments.py"
Task: "T020 [US2] Add deep gherkin coverage tests in tests/messages/test_messages.py"
Task: "T021 [US2] Add external attachment coverage tests in tests/messages/test_message_validation.py"
Task: "T022 [US2] Upgrade dedicated audit assertions in tests/messages_coverage/test_full_capability_governance.py"
```

### User Story 3

```bash
Task: "T031 [US3] Add report-flag contract tests in tests/contract/test_messages_capability_coverage_contract.py"
Task: "T032 [US3] Add governance mandatory-scope tests in tests/messages/test_governance.py"
Task: "T033 [US3] Add CLI contract schema tests in tests/messages/test_governance_cli_contract.py"
```

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate canonical inventory + decision invariants before broader runtime changes.

### Incremental Delivery

1. Deliver US1 for deterministic inventory baseline.
2. Deliver US2 for mandatory runtime field population and visibility.
3. Deliver US3 for hard governance gates and release enforcement.
4. Finish Phase 6 polish and validation.

### Parallel Team Strategy

1. Team finishes Setup + Foundational together.
2. After Phase 2:
   - Engineer A drives US1 inventory/decision model.
   - Engineer B prepares US2 runtime hook coverage tests.
3. US2 and US3 proceed after US1 normalization is merged.

## Notes

- All tasks follow strict checklist format: checkbox + Task ID + optional `[P]` + optional `[US#]` + file path.
- `[P]` tasks are parallel-safe only when file overlap and dependency ordering permit.
- MVP scope recommendation: complete through **Phase 3 (US1)** first.
