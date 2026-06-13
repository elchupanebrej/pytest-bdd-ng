# Codegen, Step Binding, and Tolerant Steps Design Specification

This design document specifies the implementation details for the enhanced BDD code generation, scenario/step binding, mock executions, and tolerant step workflows in `pytest-bdd-ng`.

## 1. Goal

Provide a streamlined, CLI-driven development flow for behavior-driven testing. The user lifecycle consists of:
1. Creating a Gherkin feature file.
2. Binding the feature file to a target test file by appending a `scenarios()` block.
3. Scanning for missing step definitions.
4. Generating step definition skeletons decorated with `@not_implemented`.
5. Running scenarios in a `--mock-run` verification mode without executing step function bodies.
6. Managing WIP/not-implemented step outcomes via `--wip-status` at runtime.
7. Supporting soft-failing/tolerant step outcomes via `@tolerant` step decorators and `--tolerant-status` at runtime.

---

## 2. CLI Options

We will add the following options to the pytest CLI parser (prefix-free, coherent with Gherkin tags and pytest marks):

| CLI Option | Action / Type | Valid Choices / Default | Description |
| :--- | :--- | :--- | :--- |
| `--bind-feature` | `store` | Path to `.feature` / `.feature.md` | Feature file to bind to a test file (requires `--target-file`). |
| `--target-file` | `store` | Path to target python test file | Target pytest file to edit for binding or generating steps. |
| `--gather-missing-steps` | `store_true` | N/A | Scans features and prints/reports missing steps via Cucumber messages. |
| `--generate-missing-steps`| `store_true` | N/A | Generates skeletons for missing steps and appends them to the target file. |
| `--mock-run` | `store_true` | N/A | Performs test collection/matching but skips step definition function execution. |
| `--wip-status` | `store` | `passed`, `skipped`, `failed` (default) | Default outcome behavior for not-implemented/WIP steps. |
| `--tolerant-status` | `store` | `failed` (default), `ignored` | Default outcome behavior for failed soft-assertion (tolerant) steps. |

---

## 3. Scenario Marks & Gherkin Tags

Scenario-level markers/tags override the default CLI behaviors:

### WIP / Not-Implemented Status Override:
* **Pytest Mark**: `@pytest.mark.wip_status("passed" | "skipped" | "failed")`
* **Gherkin Tag**: `@wip-status-passed`, `@wip-status-skipped`, or `@wip-status-failed`

### Tolerant Step Status Override:
* **Pytest Mark**: `@pytest.mark.tolerant_status("failed" | "ignored")`
* **Gherkin Tag**: `@tolerant-status-failed` or `@tolerant-status-ignored`

### Resolution Priority:
1. Pytest marker on the scenario function (e.g. `item.iter_markers("wip_status")`).
2. Gherkin tag on the scenario or feature pickle (e.g. `@wip-status-skipped`).
3. CLI option (e.g. `--wip-status`).
4. Default behavior.

---

## 4. Python Step Decorators

We will add two new public decorators to `pytest_bdd`:

### `@not_implemented`
Applied to a step definition to designate it as WIP/not-implemented:
```python
from pytest_bdd import given, not_implemented


@given("some step")
@not_implemented
def some_step():
    raise NotImplementedError
```
It sets `defn.not_implemented = True` on all step definitions registered by the decorated function.

### `@tolerant`
Applied to a step definition to mark it as a soft-assert step:
```python
from pytest_bdd import then, tolerant


@then("this check might fail but shouldn't halt scenario")
@tolerant
def check_behavior():
    assert 1 == 2
```
It sets `defn.tolerant = True` on all step definitions registered by the decorated function.

---

## 5. File Validation and Rewriting (Black/Ruff Formatting)

When `--bind-feature` or `--generate-missing-steps` is executed with a `--target-file`:
1. The target file is opened and parsed.
2. For `--bind-feature`, the block `scenarios("<relative_feature_path>")` is appended. Necessary imports (e.g., `from pytest_bdd import scenarios`) are prepended if missing.
3. For `--generate-missing-steps`, the missing steps are generated as skeletons, formatted using the `@not_implemented` decorator:
   ```python
   @given("some missing step")
   @not_implemented
   def some_missing_step():
       raise NotImplementedError
   ```
4. The file is written back to disk.
5. `ruff format <target-file>` is run programmatically to validate syntax correctness and apply standard formatting.

---

## 6. Step Execution Lifecycle

During scenario execution in `PickleRunner`:

### Mock Run Behavior (`--mock-run`):
If `--mock-run` is active, the pytest hook `pytest_bdd_get_step_caller` returns a dummy function:
```python
if request.config.option.mock_run:
    return lambda: None
```
Matching still runs and throws lookup errors if a step definition is missing, but step function bodies are skipped.

### WIP/Not-Implemented Step Behavior:
If the step definition has `not_implemented = True`:
1. Resolve the target status (`passed`, `skipped`, or `failed`).
2. If `passed`, execution is mocked (body skipped).
3. If `skipped`, `pytest.skip("Step not implemented (wip)")` is called.
4. If `failed`, the function is executed normally (raising `NotImplementedError` or similar).

### Tolerant Step Behavior:
If the step definition has `tolerant = True` and raises an exception:
1. Catch the exception.
2. Record the exception in the active scenario's `soft_failures` list.
3. Set the step outcome to `failed` in reports, but do not raise the error; let the dispatcher proceed to the next step.
4. After all steps in the scenario run:
   * If there are soft failures, resolve the target tolerant status.
   * If `failed`, raise the first recorded exception to fail the overall test.
   * If `ignored`, allow the test to pass (errors remain logged).
