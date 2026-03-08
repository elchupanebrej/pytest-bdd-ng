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

**Purpose**: Establish regression scaffolds and migration inventory for the no-`Feature` refactor.

- [X] T001 Add no-`Feature` runtime API baseline assertions in tests/compatibility/test_hook_run_api_surface.py and tests/hook/test_scenario_locator_pipeline.py
- [X] T002 [P] Add run-owned feature binding test scaffolds in tests/hook/test_scenario_run_model.py and tests/model/gherkin_document/test_feature_context_lookup.py
- [X] T003 [P] Add adapter/validation no-`Feature` regression scaffolds in tests/messages/test_execution_message_adapter.py and tests/messages/test_message_validation.py
- [X] T004 [P] Add reporter/serializer no-`Feature` regression scaffolds in tests/hook/test_gherkin_reporter_context_lifecycle.py and tests/feature/test_report.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Introduce run-owned feature state and shared lookup helpers required by all stories.

**CRITICAL**: No user story work starts until this phase is complete.

- [X] T005 Implement `FeatureRuntimeBinding` and run-owned feature registry in src/pytest_bdd/model/scenario_run.py
- [X] T006 [P] Add `Run`/`ScenarioRun` helper APIs for feature metadata, source resolution, and AST lookup in src/pytest_bdd/model/scenario_run.py and src/pytest_bdd/plugin/pickle_runner/run_access.py
- [X] T007 [P] Refactor shared registry resolution to consume run-owned bindings instead of `Feature` adapters in src/pytest_bdd/model/message_registry.py and src/pytest_bdd/model/gherkin_document/core.py
- [X] T008 [P] Update scenario-locator observer contracts to carry canonical message objects only in src/pytest_bdd/scenario_locator.py and src/pytest_bdd/plugin/scenario_test_collector/hook.py
- [X] T009 Register and hydrate feature bindings during collection and scenario setup in src/pytest_bdd/plugin/scenario_test_collector/plugin.py and src/pytest_bdd/plugin/pickle_runner/plugin.py
- [X] T010 Add foundational run-binding and stash regressions in tests/hook/test_run_fixture_stash.py and tests/hook/test_scenario_run_model.py

**Checkpoint**: Run-owned feature bindings and shared lookup helpers are available to all story phases.

---

## Phase 3: User Story 1 - Context-Driven Reporter State (Priority: P1) 🎯 MVP

**Goal**: Reporters read lifecycle and feature metadata from `Run` / `ScenarioRun` only, with no duplicated reporter state and no dependence on `Feature`.

**Independent Test**: Run reporter and scenario-report suites and verify lifecycle IDs, feature metadata, and step metadata are derived from `Run` / `ScenarioRun` without constructing or reading `Feature`.

### Tests for User Story 1

- [X] T011 [P] [US1] Add reporter read-only lifecycle regressions in tests/hook/test_gherkin_reporter_context_lifecycle.py
- [X] T012 [P] [US1] Add run-context reporter hierarchy regressions in tests/feature/test_report_context_hierarchy.py and tests/feature/test_report.py
- [X] T013 [P] [US1] Add message-emission regressions for reporter lookups without `Feature` adapters in tests/messages/test_message_emission_points.py

### Implementation for User Story 1

- [X] T014 [US1] Remove reporter-side `Feature` adapter reads from src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py
- [X] T015 [US1] Resolve scenario-report feature metadata and step serialization through run-owned helpers in src/pytest_bdd/plugin/scenario_reporter/report.py and src/pytest_bdd/plugin/scenario_reporter/plugin.py
- [X] T016 [US1] Route reporter lookup helpers through `Run` / `ScenarioRun` feature-binding accessors in src/pytest_bdd/plugin/pickle_runner/run_access.py and src/pytest_bdd/model/scenario_run.py
- [X] T017 [US1] Update reporter-facing integration assertions to consume canonical runtime objects in tests/feature/test_report.py and tests/messages/test_messages.py

**Checkpoint**: Reporter and scenario serialization flows are fully read-only over `Run` / `ScenarioRun` and do not depend on `Feature`.

---

## Phase 4: User Story 2 - Run-Owned Feature State (Priority: P2)

**Goal**: Parser, locator, collector, fixture, and code-generation boundaries stop constructing or consuming `Feature`; feature-level execution state is fully owned by `Run` / `ScenarioRun`.

**Independent Test**: Collect and execute features with nested rules/backgrounds and verify hooks, fixtures, locators, and code generation operate on `Source`, `GherkinDocument`, `Pickle`, and `Run` / `ScenarioRun` only.

### Tests for User Story 2

- [X] T018 [P] [US2] Add parser/locator no-`Feature` pipeline regressions in tests/hook/test_scenario_locator_pipeline.py and tests/model/gherkin_document/test_feature_context_lookup.py
- [X] T019 [P] [US2] Add fixture and hook surface regressions for no `feature` fixture in tests/compatibility/test_hook_run_api_surface.py and tests/hook/test_run_scenario_runtime_unit.py
- [X] T020 [P] [US2] Add code-generation and step-fixture regressions for canonical feature objects in tests/generation/test_generate.py and tests/struct_bdd/test_steps.py

### Implementation for User Story 2

- [X] T021 [US2] Stop building `Feature` adapters in parser flows in src/pytest_bdd/parser.py and src/pytest_bdd/compatibility/parser.py
- [X] T022 [US2] Replace `Feature`-typed scenario-locator protocols and filters with canonical message objects in src/pytest_bdd/scenario_locator.py and src/pytest_bdd/feature_locator.py
- [X] T023 [US2] Remove runtime `feature` fixture and related compatibility plumbing in src/pytest_bdd/plugin/pickle_runner/entrypoint.py and src/pytest_bdd/plugin/pickle_runner/api_compatibility.py
- [X] T024 [US2] Refactor collection parametrization and scenario decorators to use run-owned feature bindings instead of `Feature` wrappers in src/pytest_bdd/plugin/scenario_test_collector/plugin.py and src/pytest_bdd/scenario.py
- [X] T025 [US2] Replace remaining `Feature` helper usage in runtime and code-generation paths in src/pytest_bdd/plugin/code_generator/plugin.py and src/pytest_bdd/plugin/pickle_runner/run_access.py
- [X] T026 [US2] Remove adapter-only responsibilities from src/pytest_bdd/model/gherkin_document/core.py and narrow exports in src/pytest_bdd/model/gherkin_document/__init__.py

**Checkpoint**: Feature collection, runtime APIs, and code generation no longer construct or consume `Feature`.

---

## Phase 5: User Story 3 - Context-Based Reference Resolution (Priority: P3)

**Goal**: Adapter, validation, and governance flows resolve feature/scenario/step relationships through run-owned registries and canonical message objects only.

**Independent Test**: Run adapter, message validation, and governance suites and verify reference resolution and coverage gating work with run-owned bindings and without any `Feature` adapter involvement.

### Tests for User Story 3

- [X] T027 [P] [US3] Add adapter projection tests for run-owned feature bindings in tests/messages/test_execution_message_adapter.py and tests/messages/test_execution_message_adapter_roundtrip.py
- [X] T028 [P] [US3] Add validation and governance regressions for the no-`Feature` adapter path in tests/messages/test_message_validation.py and tests/messages/test_governance.py
- [X] T029 [US3] Add end-to-end reference-resolution regressions through run-owned registries in tests/hook/test_scenario_reference_resolution.py and tests/messages_coverage/test_full_capability_governance.py

### Implementation for User Story 3

- [X] T030 [US3] Extend execution/message projections to use `FeatureRuntimeBinding` and canonical message objects only in src/pytest_bdd/model/execution_message_adapter.py
- [X] T031 [US3] Route validation and reporter emission through adapter-normalized run-owned projections in src/pytest_bdd/model/message_validation.py and src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py
- [X] T032 [US3] Resolve feature/scenario/step metadata through run-owned registries in src/pytest_bdd/model/message_registry.py and src/pytest_bdd/plugin/pickle_runner/run_access.py
- [X] T033 [US3] Enforce governance rules for the no-`Feature` runtime surface in src/pytest_bdd/model/message_status_governance.py and src/pytest_bdd/script/message_capability_governance.py

**Checkpoint**: Adapter, validation, and governance flows are fully aligned to run-owned feature state and canonical message objects.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize documentation, validation evidence, and cross-cutting cleanup for the no-`Feature` API surface.

- [X] T034 [P] Update quickstart validation commands for the no-`Feature` runtime surface in specs/009-execution-context-reporting/quickstart.md
- [X] T035 [P] Update execution-context and adapter contracts for the final no-`Feature` API in specs/009-execution-context-reporting/contracts/execution-context-boundary.md and specs/009-execution-context-reporting/contracts/execution-message-adapter.md and specs/009-execution-context-reporting/contracts/runtime-api-without-feature.md
- [X] T036 [P] Update governance and research artifacts for the final no-`Feature` design in specs/009-execution-context-reporting/contracts/governance-gate-contract.md and specs/009-execution-context-reporting/research.md
- [X] T037 Run targeted no-`Feature` regression commands from tests/hook/test_scenario_locator_pipeline.py and tests/compatibility/test_hook_run_api_surface.py and tests/feature/test_report.py and tests/messages/test_execution_message_adapter.py and record outcomes in specs/009-execution-context-reporting/plan.md
- [X] T038 Run the full strict audit from specs/009-execution-context-reporting/quickstart.md and record evidence in specs/009-execution-context-reporting/plan.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: starts immediately
- **Phase 2 (Foundational)**: depends on Phase 1 and blocks all user stories
- **Phase 3 (US1)**: depends on Phase 2
- **Phase 4 (US2)**: depends on Phase 2
- **Phase 5 (US3)**: depends on Phases 3 and 4 stabilizing run-owned binding and adapter inputs
- **Phase 6 (Polish)**: depends on completed story phases

### User Story Dependency Graph

- `Setup -> Foundational -> {US1, US2} -> US3 -> Polish`

### Within Each User Story

- Tests first; confirm failing state before implementation
- Runtime model and lookup helpers before plugin integration
- Plugin integration before end-to-end regression updates
- Story-level validation before moving to the next priority

### Parallel Opportunities

- Setup: `T002`, `T003`, `T004`
- Foundational: `T006`, `T007`, `T008`
- US1 tests: `T011`, `T012`, `T013`
- US2 tests: `T018`, `T019`, `T020`
- US3 tests: `T027`, `T028`
- Polish docs: `T034`, `T035`, `T036`

---

## Parallel Example: User Story 1

```bash
T011 tests/hook/test_gherkin_reporter_context_lifecycle.py
T012 tests/feature/test_report_context_hierarchy.py
T013 tests/messages/test_message_emission_points.py
```

## Parallel Example: User Story 2

```bash
T018 tests/hook/test_scenario_locator_pipeline.py
T019 tests/compatibility/test_hook_run_api_surface.py
T020 tests/generation/test_generate.py
```

## Parallel Example: User Story 3

```bash
T027 tests/messages/test_execution_message_adapter.py
T028 tests/messages/test_message_validation.py
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate reporter and scenario serialization behavior independently.
4. Ship the read-only reporter boundary before broader API-surface migration.

### Incremental Delivery

1. Setup + Foundational
2. US1 (reporter and serializer read-only boundary)
3. US2 (remove `Feature` from parser, locator, fixture, and codegen paths)
4. US3 (adapter, validation, and governance alignment)
5. Polish and full strict validation

### Parallel Team Strategy

1. Engineer A: run-owned binding model and shared lookup helpers
2. Engineer B: reporter and serializer migration (US1)
3. Engineer C: parser/locator/fixture/codegen migration (US2)
4. Converge for adapter/governance work (US3) and final validation

---

## Notes

- All tasks follow strict checklist format.
- Story labels are used only in user-story phases.
- Tasks include concrete file paths and are executable without extra context.
