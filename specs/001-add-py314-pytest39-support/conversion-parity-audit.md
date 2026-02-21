<!-- markdownlint-disable MD013 -->

# Conversion Parity Audit

## Purpose

Validate each conversion commit against the original pytest test intent. Converted
feature docs may be more user-friendly, but must preserve behavioral intent,
explicitly state what is validated, and avoid stale links to deletable files.

## Parity Rubric

A conversion is `PASS` only when all checks pass:

1. **Intent match**: converted scenario validates the same user-facing behavior
   as the original pytest test.
2. **Behavioral assertions**: converted scenario has explicit assertions beyond
   "no exceptions" (outcomes, output match, or state assertions).
3. **Description clarity**: top-level description explains what is tested and why.
4. **No stale source links**: feature docs do not depend on links to files that
   are expected to be deleted.

## High-Priority Conversion Commit Map

| Task | Commit | Original pytest module | Converted feature file |
|------|--------|------------------------|------------------------|
| T016 | fac73ca | `tests/feature/test_alias.py` | `features/Scenario/Alias.feature.md` |
| T017 | c64fc4d | `tests/feature/test_background.py` | `features/Scenario/Background.feature.md` |
| T018 | ce6bf8d | `tests/feature/test_markdown.py` | `features/Feature/Markdown parsing.feature.md` |
| T019 | 65f64b2 | `tests/feature/test_no_sctrict_gherkin.py` | `features/Feature/Non-strict gherkin.feature.md` |
| T020 | 729b70b | `tests/feature/test_outline.py` (runtime-expansion part) | `features/Scenario/Outline/Runtime expansion.feature.md` |
| T021 | 5d229c2 | `tests/feature/test_outline_empty_values.py` | `features/Scenario/Outline/Empty values.feature.md` |
| T022 | 868a1ba | `tests/feature/test_rule.py` | `features/Feature/Rule.feature.md` |
| T023 | 716c808 | `tests/feature/test_scenario.py` | `features/Scenario/Scenario binding.feature.md` |
| T024 | 9600408 | `tests/feature/test_scenarios.py` | `features/Scenario/Scenarios loader.feature.md` |
| T025 | 25dd4b3 | `tests/feature/test_tags.py` | `features/Scenario/Tag filtering.feature.md` |
| T026 | d4560e9 | `tests/feature/test_wrong.py` | `features/Feature/Error reporting.feature.md` |
| T027 | 63fcad9 | `tests/feature/test_http.py` (user-facing part) | `features/Feature/Load/HTTP feature loading.feature.md` |

## Medium-Priority Conversion Commit Map

| Task | Commit | Original pytest module | Converted feature file |
|------|--------|------------------------|------------------------|
| T030 | 7317931 | `tests/feature/test_autoload.py` (user-facing part) | `features/Feature/Load/Autoload.feature.md` |
| T031 | 65fe32e | `tests/feature/test_cucumber_json.py` (user-facing part) | `features/Report/Cucumber JSON reporter.feature.md` |
| T032 | 96c9c90 | `tests/feature/test_gherkin_terminal_reporter.py` (user-facing part) | `features/Report/Gherkin terminal reporter.feature.md` |
| T033 | 58ecb16 | `tests/feature/test_report.py` (user-facing part) | `features/Report/Gathering.feature.md` |
| T034 | d28ebce | `tests/feature/test_steps.py` (user-facing part) | `features/Step/Step lifecycle and errors.feature.md` |
| T035 | ebcc6c4 | `tests/allure_/test_allure_outline.py` (user-facing part) | `features/Report/Allure outline.feature.md` |
| T036 | 4a69187 | `tests/allure_/test_allure_scenario.py` (user-facing part) | `features/Report/Allure scenario.feature.md` |
| T037 | c5ae120 | `tests/struct_bdd/test_deserialization.py` (user-facing part) | `features/StructBDD/Deserialization.feature.md` |
| T038 | b7c64c4 | `tests/struct_bdd/test_steps.py` (user-facing part) | `features/StructBDD/Steps.feature.md` |

## Audit Results

| Task | Commit | Verdict | Findings | Follow-up commit |
|------|--------|---------|----------|------------------|
| T016 | fac73ca | PASS | Original commit failed intent parity; fixed in follow-up commit with alias-specific behavior assertions. | `34a387b` |
| T017 | c64fc4d | PASS | Original commit used a generic sample; follow-up restores background order and doc-string intent with explicit assertions. | Pending |
| T018 | ce6bf8d | PASS | Original commit used a generic sample; follow-up restores Markdown-Gherkin parsing and step-by-step assertions. | Pending |
| T019 | 65f64b2 | PASS | Original commit used a generic sample; follow-up restores non-strict background/scenario `When`-only execution intent. | Pending |
| T020 | 729b70b | PENDING | Not audited yet. | Pending |
| T021 | 5d229c2 | PENDING | Not audited yet. | Pending |
| T022 | 868a1ba | PENDING | Not audited yet. | Pending |
| T023 | 716c808 | PENDING | Not audited yet. | Pending |
| T024 | 9600408 | PENDING | Not audited yet. | Pending |
| T025 | 25dd4b3 | PENDING | Not audited yet. | Pending |
| T026 | d4560e9 | PENDING | Not audited yet. | Pending |
| T027 | 63fcad9 | PENDING | Not audited yet. | Pending |
| T030 | 7317931 | PENDING | Not audited yet. | Pending |
| T031 | 65fe32e | PENDING | Not audited yet. | Pending |
| T032 | 96c9c90 | PENDING | Not audited yet. | Pending |
| T033 | 58ecb16 | PENDING | Not audited yet. | Pending |
| T034 | d28ebce | PENDING | Not audited yet. | Pending |
| T035 | ebcc6c4 | PENDING | Not audited yet. | Pending |
| T036 | 4a69187 | PENDING | Not audited yet. | Pending |
| T037 | c5ae120 | PENDING | Not audited yet. | Pending |
| T038 | b7c64c4 | PENDING | Not audited yet. | Pending |
