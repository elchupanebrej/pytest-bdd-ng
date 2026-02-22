# Data Model: E2E Conversion Tracking

## Entity: ConversionCandidate

- `source_test_path` (string, unique, required)
- `priority` (enum: high, medium, low)
- `convertible` (boolean, required)
- `non_convertible_reason` (string, optional)

## Entity: ConvertedScenario

- `feature_path` (string, unique, required)
- `source_test_path` (string, required)
- `intent_summary` (string, required)
- `assertion_summary` (string, required)

## Entity: ParityAuditEntry

- `task_id` (string, required)
- `source_test_path` (string, required)
- `feature_path` (string, required)
- `verdict` (enum: pass, pending, fail)
- `follow_up_commit` (string, optional)

## Entity: RetentionMarker

- `test_path` (string, unique, required)
- `marker` (string, required)
- `reason` (string, required)
