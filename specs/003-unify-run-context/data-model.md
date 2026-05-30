<!-- markdownlint-disable MD013 -->

# Data Model: Session-Root Execution Context Hierarchy

## Entity: SessionExecutionContext

- Description: Root execution context created once per pytest session at `pytest_sessionstart`.
- Fields:
  - `session_context_id` (string, required, unique per session)
  - `run_ref` (LifecycleObjectRef, required)
  - `active_feature_context_id` (string, optional)
  - `active_scenario_context_id` (string, optional)
  - `active_step_context_id` (string, optional)
  - `status` (ExecutionStatus enum, required)
  - `transition_index` (integer, required, monotonic)
  - `last_error` (ContextErrorState, optional)
- Validation rules:
  - `transition_index` MUST increase by exactly one per accepted transition.
  - `run_ref.is_active` MUST remain true during session execution.

## Entity: SessionContextStashBinding

- Description: Canonical binding of session context into `pytest.config.stash`.
- Fields:
  - `stash_key` (string, required, stable constant for plugin version)
  - `session_context_id` (string, required, references SessionExecutionContext)
  - `stored_at_stage` (ExecutionStage enum, required)
- Validation rules:
  - `stash_key` MUST map to exactly one `SessionExecutionContext` per pytest session.
  - Stored context instance identity MUST equal fixture-resolved context instance identity.

## Entity: SessionContextFixtureBinding

- Description: Session-scoped fixture exposure for `SessionExecutionContext`.
- Fields:
  - `fixture_name` (string, required)
  - `scope` (enum: `session`, required)
  - `session_context_id` (string, required)
- Validation rules:
  - Fixture resolution MUST succeed from early runtime stage (`pytest_bdd_before_scenario`) onward.
  - Fixture object identity MUST equal stash-backed canonical object identity.

## Entity: ExecutionContextNode

- Description: Child context node in hierarchy (`feature`, `scenario`, `step`).
- Fields:
  - `context_id` (string, required, unique)
  - `parent_context_id` (string, required for non-root nodes)
  - `kind` (enum: `feature`, `scenario`, `step`, required)
  - `object_ref` (LifecycleObjectRef, required)
  - `is_active` (boolean, required)
  - `opened_at_transition` (integer, required)
  - `closed_at_transition` (integer, optional)
- Validation rules:
  - `parent_context_id` MUST point to `SessionExecutionContext` or a valid ancestor node.
  - Active step nodes MUST be descendants of an active scenario node.

## Entity: LifecycleObjectRef

- Description: Normalized reference to runtime lifecycle objects.
- Fields:
  - `kind` (enum: `run`, `feature`, `scenario`, `step`, required)
  - `object_id` (string, required)
  - `name` (string, optional)
  - `source` (string, optional)
  - `is_active` (boolean, required)
- Validation rules:
  - (`kind`, `object_id`) MUST be unique within one active snapshot.

## Entity: ActiveObjectSet

- Description: Snapshot view derived from session root and active child nodes at hook/reporting time.
- Fields:
  - `run` (LifecycleObjectRef, required)
  - `feature` (LifecycleObjectRef, optional)
  - `scenario` (LifecycleObjectRef, optional)
  - `step` (LifecycleObjectRef, optional)
  - `previous_step` (LifecycleObjectRef, optional)
  - `captured_at_stage` (ExecutionStage enum, required)
- Validation rules:
  - Snapshot MUST reflect currently active nodes only.
  - `step` MUST be null outside step stages.

## Entity: HookParameterModel

- Description: Existing hook parameter model enriched with `execution_context` field/reference.
- Fields:
  - `request` (runtime request reference, required)
  - `feature` (feature model reference, optional)
  - `scenario` (scenario model reference, optional)
  - `step` (step model reference, optional)
  - `execution_context` (ExecutionContextView, required during BDD runtime)
- Validation rules:
  - All parameter objects in one hook invocation MUST reference the same `ExecutionContextView` identity.
  - Contract remains field-based; separate top-level hook argument is not required.

## Entity: ExecutionContextView

- Description: Hook/reporting-consumable view composed from root + active nodes.
- Fields:
  - `session` (SessionExecutionContext, required)
  - `active_set` (ActiveObjectSet, required)
  - `active_hook` (HookPhase enum, required)
  - `stage` (ExecutionStage enum, required)
  - `status` (ExecutionStatus enum, required)
- Validation rules:
  - `active_set.captured_at_stage` MUST equal `stage`.

## Entity: ReportingContextSnapshot

- Description: Reporting-safe read model derived from context hierarchy.
- Fields:
  - `session_context_id` (string, required)
  - `active_set` (ActiveObjectSet, required)
  - `stage` (ExecutionStage enum, required)
  - `resolved_from_hierarchy` (boolean, required)
  - `fallback_reason` (string, optional)
- Validation rules:
  - `resolved_from_hierarchy=true` when corresponding node(s) are active.
  - If `resolved_from_hierarchy=false`, `fallback_reason` MUST be present.

## Entity: ContextErrorState

- Description: Structured diagnostics for inactive-object and transition errors.
- Fields:
  - `code` (enum: `object_inactive`, `transition_order_violation`, `context_not_initialized`, required)
  - `message` (string, required)
  - `hook_name` (string, required)
  - `stage` (ExecutionStage enum, required)
  - `requested_kind` (enum: `run`, `feature`, `scenario`, `step`, optional)
- Validation rules:
  - `requested_kind` MUST be present when `code=object_inactive`.

## Entity: ExternalApiCompatibilityRecord

- Description: Compatibility report proving additive-only external API evolution.
- Fields:
  - `api_surface_id` (string, required)
  - `baseline_reference` (string, required)
  - `changed_symbols` (array[string], required)
  - `removed_symbols` (array[string], required)
  - `renamed_symbols` (array[string], required)
  - `additive_symbols` (array[string], required)
  - `consumer_migration_required` (boolean, required)
- Validation rules:
  - `removed_symbols` MUST be empty.
  - `renamed_symbols` MUST be empty.
  - `consumer_migration_required` MUST be false.

## Enums

- `HookPhase`: `before_scenario`, `run_scenario`, `after_scenario`, `run_step`, `before_step`, `before_step_call`, `after_step`, `step_error`, `step_lookup_error`
- `ExecutionStage`: `idle`, `scenario_setup`, `scenario_running`, `step_running`, `scenario_teardown`, `finished`
- `ExecutionStatus`: `ok`, `failed`, `interrupted`

## State Transitions

1. `pytest_sessionstart` creates `SessionExecutionContext`, stores it in stash, and enables session-scoped fixture resolution.
2. Before-scenario opens feature/scenario child nodes and moves stage to `scenario_setup`.
3. Scenario execution transitions to `scenario_running`.
4. Step dispatch opens/updates step node and moves to `step_running`.
5. After step closes step node and returns to `scenario_running`.
6. After scenario closes scenario/step child nodes and moves to `scenario_teardown`, then `finished` for scenario scope.
7. Failure transitions set `status=failed` while retaining latest valid active snapshot for reporting.

## Relationships

- `SessionExecutionContext` is the root for all `ExecutionContextNode` entities in one pytest session.
- `SessionContextStashBinding` and `SessionContextFixtureBinding` both reference the same `SessionExecutionContext` identity.
- `ExecutionContextView` references one `SessionExecutionContext` and one derived `ActiveObjectSet`.
- `HookParameterModel.execution_context` references one `ExecutionContextView`.
- `ReportingContextSnapshot` is derived from `ExecutionContextView`/hierarchy and may include fallback metadata.
- `ContextErrorState` is attached to session/view objects for diagnostics.
- `ExternalApiCompatibilityRecord` validates public API impact independently from runtime state.
