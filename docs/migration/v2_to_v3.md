# Migration Guide: 2.3.1 to 3.0.0

`pytest-bdd-ng` 3.0.0 represents a clean-room architectural rewrite, establishing an 8-layer cycle-free DAG, pure domain models, modernized Cucumber Messages v22+ compatibility, and well-defined architecture seams.

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
from pytest_bdd import given, when, then, parsers

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
from pytest_bdd import scenarios

scenarios("features")
```

### Tag Filtering & Hooks
Tag expressions follow standard Gherkin syntax:

```python
from pytest_bdd.hook import before_tag, after_tag

@before_tag("@smoke")
def setup_smoke_test(request):
    pass
```

### Reporting & Compatibility
- **Cucumber Messages**: Pass `--messages-ndjson=<path>` to emit v22+ compliant messages.
- **Cucumber JSON**: Pass `--cucumberjson=<path>` for standard JSON execution reports.
- **Allure**: Native integration via `pytest_bdd.allure_logging` when `allure-pytest` is installed.
