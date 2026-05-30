---
description: "Task list for Cucumber Formatter Support"
---

# Tasks: Cucumber Formatter Support

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/`
**Prerequisites**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/plan.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/spec.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/research.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/data-model.md`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/contracts/`

**Tests**: Validation-first delivery is required for this feature. Add the listed contract, e2e, compatibility, and hook regressions before implementation tasks are considered complete.

**Organization**: Tasks are grouped by user story to keep the formatter CLI increment independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps the task to one user story (`[US1]`)
- Include exact file paths in every task description

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the shared validation scaffolding and test harness used across formatter scenarios

- [X] T001 Create contract and fake-runtime scaffolding in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_cucumber_formatter_cli_contract.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/cucumber_formatter_support.py`
- [X] T002 [P] Create BDD formatter acceptance scaffolding in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/_cucumber_formatters.feature` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters_feature.py`
- [X] T003 [P] Create pytest and lifecycle regression scaffolding in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_gherkin_reporter_context_lifecycle.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared formatter metadata, validation, and compatibility boundaries that block all story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Define supported formatter metadata and CLI option ownership in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py`
- [X] T005 Implement the formatter execution-plan and validation primitives in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T006 [P] Add npm package discovery and global auto-provisioning helpers in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/util/npm_resource.py`
- [X] T007 [P] Preserve legacy `--cucumberjson` ownership in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/cucumber_json/entrypoint.py`

**Checkpoint**: Formatter metadata, validation rules, package-resolution helpers, and legacy JSON option boundaries are defined for story implementation.

---

## Phase 3: User Story 1 - Configure formatters via command-line flags (Priority: P1) 🎯 MVP

**Goal**: Users can request any supported cucumber formatter from pytest CLI flags, receive one validated terminal formatter at most, generate non-conflicting file outputs, and get deterministic diagnostics for provisioning or path failures.

**Independent Test**: Run a sample suite with each supported formatter flag, verify terminal/file outputs, confirm xdist uses the consolidated NDJSON stream, and verify fail-fast errors for terminal conflicts, duplicate file targets, and missing directories.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests first, ensure they fail before implementation**

- [X] T008 [P] [US1] Add contract tests for supported flags, output modes, legacy JSON separation, and validation errors in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_cucumber_formatter_cli_contract.py`
- [X] T009 [P] [US1] Add pytest e2e coverage for terminal/file formatter outputs, duplicate file targets, missing directories, and provisioning diagnostics in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters.py`
- [X] T010 [P] [US1] Add BDD acceptance scenarios for user-visible formatter output and fail-fast CLI errors in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/_cucumber_formatters.feature` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters_feature.py`
- [X] T011 [P] [US1] Add sessionfinish, xdist, standalone-reuse, and legacy-boundary regressions in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_gherkin_reporter_context_lifecycle.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_e2e.py`, `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_render_cucumber_formatters.py`, and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/feature/test_cucumber_json.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement formatter request normalization and CLI wiring in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T013 [US1] Implement fail-fast validation for terminal conflicts, missing directories, and duplicate file targets in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/render_cucumber_formatters.py`
- [X] T014 [US1] Implement NDJSON-to-formatter render planning and Node subprocess execution in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- [X] T015 [US1] Implement formatter package auto-provisioning and manual-install diagnostics in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/util/npm_resource.py`
- [X] T016 [US1] Align xdist-safe post-session rendering and standalone renderer reuse with the shared execution plan in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/render_cucumber_formatters.py`

**Checkpoint**: User Story 1 is fully functional and independently testable through pytest CLI flags, with deterministic validation and consolidated post-run rendering.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Finalize user-facing documentation, markdown-backed examples, and command-level validation notes

- [X] T017 [P] Update user-facing formatter documentation and markdown-backed examples in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/07 Report/09 Cucumber formatter reports.feature.md` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/doc/test_cucumber_formatter_report_doc_parse.py`
- [X] T018 [P] Update quickstart-aligned acceptance notes in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/quickstart.md` and `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_report_doc_cucumber_formatters.py`
- [X] T019 Document the final validation command set and any command corrections in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/012-cucumber-formatters-support/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all story work
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **Polish (Phase 4)**: Depends on User Story 1 completion

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Phase 2 and has no dependencies on other user stories

### Within User Story 1

- Tests in `T008`-`T011` must be written and failing before `T012`-`T016`
- `T012` depends on `T004`-`T007`
- `T013` depends on `T005` and `T012`
- `T014` depends on `T012` and `T013`
- `T015` depends on `T006` and `T014`
- `T016` depends on `T014` and `T015`

### Dependency Graph

- `Phase 1 -> Phase 2 -> US1 -> Phase 4`
- `T004 -> T012 -> T013 -> T014 -> T015 -> T016`
- `T006 -> T015`
- `T007 -> T011`

## Parallel Opportunities

- `T002` and `T003` can run in parallel after `T001`
- `T006` and `T007` can run in parallel after `T004`
- `T008`, `T009`, `T010`, and `T011` can run in parallel once Phase 2 completes
- `T017` and `T018` can run in parallel after `T016`

---

## Parallel Example: User Story 1

```bash
# Launch the User Story 1 validation tasks together:
Task: "Add contract tests for supported flags, output modes, legacy JSON separation, and validation errors in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_cucumber_formatter_cli_contract.py"
Task: "Add pytest e2e coverage for terminal/file formatter outputs, duplicate file targets, missing directories, and provisioning diagnostics in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters.py"
Task: "Add BDD acceptance scenarios for user-visible formatter output and fail-fast CLI errors in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/_cucumber_formatters.feature and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters_feature.py"
Task: "Add sessionfinish, xdist, standalone-reuse, and legacy-boundary regressions in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_gherkin_reporter_context_lifecycle.py, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_e2e.py, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_render_cucumber_formatters.py, and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/feature/test_cucumber_json.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run the focused formatter contract, e2e, compatibility, hook, and xdist checks for User Story 1
5. Only after US1 passes, continue to Phase 4 documentation and quickstart polish

### Incremental Delivery

1. Setup the shared test harness and scaffolding
2. Add the foundational formatter metadata, validation, and compatibility boundaries
3. Deliver User Story 1 as one independently testable CLI/reporting increment
4. Finish with documentation and command-validation polish

### Suggested MVP Scope

- `T001`-`T016` only
- This delivers the entire P1 user story without waiting on markdown-doc polish tasks

---

## Notes

- `[P]` tasks touch disjoint files and can proceed concurrently
- Every task includes exact file paths for direct execution
- Legacy `--cucumberjson` compatibility is preserved but remains outside the new `--cucumber-json` contract
- Same-path file output conflicts are treated as part of the feature validation scope
- Mark completed tasks as `[X]` in this file as implementation progresses
