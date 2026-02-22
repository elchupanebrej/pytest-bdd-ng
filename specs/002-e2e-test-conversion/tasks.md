<!-- markdownlint-disable MD013 -->

# Tasks: E2E Test Conversion to Feature Documentation

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/002-e2e-test-conversion/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/e2e-conversion.openapi.yaml`, `quickstart.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: establish parity accounting and inventory structure used by all stories.

- [X] T001 Align marker declarations in `pytest.ini` for `e2e_convert_candidate`, `e2e_retain_technical`, and `e2e_deferred_conversion`
- [X] T002 Define category-parity checklist fields (happy/failure/boundary) in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T003 Add restoration-required flag column for FR-006B in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [X] T004 Sync OpenAPI parity fields with category-parity rule in `specs/002-e2e-test-conversion/contracts/e2e-conversion.openapi.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: classify tests and restore any deleted pytest sources lacking parity evidence.

**⚠️ CRITICAL**: complete this phase before any additional deletion work.

- [X] T005 Restore `tests/feature/test_autoload.py` from pre-deletion history into `tests/feature/test_autoload.py` and mark inventory status in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [X] T006 Restore `tests/feature/test_cucumber_json.py` from pre-deletion history into `tests/feature/test_cucumber_json.py` and mark inventory status in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [X] T007 Restore `tests/feature/test_gherkin_terminal_reporter.py` from pre-deletion history into `tests/feature/test_gherkin_terminal_reporter.py` and mark inventory status in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [X] T008 Restore `tests/feature/test_report.py` from pre-deletion history into `tests/feature/test_report.py` and mark inventory status in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [X] T009 Restore `tests/feature/test_steps.py` from pre-deletion history into `tests/feature/test_steps.py` and mark inventory status in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [X] T010 Restore `tests/struct_bdd/test_steps.py` from pre-deletion history into `tests/struct_bdd/test_steps.py` and mark inventory status in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [X] T011 Apply `@pytest.mark.e2e_retain_technical` to retained harness modules in `tests/e2e/test_e2e.py` and `tests/e2e/allure/test_e2e_allure.py`
- [X] T012 Apply `@pytest.mark.e2e_deferred_conversion` to deferred coverage modules in `tests/feature/test_outline.py`, `tests/feature/test_http.py`, and `tests/struct_bdd/test_deserialization.py`

**Checkpoint**: restoration + marker baseline complete.

---

## Phase 3: User Story 1 - Learn usage from feature docs (Priority: P1) 🎯 MVP

**Goal**: ensure converted feature docs preserve user-facing behavior while preventing edge-case coverage loss.

**Independent Test**: `conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/feature tests/e2e`

### High-Priority Conversion Parity

- [X] T013 [US1] Record category parity evidence for `tests/feature/test_alias.py` against `features/Scenario/Alias.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T014 [US1] Record category parity evidence for `tests/feature/test_background.py` against `features/Scenario/Background.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T015 [US1] Record category parity evidence for `tests/feature/test_markdown.py` against `features/Feature/Markdown parsing.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T016 [US1] Record category parity evidence for `tests/feature/test_no_sctrict_gherkin.py` against `features/Feature/Non-strict gherkin.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T017 [US1] Record category parity evidence for `tests/feature/test_outline_empty_values.py` against `features/Scenario/Outline/Empty values.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T018 [US1] Record category parity evidence for `tests/feature/test_rule.py` against `features/Feature/Rule.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T019 [US1] Record category parity evidence for `tests/feature/test_scenario.py` against `features/Scenario/Scenario binding.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T020 [US1] Record category parity evidence for `tests/feature/test_scenarios.py` against `features/Scenario/Scenarios loader.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T021 [US1] Record category parity evidence for `tests/feature/test_tags.py` against `features/Scenario/Tag filtering.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T022 [US1] Record category parity evidence for `tests/feature/test_wrong.py` against `features/Feature/Error reporting.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T023 [US1] Keep deferred split status for `tests/feature/test_outline.py` and `tests/feature/test_http.py` synchronized in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`

### Medium-Priority Conversion Parity

- [X] T024 [US1] Record category parity evidence for `tests/feature/test_autoload.py` against `features/Feature/Load/Autoload.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T025 [US1] Record category parity evidence for `tests/feature/test_cucumber_json.py` against `features/Report/Cucumber JSON reporter.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T026 [US1] Record category parity evidence for `tests/feature/test_gherkin_terminal_reporter.py` against `features/Report/Gherkin terminal reporter.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T027 [US1] Record category parity evidence for `tests/feature/test_report.py` against `features/Report/Gathering.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T028 [US1] Record category parity evidence for `tests/feature/test_steps.py` against `features/Step/Step lifecycle and errors.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T029 [US1] Record category parity evidence for `tests/allure_/test_allure_outline.py` against `features/Report/Allure outline.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T030 [US1] Record category parity evidence for `tests/allure_/test_allure_scenario.py` against `features/Report/Allure scenario.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T031 [US1] Record category parity evidence for `tests/struct_bdd/test_steps.py` against `features/StructBDD/Steps.feature.md` in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T032 [US1] Keep deferred split status for `tests/struct_bdd/test_deserialization.py` synchronized in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`

### Conditional Deletion (Only After Evidence)

- [X] T033 [US1] Delete `tests/feature/test_autoload.py` only when T024 category parity is PASS and record deletion evidence in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T034 [US1] Delete `tests/feature/test_cucumber_json.py` only when T025 category parity is PASS and record deletion evidence in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T035 [US1] Delete `tests/feature/test_gherkin_terminal_reporter.py` only when T026 category parity is PASS and record deletion evidence in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T036 [US1] Delete `tests/feature/test_report.py` only when T027 category parity is PASS and record deletion evidence in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T037 [US1] Delete `tests/feature/test_steps.py` only when T028 category parity is PASS and record deletion evidence in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T038 [US1] Delete `tests/struct_bdd/test_steps.py` only when T031 category parity is PASS and record deletion evidence in `specs/002-e2e-test-conversion/conversion-parity-audit.md`

**Checkpoint**: converted features have explicit edge-case parity evidence before deletion.

---

## Phase 4: User Story 2 - Preserve technical coverage boundaries (Priority: P2)

**Goal**: prevent regression by retaining technical/deferred coverage until parity requirements are met.

**Independent Test**: `conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/compatibility/test_e2e_inventory.py tests/compatibility/test_e2e_no_duplicates.py`

- [X] T039 [US2] Add enforcement test for FR-006B restoration rule in `tests/compatibility/test_e2e_no_duplicates.py`
- [X] T040 [US2] Add enforcement test for category-parity fields in parity audit rows in `tests/compatibility/test_e2e_inventory.py`
- [X] T041 [US2] Ensure retained/deferred markers and unblock metadata stay synchronized in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`

**Checkpoint**: technical and deferred coverage cannot be accidentally dropped.

---

## Phase 5: User Story 3 - Audit conversion parity per commit (Priority: P2)

**Goal**: maintain commit-level traceability and auditable parity outcomes for each conversion.

**Independent Test**: `conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/compatibility tests/e2e`

- [X] T042 [US3] Record source-to-feature mapping and verdict for T013-T032 in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T043 [US3] Record follow-up remediation commit IDs for any non-PASS parity entries in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T044 [US3] Validate no stale links to deleted pytest files in `features/` and document command/output in `specs/002-e2e-test-conversion/conversion-parity-audit.md`

**Checkpoint**: every conversion decision is traceable and reproducible.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: run final validation and publish migration summary.

- [X] T045 Run full static checks with `conda run -n pytest-bdd-ng-py314 pre-commit run --all-files`
- [X] T046 Run CI-aligned validation slice `conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/compatibility tests/e2e`
- [X] T047 Update quickstart commands and expected outcomes in `specs/002-e2e-test-conversion/quickstart.md`
- [X] T048 Recalculate migration metrics and threshold status in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** → no dependencies.
- **Phase 2** → depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)** → depends on Phase 2.
- **Phase 4 (US2)** → depends on Phase 2 and should complete before Phase 6.
- **Phase 5 (US3)** → depends on Phase 3 parity evidence.
- **Phase 6** → depends on Phases 3, 4, and 5.

### User Story Dependencies

- **US1 (P1)**: requires restoration + marker baseline first.
- **US2 (P2)**: enforces retention/deferred and restoration guardrails used by US1.
- **US3 (P2)**: consumes parity outputs from US1 and rule checks from US2.

### Within Each User Story

- Write parity evidence before deletion tasks.
- Delete source pytest files only after category parity PASS entries exist.
- Record follow-up commits for any parity remediation.

## Parallel Execution Examples

### US1 Parallel Example

```bash
Task: "T024 Record category parity for tests/feature/test_autoload.py"
Task: "T025 Record category parity for tests/feature/test_cucumber_json.py"
Task: "T026 Record category parity for tests/feature/test_gherkin_terminal_reporter.py"
```

### US2 Parallel Example

```bash
Task: "T039 Add FR-006B restoration guard in tests/compatibility/test_e2e_no_duplicates.py"
Task: "T040 Add category-parity audit guard in tests/compatibility/test_e2e_inventory.py"
```

### US3 Parallel Example

```bash
Task: "T042 Record mapping/verdict rows in conversion-parity-audit.md"
Task: "T044 Validate stale links in features/ and append evidence to conversion-parity-audit.md"
```

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Complete US1 parity evidence tasks (T013-T032).
3. Execute conditional deletion tasks only for PASS-parity cases.

### Incremental Delivery

1. Enforce US2 regression guards.
2. Complete US3 traceability and stale-link verification.
3. Run polish checks and update migration summary.

### Commit Discipline

1. Commit per completed task or tightly related pair with task IDs in message.
2. Run pre-commit before each commit and resolve all issues.
3. Keep parity remediations in follow-up commits; do not rewrite history.
