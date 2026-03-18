---
description: "Task list for feature 015-replace-step-context implementation"
---

# Tasks: Replace extended_step_context with StepRun

**Input**: Design documents from `/specs/015-replace-step-context/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify existing test suite runs successfully on current branch to establish a baseline

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Create `StepRun` dataclass/attr definition in a suitable location, e.g., `src/pytest_bdd/model/step_run.py` or existing model files.
- [x] T003 Update `ScenarioRun` class in `src/pytest_bdd/model/scenario_run.py` to include `step_run: Optional[StepRun] = None` attribute.

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Expose Step Execution Context via StepRun (Priority: P1) 🎯 MVP

**Goal**: Framework users writing step definitions or plugins can access the current step's execution context through a dedicated `StepRun` object available at `run.scenario_run.step_run`, completely replacing `extended_step_context`.

**Independent Test**: Can be tested by executing a suite with multiple steps and verifying that a hook or fixture accessing `run.scenario_run.step_run` receives an object that accurately reflects the properties of the currently executing step, and that `extended_step_context` is no longer available.

### Implementation for User Story 1

- [x] T004 [US1] Update runtime execution in `src/pytest_bdd/plugin/pickle_runner/plugin.py` to instantiate and assign `StepRun` to `run.scenario_run.step_run` during step setup/execution.
- [x] T005 [P] [US1] Update `tests/hook/test_scenario_reference_resolution.py` to test context resolution via `run.scenario_run.step_run` instead of `extended_step_context`.
- [x] T006 [US1] Remove the `extended_step_context` context manager/method completely from `src/pytest_bdd/plugin/pickle_runner/plugin.py` and any other definitions.
- [x] T007 [US1] Refactor any other internal usages of `extended_step_context` found in the codebase to use `run.scenario_run.step_run`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T008 [P] Ensure all test suites pass using `pytest`.
- [ ] T009 [P] Check compatibility with existing plugins/hooks if any rely on undocumented context injection.
- [ ] T010 Run `pre-commit run --all-files` to ensure all styling and type-checking pass.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- Models (`StepRun` and `ScenarioRun`) before services (execution runners).
- Setup of context before removal of deprecated context.

### Parallel Opportunities

- Tests updates can be run in parallel with implementation where they don't block.
- Refactoring usages and removing `extended_step_context` could potentially be handled in parallel with adding the new feature to the runner.

---

## Parallel Example: User Story 1

```bash
# Launch test refactoring and context removal simultaneously:
Task: "Update tests/hook/test_scenario_reference_resolution.py to test context resolution via run.scenario_run.step_run instead of extended_step_context."
Task: "Remove the extended_step_context context manager/method completely from src/pytest_bdd/plugin/pickle_runner/plugin.py and any other definitions."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently by running the test suite
5. Complete Phase 4: Polish & Cross-Cutting Concerns

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deliver feature increment

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group with the Task ID in the commit message (e.g. `feat: add StepRun class (T002)`)
- Stop at any checkpoint to validate story independently