---
description: "Task list for Maximize Messages Capability Coverage implementation"
---

# Tasks: Maximize Messages Capability Coverage

**Input**: Design documents from `/specs/007-maximize-messages-coverage/`
**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create coverage package structure in `src/pytest_bdd/model/coverage/__init__.py`
- [X] T002 Add `jsonschema` dependency to project configuration in `setup.cfg`
- [X] T003 [P] Create schema definition for governance report in `specs/007-maximize-messages-coverage/contracts/governance.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create foundational entity models (`CapabilityInventory`, `FieldMetadata`) in `src/pytest_bdd/model/coverage/inventory.py`
- [X] T005 [P] Create foundational entity model (`ObservedCoverage`) in `src/pytest_bdd/model/coverage/tracker.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Complete capability inventory (Priority: P1) 🎯 MVP

**Goal**: Automatically maintain a canonical inventory of all upstream messages capabilities derived from the official JSON Schema to ensure 100% field coverage.

**Independent Test**: Review the capability inventory and confirm every relevant capability is listed exactly once with a defined support status and rationale when not implemented.

### Tests for User Story 1

- [X] T006 [P] [US1] Create unit tests for schema parser and inventory generation in `tests/messages/test_coverage.py`

### Implementation for User Story 1

- [X] T007 [US1] Implement `CapabilityInventory` generator logic to parse `Envelope.json` in `src/pytest_bdd/model/coverage/inventory.py`
- [X] T008 [US1] Implement CLI interface for inventory generator in `src/pytest_bdd/model/coverage/inventory.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. The inventory can be generated from the schema.

---

## Phase 4: User Story 2 - Consistent event coverage (Priority: P2)

**Goal**: Runtime outcomes map consistently to messages capabilities. Validate emitted payloads during runtime and dynamically track covered fields.

**Independent Test**: Run a fixed release-readiness matrix (including pass, fail, skipped, undefined, interrupted) and verify each reported outcome maps to a defined capability and is structurally sound.

### Tests for User Story 2

- [X] T009 [P] [US2] Create schema-driven coverage tests for payload validation in `tests/messages/test_coverage.py`
- [X] T010 [P] [US2] Add evidence Gherkin scenarios for state-dependent fields in `tests/messages/scenarios/evidence.feature`
- [X] T011 [P] [US2] Create test runner for evidence scenarios in `tests/messages/scenarios/test_evidence.py`

### Implementation for User Story 2

- [X] T012 [P] [US2] Update `_build_step_match_arguments_lists` to use exact offsets in `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T013 [P] [US2] Update schema-based helper methods in `src/pytest_bdd/model/message_extension.py`
- [X] T014 [US2] Implement dynamic traceability via `FieldCoverageTracker` in `src/pytest_bdd/model/coverage/tracker.py`
- [X] T015 [US2] Integrate `jsonschema` validation into `validate_message_stream` in `src/pytest_bdd/model/message_validation.py`
- [X] T016 [US2] Integrate `FieldCoverageTracker` into validation flow in `src/pytest_bdd/model/message_validation.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Test runs will dynamically track capability coverage and validate payload integrity.

---

## Phase 5: User Story 3 - Governance for release decisions (Priority: P3)

**Goal**: Publish a governance checklist showing coverage decisions for all capabilities so readiness can be evaluated without manual discovery.

**Independent Test**: Use only the governance checklist to identify implemented capabilities, intentional exclusions, and unresolved items for release sign-off.

### Tests for User Story 3

- [X] T017 [P] [US3] Create tests for governance report generation in `tests/messages/test_governance.py`

### Implementation for User Story 3

- [X] T018 [US3] Implement `GovernanceReport` entity and mapping rules in `src/pytest_bdd/script/message_capability_governance.py`
- [X] T019 [US3] Implement script to generate governance artifact from NDJSON in `src/pytest_bdd/script/message_capability_governance.py`

**Checkpoint**: All user stories should now be independently functional. The governance report can be fully generated.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T020 [P] Update documentation with capability status definitions in `docs/messages-coverage.md`
- [X] T021 Run quickstart.md validation locally to ensure all provided commands function correctly
- [X] T022 Code cleanup and formatting using `ruff` and `pre-commit` across `src/pytest_bdd/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - Proceed sequentially in priority order (P1 → P2 → P3) or in parallel if staffed
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates tracking which builds on inventory logic, but implementation is mostly independent
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on runtime output of US2, but script logic can be built concurrently

### Parallel Opportunities

- Foundational data models (T004, T005) can be created in parallel
- All tests (T006, T009, T010, T011, T017) can be written independently before their implementations
- US2 structural components (T012, T013) can be worked on concurrently with core coverage logic
- Documentation (T020) can be drafted in parallel with later implementation tasks

---

## Parallel Execution Examples

### User Story 1
```bash
# Launch test and implementation together (if using TDD)
Task: "Create unit tests for schema parser and inventory generation in tests/messages/test_coverage.py"
```

### User Story 2
```bash
# Launch validation tests and evidence scenarios together
Task: "Create schema-driven coverage tests for payload validation in tests/messages/test_coverage.py"
Task: "Add evidence Gherkin scenarios for state-dependent fields in tests/messages/scenarios/evidence.feature"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Schema-driven Capability Inventory Generator)
4. **STOP and VALIDATE**: Verify that the CLI can parse `Envelope.json` and dump an inventory locally.

### Incremental Delivery

1. Deliver Capability Inventory generation (US1).
2. Follow up with the Runtime Field Observer & Validation integration (US2) to start generating trace data.
3. Finish with the Governance script (US3) to bundle traces and inventory into the final `governance.json` artifact for the release.
