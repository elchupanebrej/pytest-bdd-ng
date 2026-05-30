# Tasks: Execution Context Reporting Consistency

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. The specification defines independent tests per story and strict validation/gating behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable (different files, no dependency on incomplete tasks)
- **[Story]**: Present only for user-story phases (`[US1]`, `[US2]`, `[US3]`)
- Every task includes concrete file path(s)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish failing regressions for the no-`Feature`, stash-backed runtime boundary.

- [X] T001 Add no-`Feature` and stash-only runtime API baseline assertions in `tests/compatibility/test_hook_run_api_surface.py` and `tests/hook/test_scenario_locator_pipeline.py`
- [X] T002 [P] Add run-owned feature binding and shared-registry regression scaffolds in `tests/hook/test_scenario_run_model.py` and `tests/model/gherkin_document/test_feature_context_lookup.py`
- [X] T003 [P] Add reporter lifecycle and stash-backed ID-generation regressions in `tests/hook/test_gherkin_reporter_context_lifecycle.py` and `tests/hook/test_reporting_context_snapshot_unit.py`
- [X] T004 [P] Add adapter, validation, and governance scaffolds for stash-backed IDs and no-`Feature` surfaces in `tests/messages/test_execution_message_adapter.py`, `tests/messages/test_message_validation.py`, and `tests/messages/test_governance.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Introduce stash-backed runtime services and run-owned lookup helpers required by all stories.

**CRITICAL**: No user story work starts until this phase is complete.

- [X] T005 Implement stash-backed session service accessors for `Run`, `EnvelopeRegistry`, and `pytest_bdd_id_generator` in `src/pytest_bdd/model/scenario_run.py` and `src/pytest_bdd/plugin/pickle_runner/run_access.py`
- [X] T006 [P] Remove config-attribute `pytest_bdd_id_generator` protocol assumptions from `src/pytest_bdd/types/protocol.py` and update runtime hook access in `src/pytest_bdd/hook.py`
- [X] T007 [P] Initialize and reuse `pytest_bdd_id_generator` through `config.stash` during plugin startup in `src/pytest_bdd/plugin/pickle_runner/entrypoint.py` and `src/pytest_bdd/plugin/pickle_runner/plugin.py`
- [X] T008 [P] Refactor parser and scenario-location entry points to resolve the ID generator from stash-backed helpers in `src/pytest_bdd/parser.py` and `src/pytest_bdd/scenario_locator.py`
- [X] T009 [P] Refactor step-definition and struct-BDD message builders to use stash-backed ID-generator lookup in `src/pytest_bdd/steps.py` and `src/pytest_bdd/plugin/struct_bdd/model.py`
- [X] T010 Register feature bindings and canonical `Source -> GherkinDocument -> Pickle` collection events in `src/pytest_bdd/plugin/scenario_test_collector/plugin.py` and `src/pytest_bdd/plugin/scenario_test_collector/hook.py`
- [X] T011 Add foundational stash and collection-order regressions in `tests/hook/test_run_fixture_stash.py`, `tests/hook/test_scenario_collection_read_hooks.py`, and `tests/hook/test_run_scenario_runtime_unit.py`

**Checkpoint**: Stash-backed runtime services and run-owned feature bindings are available to all story phases.

---

## Phase 3: User Story 1 - Context-Driven Reporter State (Priority: P1) 🎯 MVP

**Goal**: Reporters read lifecycle and feature metadata from `Run` / `ScenarioRun` only, with no duplicated reporter state and no ad-hoc `config` attribute access.

**Independent Test**: Run reporter and scenario-report suites and verify lifecycle IDs, feature metadata, and step metadata are derived from `Run` / `ScenarioRun` and stash-backed services only.

### Tests for User Story 1

- [X] T012 [P] [US1] Add reporter read-only lifecycle regressions for stash-backed IDs in `tests/hook/test_gherkin_reporter_context_lifecycle.py`
- [X] T013 [P] [US1] Add report-context and serialized metadata regressions in `tests/feature/test_report_context_hierarchy.py` and `tests/feature/test_report.py`
- [X] T014 [P] [US1] Add message-emission regressions for reporter paths without `Feature` or config-attribute access in `tests/messages/test_message_emission_points.py` and `tests/messages/test_messages.py`

### Implementation for User Story 1

- [X] T015 [US1] Remove ad-hoc `config.pytest_bdd_id_generator` reads from `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T016 [US1] Resolve reporter lifecycle correlation and feature metadata through `Run` / `ScenarioRun` helpers in `src/pytest_bdd/plugin/scenario_reporter/report.py` and `src/pytest_bdd/plugin/scenario_reporter/plugin.py`
- [X] T017 [US1] Route reporter lookup and snapshot helpers through stash-backed run access in `src/pytest_bdd/plugin/pickle_runner/run_access.py` and `src/pytest_bdd/hook.py`
- [X] T018 [US1] Update reporter-facing integration assertions to consume canonical runtime objects and stash-backed IDs in `tests/feature/test_report.py` and `tests/messages/test_messages.py`

**Checkpoint**: Reporter and scenario-serialization flows are fully read-only over `Run` / `ScenarioRun` and no longer depend on `Feature` or config attributes for ID generation.

---

## Phase 4: User Story 2 - Run-Owned Feature State (Priority: P2)

**Goal**: Parser, locator, collector, fixture, and code-generation boundaries stop constructing or consuming `Feature`; feature-level execution state and shared ID services are fully owned by `Run` / `ScenarioRun` and `config.stash`.

**Independent Test**: Collect and execute features with nested rules and backgrounds and verify hooks, fixtures, locators, and code generation operate on `Source`, `GherkinDocument`, `Pickle`, and stash-backed runtime services only.

### Tests for User Story 2

- [X] T019 [P] [US2] Add parser and locator regressions for no-`Feature` and stash-backed ID resolution in `tests/hook/test_scenario_locator_pipeline.py` and `tests/hook/test_scenario_collection_read_hooks.py`
- [X] T020 [P] [US2] Add fixture and hook-surface regressions for run-only and stash-only runtime services in `tests/compatibility/test_hook_run_api_surface.py` and `tests/hook/test_run_scenario_runtime_unit.py`
- [X] T021 [P] [US2] Add code-generation and struct-BDD regressions for canonical message objects and stash-backed IDs in `tests/generation/test_generate.py`, `tests/struct_bdd/test_deserialization.py`, and `tests/struct_bdd/test_gherkin_document_model_compat.py`

### Implementation for User Story 2

- [X] T022 [US2] Stop relying on config-attribute ID-generator state in parser compatibility flows in `src/pytest_bdd/compatibility/parser.py` and `src/pytest_bdd/parser.py`
- [X] T023 [US2] Replace config-attribute ID-generator resolution in feature discovery and scenario location in `src/pytest_bdd/scenario_locator.py` and `src/pytest_bdd/feature_locator.py`
- [X] T024 [US2] Remove executable `feature` and `scenario` compatibility plumbing and surface only canonical fixtures in `src/pytest_bdd/plugin/pickle_runner/entrypoint.py` and `src/pytest_bdd/plugin/pickle_runner/api_compatibility.py`
- [X] T025 [US2] Refactor collection parametrization and scenario decorators to consume `Source`, `GherkinDocument`, `Pickle`, and stash-backed runtime services in `src/pytest_bdd/plugin/scenario_test_collector/plugin.py` and `src/pytest_bdd/scenario.py`
- [X] T026 [US2] Replace remaining feature-wrapper and config-attribute helper usage in code-generation and struct-BDD paths in `src/pytest_bdd/plugin/code_generator/plugin.py`, `src/pytest_bdd/plugin/struct_bdd/model.py`, and `src/pytest_bdd/plugin/struct_bdd/model_builder.py`
- [X] T027 [US2] Remove leftover runtime API references to `Feature` and `config.pytest_bdd_id_generator` in `src/pytest_bdd/hook.py` and `src/pytest_bdd/plugin/pickle_runner/run_access.py`

**Checkpoint**: Feature collection, runtime APIs, and code generation no longer construct or consume `Feature`, and session-shared ID generation is fully stash-backed.

---

## Phase 5: User Story 3 - Context-Based Reference Resolution (Priority: P3)

**Goal**: Adapter, validation, and governance flows resolve feature, scenario, and step relationships through run-owned registries and stash-backed services only.

**Independent Test**: Run adapter, message validation, and governance suites and verify reference resolution and coverage gating work with run-owned bindings, canonical message objects, and stash-backed runtime services only.

### Tests for User Story 3

- [X] T028 [P] [US3] Add adapter projection and round-trip regressions for run-owned registry lookup in `tests/messages/test_execution_message_adapter.py` and `tests/messages/test_execution_message_adapter_roundtrip.py`
- [X] T029 [P] [US3] Add validation and governance regressions for stash-backed runtime evidence in `tests/messages/test_message_validation.py`, `tests/messages/test_governance.py`, and `tests/messages_coverage/test_run_governance_regression.py`
- [X] T030 [US3] Add end-to-end reference-resolution regressions through shared registries in `tests/hook/test_scenario_reference_resolution.py` and `tests/messages_coverage/test_full_capability_governance.py`

### Implementation for User Story 3

- [X] T031 [US3] Route execution-message projections through run-owned registries and stash-backed services only in `src/pytest_bdd/model/execution_message_adapter.py` and `src/pytest_bdd/model/message_registry.py`
- [X] T032 [US3] Enforce adapter-normalized validation paths without config-attribute fallbacks in `src/pytest_bdd/model/message_validation.py` and `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T033 [US3] Align governance classification and capability inventory with stash-backed and runtime-only evidence rules in `src/pytest_bdd/model/message_status_governance.py`, `src/pytest_bdd/script/message_capability_governance.py`, and `src/pytest_bdd/model/coverage/tracker.py`
- [X] T034 [US3] Resolve remaining feature, scenario, and step lookups through `Run` / `ScenarioRun` helpers in `src/pytest_bdd/model/scenario_run.py` and `src/pytest_bdd/plugin/pickle_runner/run_access.py`

**Checkpoint**: Adapter, validation, and governance flows are fully aligned to run-owned registries, canonical message objects, and stash-backed ID generation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize documentation, contract text, and validation evidence for the stash-backed no-`Feature` runtime surface.

- [X] T035 [P] Update quickstart validation commands for stash-backed runtime services and the no-`Feature` API in `specs/009-execution-context-reporting/quickstart.md`
- [X] T036 [P] Update research, data-model, and execution-context contract text for stash-only `pytest_bdd_id_generator` and shared registry ownership in `specs/009-execution-context-reporting/research.md`, `specs/009-execution-context-reporting/data-model.md`, and `specs/009-execution-context-reporting/contracts/execution-context-boundary.md`
- [X] T037 [P] Update runtime API and adapter contract text for stash-backed ID services in `specs/009-execution-context-reporting/contracts/runtime-api-without-feature.md` and `specs/009-execution-context-reporting/contracts/execution-message-adapter.md`
- [X] T038 Run targeted stash and no-`Feature` regression commands from `specs/009-execution-context-reporting/quickstart.md` and record outcomes in `specs/009-execution-context-reporting/plan.md`
- [X] T039 Run the full strict audit from `specs/009-execution-context-reporting/quickstart.md` and record evidence in `specs/009-execution-context-reporting/plan.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: starts immediately
- **Phase 2 (Foundational)**: depends on Phase 1 and blocks all user stories
- **Phase 3 (US1)**: depends on Phase 2
- **Phase 4 (US2)**: depends on Phase 2
- **Phase 5 (US3)**: depends on Phases 3 and 4 stabilizing run-owned bindings and adapter inputs
- **Phase 6 (Polish)**: depends on completed story phases

### User Story Dependency Graph

- `Setup -> Foundational -> {US1, US2} -> US3 -> Polish`

### Within Each User Story

- Tests first; confirm failing state before implementation
- Runtime and stash-service helpers before plugin integration
- Plugin integration before end-to-end regression updates
- Story-level validation before moving to the next priority

### Parallel Opportunities

- Setup: `T002`, `T003`, `T004`
- Foundational: `T006`, `T007`, `T008`, `T009`
- US1 tests: `T012`, `T013`, `T014`
- US2 tests: `T019`, `T020`, `T021`
- US3 tests: `T028`, `T029`
- Polish docs: `T035`, `T036`, `T037`

---

## Parallel Example: User Story 1

```bash
T012 tests/hook/test_gherkin_reporter_context_lifecycle.py
T013 tests/feature/test_report_context_hierarchy.py
T014 tests/messages/test_message_emission_points.py
```

## Parallel Example: User Story 2

```bash
T019 tests/hook/test_scenario_locator_pipeline.py
T020 tests/compatibility/test_hook_run_api_surface.py
T021 tests/generation/test_generate.py
```

## Parallel Example: User Story 3

```bash
T028 tests/messages/test_execution_message_adapter.py
T029 tests/messages/test_message_validation.py
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate reporter and scenario-serialization behavior independently.
4. Ship the read-only reporter boundary before broader collection and governance migration.

### Incremental Delivery

1. Setup + Foundational
2. US1 (reporter and serializer read-only boundary)
3. US2 (remove `Feature` and config-attribute ID access from parser, locator, fixture, and code-generation paths)
4. US3 (adapter, validation, and governance alignment)
5. Polish and full strict validation

### Parallel Team Strategy

1. Engineer A: stash-backed runtime services and shared lookup helpers
2. Engineer B: reporter and serializer migration (US1)
3. Engineer C: parser, locator, fixture, and code-generation migration (US2)
4. Converge for adapter and governance work (US3) and final validation

---

## Notes

- All tasks follow the strict checklist format.
- Story labels are used only in user-story phases.
- Tasks include concrete file paths and are executable without extra context.
