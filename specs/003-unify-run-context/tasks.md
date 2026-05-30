<!-- markdownlint-disable MD013 -->

# Tasks: Unified Test Run Context Model

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/003-unify-run-context/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/hook-execution-context.openapi.yaml`, `quickstart.md`
**Language**: English (all task descriptions and notes)

**Tests**: Test tasks are included because the specification defines independent test criteria and measurable validation outcomes.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create scaffolding for session-root context hierarchy, hook parameter models, and validation suites.

- [X] T001 Create gherkin document package scaffold in `src/pytest_bdd/model/gherkin_document/__init__.py`
- [X] T002 Create gherkin document core scaffold in `src/pytest_bdd/model/gherkin_document/core.py`
- [X] T003 Create gherkin document registry scaffold in `src/pytest_bdd/model/gherkin_document/registry.py`
- [X] T004 Create hook parameter model scaffold in `src/pytest_bdd/model/hook_parameter_model.py`
- [X] T005 [P] Create contract test scaffold for session-root endpoints in `tests/contract/test_execution_context_contract.py`
- [X] T006 [P] Create hook parameter integration test scaffold in `tests/feature/test_execution_context_hooks.py`
- [X] T007 [P] Create hierarchy transition test scaffold in `tests/hook/test_execution_context_transitions.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build core entities, deterministic transition primitives, and baseline compatibility guarantees.

**⚠️ CRITICAL**: No user story implementation should start before this phase is complete.

- [X] T008 Implement `SessionExecutionContext` and `ExecutionContextNode` entities in `src/pytest_bdd/model/execution_context.py`
- [X] T009 Implement `HookParameterModel` and `ExecutionContextView` entities in `src/pytest_bdd/model/hook_parameter_model.py`
- [X] T010 Export session-root context symbols in `src/pytest_bdd/model/__init__.py`
- [X] T011 Implement session-root context store and child-node registry in `src/pytest_bdd/plugin/scenario_runner/context_store.py`
- [X] T012 Implement deterministic hierarchy transition engine in `src/pytest_bdd/plugin/scenario_runner/context_transitions.py`
- [X] T013 Implement hook parameter model builder utilities in `src/pytest_bdd/plugin/scenario_runner/context_access.py`
- [X] T014 Implement foundational model invariants tests in `tests/hook/test_execution_context_model.py`
- [X] T015 Implement session-root transition ordering tests in `tests/hook/test_execution_context_transitions.py`
- [X] T016 Implement baseline contract path assertions for session-root model in `tests/contract/test_execution_context_contract.py`
- [X] T017 Implement compatibility record baseline builder in `src/pytest_bdd/plugin/scenario_runner/api_compatibility.py`

**Checkpoint**: Session-root hierarchy primitives and baseline compatibility controls are ready.

---

## Phase 3: User Story 1 - Access Shared Context In Hooks (Priority: P1) 🎯 MVP

**Goal**: Hook consumers read `execution_context` from existing hook parameter models, not from a separate top-level hook argument.

**Independent Test**: Run hook flow tests to verify all supported hook parameter models expose the same embedded `execution_context` reference during one lifecycle point.

### Tests for User Story 1

- [X] T018 [P] [US1] Add contract assertions for `/hooks/{hookName}/parameter-model` in `tests/contract/test_execution_context_contract.py`
- [X] T019 [US1] Add hook parameter field-access integration tests in `tests/feature/test_execution_context_hooks.py`

### Implementation for User Story 1

- [X] T020 [US1] Integrate `HookParameterModel` creation into hook dispatch in `src/pytest_bdd/plugin/scenario_runner/plugin.py`
- [X] T021 [US1] Attach `execution_context` field/reference to existing hook parameter models in `src/pytest_bdd/plugin/scenario_runner/context_access.py`
- [X] T022 [US1] Update decorator-based hooks to consume parameter-model context field in `src/pytest_bdd/hook.py`
- [X] T023 [US1] Preserve compatibility adapters for existing hook usage patterns in `src/pytest_bdd/plugin/scenario_runner/hook.py`
- [X] T024 [US1] Add non-regression checks for existing hook consumers in `tests/hook/test_hook_execution_context_regression.py`

**Checkpoint**: Hook parameter models expose shared execution context consistently and compatibly.

---

## Phase 4: User Story 2 - Track Active Lifecycle Objects (Priority: P2)

**Goal**: Session-root context and hierarchical child nodes track active lifecycle objects deterministically with scenario isolation.

**Independent Test**: Execute hierarchy transition and isolation suites and verify correct active/inactive state across scenario boundaries.

### Tests for User Story 2

- [X] T025 [P] [US2] Add session-root lifecycle matrix tests in `tests/hook/test_execution_context_transitions.py`
- [X] T026 [US2] Add scenario isolation tests for child contexts in `tests/feature/test_execution_context_lifecycle.py`
- [X] T027 [P] [US2] Add gherkin-model refactor compatibility tests in `tests/struct_bdd/test_gherkin_document_model_compat.py`

### Implementation for User Story 2

- [X] T028 [US2] Refactor gherkin document core structures in `src/pytest_bdd/model/gherkin_document/core.py`
- [X] T029 [US2] Refactor gherkin registry and traversal helpers in `src/pytest_bdd/model/gherkin_document/registry.py`
- [X] T030 [US2] Add gherkin lookup helper module in `src/pytest_bdd/model/gherkin_document/lookup.py`
- [X] T031 [US2] Convert `src/pytest_bdd/model/gherkin_document.py` into compatibility facade re-exporting refactored modules in `src/pytest_bdd/model/gherkin_document.py`
- [X] T032 [US2] Wire scenario runner transitions to session-root and child-node contexts in `src/pytest_bdd/plugin/scenario_runner/plugin.py`
- [X] T033 [US2] Enforce child-context cleanup between scenarios while retaining session root in `src/pytest_bdd/plugin/scenario_runner/context_store.py`
- [X] T034 [US2] Add contract assertions for `/execution-context/session-root` and `/execution-context/active-set` in `tests/contract/test_execution_context_contract.py`

**Checkpoint**: Session-root hierarchy lifecycle tracking is deterministic and isolated.

---

## Phase 5: User Story 3 - Provide Clear Context For Diagnostics (Priority: P3)

**Goal**: Inactive-object and failure paths produce explicit diagnostics while keeping external API evolution additive-only.

**Independent Test**: Run diagnostic and compatibility suites and verify stable error reporting plus `removed_symbols=0` and `renamed_symbols=0`.

### Tests for User Story 3

- [X] T035 [P] [US3] Add inactive-object diagnostic tests for parameter-model access in `tests/hook/test_execution_context_diagnostics.py`
- [X] T036 [US3] Add failure-path diagnostic integration tests in `tests/struct_bdd/test_execution_context_diagnostics.py`
- [X] T037 [P] [US3] Add additive-only API compatibility tests in `tests/compatibility/test_hook_execution_context_api_surface.py`

### Implementation for User Story 3

- [X] T038 [US3] Implement structured `ContextErrorState` propagation for hierarchy lookups in `src/pytest_bdd/plugin/scenario_runner/context_access.py`
- [X] T039 [US3] Populate failure diagnostics during hook/step errors in `src/pytest_bdd/plugin/scenario_runner/plugin.py`
- [X] T040 [US3] Update compatibility symbol baseline snapshot in `tests/compatibility/hook_public_api_baseline.json`
- [X] T041 [US3] Add contract assertions for `/compatibility/external-api` in `tests/contract/test_execution_context_contract.py`

**Checkpoint**: Diagnostics are explicit and compatibility constraints are enforced.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize docs and full validation traces.

- [X] T042 [P] Document session-root hierarchy and parameter-model field contract in `docs/features/features.rst`
- [X] T043 [P] Update quickstart commands and expectations in `specs/003-unify-run-context/quickstart.md`
- [X] T044 Run full feature validation flow and record results in `specs/003-unify-run-context/quickstart.md`
- [X] T045 Record final constitution gate and compatibility evidence in `specs/003-unify-run-context/plan.md`

---

## Phase 7: Session Fixture + Stash Follow-up

**Purpose**: Implement clarified requirements for `SessionExecutionContext` fixture injection, stash canonical storage, and reporting hierarchy usage.

- [X] T046 Add session root initialization at `pytest_sessionstart` in `src/pytest_bdd/plugin/scenario_runner/plugin.py`
- [X] T047 Add canonical stash helpers and session-root bootstrap in `src/pytest_bdd/plugin/scenario_runner/context_store.py`
- [X] T048 Add session-scoped `session_execution_context` fixture in `src/pytest_bdd/plugin/scenario_runner/entrypoint.py`
- [X] T049 Add reporting snapshot builder over hierarchy/stash in `src/pytest_bdd/plugin/scenario_runner/context_access.py`
- [X] T050 Integrate reporting hierarchy snapshot capture in `src/pytest_bdd/plugin/scenario_reporter/plugin.py`
- [X] T051 Extend reporting model for context snapshot transport in `src/pytest_bdd/plugin/scenario_reporter/report.py`
- [X] T052 Add fixture/stash integration test in `tests/hook/test_execution_context_fixture_stash.py`
- [X] T053 Add reporting hierarchy test in `tests/feature/test_report_context_hierarchy.py`
- [X] T054 Extend contract path coverage for fixture/stash/reporting endpoints in `tests/contract/test_execution_context_contract.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 5 -> Phase 6.
- Phase 2 blocks all user stories.
- Phase 6 depends on completion of the selected story scope.

### User Story Dependency Graph

- US1 (P1) -> US2 (P2) -> US3 (P3)

Rationale: US1 defines hook-parameter integration contract; US2 builds hierarchy tracking and gherkin-model refactor on top of that contract; US3 depends on finalized hierarchy behavior for diagnostics and compatibility assertions.

### Within Each User Story

- Story tests first, then implementation.
- Contract assertions are added before or alongside behavior changes.
- Compatibility assertions must remain green after each story checkpoint.

---

## Parallel Execution Examples

### User Story 1

```bash
Task T018 in tests/contract/test_execution_context_contract.py
Task T019 in tests/feature/test_execution_context_hooks.py
```

### User Story 2

```bash
Task T025 in tests/hook/test_execution_context_transitions.py
Task T027 in tests/struct_bdd/test_gherkin_document_model_compat.py
```

### User Story 3

```bash
Task T035 in tests/hook/test_execution_context_diagnostics.py
Task T037 in tests/compatibility/test_hook_execution_context_api_surface.py
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Setup and Foundational phases (T001-T017).
2. Complete US1 (T018-T024).
3. Validate hook parameter-model behavior and compatibility before continuing.

### Incremental Delivery

1. Deliver US1 field-based context access in hook parameter models.
2. Deliver US2 session-root hierarchy tracking plus broad `gherkin_document` refactor.
3. Deliver US3 diagnostics and compatibility enforcement.
4. Complete polish tasks and full validation evidence.

### Task Completeness Validation

- Every user story has explicit test and implementation tasks.
- Data-model entities map to concrete implementation files.
- Contract paths map to explicit contract test tasks.
- External API minimal-change requirement is enforced by compatibility tasks.
