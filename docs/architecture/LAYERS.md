# Architectural Layer Model

pytest-bdd-ng uses an 8-layer directed acyclic graph (DAG) architecture where each
layer may only import from layers with strictly lower order. This document defines
the layer hierarchy, module assignments, allowed imports, and enforcement rules.

See [OBJECT_MAP.md](OBJECT_MAP.md) for per-object architectural scores across
7 criteria for all public API objects.

## Layer Diagram

```text
                          ┌────────────────────┐
                          │   EXTRA PLUGINS    │  Order 8
                          │  struct_bdd,       │
                          │  code_generator,   │
                          │  allure_logger     │
                          └────────┬───────────┘
                                   │
                          ┌────────┴───────────┐
                          │    REPORTING       │  Order 7
                          │  cucumber_*,       │
                          │  gherkin_terminal, │
                          │  scenario_reporter │
                          └────────┬───────────┘
                                   │
                          ┌────────┴───────────┐
                          │     RUNTIME        │  Order 6
                          │  pickle_runner,    │
                          │  scenario_test_    │
                          │    collector       │
                          └────────┬───────────┘
                                   │
                          ┌────────┴───────────┐
                          │    COLLECTION      │  Order 5
                          │  collector,        │
                          │  feature_locator,  │
                          │  scenario_locator, │
                          │  scenario          │
                          └────────┬───────────┘
                                   │
                          ┌────────┴───────────┐
                          │  STEP DEFINITION   │  Order 4
                          │  steps, hook       │
                          └────────┬───────────┘
                                   │
                          ┌────────┴───────────┐
                          │      MODEL         │  Order 3
                          │  Run, ScenarioRun, │
                          │  StashBound,       │
                          │  message_converter │
                          └────────┬───────────┘
                                   │
                          ┌────────┴───────────┐
                          │     PARSING        │  Order 2
                          │  parser, parsers,  │
                          │  collector_batch,  │
                          │  _gherkin_go       │
                          └────────┬───────────┘
                                   │
                          ┌────────┴───────────┐
                          │     UTILITY        │  Order 1
                          │  util/             │
                          └────────┬───────────┘
                                   │
                          ┌────────┴───────────┐
                          │    FOUNDATION      │  Order 0
                          │  compatibility,    │
                          │  types, const,     │
                          │  mimetype          │
                          └────────────────────┘

Import direction: bottom-up only (higher layers → lower layers).
Horizontal imports across plugins in same layer are forbidden (BLQ1302).
```

## Per-Layer Module Tables

### Foundation (Order 0)

| Module | Description |
|--------|-------------|
| `pytest_bdd.compatibility` | Cross-version Python/pytest shims |
| `pytest_bdd.types` | Custom exception and warning types |
| `pytest_bdd.const` | Project-wide constants and enums |
| `pytest_bdd.mimetype` | MIME type constants for feature files |

**Allowed imports:** stdlib and third-party only. No internal imports permitted.

### Utility (Order 1)

| Module | Description |
|--------|-------------|
| `pytest_bdd.util` | Shared helpers: IdGenerator, data_table, test_group_ordering, URL utilities |

**Allowed imports:** `foundation`

### Parsing (Order 2)

| Module | Description |
|--------|-------------|
| `pytest_bdd.parser` | Python Gherkin parser (plain + Markdown) |
| `pytest_bdd.parsers` | Step parser implementations (re, parse, cfparse, cucumber_expression, etc.) |
| `pytest_bdd.collector_batch` | Lazy-batched async feature parsing |
| `pytest_bdd._gherkin_go` | Go ctypes parser backend bridge |

**Allowed imports:** `foundation`, `utility`

### Model (Order 3)

| Module | Description |
|--------|-------------|
| `pytest_bdd.model` | Domain objects: Run, ScenarioRun, FeatureRuntimeBinding, StashBound, message conversion/validation |

**Allowed imports:** `foundation`, `utility`

**Exception:** Model may import from `parsing` for gherkin pickle compilation
(`FeatureRuntimeBinding.ensure_pickles()`). See `layers.toml` exceptions table.

### Step Definition (Order 4)

| Module | Description |
|--------|-------------|
| `pytest_bdd.steps` | Step definition registry, matcher, @given/@when/@then decorators |
| `pytest_bdd.hook` | Before/after/around BDD lifecycle hooks |

**Allowed imports:** `foundation`, `utility`, `parsing`, `model`

### Collection (Order 5)

| Module | Description |
|--------|-------------|
| `pytest_bdd.collector` | FeatureFileModule — pytest collector for .feature files |
| `pytest_bdd.feature_locator` | ScenarioLocatorBuilder, FeatureLocator |
| `pytest_bdd.scenario_locator` | FileScenarioLocator, UrlScenarioLocator |
| `pytest_bdd.scenario` | Public API: scenario(), scenarios() |

**Allowed imports:** `foundation`, `utility`, `parsing`, `model`, `step_definition`

### Runtime (Order 6)

| Module | Description |
|--------|-------------|
| `pytest_bdd.plugin.pickle_runner` | Scenario execution runtime (step dispatch, state machine, hooks) |
| `pytest_bdd.plugin.scenario_test_collector` | Feature autoload, test generation, step matching |

**Allowed imports:** `foundation`, `utility`, `parsing`, `model`, `step_definition`, `collection`

### Reporting (Order 7)

| Module | Description |
|--------|-------------|
| `pytest_bdd.plugin.gherkin_message_reporter` | Live reporting bridge (NDJSON) |
| `pytest_bdd.plugin.cucumber_json` | Cucumber JSON reporter |
| `pytest_bdd.plugin.cucumber_json_formatter` | JSON formatter output |
| `pytest_bdd.plugin.cucumber_json_dispatcher` | JSON dispatcher |
| `pytest_bdd.plugin.cucumber_junit` | JUnit XML formatter |
| `pytest_bdd.plugin.cucumber_pretty` | Pretty terminal formatter |
| `pytest_bdd.plugin.cucumber_progress` | Progress bar formatter |
| `pytest_bdd.plugin.cucumber_progress_bar` | Alternative progress bar |
| `pytest_bdd.plugin.cucumber_snippets` | Undefined step snippet generator |
| `pytest_bdd.plugin.cucumber_summary` | Summary statistics formatter |
| `pytest_bdd.plugin.cucumber_usage` | Step usage statistics |
| `pytest_bdd.plugin.cucumber_usage_json` | JSON step usage stats |
| `pytest_bdd.plugin.gherkin_terminal_reporter` | Terminal reporter |
| `pytest_bdd.plugin.scenario_reporter` | Scenario reporter |

**Allowed imports:** All lower layers. Cross-plugin imports between reporting
plugins are forbidden (enforced by BLQ1002).

### Extra Plugins (Order 8)

| Module | Description |
|--------|-------------|
| `pytest_bdd.plugin.struct_bdd` | YAML/JSON/TOML/HOCON BDD feature definitions |
| `pytest_bdd.plugin.code_generator` | Missing step definition code generator |
| `pytest_bdd.plugin.allure_logger` | Allure test reporting integration |

**Allowed imports:** All lower layers.

## Enforcement Rules

### BLQ1301 — Downward Import

Fires when a module imports from a layer with equal or higher order that is
not in its `allowed_imports` list. This prevents circular dependencies and
preserves the architectural DAG.

**Message format:**
```text
BLQ1301: downward import — module {current_module} (layer {current_layer},
order {current_order}) imports {imported_module} (layer {imported_layer},
order {imported_order}). Allowed: {allowed_layers}
```

### BLQ1302 — Horizontal Import

Fires when a module imports from the same layer but a different plugin/package
boundary. Prevents tight coupling between sibling plugins.

**Message format:**
```text
BLQ1302: horizontal import — module {current_module} (layer {current_layer})
imports {imported_module} from same layer. Cross-module imports within layer
{imported_layer} are forbidden.
```

### Enforcement via Pylint Plugin

Layer enforcement is verified via the custom Pylint checkers (plugin) located under `src/pytest_bdd/_pylint/`.

To run the layer enforcement and all other custom rules:
```bash
make custom-rules
```
or directly via:
```bash
uv run pylint --load-plugins=pytest_bdd._pylint --disable=all --enable=downward-layer-import,horizontal-layer-import src/
```

The custom Pylint checker reads `docs/architecture/layers.toml` at startup and validates all imports against the configured DAG.

Configuration is driven by `layers.toml` — layer boundaries can be updated
without modifying the enforcement plugin.

## Known Exceptions

Documented in `layers.toml` `[exceptions]` table:

| From Module | To Module | Justification |
|-------------|-----------|---------------|
| `pytest_bdd.model` | `pytest_bdd.parser` | Gherkin pickle compilation required by FeatureRuntimeBinding |
| `pytest_bdd.parsers` | `pytest_bdd.model` | Step parser references StepDefinitionPatternType enum |

These exceptions are validated at enforcement time and do not trigger
BLQ1301/BLQ1302 violations.
