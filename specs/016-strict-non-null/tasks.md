<!-- markdownlint-disable MD013 -->

# Tasks: Strict Non-Null Lifecycle Refactoring

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/`
**Prerequisites**: [plan.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/plan.md), [spec.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/spec.md), [research.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/research.md), [data-model.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/data-model.md), [contracts/](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/contracts/)

**Tests**: This feature requires test work because the spec demands acceptance coverage for each in-scope lifecycle flow and the constitution requires validation-first changes.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently after the shared guard and Empty-State Object foundation is in place.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`)
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the shared type, compatibility, and validation scaffolding needed by the refactor.

- [ ] T001 Introduce shared Empty-State Object and lifecycle guard type declarations in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/scenario_run.py
- [ ] T002 [P] Extend stash-backed non-null access helpers in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/stash_access.py
- [ ] T003 [P] Refresh public API compatibility scaffolding in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/api_compatibility.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/hook_public_api_baseline.json

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared runtime guard and Empty-State Object foundation that all user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Add foundational guard and stash coverage in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_run_fixture_stash.py, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_scenario_run_model.py, and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_run_scenario_runtime_unit.py
- [ ] T005 Implement centralized lifecycle guard resolution in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/run_access.py
- [ ] T006 Implement dedicated runtime Empty-State Objects and guard state in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/scenario_run.py
- [ ] T007 Wire guard-backed lifecycle transitions in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/run_transitions.py
- [ ] T008 Align parse-error boundary setup with centralized guard behavior in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/parser.py

**Checkpoint**: Foundation ready; user story implementation can now proceed.

---

## Phase 3: User Story 1 - Safe Lifecycle Access (Priority: P1) 🎯 MVP

**Goal**: Make active lifecycle phases expose populated runtime objects directly so consumers stop branching on missing state in normal flows.

**Independent Test**: Run `tests/hook/test_run_transitions.py`, `tests/feature/test_run_hooks.py`, `tests/feature/test_run_lifecycle.py`, and `tests/feature/test_report_context_hierarchy.py` and confirm active phases use populated runtime objects without caller-side absence checks.

### Tests for User Story 1

- [ ] T009 [P] [US1] Add active-phase runtime guard coverage in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_run_transitions.py
- [ ] T010 [P] [US1] Add active lifecycle feature coverage in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/feature/test_run_hooks.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/feature/test_run_lifecycle.py

### Implementation for User Story 1

- [ ] T011 [US1] Refactor active lifecycle accessors to return populated objects through guards in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/run_access.py
- [ ] T012 [US1] Update pickle runner hook orchestration to consume populated lifecycle contracts in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/plugin.py
- [ ] T013 [P] [US1] Update active lifecycle entry points in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/scenario_test_collector/plugin.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py
- [ ] T014 [US1] Align active hierarchy assertions in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/feature/test_report_context_hierarchy.py

**Checkpoint**: User Story 1 is independently functional and validates the MVP non-null active lifecycle contract.

---

## Phase 4: User Story 2 - Explicit Empty-State Exceptions (Priority: P2)

**Goal**: Replace semantically valid inactive lifecycle gaps with dedicated Empty-State Objects that preserve the required consumer contract subset.

**Independent Test**: Run `tests/hook/test_reporting_context_snapshot_unit.py`, `tests/hook/test_scenario_reference_resolution.py`, `tests/hook/test_parse_error_sink.py`, `tests/contract/test_event_message_reporting_contract.py`, `tests/contract/test_xdist_consolidated_stream_contract.py`, and `tests/contract/test_cucumber_formatter_cli_contract.py` and confirm exceptional flows remain polymorphic without `None` checks.

### Tests for User Story 2

- [ ] T015 [P] [US2] Add reporter snapshot empty-state coverage in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_reporting_context_snapshot_unit.py
- [ ] T016 [P] [US2] Add empty-state and unresolved enrichment coverage in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_scenario_reference_resolution.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_parse_error_sink.py
- [ ] T017 [P] [US2] Add reporting contract coverage for Empty-State Objects in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_event_message_reporting_contract.py, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_xdist_consolidated_stream_contract.py, and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_cucumber_formatter_cli_contract.py

### Implementation for User Story 2

- [ ] T018 [US2] Implement previous-step and inactive-slot Empty-State Objects in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/scenario_run.py
- [ ] T019 [US2] Update reporting snapshot construction to return dedicated Empty-State Objects in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/run_access.py
- [ ] T020 [P] [US2] Update reporter consumers to read Empty-State Objects polymorphically in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/scenario_reporter/plugin.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/allure_logger/plugin.py
- [ ] T021 [P] [US2] Update gherkin message runtime and parse-error emission to use Empty-State Object contracts in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/parser.py

**Checkpoint**: User Story 2 is independently functional and all approved exceptional flows use dedicated Empty-State Objects instead of nullable contracts.

---

## Phase 5: User Story 3 - Enforced Lifecycle Invariants (Priority: P3)

**Goal**: Enforce lifecycle availability through centralized guards with deterministic failures while keeping the public hook and plugin surface compatibility-stable.

**Independent Test**: Run `tests/hook/test_run_diagnostics.py`, `tests/contract/test_hook_lifecycle_non_null_contract.py`, `tests/contract/test_run_contract.py`, and `tests/compatibility/test_hook_run_api_surface.py` and confirm invalid lifecycle states fail at the guard boundary without changing the public API surface.

### Tests for User Story 3

- [ ] T022 [P] [US3] Add deterministic lifecycle guard failure coverage in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_run_diagnostics.py
- [ ] T023 [P] [US3] Add hook and run contract coverage for centralized guards in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_hook_lifecycle_non_null_contract.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_run_contract.py
- [ ] T024 [P] [US3] Add public surface compatibility coverage in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_hook_run_api_surface.py

### Implementation for User Story 3

- [ ] T025 [US3] Centralize lifecycle invariant enforcement and deterministic error creation in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/run_access.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/model/scenario_run.py
- [ ] T026 [US3] Update hook orchestration to reject invalid lifecycle states at guard boundaries in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/plugin.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/run_transitions.py
- [ ] T027 [US3] Refresh compatibility baseline generation in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/plugin/pickle_runner/api_compatibility.py and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/hook_public_api_baseline.json

**Checkpoint**: User Story 3 is independently functional and invalid lifecycle transitions fail deterministically without public API breakage.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish shared documentation, validation, and repository-wide checks.

- [ ] T028 [P] Update feature contracts and validation guidance in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/contracts/hook-lifecycle-non-null.openapi.yaml, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/contracts/reporting-lifecycle-boundary.md, /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/contracts/hook-plugin-public-api-compatibility.md, and /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/quickstart.md
- [ ] T029 Run the targeted lifecycle validation slice documented in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/016-strict-non-null/quickstart.md
- [ ] T030 Run compatibility regression in /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/
- [ ] T031 Run repository quality gates from /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.pre-commit-config.yaml

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies; start immediately.
- **Phase 2: Foundational**: Depends on Phase 1; blocks all user stories.
- **Phase 3: US1**: Depends on Phase 2 only.
- **Phase 4: US2**: Depends on Phase 2 only; may reuse US1 foundations but remains independently testable.
- **Phase 5: US3**: Depends on Phase 2 only; validates guard enforcement and compatibility on top of the shared foundation.
- **Phase 6: Polish**: Depends on all implemented stories.

### User Story Dependencies

- **US1 (P1)**: First MVP increment after foundational work; no dependency on US2 or US3.
- **US2 (P2)**: Starts after foundational work; can integrate with US1 artifacts but must be verifiable on its own.
- **US3 (P3)**: Starts after foundational work; can tighten behavior on top of US1/US2 without requiring a public API redesign.

### Within Each User Story

- Test tasks come before implementation tasks.
- Guard and model changes come before downstream consumer rewrites.
- Runtime access changes come before compatibility baseline refreshes.
- Each story must pass its independent test slice before moving on.

### Dependency Graph

- `Setup -> Foundational -> {US1, US2, US3} -> Polish`
- `US1` is the recommended MVP.
- `US2` and `US3` can proceed in parallel after `Foundational` if staffing allows.

---

## Parallel Opportunities

### Phase 1

- `T002` and `T003` can run in parallel after `T001`.

### Phase 2

- `T004` can run in parallel with source preparation tasks because it touches only test files.

### User Story 1

- `T009` and `T010` can run in parallel.
- `T013` can run in parallel with `T012` after `T011`.

### User Story 2

- `T015`, `T016`, and `T017` can run in parallel.
- `T020` and `T021` can run in parallel after `T018` and `T019`.

### User Story 3

- `T022`, `T023`, and `T024` can run in parallel.

### Polish

- `T028` can run in parallel with validation preparation before `T029` starts.

---

## Parallel Example: User Story 2

```bash
# Launch the US2 validation tasks together:
Task: "Add reporter snapshot empty-state coverage in tests/hook/test_reporting_context_snapshot_unit.py"
Task: "Add empty-state and unresolved enrichment coverage in tests/hook/test_scenario_reference_resolution.py and tests/hook/test_parse_error_sink.py"
Task: "Add reporting contract coverage for Empty-State Objects in tests/contract/test_event_message_reporting_contract.py, tests/contract/test_xdist_consolidated_stream_contract.py, and tests/contract/test_cucumber_formatter_cli_contract.py"

# After the shared Empty-State Object implementation lands, launch the independent consumer updates together:
Task: "Update reporter consumers to read Empty-State Objects polymorphically in src/pytest_bdd/plugin/scenario_reporter/plugin.py and src/pytest_bdd/plugin/allure_logger/plugin.py"
Task: "Update gherkin message runtime and parse-error emission to use Empty-State Object contracts in src/pytest_bdd/plugin/gherkin_message_reporter/scenario_runtime.py and src/pytest_bdd/parser.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the US1 independent test slice before proceeding.

### Incremental Delivery

1. Land the shared guard and Empty-State Object foundation.
2. Deliver US1 to remove nullable access from active phases.
3. Deliver US2 to cover exceptional empty-state flows.
4. Deliver US3 to centralize invariant enforcement and compatibility diagnostics.
5. Finish with Phase 6 validation and documentation refresh.

### Parallel Team Strategy

1. One engineer handles the shared foundation in `scenario_run.py`, `run_access.py`, and `run_transitions.py`.
2. After foundation completion:
   - Engineer A takes US1 active-phase consumers.
   - Engineer B takes US2 reporting and empty-state consumers.
   - Engineer C takes US3 diagnostics and compatibility guardrails.

---

## Notes

- All task lines follow the required checkbox, task ID, optional `[P]`, optional story label, and exact file path format.
- Tests are included because the spec and constitution require executable validation for each lifecycle contract.
- Keep Empty-State Object work constrained to semantically valid inactive states; do not use it to hide genuine lifecycle violations.
- Preserve the public hook/plugin surface while tightening internal lifecycle guarantees.
