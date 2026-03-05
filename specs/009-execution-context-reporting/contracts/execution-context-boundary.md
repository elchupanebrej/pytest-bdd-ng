# Contract: Execution Context Ownership Boundary

## Scope

Defines read/write ownership of runtime execution context and shared lookup data between execution plugins and reporting plugins.

## Writers (Execution Layer)

Allowed writers:
- `src/pytest_bdd/plugin/scenario_runner/context_store.py`
- `src/pytest_bdd/plugin/scenario_runner/context_transitions.py`
- `src/pytest_bdd/plugin/scenario_runner/plugin.py`
- execution-side writer helpers in `src/pytest_bdd/plugin/scenario_runner/context_access.py`

Writer obligations:
- Create and mutate `ExecutionContext` and `SessionExecutionContext`.
- Initialize/update `reporting_state`, `gherkin_registry`, and message reference index.
- Publish context identity through `config.stash` for cross-plugin access.

## Readers (Reporting Layer)

Read-only consumers:
- `src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py`
- `src/pytest_bdd/plugin/scenario_reporter/plugin.py`
- any reporting serializer plugin consuming runtime context

Reader obligations:
- Resolve required state only via read accessors.
- Never call context bootstrap/mutation APIs.
- On missing context state, emit deterministic diagnostics and skip only correlation-dependent fields.

## API Boundary

Reporter-allowed access:
- `resolve_request_execution_context(...)`
- read-only resolver helpers (`resolve_step_runtime_enrichment`, `resolve_scenario_description`, `resolve_test_step_id_for_runtime_step`)

Reporter-disallowed behavior:
- Calls to `initialize_session_root`, `get_or_create`, `set`, `pop`, `ensure_session_root_for_session`
- Direct assignment to `execution_context.reporting_state.*`
- local `current_<item>` lifecycle state mirrors

## Shared Transport

- Canonical session/context transport uses `config.stash` keys owned by execution flow.
- Stash entries expose context identity; message reference index ownership remains inside execution context objects.

## Compatibility Invariants

- External envelope schema remains unchanged.
- Correlation IDs come from execution context state.
- Missing links stay deterministic and non-fabricated.

## Validation Requirements

- Tests assert reporter has no context-writer behavior.
- Tests assert no `current_*` lifecycle ownership in reporter.
- Tests assert missing context path emits deterministic diagnostics.
