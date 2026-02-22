<!-- markdownlint-disable MD013 -->

# Conversion Parity Audit

## Purpose

Validate each conversion commit against the original pytest test intent. Converted
feature docs may be more user-friendly, but must preserve behavioral intent,
explicitly state what is validated, and avoid stale links to deletable files.

## Canonical Terms and Markers

- **ConversionCandidate**: test marked `@pytest.mark.e2e_convert_candidate`.
- **RetentionMarker**: `@pytest.mark.e2e_retain_technical` for non-convertible
  technical tests retained in `tests/`.
- **ParityAuditEntry**: audit row linking source pytest test, converted feature
  file, verdict, and follow-up commit.

## Parity Rubric

A conversion is `PASS` only when all checks pass:

1. **Intent match**: converted scenario validates the same user-facing behavior
   as the original pytest test.
2. **Behavioral assertions**: converted scenario has explicit assertions beyond
   "no exceptions" (outcomes, output match, or state assertions).
3. **Description clarity**: top-level description explains what is tested and why.
4. **No stale source links**: feature docs do not depend on links to files that
   are expected to be deleted.

## Parity Checklist Template

Use this checklist for each conversion task before deleting duplicate pytest coverage:

- [ ] Intent parity verified against original pytest test behavior
- [ ] Happy-path category covered
- [ ] Failure-path category covered
- [ ] Boundary/empty-path category covered
- [ ] Explicit assertions exist (not only "no exception")
- [ ] Feature description explains what is tested and why
- [ ] No stale links to deletable pytest sources
- [ ] Follow-up remediation commit recorded when parity initially failed

## High-Priority Conversion Commit Map

| Task | Commit | Original pytest module | Converted feature file |
|------|--------|------------------------|------------------------|
| T013 | fac73ca | `tests/feature/test_alias.py` | `features/Scenario/Alias.feature.md` |
| T014 | c64fc4d | `tests/feature/test_background.py` | `features/Scenario/Background.feature.md` |
| T015 | ce6bf8d | `tests/feature/test_markdown.py` | `features/Feature/Markdown parsing.feature.md` |
| T016 | 65f64b2 | `tests/feature/test_no_sctrict_gherkin.py` | `features/Feature/Non-strict gherkin.feature.md` |
| T017 | 5d229c2 | `tests/feature/test_outline_empty_values.py` | `features/Scenario/Outline/Empty values.feature.md` |
| T018 | 868a1ba | `tests/feature/test_rule.py` | `features/Feature/Rule.feature.md` |
| T019 | 716c808 | `tests/feature/test_scenario.py` | `features/Scenario/Scenario binding.feature.md` |
| T020 | 9600408 | `tests/feature/test_scenarios.py` | `features/Scenario/Scenarios loader.feature.md` |
| T021 | 25dd4b3 | `tests/feature/test_tags.py` | `features/Scenario/Tag filtering.feature.md` |
| T022 | d4560e9 | `tests/feature/test_wrong.py` | `features/Feature/Error reporting.feature.md` |
| T023 | 729b70b + 63fcad9 | `tests/feature/test_outline.py`, `tests/feature/test_http.py` | `features/Scenario/Outline/Runtime expansion.feature.md`, `features/Feature/Load/HTTP feature loading.feature.md` |

## Medium-Priority Conversion Commit Map

| Task | Commit | Original pytest module | Converted feature file |
|------|--------|------------------------|------------------------|
| T024 | 7317931 | `tests/feature/test_autoload.py` | `features/Feature/Load/Autoload.feature.md` |
| T025 | 65fe32e | `tests/feature/test_cucumber_json.py` | `features/Report/Cucumber JSON reporter.feature.md` |
| T026 | 96c9c90 | `tests/feature/test_gherkin_terminal_reporter.py` | `features/Report/Gherkin terminal reporter.feature.md` |
| T027 | 58ecb16 | `tests/feature/test_report.py` | `features/Report/Gathering.feature.md` |
| T028 | d28ebce | `tests/feature/test_steps.py` | `features/Step/Step lifecycle and errors.feature.md` |
| T029 | ebcc6c4 | `tests/allure_/test_allure_outline.py` | `features/Report/Allure outline.feature.md` |
| T030 | 4a69187 | `tests/allure_/test_allure_scenario.py` | `features/Report/Allure scenario.feature.md` |
| T031 | b7c64c4 | `tests/struct_bdd/test_steps.py` | `features/StructBDD/Steps.feature.md` |
| T032 | c5ae120 | `tests/struct_bdd/test_deserialization.py` | `features/StructBDD/Deserialization.feature.md` |

## Audit Results

| Task | Commit | Verdict | Findings | Follow-up commit |
|------|--------|---------|----------|------------------|
| T013 | fac73ca | PASS | Source pytest test removed; converted feature remains runnable with explicit assertions and intent description. | `34a387b` |
| T014 | c64fc4d | PASS | Source pytest test removed; feature preserves background order and assertions. | `already-squashed` |
| T015 | ce6bf8d | PASS | Source pytest test removed; feature preserves markdown parsing intent and explicit checks. | `already-squashed` |
| T016 | 65f64b2 | PASS | Source pytest test removed; feature preserves non-strict behavior and assertions. | `already-squashed` |
| T017 | 5d229c2 | PASS | Source pytest test removed; empty-values outline behavior covered in feature docs. | `already-squashed` |
| T018 | 868a1ba | PASS | Source pytest test removed; rule behavior mapped to feature with explicit outcomes. | `already-squashed` |
| T019 | 716c808 | PASS | Source pytest test removed; scenario binding checks preserved in feature docs. | `already-squashed` |
| T020 | 9600408 | PASS | Source pytest test removed; scenarios loader behavior preserved in feature docs. | `already-squashed` |
| T021 | 25dd4b3 | PASS | Source pytest test removed; tag filtering intent and expectations preserved. | `already-squashed` |
| T022 | d4560e9 | PASS | Source pytest test removed; error-reporting behavior preserved in converted feature. | `already-squashed` |
| T023 | 729b70b + 63fcad9 | PASS | Outline parse-failure coverage and HTTP loading variants are now documented in executable feature scenarios. | `current-branch` |
| T024 | 7317931 | PASS | Source pytest test removed in this branch; autoload behavior documented in feature file with boundary case. | `current-branch` |
| T025 | 65fe32e | PASS | Source pytest test removed in this branch; cucumber JSON reporting includes outline boundary coverage. | `current-branch` |
| T026 | 96c9c90 | PASS | Source pytest test removed in this branch; gherkin terminal reporter includes `-vv` substitution boundary. | `current-branch` |
| T027 | 58ecb16 | PASS | Source pytest test removed in this branch; report gathering includes complex-parameter boundary coverage. | `current-branch` |
| T028 | d28ebce | PASS | Source pytest test removed in this branch; step lifecycle covers unknown-first-keyword boundary case. | `current-branch` |
| T029 | ebcc6c4 | PASS | Source pytest test already removed; allure outline behavior covered in feature file. | `already-squashed` |
| T030 | 4a69187 | PASS | Source pytest test already removed; allure scenario behavior covered in feature file. | `already-squashed` |
| T031 | b7c64c4 | PASS | Source pytest test removed in this branch; StructBDD steps include examples-expansion boundary coverage. | `current-branch` |
| T032 | c5ae120 | PARTIAL | Core StructBDD behavior is covered in feature docs, but full edge-case granularity is not 1:1 with the original 24-case pytest suite. Original pytest module restored and marked deferred conversion. | `current-branch` |

## Category Parity Matrix (T013-T032)

| Task | Happy path | Failure path | Boundary/empty path | Category parity PASS | Notes |
|------|------------|--------------|---------------------|----------------------|-------|
| T013 | yes | yes | yes | yes | Alias behavior evidence accepted from prior conversion audit. |
| T014 | yes | yes | yes | yes | Background ordering + failure mode covered in prior audit. |
| T015 | yes | yes | yes | yes | Markdown parsing and malformed cases covered in prior audit. |
| T016 | yes | yes | yes | yes | Non-strict parsing happy/failure/boundary cases documented. |
| T017 | yes | yes | yes | yes | Empty value outline scenarios provide boundary coverage. |
| T018 | yes | yes | yes | yes | Rule conversion keeps positive/negative/example boundaries. |
| T019 | yes | yes | yes | yes | Scenario binding includes expected and failing assertions. |
| T020 | yes | yes | yes | yes | Loader scenarios include absent/malformed source cases. |
| T021 | yes | yes | yes | yes | Tag filtering includes include/exclude/empty edge behavior. |
| T022 | yes | yes | yes | yes | Error reporting conversion includes failing and edge cases. |
| T023 | yes | yes | yes | yes | Outline parse errors and HTTP loading variants are covered in feature docs. |
| T024 | yes | yes | yes | yes | Boundary coverage added for explicit `features_base_dir` with autoload disabled. |
| T025 | yes | yes | yes | yes | Boundary coverage added for outline row serialization and jq row-count checks. |
| T026 | yes | yes | yes | yes | Boundary coverage added for `-vv` output with substituted outline values. |
| T027 | yes | yes | yes | yes | Boundary coverage added for complex parameter serialization path in verbose mode. |
| T028 | yes | yes | yes | yes | Boundary coverage added for unknown first keyword (`*`) via generic step decorator. |
| T029 | yes | yes | yes | yes | Allure outline feature already covers sample boundary table cases. |
| T030 | yes | yes | yes | yes | Allure scenario feature retains failure and boundary contexts. |
| T031 | yes | yes | yes | yes | Boundary coverage added for StructBDD examples expansion across two rows. |
| T032 | yes | no | no | no | Core paths are covered in feature docs; detailed edge-case assertions are retained in `tests/struct_bdd/test_deserialization.py` until parity completion. |

## Stale Link Validation (T044)

- Validation command:
  - `rg -n "tests/(feature|allure_|struct_bdd)/test_(autoload|cucumber_json|gherkin_terminal_reporter|report|steps|struct_bdd/test_steps)\\.py" features/`
- Result:
  - No stale links found in converted feature documentation for deleted pytest files.
