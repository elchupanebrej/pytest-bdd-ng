<!-- markdownlint-disable MD013 -->

# E2E Migration Inventory

## Rubric Columns

- `user_facing_value`: scenario teaches library usage to end users.
- `external_observability`: scenario validates externally visible behavior.
- `stability_suitability`: scenario can live as long-term feature documentation.
- `classification`: `convert_candidate`, `retain_technical`, or `deferred_conversion`.

## Conversion Candidate and Retention Matrix

| Source test path | Priority | user_facing_value | external_observability | stability_suitability | classification | Marker | Decision rationale | Unblock condition | Target cycle |
|---|---|---:|---:|---:|---|---|---|---|---|
| `tests/feature/test_alias.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_background.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_markdown.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_no_sctrict_gherkin.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_outline.py` | high | yes | yes | no | deferred_conversion | `e2e_deferred_conversion` | File still contains mixed parser-internal and user-facing assertions. | Split internal assertions from user-facing flow. | next-feature-cycle |
| `tests/feature/test_outline_empty_values.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_rule.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_scenario.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_scenarios.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_tags.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_wrong.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_http.py` | high | yes | yes | no | deferred_conversion | `e2e_deferred_conversion` | Remaining variants are transport-heavy and not yet doc-ready. | Extract remote transport variants into feature docs. | next-feature-cycle |
| `tests/feature/test_autoload.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | Converted coverage retained in `features/Feature/Load/Autoload.feature.md`. | n/a | completed |
| `tests/feature/test_cucumber_json.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | Converted coverage retained in `features/Report/Cucumber JSON reporter.feature.md`. | n/a | completed |
| `tests/feature/test_gherkin_terminal_reporter.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | Converted coverage retained in `features/Report/Gherkin terminal reporter.feature.md`. | n/a | completed |
| `tests/feature/test_report.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | Converted coverage retained in `features/Report/Gathering.feature.md`. | n/a | completed |
| `tests/feature/test_steps.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | Converted coverage retained in `features/Step/Step lifecycle and errors.feature.md`. | n/a | completed |
| `tests/allure_/test_allure_outline.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | Converted coverage retained in `features/Report/Allure outline.feature.md`. | n/a | completed |
| `tests/allure_/test_allure_scenario.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | Converted coverage retained in `features/Report/Allure scenario.feature.md`. | n/a | completed |
| `tests/struct_bdd/test_deserialization.py` | medium | yes | yes | no | deferred_conversion | `e2e_deferred_conversion` | StructBDD deserialization cases remain too technical for user-facing docs in current state. | Split technical deserialization internals from user-facing examples. | next-feature-cycle |
| `tests/struct_bdd/test_steps.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | Converted coverage retained in `features/StructBDD/Steps.feature.md`. | n/a | completed |
| `tests/e2e/test_e2e.py` | n/a | no | yes | yes | retain_technical | `e2e_retain_technical` | E2E harness glue is technical and should stay in pytest. | n/a | reviewed-each-cycle |
| `tests/e2e/allure/test_e2e_allure.py` | n/a | no | yes | yes | retain_technical | `e2e_retain_technical` | Allure harness filtering is technical test infrastructure. | n/a | reviewed-each-cycle |

## Progress

- [ ] High-priority remaining conversion in pytest sources (`test_outline.py`, `test_http.py`)
- [ ] Medium-priority conversion in pytest sources (`test_deserialization.py`)
- [x] Retained technical harness tests marked and tracked
- [x] Deferred conversion entries include unblock condition and target cycle

## Coverage Summary (T048)

| Metric | Value |
|---|---:|
| Total user-facing scenarios tracked | 21 |
| Converted to feature docs | 18 |
| Deferred conversion | 3 |
| Coverage across tracked user-facing scenarios | 85.71% |
| Threshold target | 80% |
| Threshold met | yes |
