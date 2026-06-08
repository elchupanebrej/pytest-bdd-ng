# Hook Taxonomy for Mock-Run (Dry-Run) Mode

This document outlines which hooks are permitted to run during a mock-run and which hooks/bodies are prohibited, ensuring that IDE bootstrap synchronization does not execute heavy user logic or scenario setup code.

## Allowed Hooks (Collection & Registry)
These hooks are necessary for pytest-bdd to collect feature files, build scenario bindings, and register step definitions:
- `pytest_bdd_before_step_definition`
- `pytest_bdd_step_definition_added`
- Pytest collection hooks (e.g., `pytest_collect_file`, `pytest_pycollect_makeitem`)
- Pytest initialization/session hooks

## Prohibited Hooks & Bodies (Scenario/Step Execution Lifecycle)
These hooks and bodies must not run during a mock-run:
- `pytest_bdd_before_scenario`
- `pytest_bdd_after_scenario`
- `pytest_bdd_before_step`
- `pytest_bdd_after_step`
- `pytest_bdd_step_error`
- `pytest_bdd_get_step_caller`
- Step definition function bodies (step implementation logic)
- Pytest fixture function bodies (setup and teardown logic)

## Verification
Mock-run contract tests verify this denylist by asserting that probe side-effects (e.g., writing to probe files) in fixtures, step bodies, or scenario hooks do not occur.
