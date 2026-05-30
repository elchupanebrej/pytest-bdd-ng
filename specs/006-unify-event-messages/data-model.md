<!-- markdownlint-disable MD013 -->

# Data Model: Unify Event Message Reporting

## Entity: EventEnvelope

- Description: Canonical reporting container with exactly one lifecycle or diagnostic payload.
- Fields:
  - `envelope_id` (string, required, unique)
  - `payload_kind` (enum: `meta`, `source`, `gherkin_document`, `pickle`, `step_definition`, `parameter_type`, `hook`, `test_run_started`, `test_case`, `test_case_started`, `test_step_started`, `test_step_finished`, `test_case_finished`, `test_run_finished`, `attachment`, required)
  - `payload` (object, required)
  - `emitted_at` (timestamp, required)
- Validation rules:
  - Exactly one payload field MUST be set per envelope.
  - `payload_kind` MUST match the concrete payload object.

## Entity: LifecycleCorrelation

- Description: Identifier mapping used to link run/scenario/step lifecycle events and derived outputs for one execution attempt.
- Fields:
  - `run_id` (string, required)
  - `scenario_attempt_id` (string, required, unique per attempt)
  - `step_id` (string, optional)
  - `worker_id` (string, required)
  - `attempt_index` (integer, required)
- Validation rules:
  - `scenario_attempt_id` MUST be unique across retries and parallel workers.
  - `attempt_index` MUST be >= 0.

## Entity: LifecycleEvent

- Description: Start or finish record for run, scenario, or step execution.
- Fields:
  - `event_id` (string, required, unique)
  - `scope` (enum: `run`, `scenario`, `step`, required)
  - `phase` (enum: `started`, `finished`, required)
  - `status` (enum: `passed`, `failed`, `skipped`, `undefined`, optional)
  - `timestamp` (timestamp, required)
  - `duration_nanos` (integer, optional)
  - `correlation` (LifecycleCorrelation, required)
- Validation rules:
  - A `finished` event MUST reference a prior `started` event for the same scope/correlation.
  - `duration_nanos` MUST be present and >= 0 for finished step events.

## Entity: DerivedReportView

- Description: Legacy or user-facing report output rendered from canonical envelopes.
- Fields:
  - `view_id` (string, required)
  - `view_kind` (enum: `scenario_report`, `terminal_output`, `json_output`, required)
  - `source_run_id` (string, required)
  - `rendered_content` (object|string, required)
  - `rendered_at` (timestamp, required)
- Validation rules:
  - Every rendered status/outcome MUST map to canonical lifecycle events from the same `source_run_id`.
  - View generation MUST NOT introduce independent event construction.

## Entity: MessageValidationRun

- Description: One full validation pass over produced message stream and derived outputs.
- Fields:
  - `validation_run_id` (string, required)
  - `protocol_version` (string, required)
  - `stream_entries` (integer, required)
  - `orphan_reference_count` (integer, required)
  - `duplicate_lifecycle_id_count` (integer, required)
  - `status` (enum: `pass`, `fail`, required)
  - `started_at` (timestamp, required)
  - `finished_at` (timestamp, required)
- Validation rules:
  - `protocol_version` MUST equal latest supported version in this feature scope.
  - `status` MUST be `fail` when orphan or duplicate counts are non-zero.

## Entity: SpecCatalogEntry

- Description: Specification directory metadata used by prerequisite scripts to resolve one active feature path per prefix.
- Fields:
  - `prefix` (string, required, pattern `^[0-9]{3}$`)
  - `name` (string, required)
  - `path` (string, required)
  - `is_conflict` (boolean, required)
  - `resolved_prefix` (string, optional)
- Validation rules:
  - Exactly one active entry MUST exist per prefix after conflict cleanup.
  - If `is_conflict` is true, `resolved_prefix` MUST be populated with next available prefix.

## Relationships

- `EventEnvelope` may contain one `LifecycleEvent` payload.
- `LifecycleEvent` requires one `LifecycleCorrelation`.
- `DerivedReportView.source_run_id` references lifecycle events in canonical envelopes.
- `MessageValidationRun` validates `EventEnvelope` stream and `DerivedReportView` consistency.
- `SpecCatalogEntry` governs feature-directory resolution for plan/spec prerequisites.

## State Transitions

1. Emit canonical `EventEnvelope` records during run/scenario/step lifecycle.
2. Associate each lifecycle event with `LifecycleCorrelation` at attempt scope.
3. Finalize lifecycle chains (`started` -> `finished`) and compute durations/status.
4. Build `DerivedReportView` outputs exclusively from canonical envelopes.
5. Execute `MessageValidationRun` to verify schema, ordering, uniqueness, and derived-output consistency.
6. Audit `SpecCatalogEntry` records and resolve duplicate prefixes to deterministic unique mappings.
