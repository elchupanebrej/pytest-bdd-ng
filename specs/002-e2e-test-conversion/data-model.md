# Data Model: E2E Conversion Tracking

## Entity: ConversionCandidate

- `source_test_path` (string, required, unique)
- `priority` (enum: `high`, `medium`, `low`, required)
- `classification` (enum: `convert_candidate`, `retain_technical`, `deferred_conversion`, required)
- `rubric_user_facing_value` (boolean, required)
- `rubric_external_observability` (boolean, required)
- `rubric_stability_suitability` (boolean, required)
- `decision_rationale` (string, required)
- `target_cycle` (string, optional; required when classification is `deferred_conversion`)
- `unblock_condition` (string, optional; required when classification is `deferred_conversion`)

## Entity: ConvertedScenario

- `feature_path` (string, required, unique)
- `source_test_path` (string, required)
- `task_id` (string, required)
- `intent_summary` (string, required)
- `assertion_summary` (string, required)
- `stale_source_link_check` (boolean, required)

## Entity: ParityAuditEntry

- `task_id` (string, required)
- `source_test_path` (string, required)
- `feature_path` (string, required)
- `verdict` (enum: `pass`, `pending`, `fail`, required)
- `findings` (string, required)
- `remediation_commit` (string, optional)

## Entity: RetentionMarker

- `test_path` (string, required, unique)
- `marker` (enum: `e2e_retain_technical`, `e2e_deferred_conversion`, required)
- `reason` (string, required)

## Relationships

- `ConversionCandidate.source_test_path` -> `ConvertedScenario.source_test_path` (1-to-0/1)
- `ConvertedScenario.task_id` -> `ParityAuditEntry.task_id` (1-to-many)
- `ConversionCandidate.source_test_path` -> `RetentionMarker.test_path` (1-to-0/1, only non-convertible states)

## State Transitions

- `convert_candidate` -> `converted` when feature scenario is created and parity verdict is `pass`.
- `deferred_conversion` -> `convert_candidate` when unblock condition is resolved in target cycle.
- `retain_technical` remains retained but must be re-evaluated each feature cycle.
