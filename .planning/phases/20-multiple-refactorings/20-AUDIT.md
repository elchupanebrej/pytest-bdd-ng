# Plugin Audit Report — Phase 20 Plan 03

**Audited:** 2026-06-08
**Scope:** 18 plugin directories under `src/pytest_bdd/plugin/`
**Method:** `plugin_patterns.py` (BLQ1001-BLQ1003) + manual core-to-plugin import analysis

## Summary

- **0 cross-plugin imports** (BLQ1002 pass) — all 18 plugins use hooks for inter-plugin communication
- **0 missing required files** (BLQ1001 pass) — all plugins have entrypoint.py, hook.py, plugin.py
- **BLQ1003** (stash access) — zero violations among plugins
- **8 core-to-plugin layer violations** found across 5 file locations — model, steps, parser, util, testing, and script layers importing from plugin packages
- **3 core plugins** identified per D-12: scenario_test_collector, pickle_runner, gherkin_message_reporter
- **15 extra plugins** grouped into 4 thematic extras per D-13: formatters (13), struct-bdd (1), code-gen (1), allure (0 — allure_logger not in plugin dirs)

---

## Per-Plugin Audit

### Core Plugins (always loaded)

| # | Plugin | Dir | SRP | Lifecycle Layer | LOC (>400?) | Recommendation |
|---|--------|-----|-----|-----------------|-------------|----------------|
| 1 | scenario_test_collector | `plugin/scenario_test_collector/` | Feature collection, test file generation, step matching hook | Collection | No | CORE |
| 2 | pickle_runner | `plugin/pickle_runner/` | Scenario execution runtime, step dispatch, lifecycle state machine | Runtime | plugin.py: 618L | CORE |
| 3 | gherkin_message_reporter | `plugin/gherkin_message_reporter/` | Live reporting bridge, NDJSON message transport, formatter orchestration | Reporting | lifecycle_runtime.py: 618L | CORE |

### Formatters (group: `formatters`)

| # | Plugin | Dir | SRP | Lifecycle Layer | Recommendation |
|---|--------|-----|-----|-----------------|----------------|
| 4 | cucumber_json_formatter | `plugin/cucumber_json_formatter/` | Cucumber JSON output formatter | Reporting | formatters |
| 5 | cucumber_junit | `plugin/cucumber_junit/` | JUnit XML output formatter | Reporting | formatters |
| 6 | cucumber_pretty | `plugin/cucumber_pretty/` | Pretty terminal output formatter | Reporting | formatters |
| 7 | cucumber_progress | `plugin/cucumber_progress/` | Progress indicator formatter | Reporting | formatters |
| 8 | cucumber_progress_bar | `plugin/cucumber_progress_bar/` | Alternative progress bar formatter | Reporting | formatters |
| 9 | cucumber_snippets | `plugin/cucumber_snippets/` | Step snippet generator for undefined steps | Reporting | formatters |
| 10 | cucumber_summary | `plugin/cucumber_summary/` | Summary output formatter | Reporting | formatters |
| 11 | cucumber_usage | `plugin/cucumber_usage/` | Step usage statistics formatter | Reporting | formatters |
| 12 | cucumber_usage_json | `plugin/cucumber_usage_json/` | JSON step usage statistics formatter | Reporting | formatters |
| 13 | cucumber_json | `plugin/cucumber_json/` | Cucumber JSON reporter (NDJSON stream) | Reporting | formatters |
| 14 | cucumber_json_dispatcher | `plugin/cucumber_json_dispatcher/` | JSON message dispatcher | Reporting | formatters |
| 15 | gherkin_terminal_reporter | `plugin/gherkin_terminal_reporter/` | Terminal reporter for gherkin output | Reporting | formatters |
| 16 | scenario_reporter | `plugin/scenario_reporter/` | Scenario-level reporting events | Reporting | formatters |

### Struct BDD (group: `struct-bdd`)

| # | Plugin | Dir | SRP | Lifecycle Layer | Recommendation |
|---|--------|-----|-----|-----------------|----------------|
| 17 | struct_bdd | `plugin/struct_bdd/` | YAML/JSON/HOCON/TOML feature definition parser and plugin | Extra (parsing) | struct-bdd |

### Code Generation (group: `code-gen`)

| # | Plugin | Dir | SRP | Lifecycle Layer | Recommendation |
|---|--------|-----|-----|-----------------|----------------|
| 18 | code_generator | `plugin/code_generator/` | Test code generation from feature files | Extra (tooling) | code-gen |

---

## Core-to-Plugin Layer Violations

Layer hierarchy (bottom-up): FOUNDATION → UTILITY → PARSING → MODEL → STEP DEFINITION → COLLECTION → RUNTIME → REPORTING → EXTRA PLUGINS

### Violation 1: MODEL → pickle_runner (RUNTIME)

**File:** `src/pytest_bdd/model/run_access.py:19`
```python
from pytest_bdd.plugin.pickle_runner.run_transitions import build_lifecycle_ref
```
**Severity:** HIGH — MODEL layer imports from RUNTIME layer (downward dependency)
**Resolution strategy:** Hook indirection — define `pytest_bdd_build_lifecycle_ref` hook that pickle_runner implements

### Violation 2: MODEL → pickle_runner (RUNTIME)

**File:** `src/pytest_bdd/model/run/lifecycle.py:392`
```python
from pytest_bdd.plugin.pickle_runner.run_transitions import (
    build_lifecycle_ref,
    initial_scenario_run_id,
    runtime_object_id,
)
```
**Severity:** HIGH — MODEL layer imports from RUNTIME layer (downward dependency, lazy import)
**Resolution strategy:** Hook indirection — these are runtime lifecycle helpers; pickle_runner hook implementations return them

### Violation 3: STEP DEFINITION → pickle_runner (RUNTIME)

**File:** `src/pytest_bdd/steps/matcher.py:14`
```python
from pytest_bdd.plugin.pickle_runner.const import Steps
```
**Severity:** MEDIUM — Steps is a simple constants class (StrEnum) with Ini/Cli option names
**Resolution strategy:** Move `Steps` constants to a shared location (`src/pytest_bdd/const.py` or `src/pytest_bdd/types/`). This is not behavioral — it's configuration constants that belong in the FOUNDATION or UTILITY layer.

### Violation 4: PARSING → struct_bdd (EXTRA PLUGIN)

**File:** `src/pytest_bdd/parser.py:31-32`
```python
if STRUCT_BDD_INSTALLED:
    from pytest_bdd.plugin.struct_bdd.parser import StructBDDParser
```
**Severity:** LOW — Already guarded by `STRUCT_BDD_INSTALLED` flag; type-only import in a lazy block. The import is for runtime parser registration, not compile-time.
**Resolution strategy:** Hook indirection — define `pytest_bdd_get_struct_bdd_parser` hook that struct_bdd plugin implements

### Violation 5: UTILITY → gherkin_message_reporter (REPORTING)

**File:** `src/pytest_bdd/util/cucumber_formatter_support/standalone.py:7`
```python
from pytest_bdd.plugin.gherkin_message_reporter.session import (...)
```
**Severity:** MEDIUM — UTILITY layer imports from REPORTING layer (downward dependency)
**Resolution strategy:** Move the shared symbols (render/format helpers) to a `util/` or model-level module that both can import

### Violation 6: UTILITY → gherkin_message_reporter (REPORTING)

**File:** `src/pytest_bdd/util/cucumber_formatter_support/registry.py:11`
```python
from pytest_bdd.plugin.gherkin_message_reporter.session import render_live_formatter_bridge
```
**Severity:** MEDIUM — UTILITY layer imports from REPORTING layer (downward dependency)
**Resolution strategy:** Same as Violation 5

### Violation 7: TESTING → gherkin_message_reporter (REPORTING)

**File:** `src/pytest_bdd/testing/cucumber_formatters.py:21`
```python
from pytest_bdd.plugin.gherkin_message_reporter.session import (...)
```
**Severity:** LOW — Testing utility; test-scoped, not production code path
**Resolution strategy:** Same as Violation 5/6 — move shared symbols out of plugin

### Violation 8: SCRIPT → gherkin_message_reporter (REPORTING)

**File:** `src/pytest_bdd/script/render_cucumber_formatters.py:9`
```python
from pytest_bdd.plugin.gherkin_message_reporter.standalone_renderer import (...)
```
**Severity:** LOW — CLI script importing plugin; acceptable for CLI tools
**Resolution strategy:** Documented exception — scripts are allowed to import plugins

---

## File Size Concerns (>400 LOC)

| File | LOC | Owner Layer | Concern |
|------|-----|-------------|---------|
| `parsers.py` | 772 | Parsing | 7 parser implementations; split candidate (A1 scope) |
| `plugin/pickle_runner/plugin.py` | 618 | Runtime | Split into hook impl + step dispatch + transitions |
| `plugin/gherkin_message_reporter/lifecycle_runtime.py` | 618 | Reporting | Split into smaller runtime components |

---

## Cross-Plugin Import Check

`plugin_patterns.py` (BLQ1002) exits 0 — zero cross-plugin imports among all 18 plugin directories. All inter-plugin communication uses pytest-bdd hooks.

---

## Recommendations

1. **Fix Violations 1-2** (model→pickle_runner): Add `pytest_bdd_get_lifecycle_helpers` hook to `hook.py`, implement in `pickle_runner/hook.py`
2. **Fix Violation 3** (steps→pickle_runner): Move `Steps` class to `src/pytest_bdd/const.py` or `src/pytest_bdd/types/`
3. **Fix Violation 4** (parser→struct_bdd): Add `pytest_bdd_get_struct_bdd_parser` hook, implement in `struct_bdd/hook.py`
4. **Fix Violations 5-7** (util/testing→gherkin_message_reporter): Move shared session/rendering symbols to `util/cucumber_formatter_support/` package
5. **Document Violation 8** (script→plugin): Accept as architectural exception — CLI scripts may import plugins

---

*Audit completed: 2026-06-08*
