<!-- markdownlint-disable MD013 -->

# Tasks: E2E Test Conversion to Feature Documentation

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/002-e2e-test-conversion/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/e2e-conversion.openapi.yaml`, `quickstart.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish inventory, parity rubric, and marker contract for all later conversion work.

- [X] T001 Build conversion candidate inventory with rubric columns in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [X] T002 Define parity checklist template (intent, assertions, clarity, stale-link check) in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T003 Register canonical markers `e2e_convert_candidate`, `e2e_retain_technical`, and `e2e_deferred_conversion` in `pytest.ini`
- [X] T004 Align conversion API schema enums and fields with marker policy in `specs/002-e2e-test-conversion/contracts/e2e-conversion.openapi.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Apply classification marks and baseline retention/deferred policy before any conversion.

**⚠️ CRITICAL**: User story conversion tasks start only after this phase is complete.

- [X] T005 Mark conversion candidates with `@pytest.mark.e2e_convert_candidate` in `tests/feature/test_alias.py`, `tests/feature/test_background.py`, `tests/feature/test_markdown.py`, `tests/feature/test_no_sctrict_gherkin.py`, `tests/feature/test_outline.py`, `tests/feature/test_outline_empty_values.py`, `tests/feature/test_rule.py`, `tests/feature/test_scenario.py`, `tests/feature/test_scenarios.py`, `tests/feature/test_tags.py`, `tests/feature/test_wrong.py`, and `tests/feature/test_http.py`
- [X] T006 Mark conversion candidates with `@pytest.mark.e2e_convert_candidate` in `tests/feature/test_autoload.py`, `tests/feature/test_cucumber_json.py`, `tests/feature/test_gherkin_terminal_reporter.py`, `tests/feature/test_report.py`, `tests/feature/test_steps.py`, `tests/allure_/test_allure_outline.py`, `tests/allure_/test_allure_scenario.py`, `tests/struct_bdd/test_deserialization.py`, and `tests/struct_bdd/test_steps.py`
- [X] T007 Mark retained technical tests with `@pytest.mark.e2e_retain_technical` in `tests/e2e/test_e2e.py` and `tests/e2e/allure/test_e2e_allure.py`
- [X] T008 Mark blocked-but-convertible tests with `@pytest.mark.e2e_deferred_conversion` (with unblock notes) in `tests/compatibility/test_e2e_inventory.py`
- [X] T009 Persist classification decisions and rationale for all marked tests in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`

**Checkpoint**: Marker and inventory baseline is complete; conversion tasks can start.

---

## Phase 3: User Story 1 - Learn usage from feature docs (Priority: P1) 🎯 MVP

**Goal**: Convert user-facing pytest scenarios into feature documentation with parity and optional source-test deletion.

**Independent Test**: `python -m pytest -q tests/e2e tests/compatibility/test_e2e_no_duplicates.py`

### Implementation for User Story 1 (High Priority)

- [X] T010 [US1] Convert `tests/feature/test_alias.py` to `features/Scenario/Alias.feature.md` and delete converted pytest coverage from `tests/feature/test_alias.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T011 [US1] Convert `tests/feature/test_background.py` to `features/Scenario/Background.feature.md` and delete converted pytest coverage from `tests/feature/test_background.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T012 [US1] Convert `tests/feature/test_markdown.py` to `features/Feature/Markdown parsing.feature.md` and delete converted pytest coverage from `tests/feature/test_markdown.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T013 [US1] Convert `tests/feature/test_no_sctrict_gherkin.py` to `features/Feature/Non-strict gherkin.feature.md` and delete converted pytest coverage from `tests/feature/test_no_sctrict_gherkin.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T014 [US1] Keep deferred technical coverage in `tests/feature/test_outline.py` while user-facing conversion remains in `features/Scenario/Outline/Runtime expansion.feature.md` with deferred status tracked in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [X] T015 [US1] Convert `tests/feature/test_outline_empty_values.py` to `features/Scenario/Outline/Empty values.feature.md` and delete converted pytest coverage from `tests/feature/test_outline_empty_values.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T016 [US1] Convert `tests/feature/test_rule.py` to `features/Feature/Rule.feature.md` and delete converted pytest coverage from `tests/feature/test_rule.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T017 [US1] Convert `tests/feature/test_scenario.py` to `features/Scenario/Scenario binding.feature.md` and delete converted pytest coverage from `tests/feature/test_scenario.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T018 [US1] Convert `tests/feature/test_scenarios.py` to `features/Scenario/Scenarios loader.feature.md` and delete converted pytest coverage from `tests/feature/test_scenarios.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T019 [US1] Convert `tests/feature/test_tags.py` to `features/Scenario/Tag filtering.feature.md` and delete converted pytest coverage from `tests/feature/test_tags.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T020 [US1] Convert `tests/feature/test_wrong.py` to `features/Feature/Error reporting.feature.md` and delete converted pytest coverage from `tests/feature/test_wrong.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T021 [US1] Keep deferred technical coverage in `tests/feature/test_http.py` while user-facing conversion remains in `features/Feature/Load/HTTP feature loading.feature.md` with deferred status tracked in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`

### Implementation for User Story 1 (Medium Priority)

- [X] T030 [US1] Convert `tests/feature/test_autoload.py` to `features/Feature/Load/Autoload.feature.md` and delete converted pytest coverage from `tests/feature/test_autoload.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T031 [US1] Convert `tests/feature/test_cucumber_json.py` to `features/Report/Cucumber JSON reporter.feature.md` and delete converted pytest coverage from `tests/feature/test_cucumber_json.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T032 [US1] Convert `tests/feature/test_gherkin_terminal_reporter.py` to `features/Report/Gherkin terminal reporter.feature.md` and delete converted pytest coverage from `tests/feature/test_gherkin_terminal_reporter.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T033 [US1] Convert `tests/feature/test_report.py` to `features/Report/Gathering.feature.md` and delete converted pytest coverage from `tests/feature/test_report.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T034 [US1] Convert user-facing part of `tests/feature/test_steps.py` to `features/Step/Step lifecycle and errors.feature.md` and delete only converted pytest coverage from `tests/feature/test_steps.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T035 [US1] Convert user-facing part of `tests/allure_/test_allure_outline.py` to `features/Report/Allure outline.feature.md` and delete only converted pytest coverage from `tests/allure_/test_allure_outline.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T036 [US1] Convert user-facing part of `tests/allure_/test_allure_scenario.py` to `features/Report/Allure scenario.feature.md` and delete only converted pytest coverage from `tests/allure_/test_allure_scenario.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T037 [US1] Defer conversion of `tests/struct_bdd/test_deserialization.py` and track unblock condition/target cycle in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [X] T038 [US1] Convert user-facing part of `tests/struct_bdd/test_steps.py` to `features/StructBDD/Steps.feature.md` and delete only converted pytest coverage from `tests/struct_bdd/test_steps.py` when parity is PASS in `specs/002-e2e-test-conversion/conversion-parity-audit.md`

**Checkpoint**: User-facing conversion set is runnable from `features/` with duplicate cleanup only for parity-complete coverage.

---

## Phase 4: User Story 2 - Preserve technical coverage boundaries (Priority: P2)

**Goal**: Keep technical tests in pytest with enforceable retention/deferred policy.

**Independent Test**: `python -m pytest -q tests/compatibility/test_e2e_classification.py tests/e2e/test_e2e.py`

- [X] T040 [US2] Verify every retained technical module has `@pytest.mark.e2e_retain_technical` in `tests/e2e/test_e2e.py` and `tests/e2e/allure/test_e2e_allure.py`
- [X] T041 [US2] Verify deferred tests include `@pytest.mark.e2e_deferred_conversion` and unblock metadata in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [X] T042 [US2] Add non-removal guard checks for retained/deferred tests in `tests/compatibility/test_e2e_no_duplicates.py`

**Checkpoint**: Non-convertible tests are protected from accidental deletion.

---

## Phase 5: User Story 3 - Audit conversion parity per commit (Priority: P2)

**Goal**: Enforce conversion quality and commit-level remediation traceability.

**Independent Test**: `python -m pytest -q tests/compatibility/test_e2e_inventory.py tests/compatibility/test_e2e_migration_threshold.py`

- [X] T043 [US3] Record parity verdict for T010-T038 with source/feature mapping in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T044 [US3] Record follow-up fix commit IDs for failed parity checks in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [X] T045 [US3] Validate no converted feature references deleted pytest files and record check results in `specs/002-e2e-test-conversion/conversion-parity-audit.md`

**Checkpoint**: Every conversion task has auditable parity status and remediation linkage.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final quality checks across all stories.

- [X] T046 Run full pre-commit checks and resolve findings in `.pre-commit-config.yaml`
- [X] T047 Run quickstart validation commands and update expected workflow notes in `specs/002-e2e-test-conversion/quickstart.md`
- [X] T048 Recalculate migration threshold progress and update summary rows in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: starts immediately.
- **Phase 2 (Foundational)**: depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)**: depends on Phase 2.
- **Phase 4 (US2)**: depends on Phase 2; should run after or alongside late Phase 3 cleanup.
- **Phase 5 (US3)**: depends on Phase 3 outputs and uses Phase 4 safeguards.
- **Phase 6 (Polish)**: depends on completion of Phases 3-5.

### User Story Dependencies

- **US1 (P1)**: starts after foundational markers/inventory are complete.
- **US2 (P2)**: depends on marker baseline and feeds cleanup guardrails used by US1 cleanup.
- **US3 (P2)**: depends on conversion outputs from US1 and classification/retention signals from US2.

### Within Each User Story

- Apply/update markers and inventory baseline before converting tests.
- For each conversion task: convert -> validate parity -> delete duplicate pytest coverage only when parity is PASS.
- Record parity and remediation commit links before marking task complete.

## Parallel Execution Examples

### US1 Parallel Example

```bash
Task: "T010 Convert tests/feature/test_alias.py -> features/Scenario/Alias.feature.md"
Task: "T011 Convert tests/feature/test_background.py -> features/Scenario/Background.feature.md"
Task: "T012 Convert tests/feature/test_markdown.py -> features/Feature/Markdown parsing.feature.md"
```

### US2 Parallel Example

```bash
Task: "T040 Verify retained markers in tests/e2e/test_e2e.py and tests/e2e/allure/test_e2e_allure.py"
Task: "T041 Verify deferred markers/unblock metadata in specs/002-e2e-test-conversion/e2e-migration-inventory.md"
```

### US3 Parallel Example

```bash
Task: "T043 Record parity verdicts in specs/002-e2e-test-conversion/conversion-parity-audit.md"
Task: "T045 Record stale-link validation in specs/002-e2e-test-conversion/conversion-parity-audit.md"
```

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Deliver high-priority US1 conversions (T010-T021).
3. Validate parity and delete duplicates only where PASS.

### Incremental Delivery

1. Finish medium-priority US1 conversions (T030-T038).
2. Apply US2 retention/deferred safeguards.
3. Finalize US3 parity traceability and polish checks.

### Commit Discipline

1. Commit each completed task (or tightly coupled task pair) with task IDs in commit message.
2. Run pre-commit before every commit and fix all findings.
3. Keep parity remediations in follow-up commits only.
