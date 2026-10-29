# Migration Guide: pytest-bdd-ng 2.3.1 to pytest-cuke

The current rewrite is distributed as `pytest-cuke` at version 2.3.1. It is a clean break from the previous `pytest-bdd-ng` package and import namespace. Install the new distribution and use the seven-name public facade:

```sh
python -m pip install pytest-cuke
```

```python
from pytest_cuke import given, when, then, step, parsers, scenario, scenarios
```

The pytest plugin is discovered through the `cuke` entry point. Use `pytest-cuke` or `cuke` for the standalone command tree, and use `--cuke-*` options with `cuke_*` ini keys. The previous package imports and CLI aliases are not retained.

The rewrite establishes a cycle-free architecture, pure domain models, modernized Cucumber Messages v22+ compatibility, and well-defined architecture seams.

## 1. Architectural Highlights

- **8-Layer Cycle-Free DAG**: Strict unidirectional dependency flow (L0 Types -> L1 Core -> L2 Models -> L3 Parsers -> L4 Steps -> L5 Execution -> L6 Reporting -> L7 Plugins). Verified via automated DAG tests (`test_layer_architecture.py`).
- **Pure L2 Domain Models**: `Feature`, `Scenario`, and `Step` data models are pure, immutable, and decoupled from pytest runtime fixtures.
- **Seams 1–6 Architecture**:
  - **Seam 1**: Hook specifications and plugin lifecycle.
  - **Seam 2**: Parsers (`.feature`, `.feature.md`, `.bdd.yaml`) producing pure L2 AST models.
  - **Seam 3**: Step definition registry and specificity matcher engine.
  - **Seam 4**: Execution context and stash runtime state.
  - **Seam 5**: Cucumber Messages v22+ serialization and protocol transport.
  - **Seam 6**: Bootstrap configuration and CLI entrypoints.
- **Modernized Cucumber Messages**: Standardized NDJSON streaming and protocol compliance.
- **Elimination of Legacy Hacks**: Replaced pytest internals monkeypatching with pytest Stash and official extension APIs.

## 2. Key Changes & Migration Steps

### Step Definitions
Step definition decorators (`@given`, `@when`, `@then`, `@step`) support string templates, regex, and Cucumber Expressions natively:

```python
from pytest_cuke import given, when, then, parsers

@given(parsers.cucumber_expression("I have {int} cucumbers in my belly"))
def cucumbers(int_value: int):
    return {"cucumbers": int_value}

@when("I eat 2 cucumbers")
def eat_cucumbers(cucumbers):
    cucumbers["cucumbers"] -= 2

@then("I should have 3 cucumbers")
def assert_cucumbers(cucumbers):
    assert cucumbers["cucumbers"] == 3
```

### Scenario Discovery & Execution
Use `scenarios()` for automatic feature discovery and parameterization:

```python
from pytest_cuke import scenarios

scenarios("features")
```

### Tag Filtering & Hooks
Tag expressions follow standard Gherkin syntax:

```python
from pytest_cuke.hook import before_tag, after_tag

@before_tag("@smoke")
def setup_smoke_test(request):
    pass
```

### Reporting & Compatibility
- **Cucumber Messages**: Pass `--cuke-messages-ndjson=<path>` to emit v22+ compliant messages.
- **Cucumber JSON**: Pass `--cuke-json[=<path>]` for the official message-driven JSON execution report (`cucumber.json` by default). Use `--cuke-json-backend=native` to retain the earlier pytest-cuke JSON writer; `cuke_json_backend = "native"` provides the same routing in configuration.
- **Cucumber JUnit XML**: Pass `--cuke-junit[=<path>]` for the official message-driven JUnit XML report (`cucumber.xml` by default), or set `cuke_junit = "path"` in pytest configuration. It can coexist with pytest's native `--junitxml` when each report has a distinct path.
- **Allure**: Native live reporting uses `--cuke-allure[=DIR]` (default `allure-results`) or the `cuke_allure` pytest setting. Install its runtime support with `pytest-cuke[allure]`; a Messages NDJSON file is not required. If you also enable `allure-pytest` with `--alluredir`, use a separate output directory.
