# Data Model: Compatibility Alignment

## Entity: CompatibilityMatrixEntry

- Description: One Python/pytest pair with derived compatibility and execution metadata.
- Fields:
  - `python_version` (string, required)
  - `pytest_version` (string, required)
  - `is_compatible` (boolean, required)
  - `compatibility_source` (enum: `pytest-metadata`, required)
  - `reason_code` (enum: `compatible`, `python_not_supported_by_pytest`, `pytest_unavailable`, `python_unavailable`, required)
  - `execution_targets` (array of enum: `lin`, `mac`, `win`)
  - `tox_env_name` (string, optional; required when `is_compatible=true`)

- Validation rules:
  - Pair uniqueness by (`python_version`, `pytest_version`).
  - `tox_env_name` must be unique if present.
  - `is_compatible=true` requires `reason_code=compatible`.

- State transitions:
  - `discovered` -> `filtered` -> `scheduled` -> `executed` -> (`passed` | `failed`).

## Entity: ValidationJob

- Description: Executable tox job mapped from one or more compatible matrix entries.
- Fields:
  - `job_id` (string, required, unique)
  - `entries` (array of CompatibilityMatrixEntry references, required)
  - `platform` (enum: `lin`, `mac`, `win`, required)
  - `status` (enum: `pending`, `running`, `passed`, `failed`, `skipped`, required)
  - `started_at` (datetime, optional)
  - `completed_at` (datetime, optional)

- Validation rules:
  - `entries` cannot be empty.
  - `status=skipped` allowed only with explicit non-compatibility reason.

## Entity: SupportDeclaration

- Description: Contributor-facing statement of support policy and commands.
- Fields:
  - `policy_statement` (string, required)
  - `compatibility_reference` (string, required)
  - `verification_commands` (array of strings, required)
  - `last_updated` (date, required)

- Relationships:
  - One SupportDeclaration governs many CompatibilityMatrixEntry records.
  - ValidationJob consumes one or many compatible CompatibilityMatrixEntry records.
