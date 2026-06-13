# Quickstart: Using StepRun

This guide provides a quick overview of how to access step execution context using the new `StepRun` object in `pytest-bdd-ng`.

## Overview

The `extended_step_context` has been completely replaced by a structured object `run.scenario_run.step_run`. This `StepRun` object provides a clean, strongly-typed interface for accessing information about the currently executing step.

## Accessing `StepRun`

The `run` object is typically available in hooks or via fixtures. You access the current step's context through its nested properties.

### Example: Inside a pytest hook

```python
import pytest


def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    run = request.stash.get(RUN_KEY)

    # Access the active StepRun
    if run and run.scenario_run and run.scenario_run.step_run:
        step_run = run.scenario_run.step_run

        # Access attributes
        print(f"Executing step keyword: {step_run.keyword}")
        print(f"Executing step text: {step_run.text}")
        print(f"Parsed parameters: {step_run.parameters}")
```

## Migration from `extended_step_context`

If your code previously used `extended_step_context`, you MUST update it.

**Old Code:**
```python
# Accessing legacy context
from pytest_bdd.steps import extended_step_context

context = extended_step_context.get()
```

**New Code:**
```python
# Accessing StepRun via the active run context
# The exact access pattern may depend on how the request or run is passed to your function
step_run = request.stash.get(RUN_KEY).scenario_run.step_run
```

Ensure that your plugins or hooks are designed to gracefully handle scenarios where `step_run` might be `None` (e.g., executing before the first step has officially started).
