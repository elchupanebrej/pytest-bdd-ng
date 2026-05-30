<!-- markdownlint-disable MD013 -->

# Tasks: Enforce Non-empty BDD Headings

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/005-no-empty-bdd-headings/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/empty-heading-validation.openapi.yaml`, `quickstart.md`
**Language**: English (all task descriptions and notes)

**Tests**: Test tasks are included because the specification defines explicit independent test criteria and measurable validation outcomes.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare validation scaffolding and story-focused test modules.

- [X] T001 Create validation CLI scaffold in `src/pytest_bdd/script/validate_feature_headings.py`
- [X] T002 [P] Create heading validation model scaffold in `src/pytest_bdd/model/heading_validation.py`
- [X] T003 [P] Create parser-level validation test module in `tests/feature/test_empty_bdd_headings_validation.py`
- [X] T004 [P] Create diagnostics test module in `tests/hook/test_heading_validation_diagnostics.py`
- [X] T005 [P] Create contract test module in `tests/contract/test_empty_heading_validation_contract.py`
- [X] T006 [P] Create baseline compliance test module in `tests/doc/test_features_repository_heading_baseline.py`
- [X] T007 [P] Create snippet-boundary test module in `tests/feature/test_heading_validation_snippet_boundaries.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared validation primitives required by all user stories.

**⚠️ CRITICAL**: No user story implementation should start before this phase is complete.

- [X] T008 Implement `HeadingValidationPolicy`/`HeadingValidationViolation`/`HeadingValidationRun` dataclasses in `src/pytest_bdd/model/heading_validation.py`
- [X] T009 Implement AST heading extraction for parsed `Feature`/`Scenario`/`Scenario Outline` nodes in `src/pytest_bdd/script/validate_feature_headings.py`
- [X] T010 Implement repository scan orchestration for `features/` with deterministic file ordering in `src/pytest_bdd/script/validate_feature_headings.py`
- [X] T011 Implement deterministic violation formatting (`path`, `line`, `heading_type`, `code`, `message`) in `src/pytest_bdd/script/validate_feature_headings.py`
- [X] T012 Implement reusable validation runner API for tests and hooks in `src/pytest_bdd/script/validate_feature_headings.py`
- [X] T013 Add local pre-commit hook `validate-feature-headings` in `.pre-commit-config.yaml`

**Checkpoint**: Shared heading validation model, scan pipeline, and workflow hook are available.

---

## Phase 3: User Story 1 - Block Empty Parsed Headings (Priority: P1) 🎯 MVP

**Goal**: Reject empty parsed `Feature`, `Scenario`, and `Scenario Outline` headings with actionable diagnostics.

**Independent Test**: Seed temporary feature files with empty parsed headings and verify validation fails with path+line+heading type diagnostics.

### Tests for User Story 1

- [X] T014 [P] [US1] Add failing test for empty parsed `Feature` heading detection in `tests/feature/test_empty_bdd_headings_validation.py`
- [X] T015 [P] [US1] Add failing tests for empty parsed `Scenario` and `Scenario Outline` detection in `tests/feature/test_empty_bdd_headings_validation.py`
- [X] T016 [P] [US1] Add failing diagnostics field assertions in `tests/hook/test_heading_validation_diagnostics.py`
- [X] T017 [P] [US1] Add contract assertions for policy and scan response payloads in `tests/contract/test_empty_heading_validation_contract.py`

### Implementation for User Story 1

- [X] T018 [US1] Implement empty-title checks for parsed `Feature` headings in `src/pytest_bdd/script/validate_feature_headings.py`
- [X] T019 [US1] Implement empty-title checks for parsed `Scenario`/`Scenario Outline` headings in `src/pytest_bdd/script/validate_feature_headings.py`
- [X] T020 [US1] Implement whitespace-normalization policy application in `src/pytest_bdd/model/heading_validation.py`
- [X] T021 [US1] Implement non-zero exit behavior when violations are present in `src/pytest_bdd/script/validate_feature_headings.py`

**Checkpoint**: Empty parsed heading violations are detected and reported deterministically.

---

## Phase 4: User Story 2 - Normalize Existing Repository Files (Priority: P2)

**Goal**: Bring current repository `features/` content into compliance with zero empty parsed headings.

**Independent Test**: Run baseline scan across `features/` and confirm zero violations.

### Tests for User Story 2

- [X] T022 [P] [US2] Add failing baseline zero-violation assertion for repository features in `tests/doc/test_features_repository_heading_baseline.py`
- [X] T023 [P] [US2] Add baseline-audit contract assertions for `violations_count` and `compliant` in `tests/contract/test_empty_heading_validation_contract.py`

### Implementation for User Story 2

- [X] T024 [P] [US2] Replace empty scenario heading in `features/Feature/Load/Scenario search from base directory.feature.md`
- [X] T025 [P] [US2] Replace empty scenario heading in `features/Feature/Load/Scenario search from base url.feature.md`
- [X] T026 [P] [US2] Replace empty scenario heading in `features/Feature/Localization.feature.md`
- [X] T027 [P] [US2] Replace empty scenario heading in `features/Feature/Description.feature.md`
- [X] T028 [P] [US2] Replace empty scenario heading in `features/Feature/Tag conversion.feature.md`
- [X] T029 [P] [US2] Replace empty scenario heading in `features/Scenario/Description.feature.md`
- [X] T030 [P] [US2] Replace empty scenario heading in `features/Step/Data table.feature.md`
- [X] T031 [P] [US2] Replace empty scenario heading in `features/Step/Doc string.feature.md`
- [X] T032 [P] [US2] Replace empty scenario heading in `features/Scenario/Outline/Examples Tag.feature.md`
- [X] T033 [P] [US2] Replace empty scenario heading in `features/Step definition/Pytest fixtures substitution.feature.md`
- [X] T034 [P] [US2] Replace empty scenario heading in `features/Step definition/Parameters/Parsing by custom parser.feature.md`
- [X] T035 [P] [US2] Replace empty scenario heading in `features/Step definition/Parameters/Defaults.feature.md`
- [X] T036 [US2] Implement baseline audit summary output (`violations_count`, `compliant`) in `src/pytest_bdd/script/validate_feature_headings.py`

**Checkpoint**: Repository baseline under `features/` is compliant with heading policy.

---

## Phase 5: User Story 3 - Keep Scope Focused on Real Parsed Headings (Priority: P3)

**Goal**: Enforce the rule only on parser-recognized headings and avoid false positives from literal snippets.

**Independent Test**: Provide markdown/code snippets containing `Feature:`/`Scenario:` text and verify they do not trigger violations.

### Tests for User Story 3

- [X] T037 [P] [US3] Add failing snippet-boundary test for indented literal keyword lines in `tests/feature/test_heading_validation_snippet_boundaries.py`
- [X] T038 [P] [US3] Add failing snippet-boundary test for fenced gherkin snippets in `tests/feature/test_heading_validation_snippet_boundaries.py`

### Implementation for User Story 3

- [X] T039 [US3] Implement parsed-heading-only filtering to ignore non-heading snippet content in `src/pytest_bdd/script/validate_feature_headings.py`
- [X] T040 [US3] Document heading-validation scope and false-positive boundaries in `docs/internal/feature-heading-validation.rst`
- [X] T041 [US3] Add heading-validation notes entry to `docs/internal/index.rst`
- [X] T042 [US3] Restrict `validate-feature-headings` hook input to repository feature paths in `.pre-commit-config.yaml`

**Checkpoint**: False positives from non-parsed snippet content are prevented.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation evidence and delivery readiness checks across all stories.

- [X] T043 [P] Run targeted heading-validation pytest suites and record commands in `specs/005-no-empty-bdd-headings/quickstart.md`
- [X] T044 [P] Run pre-commit validation and record pass criteria in `specs/005-no-empty-bdd-headings/quickstart.md`
- [X] T045 [P] Run optional tox slice (`py314-pytestlatest`) and record result in `specs/005-no-empty-bdd-headings/quickstart.md`
- [X] T046 Verify final task-to-story traceability notes in `specs/005-no-empty-bdd-headings/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2.
- **Phase 5 (US3)**: Depends on Phase 2 plus US1 and US2 completion.
- **Phase 6 (Polish)**: Depends on all user stories being complete.

### User Story Dependency Graph

- **US1 (P1)** and **US2 (P2)** can proceed in parallel after Foundational completion.
- **US3 (P3)** depends on US1 detection behavior and US2 baseline normalization.

Graph: `Foundational -> {US1, US2} -> US3`

### Within Each User Story

- Tests are written first and should fail before implementation changes.
- Data/policy model updates precede scan/report wiring.
- Story-level validations pass before moving to next priority scope.

---

## Parallel Execution Examples

### User Story 1

```bash
Task T014 in tests/feature/test_empty_bdd_headings_validation.py
Task T016 in tests/hook/test_heading_validation_diagnostics.py
Task T017 in tests/contract/test_empty_heading_validation_contract.py
```

### User Story 2

```bash
Task T024 in features/Feature/Load/Scenario search from base directory.feature.md
Task T025 in features/Feature/Load/Scenario search from base url.feature.md
Task T026 in features/Feature/Localization.feature.md
```

### User Story 3

```bash
Task T037 in tests/feature/test_heading_validation_snippet_boundaries.py
Task T038 in tests/feature/test_heading_validation_snippet_boundaries.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate parser-level rejection and deterministic diagnostics.

### Incremental Delivery

1. Deliver US1 (detection and diagnostics).
2. Deliver US2 (repository baseline cleanup).
3. Deliver US3 (false-positive boundary enforcement).
4. Run Phase 6 cross-cutting validation and record evidence.

### Parallel Team Strategy

1. Complete Setup + Foundational together.
2. Split US1 and US2 implementation in parallel.
3. Integrate US1+US2 outputs into US3 scope and finish polish.

---

## Notes

- `[P]` tasks touch different files and can run in parallel.
- `[US1]`, `[US2]`, `[US3]` labels map tasks directly to user stories.
- Every task includes an explicit file path for direct execution.
- Commit with task IDs in commit messages per constitution requirements.
- Run pre-commit and resolve all issues before each commit.
- Traceability check completed on 2026-02-25: each user-story task includes
  story label and explicit file path.
