<!-- markdownlint-disable MD013 -->

# Tasks: E2E Conversion to Feature Documentation

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/002-e2e-test-conversion/`
**Prerequisites**: `plan.md`, `spec.md`, `e2e-migration-inventory.md`, `conversion-parity-audit.md`

## Phase 1: Setup

- [ ] T001 Build/refresh conversion candidate inventory in `specs/002-e2e-test-conversion/e2e-migration-inventory.md`
- [ ] T002 Define/refresh parity rubric in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [ ] T003 Add retention marker policy for non-convertible technical tests in `tests/`

## Phase 2: High-Priority Conversion

- [ ] T010 [US1] Convert high-priority user-facing scenario `tests/feature/test_alias.py` into `features/Scenario/Alias.feature.md`
- [ ] T011 [US1] Convert high-priority user-facing scenario `tests/feature/test_background.py` into `features/Scenario/Background.feature.md`
- [ ] T012 [US1] Convert high-priority user-facing scenario `tests/feature/test_markdown.py` into `features/Feature/Markdown parsing.feature.md`
- [ ] T013 [US1] Convert high-priority user-facing scenario `tests/feature/test_no_sctrict_gherkin.py` into `features/Feature/Non-strict gherkin.feature.md`
- [ ] T014 [US1] Convert high-priority user-facing scenario `tests/feature/test_outline.py` (user-facing part) into `features/Scenario/Outline/Runtime expansion.feature.md`
- [ ] T015 [US1] Convert high-priority user-facing scenario `tests/feature/test_outline_empty_values.py` into `features/Scenario/Outline/Empty values.feature.md`
- [ ] T016 [US1] Convert high-priority user-facing scenario `tests/feature/test_rule.py` into `features/Feature/Rule.feature.md`
- [ ] T017 [US1] Convert high-priority user-facing scenario `tests/feature/test_scenario.py` into `features/Scenario/Scenario binding.feature.md`
- [ ] T018 [US1] Convert high-priority user-facing scenario `tests/feature/test_scenarios.py` into `features/Scenario/Scenarios loader.feature.md`
- [ ] T019 [US1] Convert high-priority user-facing scenario `tests/feature/test_tags.py` into `features/Scenario/Tag filtering.feature.md`
- [ ] T020 [US1] Convert high-priority user-facing scenario `tests/feature/test_wrong.py` into `features/Feature/Error reporting.feature.md`
- [ ] T021 [US1] Convert high-priority user-facing scenario `tests/feature/test_http.py` (user-facing part) into `features/Feature/Load/HTTP feature loading.feature.md`

## Phase 3: Medium-Priority Conversion

- [ ] T030 [US1] Convert medium-priority user-facing scenario `tests/feature/test_autoload.py` into `features/Feature/Load/Autoload.feature.md`
- [ ] T031 [US1] Convert medium-priority user-facing scenario `tests/feature/test_cucumber_json.py` into `features/Report/Cucumber JSON reporter.feature.md`
- [ ] T032 [US1] Convert medium-priority user-facing scenario `tests/feature/test_gherkin_terminal_reporter.py` into `features/Report/Gherkin terminal reporter.feature.md`
- [ ] T033 [US1] Convert medium-priority user-facing scenario `tests/feature/test_report.py` into `features/Report/Gathering.feature.md`
- [ ] T034 [US1] Convert medium-priority user-facing scenario `tests/feature/test_steps.py` into `features/Step/Step lifecycle and errors.feature.md`
- [ ] T035 [US1] Convert medium-priority user-facing scenario `tests/allure_/test_allure_outline.py` into `features/Report/Allure outline.feature.md`
- [ ] T036 [US1] Convert medium-priority user-facing scenario `tests/allure_/test_allure_scenario.py` into `features/Report/Allure scenario.feature.md`
- [ ] T037 [US1] Convert medium-priority user-facing scenario `tests/struct_bdd/test_deserialization.py` into `features/StructBDD/Deserialization.feature.md`
- [ ] T038 [US1] Convert medium-priority user-facing scenario `tests/struct_bdd/test_steps.py` into `features/StructBDD/Steps.feature.md`

## Phase 4: Parity and Cleanup

- [ ] T040 [US3] Audit parity for each converted task in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [ ] T041 [US3] Apply parity fixes in follow-up commits only and record links in `specs/002-e2e-test-conversion/conversion-parity-audit.md`
- [ ] T042 [US2] Add/verify technical-test retention markers for non-convertible tests in `tests/`
- [ ] T043 [US2] Remove only duplicate pytest tests that are parity-complete converted scenarios
- [ ] T044 Run `pre-commit run --all-files` and fix issues before each conversion commit
