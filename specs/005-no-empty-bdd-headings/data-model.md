<!-- markdownlint-disable MD013 -->

# Data Model: Non-empty BDD Heading Validation

## Entity: FeatureDocument

- Description: A file under `features/` that is parsed as gherkin or gherkin-in-markdown input.
- Fields:
  - `document_id` (string, required, unique)
  - `absolute_path` (string, required)
  - `relative_path` (string, required)
  - `format` (enum: `gherkin_markdown`, `gherkin_plain`, required)
  - `parsed` (boolean, required)
- Validation rules:
  - `absolute_path` MUST resolve under `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/`.
  - `parsed` MUST be true before heading validation is evaluated.

## Entity: ParsedHeadingRecord

- Description: Canonical heading record emitted from parsed AST for one BDD heading.
- Fields:
  - `heading_id` (string, required, unique within one document)
  - `document_id` (string, required, references `FeatureDocument.document_id`)
  - `heading_type` (enum: `feature`, `scenario`, `scenario_outline`, required)
  - `name_raw` (string, optional)
  - `name_trimmed` (string, optional)
  - `line` (integer, required)
  - `column` (integer, optional)
- Validation rules:
  - `line` MUST be >= 1.
  - `heading_type` MUST be one of the policy-controlled heading types.

## Entity: HeadingValidationPolicy

- Description: Rule set defining what constitutes an invalid heading title.
- Fields:
  - `policy_id` (string, required)
  - `enforced_heading_types` (array[enum], required)
  - `trim_whitespace` (boolean, required)
  - `empty_name_is_violation` (boolean, required)
  - `snippet_text_excluded` (boolean, required)
- Validation rules:
  - `enforced_heading_types` MUST include `feature`, `scenario`, and `scenario_outline`.
  - `trim_whitespace` MUST be true.
  - `empty_name_is_violation` MUST be true.
  - `snippet_text_excluded` MUST be true.

## Entity: HeadingValidationViolation

- Description: Single violation result for one invalid parsed heading.
- Fields:
  - `violation_id` (string, required, unique)
  - `document_id` (string, required)
  - `line` (integer, required)
  - `heading_type` (enum, required)
  - `code` (enum: `EMPTY_HEADING_TITLE`, required)
  - `message` (string, required)
  - `name_raw` (string, optional)
- Validation rules:
  - `code` MUST equal `EMPTY_HEADING_TITLE` for this feature scope.
  - `message` MUST include enough context to locate and fix the issue.

## Entity: HeadingValidationRun

- Description: One complete scan execution over repository feature documents.
- Fields:
  - `run_id` (string, required)
  - `started_at` (ISO-8601 datetime, required)
  - `finished_at` (ISO-8601 datetime, required)
  - `documents_scanned` (integer, required)
  - `violations` (array[HeadingValidationViolation], required)
  - `status` (enum: `pass`, `fail`, required)
- Validation rules:
  - `status` MUST be `fail` when `violations` is non-empty.
  - All violations found in scanned documents MUST be included in one run output.

## Entity: BaselineComplianceRecord

- Description: Snapshot proving repository baseline under `features/` satisfies heading policy.
- Fields:
  - `record_id` (string, required)
  - `policy_id` (string, required)
  - `run_id` (string, required)
  - `violations_count` (integer, required)
  - `compliant` (boolean, required)
- Validation rules:
  - `compliant` MUST be true only when `violations_count` equals `0`.
  - `policy_id` and `run_id` MUST reference existing policy/run records.

## Relationships

- `FeatureDocument` 1..* `ParsedHeadingRecord`
- `HeadingValidationPolicy` applies to * `ParsedHeadingRecord`
- `HeadingValidationRun` aggregates * `HeadingValidationViolation`
- `HeadingValidationViolation.document_id` references `FeatureDocument.document_id`
- `BaselineComplianceRecord` references one `HeadingValidationPolicy` and one `HeadingValidationRun`

## State Transitions

1. Discover `FeatureDocument` instances under `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/features/`.
2. Parse each document and materialize `ParsedHeadingRecord` objects.
3. Apply `HeadingValidationPolicy` to each parsed heading.
4. Emit `HeadingValidationViolation` entries for empty/missing/whitespace-only titles.
5. Finalize `HeadingValidationRun` with pass/fail status.
6. Produce `BaselineComplianceRecord` from run result for repository-level enforcement.
