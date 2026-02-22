<!-- markdownlint-disable MD013 -->

# E2E Migration Inventory

## Rubric Columns

- `user_facing_value`: scenario teaches library usage to end users.
- `external_observability`: scenario validates externally visible behavior.
- `stability_suitability`: scenario can live as long-term feature documentation.
- `classification`: `convert_candidate`, `retain_technical`, or `deferred_conversion`.

## Conversion Candidate and Retention Matrix

| Source test path | Priority | user_facing_value | external_observability | stability_suitability | classification | Marker | restoration_required | Decision rationale | Unblock condition | Target cycle |
|---|---|---:|---:|---:|---|---|---|---|---|---|
| `tests/feature/test_alias.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_background.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_markdown.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_no_sctrict_gherkin.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_outline.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | Invalid-outline parsing behavior is now documented and runnable in feature docs. | n/a | completed |
| `tests/feature/test_outline_empty_values.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_rule.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_scenario.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_scenarios.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_tags.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_wrong.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | Already converted and removed from pytest source. | n/a | completed |
| `tests/feature/test_http.py` | high | yes | yes | yes | converted | `e2e_convert_candidate` | no | URL, desktop/webloc link loading and StructBDD HTTP loading are documented in feature docs. | n/a | completed |
| `tests/feature/test_autoload.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | no | Boundary coverage added in feature docs; pytest source deleted after category parity PASS. | n/a | completed |
| `tests/feature/test_cucumber_json.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | no | Boundary coverage added in feature docs; pytest source deleted after category parity PASS. | n/a | completed |
| `tests/feature/test_gherkin_terminal_reporter.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | no | Boundary coverage added in feature docs; pytest source deleted after category parity PASS. | n/a | completed |
| `tests/feature/test_report.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | no | Boundary coverage added in feature docs; pytest source deleted after category parity PASS. | n/a | completed |
| `tests/feature/test_steps.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | no | Boundary coverage added in feature docs; pytest source deleted after category parity PASS. | n/a | completed |
| `tests/allure_/test_allure_outline.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | no | Converted coverage retained in `features/Report/Allure outline.feature.md`. | n/a | completed |
| `tests/allure_/test_allure_scenario.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | no | Converted coverage retained in `features/Report/Allure scenario.feature.md`. | n/a | completed |
| `tests/struct_bdd/test_deserialization.py` | medium | yes | yes | yes | deferred_conversion | `e2e_deferred_conversion` | yes | Feature conversion keeps core user-facing behavior, but it does not preserve full edge-case granularity from original pytest module. Keep pytest suite for detailed regression coverage. | Split remaining 24-case parity into additional feature scenarios with one-to-one edge assertions. | next-feature-cycle |
| `tests/struct_bdd/test_steps.py` | medium | yes | yes | yes | converted | `e2e_convert_candidate` | no | Boundary coverage added in feature docs; pytest source deleted after category parity PASS. | n/a | completed |
| `tests/e2e/test_e2e.py` | n/a | no | yes | yes | retain_technical | `e2e_retain_technical` | no | E2E harness glue is technical and should stay in pytest. | n/a | reviewed-each-cycle |
| `tests/e2e/allure/test_e2e_allure.py` | n/a | no | yes | yes | retain_technical | `e2e_retain_technical` | no | Allure harness filtering is technical test infrastructure. | n/a | reviewed-each-cycle |

## Progress

- [x] High-priority remaining conversion in pytest sources (`test_outline.py`, `test_http.py`)
- [x] Medium-priority conversion in pytest sources (`test_deserialization.py`) with deferred technical parity retained in pytest
- [x] Retained technical harness tests marked and tracked
- [x] Deferred conversion entries include unblock condition and target cycle

## Coverage Summary (T048)

Recalculated after completing T033-T038 conditional deletions and parity upgrades.

| Metric | Value |
|---|---:|
| Total user-facing scenarios tracked | 21 |
| Converted to feature docs | 20 |
| Deferred conversion | 1 |
| Coverage across tracked user-facing scenarios | 95.24% |
| Threshold target | 80% |
| Threshold met | yes |
