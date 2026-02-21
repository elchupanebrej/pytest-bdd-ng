# E2E Migration Inventory

## Naming Conventions

- Use `.feature.md` suffix for executable markdown feature docs.
- Use Title Case in file names for user-facing discoverability.
- Keep source-test traceability in each feature file description.

## High-Priority Candidates

- `tests/feature/test_alias.py`
- `tests/feature/test_background.py`
- `tests/feature/test_markdown.py`
- `tests/feature/test_no_sctrict_gherkin.py`
- `tests/feature/test_outline.py`
- `tests/feature/test_outline_empty_values.py`
- `tests/feature/test_rule.py`
- `tests/feature/test_scenario.py`
- `tests/feature/test_scenarios.py`
- `tests/feature/test_tags.py`
- `tests/feature/test_wrong.py`
- `tests/feature/test_http.py`

## Medium-Priority Candidates

- `tests/feature/test_autoload.py`
- `tests/feature/test_cucumber_json.py`
- `tests/feature/test_gherkin_terminal_reporter.py`
- `tests/feature/test_report.py`
- `tests/feature/test_steps.py`
- `tests/allure_/test_allure_outline.py`
- `tests/allure_/test_allure_scenario.py`
- `tests/struct_bdd/test_deserialization.py`
- `tests/struct_bdd/test_steps.py`

## Progress

- [X] High-priority migration batch complete
- [ ] Medium-priority migration batch complete

## Legacy pytest modules retained intentionally

- `tests/feature/test_outline.py` keeps parser/fixture-parameterization internals not yet
  represented as user-facing feature docs.
- `tests/feature/test_http.py` keeps advanced transport and remote source variants not yet
  represented as user-facing feature docs.

## Audit and Fix Policy

- Parity validation status is tracked in `conversion-parity-audit.md`.
- Conversion fixes are applied in new follow-up commits (no history rewrite).
