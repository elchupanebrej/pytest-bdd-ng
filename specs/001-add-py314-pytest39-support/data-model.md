# Data Model: Compatibility Alignment

## Entity: CompatibilityMatrixEntry

- Description: One Python/pytest pair with compatibility metadata and execution mapping.
- Fields:
  - `python_version` (string, required)
  - `pytest_version` (string, required)
  - `is_compatible` (boolean, required)
  - `compatibility_source` (enum: `pytest-matrix`, required)
  - `reason_code` (enum: `compatible`, `python_not_supported_by_pytest`, `pytest_unavailable`, `python_unavailable`, required)
  - `tox_env_name` (string, optional; required when `is_compatible=true`)
  - `platforms` (array of enum: `lin`, `mac`, `win`, required)

- Validation rules:
  - Uniqueness by (`python_version`, `pytest_version`).
  - `is_compatible=true` requires `reason_code=compatible`.
  - `tox_env_name` MUST be unique when present.

- State transitions:
  - `defined` -> `scheduled` -> `executed` -> (`passed` | `failed`).

## Entity: ValidationJob

- Description: Executable verification unit mapped from one or more matrix entries.
- Fields:
  - `job_id` (string, required, unique)
  - `entries` (array of CompatibilityMatrixEntry references, required)
  - `platform` (enum: `lin`, `mac`, `win`, required)
  - `status` (enum: `pending`, `running`, `passed`, `failed`, `skipped`, required)
  - `started_at` (datetime, optional)
  - `completed_at` (datetime, optional)

- Validation rules:
  - `entries` cannot be empty.
  - `status=skipped` allowed only when `reason_code` documents incompatibility or runtime unavailability.

## Entity: SupportDeclaration

- Description: Maintainer-facing support policy and verification guidance.
- Fields:
  - `policy_statement` (string, required)
  - `compatibility_reference` (string, required)
  - `verification_commands` (array of strings, required)
  - `last_updated` (date, required)

- Validation rules:
  - `policy_statement` must explicitly state pytest compatibility matrix as source of truth.
  - `verification_commands` must include at least one all-matrix command and one single-pair command.

## Entity: FeatureScopeFile

- Description: A tracked path included in current feature scope under FR-008.
- Fields:
  - `path` (string, required, unique)
  - `change_type` (enum: `modified`, `added`, `deleted`, required)
  - `included_in_feature` (boolean, required; must be true)

- Validation rules:
  - Every currently uncommitted repository path must map to one `FeatureScopeFile` record.

## Relationships

- One `SupportDeclaration` governs many `CompatibilityMatrixEntry` records.
- One `ValidationJob` consumes one or more compatible `CompatibilityMatrixEntry` records.
- One feature scope contains many `FeatureScopeFile` records and must include all uncommitted files.
