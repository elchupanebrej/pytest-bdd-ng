<!-- markdownlint-disable MD013 -->

# Data Model: Strict Non-Null Lifecycle Runtime

## Entity: Run

- Description: Session-root runtime object stored in `pytest.config.stash` and exposed through the `run_context` fixture and hook parameter `run`.
- Fields:
  - `id` (string, required, stable for one session/config owner)
  - `run_ref` (LifecycleObjectRef, required)
  - `status` (RunStatus enum, required)
  - `transition_index` (integer, required, monotonic)
  - `feature_bindings_by_uri` (map[string, FeatureRuntimeBinding], required)
  - `active_scenario` (ScenarioRun or InactiveScenarioRun, required)
  - `last_error` (ContextErrorState, optional diagnostic payload)
  - `reporting_state` (ReportingLifecycleState, required)
- Validation rules:
  - The canonical `Run` instance in stash MUST be the same object seen via fixture and hook callbacks.
  - `active_scenario` MUST never be represented by `None` in covered runtime access.
  - Session-owned lifecycle boundaries MUST use lifecycle guards when an active scenario is required.

## Entity: ScenarioRun

- Description: Per-scenario runtime context derived from `Run` and bound to one request/scenario lifecycle.
- Fields:
  - `id` (string, required)
  - `run_ref` (LifecycleObjectRef, required)
  - `active_hook` (HookPhase enum, required)
  - `stage` (RunStage enum, required)
  - `status` (RunStatus enum, required)
  - `active_set` (ActiveObjectSet, required)
  - `run` (Run, required)
  - `feature_binding` (FeatureRuntimeBinding or InactiveFeatureBinding, required)
  - `step_run` (StepRun or InactiveStepRun, required)
  - `previous_step` (PreviousStepObject, required)
  - `reference_resolver` (ReferenceResolverState, required)
  - `guard_state` (LifecycleGuardState, required)
- Validation rules:
  - Scenario creation MUST establish `feature_binding`, feature ref, and scenario ref before downstream lifecycle phases consume them.
  - `feature_binding`, `step_run`, and `previous_step` MUST be represented through populated objects or dedicated Empty-State Objects, never `None`.
  - Covered consumer methods MUST rely on lifecycle guard outcomes rather than repeating inline nullability checks.

## Entity: FeatureRuntimeBinding

- Description: Runtime binding between a feature document, its source, and compiled pickles.
- Fields:
  - `uri` (string, required)
  - `filename` (string, required)
  - `gherkin_document` (feature document object, required)
  - `source` (source object or explicit empty-state representation)
  - `pickles` (tuple/list of pickles, required)
  - `run` (Run, required)
- Validation rules:
  - A populated feature binding MUST exist before AST-linked metadata is consumed in active feature/scenario/step phases.
  - Missing binding during an active lifecycle stage MUST produce deterministic guard failure rather than a nullable return.

## Entity: StepRun

- Description: Runtime execution context for the currently executing step.
- Fields:
  - `step` (runtime step object, required during step phases)
  - `keyword` (string or unresolved enrichment object)
  - `text` (string, required)
  - `parameters` (map[string, any], required)
  - `status` (RunStatus enum, required)
  - `duration` (number, optional metadata)
  - `attachments` (array[any], required)
  - `doc_string` (text payload or empty-state object)
  - `data_table` (table payload or empty-state object)
  - `line_number` (integer or unresolved enrichment object)
- Validation rules:
  - `step` and `text` MUST be populated before `before_step_call`.
  - Invalid enrichment MUST be represented by a documented empty-state or deterministic guard failure rather than by a missing `StepRun`.

## Entity: ActiveObjectSet

- Description: Snapshot of lifecycle-owned objects visible to hook and reporting consumers at a given stage.
- Fields:
  - `run` (LifecycleObjectRef, required)
  - `feature` (LifecycleObjectRef, required)
  - `scenario` (LifecycleObjectRef, required)
  - `step` (LifecycleObjectRef, required)
  - `previous_step` (LifecycleObjectRef, required)
  - `captured_at_stage` (RunStage enum, required)
- Validation rules:
  - No lifecycle slot may be omitted to communicate runtime state.
  - Inactive slots MUST still carry explicit state and reason metadata.
  - `feature`, `scenario`, and `step` empty states MUST not mask lifecycle order violations.

## Entity: LifecycleObjectRef

- Description: Normalized reference for lifecycle-owned runtime objects and inactive lifecycle slots.
- Fields:
  - `kind` (enum: `run`, `feature`, `scenario`, `step`, required)
  - `object_id` (string, required)
  - `name` (string, optional metadata)
  - `source` (string, optional metadata)
  - `is_active` (boolean, required)
  - `empty_state_reason` (string, optional, required when inactive)
  - `fail_fast_code` (string, optional)
- Validation rules:
  - Active refs MUST correspond to the current lifecycle stage.
  - Inactive lifecycle state MUST not be represented by a missing ref when the slot itself is part of the contract.

## Entity: LifecycleGuard

- Description: Reusable guard mechanism that decides whether a covered lifecycle access returns a populated object, a dedicated Empty-State Object, or a deterministic failure.
- Fields:
  - `hook_name` (string, required)
  - `requested_kind` (enum: `run`, `feature`, `scenario`, `step`, `step_run`, `previous_step`, `binding`, required)
  - `stage` (RunStage enum, required)
  - `guard_policy` (enum: `require_populated`, `allow_empty_object`, `fail_fast`, required)
  - `allowed_empty_object` (empty-state type identifier, optional)
  - `failure_code` (ContextErrorState.code, optional)
- Validation rules:
  - Guard evaluation MUST happen before consumer logic executes.
  - Repeated inline absence checks inside consumer methods are forbidden for covered lifecycle access.

## Entity: InactiveScenarioRun

- Description: Dedicated Empty-State Object returned when a `Run` exists but no scenario is active in the covered lifecycle contract.
- Fields:
  - `id` (string, required, stable empty-state identifier)
  - `stage` (RunStage enum, required, usually `idle` or `finished`)
  - `active_set` (ActiveObjectSet, required)
  - `empty_state_reason` (string, required)
- Validation rules:
  - Consumers may inspect lifecycle metadata without branching on `None`.
  - Behavior requiring an active scenario MUST escalate through the lifecycle guard, not silently succeed.

## Entity: InactiveFeatureBinding

- Description: Dedicated Empty-State Object returned when feature binding is inactive by design in the current lifecycle stage.
- Fields:
  - `uri` (string, required empty-state identifier)
  - `empty_state_reason` (string, required)
  - `source_reference_policy` (enum: `unavailable`, `default_only`, required)
- Validation rules:
  - Reporter and parser consumers may read boundary-safe metadata through the empty object.
  - Requests for populated AST-linked behavior MUST fail through the lifecycle guard.

## Entity: InactiveStepRun

- Description: Dedicated Empty-State Object returned when step execution is not active.
- Fields:
  - `text` (string, required, may be empty)
  - `status` (RunStatus enum, required)
  - `empty_state_reason` (string, required)
  - `supported_behaviors` (array[string], required)
- Validation rules:
  - Consumers may use the documented contract subset without branching on `None`.
  - Step-execution behavior requiring a populated step MUST fail deterministically.

## Entity: PreviousStepObject

- Description: Polymorphic contract for either the real previous step object or the dedicated `NoPreviousStep` Empty-State Object.
- Variants:
  - `PreviousStep` (populated runtime step object)
  - `NoPreviousStep` (dedicated empty object)
- Validation rules:
  - `NoPreviousStep` is allowed only before a real prior step exists.
  - Consumers may access the documented previous-step metadata contract without `None` checks.

## Entity: ReportingLifecycleState

- Description: Runtime state used to connect lifecycle events to emitted reporting artifacts.
- Fields:
  - `run_started_id` (string or IdleReportingValue, required)
  - `test_run_hook_started_id` (string or IdleReportingValue, required)
  - `active_test_case_id` (string or IdleReportingValue, required)
  - `active_test_case_started_id` (string or IdleReportingValue, required)
  - `active_test_step_id` (string or IdleReportingValue, required)
  - `runtime_step_to_test_step_id` (map[int, string], required)
  - `scenario_attempt_context` (map[string, string|int] or IdleReportingValue, required)
  - `step_started_timestamp` (timestamp or IdleReportingValue, required)
  - `step_finished_timestamp` (timestamp or IdleReportingValue, required)
- Validation rules:
  - Reporter-facing reads MUST not require downstream `None` checks to understand idle lifecycle scope.
  - Idle reporting state MUST remain explicit and contract-compatible.

## Entity: IdleReportingValue

- Description: Dedicated Empty-State Object for reporter fields that are inactive outside an active scenario or step.
- Fields:
  - `empty_state_reason` (string, required)
  - `display_value` (string, required)
  - `state` (enum: `idle`, `finished`, required)
- Validation rules:
  - Reporter code may render idle values directly through a documented contract subset.
  - Idle reporting values MUST not be used to hide missing required runtime bindings.

## Entity: UnresolvedRuntimeEnrichment

- Description: Dedicated Empty-State Object for external or historical metadata that cannot be enriched into populated runtime detail.
- Fields:
  - `state` (enum: `unresolved`, required)
  - `reason` (string, required)
  - `keyword` (string or empty-state metadata)
  - `prefix` (string or empty-state metadata)
  - `line_number` (integer or empty-state metadata)
  - `doc_string` (text payload or empty-state metadata)
  - `data_table` (table payload or empty-state metadata)
- Validation rules:
  - Covered consumers may continue through the documented enrichment contract without branching on `None`.
  - Unresolved enrichment MUST remain distinguishable from lifecycle order violations.

## Entity: ParseErrorEmissionBoundary

- Description: Boundary contract that emits parse errors through pytest hooks when available and otherwise degrades to a deterministic best-effort no-op without exposing nullable helpers to callers.
- Fields:
  - `hook_available` (boolean, required)
  - `source_reference_policy` (enum: `best_effort`, `default_only`, required)
  - `caller_behavior` (enum: `emit_without_branching`, `emit_best_effort`, required)
- Validation rules:
  - Parse error emission MUST not depend on caller-visible `None` checks.
  - Missing hook emitters MUST be handled inside the boundary rather than by returning a nullable sink.

## Entity: ContextErrorState

- Description: Deterministic lifecycle failure payload used when a guard cannot provide a populated object or approved Empty-State Object.
- Fields:
  - `code` (enum: `object_inactive`, `transition_order_violation`, `context_not_initialized`, `binding_missing`, required)
  - `message` (string, required)
  - `hook_name` (string, required)
  - `stage` (RunStage enum, required)
  - `requested_kind` (LifecycleGuard.requested_kind, optional)
- Validation rules:
  - A lifecycle boundary that promises a populated object MUST produce `ContextErrorState` rather than returning a missing value.

## Entity: ReportingContextSnapshot

- Description: Reporter-facing view of lifecycle state derived from `Run` and `ScenarioRun`.
- Fields:
  - `run_id` (string, required)
  - `active_set` (ActiveObjectSet, required)
  - `stage` (RunStage enum, required)
  - `resolved_from_hierarchy` (boolean, required)
  - `fallback_reason` (string or IdleReportingValue, required)
- Validation rules:
  - Idle or finished snapshots MUST still provide complete lifecycle slots and explicit reporting values.
  - Reporter consumers MUST not infer lifecycle state from omitted fields or `None` payloads.

## Entity: ExternalApiCompatibilityRecord

- Description: Compatibility record proving the public hook/plugin surface remains additive-only while internal lifecycle modeling changes.
- Fields:
  - `api_surface_id` (string, required)
  - `baseline_reference` (string, required)
  - `changed_symbols` (array[string], required)
  - `removed_symbols` (array[string], required)
  - `renamed_symbols` (array[string], required)
  - `additive_symbols` (array[string], required)
  - `consumer_migration_required` (boolean, required)
- Validation rules:
  - `removed_symbols` MUST remain empty.
  - `renamed_symbols` MUST remain empty.
  - `consumer_migration_required` MUST remain `false`.

## Enums

- `HookPhase`: `before_scenario`, `run_scenario`, `after_scenario`, `run_step`, `before_step`, `before_step_call`, `after_step`, `step_error`, `step_lookup_error`
- `RunStage`: `idle`, `scenario_setup`, `scenario_running`, `step_running`, `scenario_teardown`, `finished`
- `RunStatus`: `ok`, `failed`, `interrupted`
- `LifecycleGuard.guard_policy`: `require_populated`, `allow_empty_object`, `fail_fast`

## State Transitions

1. Session/config initialization creates `Run`, stores it in stash, and initializes `active_scenario` with `InactiveScenarioRun`.
2. Scenario creation establishes `ScenarioRun`, a populated `FeatureRuntimeBinding`, `NoPreviousStep`, and an initial `ActiveObjectSet` with explicit lifecycle refs.
3. `before_scenario` and `run_scenario` move feature/scenario access behind populated-guarded boundaries without caller-visible missing values.
4. Step phases replace `InactiveStepRun` with populated `StepRun`; `previous_step` stays `NoPreviousStep` until the second step begins.
5. `after_step` transitions `step_run` back to `InactiveStepRun` while preserving a populated previous-step contract.
6. `after_scenario` returns `Run.active_scenario` to `InactiveScenarioRun`, resets reporting values to `IdleReportingValue`, and leaves lifecycle refs explicit rather than missing.
7. Reporter and parse-error consumers read centralized guard results, dedicated Empty-State Objects, and deterministic diagnostics instead of branching on `None`.

## Relationships

- `Run` owns many `ScenarioRun` instances over one pytest session and references one current `ScenarioRun` or `InactiveScenarioRun`.
- `ScenarioRun` references one `Run`, one `ActiveObjectSet`, one populated `FeatureRuntimeBinding` or `InactiveFeatureBinding`, one populated `StepRun` or `InactiveStepRun`, and one `PreviousStepObject`.
- `LifecycleGuard` governs access to `Run`, `ScenarioRun`, `FeatureRuntimeBinding`, `StepRun`, and previous-step contracts.
- `ReportingContextSnapshot` is derived from `Run`, `ScenarioRun`, `ActiveObjectSet`, and `IdleReportingValue`.
- `UnresolvedRuntimeEnrichment` may be attached to step metadata when covered consumers cannot receive populated enrichment.
- `ExternalApiCompatibilityRecord` validates that internal lifecycle refactoring does not break public hook/plugin surfaces.
