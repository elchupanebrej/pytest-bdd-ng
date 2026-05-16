# Plugin Audit Report — 17 Active Plugins

**Date:** 2026-05-16
**Phase:** 11-audit-prune
**Decision:** D-05, D-06 — All plugins confirmed active with entry points

---

## Audit Methodology

- **Entry points:** Cross-referenced `pyproject.toml` `[project.entry-points.pytest11]` (lines 91-108)
- **Consumers:** Searched `src/` and `tests/` for import references to each plugin module
- **Tests:** Counted test files matching each plugin name under `tests/`
- **Purpose:** Extracted from plugin `entrypoint.py` docstrings and module structure

---

## Plugin Entries

### 1. pytest-bdd-code-generator

- **Entry point:** `pytest_bdd.plugin.code_generator.entrypoint`
- **Purpose:** Missing test code generation plugin — generates step definitions for undefined Gherkin steps
- **Import consumers:** 0 (loaded dynamically via pytest entry point)
- **Test files:** 3
- **Justification:** **KEEP** — Active entry point, provides code generation for undefined steps, tested

### 2. pytest-bdd-cucumber-formatter-json

- **Entry point:** `pytest_bdd.plugin.cucumber_json_formatter.entrypoint:json_plugin`
- **Purpose:** Cucumber JSON formatter — outputs test results in Cucumber-compatible JSON format
- **Import consumers:** 0 (loaded dynamically via pytest entry point)
- **Test files:** 0
- **Justification:** **KEEP** — Active entry point, standard Cucumber formatter, part of formatter suite

### 3. pytest-bdd-cucumber-formatter-junit

- **Entry point:** `pytest_bdd.plugin.cucumber_junit.entrypoint:junit_plugin`
- **Purpose:** Cucumber JUnit formatter — outputs test results in JUnit XML format
- **Import consumers:** 0 (loaded dynamically via pytest entry point)
- **Test files:** 0
- **Justification:** **KEEP** — Active entry point, standard CI/CD integration formatter

### 4. pytest-bdd-cucumber-formatter-pretty

- **Entry point:** `pytest_bdd.plugin.cucumber_pretty.entrypoint:pretty_plugin`
- **Purpose:** Cucumber pretty formatter — human-readable test output with colors
- **Import consumers:** 0 (loaded dynamically via pytest entry point)
- **Test files:** 0
- **Justification:** **KEEP** — Active entry point, standard developer-facing formatter

### 5. pytest-bdd-cucumber-formatter-progress

- **Entry point:** `pytest_bdd.plugin.cucumber_progress.entrypoint:progress_plugin`
- **Purpose:** Cucumber progress formatter — shows test progress as dots/symbols
- **Import consumers:** 0 (loaded dynamically via pytest entry point)
- **Test files:** 0
- **Justification:** **KEEP** — Active entry point, standard CI-friendly formatter

### 6. pytest-bdd-cucumber-formatter-progress-bar

- **Entry point:** `pytest_bdd.plugin.cucumber_progress_bar.entrypoint:progress_bar_plugin`
- **Purpose:** Cucumber progress bar formatter — visual progress bar for test execution
- **Import consumers:** 0 (loaded dynamically via pytest entry point)
- **Test files:** 0
- **Justification:** **KEEP** — Active entry point, enhanced visual progress indicator

### 7. pytest-bdd-cucumber-formatter-snippets

- **Entry point:** `pytest_bdd.plugin.cucumber_snippets.entrypoint:snippets_plugin`
- **Purpose:** Cucumber snippets formatter — generates step definition snippets for undefined steps
- **Import consumers:** 0 (loaded dynamically via pytest entry point)
- **Test files:** 0
- **Justification:** **KEEP** — Active entry point, developer productivity tool

### 8. pytest-bdd-cucumber-formatter-summary

- **Entry point:** `pytest_bdd.plugin.cucumber_summary.entrypoint:summary_plugin`
- **Purpose:** Cucumber summary formatter — test execution summary output
- **Import consumers:** 0 (loaded dynamically via pytest entry point)
- **Test files:** 0
- **Justification:** **KEEP** — Active entry point, standard summary formatter

### 9. pytest-bdd-cucumber-formatter-usage

- **Entry point:** `pytest_bdd.plugin.cucumber_usage.entrypoint:usage_plugin`
- **Purpose:** Cucumber usage formatter — shows step usage statistics
- **Import consumers:** 0 (loaded dynamically via pytest entry point)
- **Test files:** 0
- **Justification:** **KEEP** — Active entry point, step usage analysis tool

### 10. pytest-bdd-cucumber-formatter-usage-json

- **Entry point:** `pytest_bdd.plugin.cucumber_usage_json.entrypoint:usage_json_plugin`
- **Purpose:** Cucumber usage JSON formatter — step usage statistics in JSON format
- **Import consumers:** 0 (loaded dynamically via pytest entry point)
- **Test files:** 0
- **Justification:** **KEEP** — Active entry point, machine-readable usage data

### 11. pytest-bdd-cucumber-json

- **Entry point:** `pytest_bdd.plugin.cucumber_json.entrypoint`
- **Purpose:** Cucumber JSON output formatter — legacy/alternate JSON output
- **Import consumers:** 1 (`tests/plugin/test_cucumber_json.py`)
- **Test files:** 23
- **Justification:** **KEEP** — Active entry point, heavily tested (23 test files), widely used

### 12. pytest-bdd-gherkin-message-reporter

- **Entry point:** `pytest_bdd.plugin.gherkin_message_reporter.entrypoint`
- **Purpose:** Gherkin message reporter — live formatter bridge for cucumber-messages protocol
- **Import consumers:** 12 (src and tests)
- **Test files:** 14
- **Justification:** **KEEP** — Active entry point, core messaging infrastructure, 12 import consumers, 14 test files

### 13. pytest-bdd-gherkin-scenario-reporter

- **Entry point:** `pytest_bdd.plugin.scenario_reporter.entrypoint`
- **Purpose:** Gherkin scenario reporter — scenario-level reporting plugin
- **Import consumers:** 1
- **Test files:** 3
- **Justification:** **KEEP** — Active entry point, scenario reporting, tested

### 14. pytest-bdd-gherkin-terminal-reporter

- **Entry point:** `pytest_bdd.plugin.gherkin_terminal_reporter.entrypoint`
- **Purpose:** Gherkin terminal reporter — custom terminal output for BDD tests
- **Import consumers:** 1
- **Test files:** 23
- **Justification:** **KEEP** — Active entry point, primary terminal output, heavily tested (23 test files)

### 15. pytest-bdd-scenario-runner

- **Entry point:** `pytest_bdd.plugin.pickle_runner.entrypoint`
- **Purpose:** Scenario runner — executes Gherkin pickles with step definitions
- **Import consumers:** 3
- **Test files:** 0 (tested via integration/e2e tests)
- **Justification:** **KEEP** — Active entry point, core runtime execution engine, 3 import consumers

### 16. pytest-bdd-scenario-test-collector

- **Entry point:** `pytest_bdd.plugin.scenario_test_collector.entrypoint`
- **Purpose:** Scenario test collector — feature autoload and batch collection
- **Import consumers:** 1
- **Test files:** 0 (tested via integration/e2e tests)
- **Justification:** **KEEP** — Active entry point, feature collection pipeline, 1 import consumer

### 17. pytest-bdd-struct-bdd

- **Entry point:** `pytest_bdd.plugin.struct_bdd.entrypoint`
- **Purpose:** Struct BDD — YAML/JSON/HOCON/TOML BDD support
- **Import consumers:** 3
- **Test files:** 4
- **Justification:** **KEEP** — Active entry point, structured BDD format support, tested

---

## Summary

| Status | Count |
|--------|-------|
| KEEP | 17 |
| REMOVE | 0 |
| MERGE | 0 |

**Total plugins:** 17
**All plugins have active entry points** registered in `pyproject.toml` `[project.entry-points.pytest11]`
**No dead code plugins found** — all 17 serve distinct purposes in the formatter suite, runtime, or collection pipeline
