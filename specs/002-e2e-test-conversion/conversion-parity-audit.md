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
- [ ] Explicit assertions exist (not only "no exception")
- [ ] Feature description explains what is tested and why
- [ ] No stale links to deletable pytest sources
- [ ] Follow-up remediation commit recorded when parity initially failed

## High-Priority Conversion Commit Map

| Task | Commit | Original pytest module | Converted feature file |
|------|--------|------------------------|------------------------|
| T010 | fac73ca | `tests/feature/test_alias.py` | `features/Scenario/Alias.feature.md` |
| T011 | c64fc4d | `tests/feature/test_background.py` | `features/Scenario/Background.feature.md` |
| T012 | ce6bf8d | `tests/feature/test_markdown.py` | `features/Feature/Markdown parsing.feature.md` |
| T013 | 65f64b2 | `tests/feature/test_no_sctrict_gherkin.py` | `features/Feature/Non-strict gherkin.feature.md` |
| T014 | 729b70b | `tests/feature/test_outline.py` (runtime-expansion part) | `features/Scenario/Outline/Runtime expansion.feature.md` |
| T015 | 5d229c2 | `tests/feature/test_outline_empty_values.py` | `features/Scenario/Outline/Empty values.feature.md` |
| T016 | 868a1ba | `tests/feature/test_rule.py` | `features/Feature/Rule.feature.md` |
| T017 | 716c808 | `tests/feature/test_scenario.py` | `features/Scenario/Scenario binding.feature.md` |
| T018 | 9600408 | `tests/feature/test_scenarios.py` | `features/Scenario/Scenarios loader.feature.md` |
| T019 | 25dd4b3 | `tests/feature/test_tags.py` | `features/Scenario/Tag filtering.feature.md` |
| T020 | d4560e9 | `tests/feature/test_wrong.py` | `features/Feature/Error reporting.feature.md` |
| T021 | 63fcad9 | `tests/feature/test_http.py` (user-facing part) | `features/Feature/Load/HTTP feature loading.feature.md` |

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
| T010 | fac73ca | PASS | Source pytest test removed; converted feature remains runnable with explicit assertions and intent description. | `34a387b` |
| T011 | c64fc4d | PASS | Source pytest test removed; feature preserves background order and assertions. | `already-squashed` |
| T012 | ce6bf8d | PASS | Source pytest test removed; feature preserves markdown parsing intent and explicit checks. | `already-squashed` |
| T013 | 65f64b2 | PASS | Source pytest test removed; feature preserves non-strict behavior and assertions. | `already-squashed` |
| T014 | 729b70b | DEFERRED | Runtime-expansion feature exists, but mixed parser-internal checks remain in pytest source by design. | `n/a-deferred` |
| T015 | 5d229c2 | PASS | Source pytest test removed; empty-values outline behavior covered in feature docs. | `already-squashed` |
| T016 | 868a1ba | PASS | Source pytest test removed; rule behavior mapped to feature with explicit outcomes. | `already-squashed` |
| T017 | 716c808 | PASS | Source pytest test removed; scenario binding checks preserved in feature docs. | `already-squashed` |
| T018 | 9600408 | PASS | Source pytest test removed; scenarios loader behavior preserved in feature docs. | `already-squashed` |
| T019 | 25dd4b3 | PASS | Source pytest test removed; tag filtering intent and expectations preserved. | `already-squashed` |
| T020 | d4560e9 | PASS | Source pytest test removed; error-reporting behavior preserved in converted feature. | `already-squashed` |
| T021 | 63fcad9 | DEFERRED | Converted user-facing HTTP feature exists; transport-heavy variants intentionally retained in pytest source. | `n/a-deferred` |
| T030 | 7317931 | PASS | Source pytest test removed in this branch; autoload behavior documented in feature file. | `current-branch` |
| T031 | 65fe32e | PASS | Source pytest test removed in this branch; cucumber JSON reporting documented in feature file. | `current-branch` |
| T032 | 96c9c90 | PASS | Source pytest test removed in this branch; gherkin terminal reporter behavior documented in feature file. | `current-branch` |
| T033 | 58ecb16 | PASS | Source pytest test removed in this branch; report gathering behavior documented in feature file. | `current-branch` |
| T034 | d28ebce | PASS | Source pytest test removed in this branch; step lifecycle behavior documented in feature file. | `current-branch` |
| T035 | ebcc6c4 | PASS | Source pytest test already removed; allure outline behavior covered in feature file. | `already-squashed` |
| T036 | 4a69187 | PASS | Source pytest test already removed; allure scenario behavior covered in feature file. | `already-squashed` |
| T037 | c5ae120 | DEFERRED | StructBDD deserialization remains technical and is deferred to next cycle. | `n/a-deferred` |
| T038 | b7c64c4 | PASS | Source pytest test removed in this branch; StructBDD steps behavior covered in feature docs. | `current-branch` |

## Stale Link Validation (T045)

- Validation command:
  - `rg -n "tests/(feature|allure_|struct_bdd)/test_(autoload|cucumber_json|gherkin_terminal_reporter|report|steps|struct_bdd/test_steps)\\.py" features/`
- Result:
  - No stale links found in converted feature documentation for deleted pytest files.
