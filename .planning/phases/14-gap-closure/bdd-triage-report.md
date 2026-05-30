# Phase 14 BDD Triage Report

Generated: 2026-05-20 11:23:31Z

## CLI command

```bash
uv run --extra test --extra testtypes --extra doc-gen --extra struct-bdd python -m pytest tests/cases/e2e/e2e/test_all_bdd_triage_tmp.py -vv -rs --tb=short --no-header
```

Temporary triage module was generated from `tests/cases/e2e/e2e/test_e2e.py` with every `filter_=_exclude_default_bdd_features` replaced by `filter_=lambda *_: True`.

## Summary counts by category

| Category | Count | Notes |
|---|---:|---|
| Collection/Infrastructure | 61 | Every `.feature.md` binding collected as `NOTSET` and skipped with `got empty parameter set for (gherkin_document, pickle, feature_source)` from `src/pytest_bdd/scenario.py:455`. |
| StepNotFound | 0 observed | No scenario body executed, so missing-step failures are currently masked. |
| AssertionError | 0 observed | No scenario body executed. |
| ImportError/ModuleNotFoundError | 0 observed | No scenario body executed. |
| FixtureLookupError | 0 observed | No scenario body executed. |
| ProductionBug | 0 observed | No scenario body executed. |
| Passing non-feature checks | 3 | Three helper tests in the loader passed. |

## Failure catalog

| Feature/scenario | Error type | Message excerpt | Root cause assessment | Recommended fix |
|---|---|---|---|---|
| 61 scenario bindings from `tests/cases/e2e/e2e/test_e2e.py` | Collection/Infrastructure | `got empty parameter set for (gherkin_document, pickle, feature_source)` | Current loader resolves zero pickles for each feature path; the historical 27 failures are not surfaced in this environment. | Fix scenario collection/binding first, then rerun all-scenarios triage to expose StepNotFound/AssertionError/import categories. |

## Fix strategy

1. Treat collection skip as the first BDD blocker for 14-03, because it prevents D-06 categorization of the hidden 27 failures.
2. Investigate why `pytest_bdd.scenarios()` yields empty parameter sets for each `.feature.md` file under current `tests/cases/e2e/e2e/test_e2e.py` and `bdd_features_base_dir = "features/"` configuration.
3. After scenario collection yields concrete pickles, rerun the same all-scenarios triage command and categorize real failures by D-07: step definition, feature-file update, source-code bug, or infrastructure exclusion.
4. Keep explicitly infrastructure-dependent scenarios (`@docker`, `@xdist`, `@allure`, jq/node/browser-dependent cases) separated from local pass criteria unless 14-03 provisions those dependencies.

## Infrastructure-dependent exclusions

- Existing loader excludes tags: `allure`, `docker`, `slow`, `xdist`.
- Existing URI exclusion: `07 report/08 xdist remote network reporting.feature.md`.
- Existing scenario exclusion: `07 report/02 gathering.feature.md::html report could be produced on the feature run`.
