# Tasks: Python and Pytest Compatibility Alignment

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/compatibility-matrix.openapi.yaml, quickstart.md

**Tests**: Include test tasks because the specification explicitly requires automated validation and independent testability for each story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish compatibility planning artifacts and baseline tooling updates.

- [X] T001 Create feature task index and execution notes in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/tasks.md
- [X] T002 [P] Add compatibility matrix helper module skeleton in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/compatibility/matrix.py
- [X] T003 [P] Add matrix CLI/helper script entry file in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/compatibility_matrix.py
- [X] T004 [P] Add compatibility test package initializer in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared compatibility logic required by all user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Implement `CompatibilityMatrixEntry` construction and normalization in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/compatibility/matrix.py
- [X] T006 Implement pytest-to-python compatibility filtering rules in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/compatibility/matrix.py
- [X] T007 [P] Implement explicit reason-code mapping (`compatible`, `python_not_supported_by_pytest`, `pytest_unavailable`, `python_unavailable`) in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/compatibility/matrix.py
- [X] T008 [P] Add unit tests for compatibility filtering and reason codes in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_matrix_rules.py
- [X] T009 Implement tox environment expansion utility from compatibility entries in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/compatibility/matrix.py
- [X] T010 Add integration test for deterministic matrix expansion output in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_matrix_expansion.py

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Run tests on compatible versions (Priority: P1) 🎯 MVP

**Goal**: Ensure maintainers can run tests for any pytest-compatible Python/pytest pair without library-imposed version caps.

**Independent Test**: Run compatibility selection and targeted tox execution for compatible and incompatible pairs; verify execution behavior and failure messaging match spec.

### Tests for User Story 1

- [X] T011 [P] [US1] Add compatibility pair validation tests in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_pair_validation.py
- [X] T012 [P] [US1] Add failure-message behavior tests for incompatible/unavailable pairs in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_failure_messages.py

### Implementation for User Story 1

- [X] T013 [US1] Remove project-specific Python/pytest cap logic from version gating in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/compatibility/pytest.py
- [X] T014 [US1] Wire compatibility matrix selection into test-runner path in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/runner.py
- [X] T015 [US1] Implement fail-fast compatibility diagnostics in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/compatibility/matrix.py
- [X] T016 [US1] Add command to validate one requested pair in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/compatibility_matrix.py
- [X] T017 [US1] Document support policy and pair-validation command in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/README.rst

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Validate compatibility in CI matrix (Priority: P2)

**Goal**: Ensure CI validates all pytest-compatible Python/pytest pairs with explicit results.

**Independent Test**: Execute matrix generation and tox listing in CI mode and verify every compatible pair maps to at least one job and none are silently skipped.

### Tests for User Story 2

- [X] T018 [P] [US2] Add CI matrix completeness tests over generated compatible pairs in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_ci_matrix_completeness.py
- [X] T019 [P] [US2] Add contract-to-implementation conformance tests for matrix and validation outputs in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_compatibility_contract.py

### Implementation for User Story 2

- [X] T020 [US2] Update tox matrix generation to include all compatible pairs in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tox.ini
- [X] T021 [US2] Add compatibility matrix manifest output for CI inspection in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/compatibility_matrix.py
- [X] T022 [US2] Update CI workflow to consume generated full compatibility matrix in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.github/workflows/tests.yml
- [X] T023 [US2] Update quickstart CI verification commands in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/quickstart.md

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Keep existing supported versions stable (Priority: P3)

**Goal**: Add compatibility expansion without regressing currently documented supported combinations.

**Independent Test**: Compare baseline supported-version runs to post-change runs and confirm no newly introduced compatibility failures for pre-existing supported combinations.

### Tests for User Story 3

- [X] T024 [P] [US3] Add regression coverage tests for pre-existing supported combinations in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_existing_support_regression.py
- [X] T025 [P] [US3] Add tox environment naming stability tests in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_tox_env_stability.py

### Implementation for User Story 3

- [X] T026 [US3] Preserve and map legacy supported combos to compatibility-generated entries in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/compatibility/matrix.py
- [X] T027 [US3] Update contributor support declaration and migration notes in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/DOCUMENTATION.rst
- [X] T028 [US3] Add backward-compatibility validation command examples in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/docs/tutorial/pytest.ini

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, documentation, and end-to-end validation across all stories.

- [ ] T029 [P] Regenerate and verify compatibility contract examples in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/contracts/compatibility-matrix.openapi.yaml
- [ ] T030 [P] Perform full quickstart command validation and record results in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/quickstart.md
- [ ] T031 Run full tox matrix smoke verification for changed compatibility paths in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tox.ini
- [ ] T032 Final documentation consistency pass for support policy wording in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/README.rst

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies; starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2; MVP target.
- **Phase 4 (US2)**: Depends on Phase 2 and benefits from US1 pair-validation utilities.
- **Phase 5 (US3)**: Depends on Phase 2 and should run after US1 compatibility policy implementation.
- **Phase 6 (Polish)**: Depends on completion of selected user stories.

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational; no dependency on other user stories.
- **US2 (P2)**: Can start after Foundational; uses shared compatibility generation from Phase 2 and US1 utilities.
- **US3 (P3)**: Can start after Foundational; validates non-regression against existing support and can proceed after US1 core behavior lands.

### Within Each User Story

- Tests first where possible, then implementation, then documentation/integration updates.
- Keep each story independently runnable via targeted test commands.

## Parallel Opportunities

- **Setup**: T002, T003, T004 can run in parallel.
- **Foundational**: T007 and T008 can run in parallel after T005/T006 begin; T010 can proceed after T009.
- **US1**: T011 and T012 parallel; T017 can run once T013-T016 interfaces stabilize.
- **US2**: T018 and T019 parallel; T021 and T022 can run in parallel once matrix generation contract is settled.
- **US3**: T024 and T025 parallel; T027 and T028 parallel once T026 finalizes behavior.
- **Polish**: T029 and T030 parallel; T031/T032 follow final integration.

## Parallel Example: User Story 1

```bash
# Run US1 tests in parallel:
Task: "T011 [US1] Add compatibility pair validation tests in tests/compatibility/test_pair_validation.py"
Task: "T012 [US1] Add failure-message behavior tests in tests/compatibility/test_failure_messages.py"

# Run US1 docs update in parallel with implementation stabilization:
Task: "T017 [US1] Document support policy in README.rst"
```

## Parallel Example: User Story 2

```bash
# Run US2 verification tracks in parallel:
Task: "T018 [US2] CI matrix completeness tests in tests/compatibility/test_ci_matrix_completeness.py"
Task: "T019 [US2] Contract conformance tests in tests/contract/test_compatibility_contract.py"
```

## Parallel Example: User Story 3

```bash
# Run US3 regression validations in parallel:
Task: "T024 [US3] Regression coverage tests in tests/compatibility/test_existing_support_regression.py"
Task: "T025 [US3] tox env naming stability tests in tests/compatibility/test_tox_env_stability.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independently using compatibility pair validation and failure-message tests.
4. Demo/release MVP behavior before expanding matrix automation.

### Incremental Delivery

1. Ship US1 (core compatibility policy and pair validation).
2. Ship US2 (full compatible-pair CI matrix coverage).
3. Ship US3 (backward-compatibility regression hardening).
4. Finish with Phase 6 polish and full-matrix smoke verification.

### Parallel Team Strategy

1. Team aligns on Phase 1 and Phase 2 shared foundations.
2. Then split by stories:
   - Engineer A: US1 core behavior
   - Engineer B: US2 CI and contract verification
   - Engineer C: US3 regression hardening
3. Merge at Phase 6 for end-to-end validation.

## Notes

- All tasks follow required checklist format: checkbox, task ID, optional [P], required [US#] labels for story phases, and explicit file paths.
- Maintain strict compatibility-policy wording: "follow pytest compatibility matrix" and "no extra library-imposed caps".
