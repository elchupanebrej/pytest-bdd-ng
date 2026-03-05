# Tasks: Execution Context Reporting Consistency

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. This feature has explicit independent-test criteria per user story and strict governance validation requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`) for story-phase tasks only
- All task descriptions include concrete file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare adapter-focused scaffolding and feature-specific test entry points.

- [X] T001 Create execution-message adapter module scaffold in src/pytest_bdd/model/execution_message_adapter.py
- [X] T002 [P] Create adapter serialization test scaffold in tests/messages/test_execution_message_adapter.py
- [X] T003 [P] Create adapter round-trip test scaffold in tests/messages/test_execution_message_adapter_roundtrip.py
- [X] T004 [P] Create adapter governance fixture scaffold in tests/messages_coverage/fixtures/capability-decisions.adapter.json

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared runtime/context infrastructure required by all stories.

**⚠️ CRITICAL**: No user story implementation starts before this phase is complete.

- [X] T005 Extend execution context models with message reference index records in src/pytest_bdd/model/execution_context.py
- [X] T006 [P] Add deterministic registry/index key utilities in src/pytest_bdd/model/gherkin_document/registry.py
- [X] T007 [P] Split context accessors into explicit read/write API surfaces in src/pytest_bdd/plugin/scenario_runner/context_access.py
- [X] T008 Move reporting lifecycle state mutation responsibilities into execution flow in src/pytest_bdd/plugin/scenario_runner/plugin.py
- [X] T009 Align stash-backed session/context initialization-pop lifecycle in src/pytest_bdd/plugin/scenario_runner/context_store.py
- [X] T010 Add foundational state and transition regressions in tests/hook/test_execution_context_store_unit.py and tests/hook/test_execution_context_transitions.py

**Checkpoint**: Foundation complete, user stories can be implemented.

---

## Phase 3: User Story 1 - Context-Driven Reporter State (Priority: P1) 🎯 MVP

**Goal**: Reporter lifecycle emission is read-only over execution context and has no `current_<item>` ownership state.

**Independent Test**: Run reporting flow for scenarios with hooks/steps and verify emitted lifecycle IDs are context-derived without reporter-side bootstrap/mutation.

### Tests for User Story 1

- [X] T011 [P] [US1] Add reporter read-only guard tests in tests/hook/test_gherkin_reporter_context_lifecycle.py
- [X] T012 [P] [US1] Add emission-point tests for context-derived run/case/step IDs in tests/messages/test_message_emission_points.py
- [X] T013 [US1] Add reporter snapshot compatibility regression in tests/feature/test_report_context_hierarchy.py

### Implementation for User Story 1

- [X] T014 [US1] Remove reporter-owned lifecycle mutation paths in src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py
- [X] T015 [US1] Route reporter ID resolution through read-only context accessors in src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py and src/pytest_bdd/plugin/scenario_runner/context_access.py
- [X] T016 [US1] Complete execution-plugin ownership of lifecycle writes in src/pytest_bdd/plugin/scenario_runner/plugin.py and src/pytest_bdd/plugin/scenario_runner/context_transitions.py
- [X] T017 [US1] Update scenario reporter serialization to consume context-driven state only in src/pytest_bdd/plugin/scenario_reporter/report.py

**Checkpoint**: US1 is independently functional and testable.

---

## Phase 4: User Story 2 - Centralized Gherkin Registry Ownership (Priority: P2)

**Goal**: Feature model remains representational; registry ownership and lookup resolution stay in execution context/stash path.

**Independent Test**: Build nested feature/rule/background/scenario samples and verify lookup works via context registry while `Feature` model does not own registry state.

### Tests for User Story 2

- [X] T018 [P] [US2] Add feature-model purity tests in tests/model/gherkin_document/test_feature_context_lookup.py
- [X] T019 [P] [US2] Add context/stash resolver tests for scenario-step links in tests/hook/test_scenario_reference_resolution.py

### Implementation for User Story 2

- [X] T020 [US2] Refactor feature lookup helpers to context/stash-backed resolution in src/pytest_bdd/model/gherkin_document/core.py
- [X] T021 [US2] Register gherkin registry state during parse flows in src/pytest_bdd/parser.py and src/pytest_bdd/plugin/struct_bdd/parser.py
- [X] T022 [US2] Update collector/code-generator call sites to config-aware registry lookup in src/pytest_bdd/plugin/scenario_test_collector/plugin.py and src/pytest_bdd/plugin/code_generator/plugin.py
- [X] T023 [US2] Harden lookup behavior for missing scenario-step AST links in src/pytest_bdd/model/gherkin_document/lookup.py
- [X] T024 [US2] Add regression coverage for generation/struct-bdd registry paths in tests/generation/test_generate_missing.py and tests/struct_bdd/test_steps.py

**Checkpoint**: US2 is independently functional and testable.

---

## Phase 5: User Story 3 - Context-Based Reference Resolution + Adapter Round-Trip (Priority: P3)

**Goal**: Introduce adapter layer for execution<->message conversion with deterministic ID/reference reconstruction and governed coverage outcomes.

**Independent Test**: Execute adapter and governance suites to prove deterministic round-trip links and strict runtime-required coverage handling.

### Tests for User Story 3

- [X] T025 [P] [US3] Add adapter serialization contract tests in tests/messages/test_execution_message_adapter.py
- [X] T026 [P] [US3] Add adapter round-trip integrity tests in tests/messages/test_execution_message_adapter_roundtrip.py
- [X] T027 [P] [US3] Add governance regression for adapter-related capability statuses in tests/messages_coverage/test_execution_context_governance_regression.py

### Implementation for User Story 3

- [X] T028 [US3] Implement adapter serialize/deserialize core in src/pytest_bdd/model/execution_message_adapter.py
- [X] T029 [US3] Add context-owned message reference index read/write helpers in src/pytest_bdd/plugin/scenario_runner/context_access.py and src/pytest_bdd/model/execution_context.py
- [X] T030 [US3] Integrate adapter serialization into message emission flow in src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py
- [X] T031 [US3] Integrate adapter deserialization projections into validation/replay logic in src/pytest_bdd/model/message_validation.py
- [X] T032 [US3] Enforce worker-aware deterministic keying and conflict diagnostics in src/pytest_bdd/model/execution_message_adapter.py and src/pytest_bdd/plugin/scenario_runner/context_store.py
- [X] T033 [US3] Update governance rule enforcement for Partly-Applicable/Non-Implementable evidence in src/pytest_bdd/script/message_capability_governance.py and tests/messages/test_governance.py

**Checkpoint**: US3 is independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation sync, and release-readiness checks.

- [X] T034 [P] Update feature quickstart with final adapter/governance command set in specs/009-execution-context-reporting/quickstart.md
- [X] T035 [P] Sync runtime/adapter contract docs with implemented APIs in specs/009-execution-context-reporting/contracts/execution-context-boundary.md and specs/009-execution-context-reporting/contracts/execution-message-adapter.md
- [X] T036 Run full strict validation flow and capture evidence notes in specs/009-execution-context-reporting/plan.md
- [X] T037 Run pre-commit on touched files and record completion in specs/009-execution-context-reporting/tasks.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all story work
- **Phase 3 (US1)**: Depends on Phase 2
- **Phase 4 (US2)**: Depends on Phase 2
- **Phase 5 (US3)**: Depends on Phase 2 and uses outputs from US1/US2 integration points
- **Phase 6 (Polish)**: Depends on all selected story phases

### User Story Dependency Graph

- `US1` and `US2` can start in parallel after Foundational.
- `US3` should start after foundational APIs stabilize and merge US1/US2 outputs.

Graph:
- `Setup -> Foundational -> {US1, US2} -> US3 -> Polish`

### Within Each User Story

- Write tests first and verify failure before implementation.
- Implement model/context primitives before plugin integration calls.
- Complete story-level validation before advancing priority.

### Parallel Opportunities

- Setup: `T002`, `T003`, `T004` can run in parallel.
- Foundational: `T006`, `T007` can run in parallel after `T005` shape decisions.
- US1: `T011`, `T012` can run in parallel.
- US2: `T018`, `T019` can run in parallel.
- US3: `T025`, `T026`, `T027` can run in parallel.
- Polish: `T034`, `T035` can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Parallel US1 tests
T011 tests/hook/test_gherkin_reporter_context_lifecycle.py
T012 tests/messages/test_message_emission_points.py
```

## Parallel Example: User Story 2

```bash
# Parallel US2 tests
T018 tests/model/gherkin_document/test_feature_context_lookup.py
T019 tests/hook/test_scenario_reference_resolution.py
```

## Parallel Example: User Story 3

```bash
# Parallel US3 tests
T025 tests/messages/test_execution_message_adapter.py
T026 tests/messages/test_execution_message_adapter_roundtrip.py
T027 tests/messages_coverage/test_execution_context_governance_regression.py
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 and Phase 2.
2. Deliver Phase 3 (US1) end-to-end.
3. Validate reporter read-only context behavior.
4. Demo/release MVP boundary improvement.

### Incremental Delivery

1. Setup + Foundational
2. US1 (reporter ownership boundary)
3. US2 (registry ownership migration)
4. US3 (adapter round-trip + governance hardening)
5. Polish and final validation

### Parallel Team Strategy

1. One engineer drives foundational context/index work (`T005-T010`).
2. Then split:
   - Engineer A: US1
   - Engineer B: US2
3. Converge on US3 adapter + governance integration.
4. Finish with shared polish/validation phase.

---

## Notes

- Every task strictly follows checklist format: `- [ ] Txxx [P] [USx] Description with file path`.
- Story labels appear only in user-story phases.
- Tasks are immediately executable by an LLM with explicit file targets.
