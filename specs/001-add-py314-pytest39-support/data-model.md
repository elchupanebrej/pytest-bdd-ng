# Data Model: Compatibility Matrix Validation

## Entity: CompatibilityPolicy

- Description: Canonical support policy used by matrix generation and validation.
- Fields:
  - `min_python` (string, required, fixed value: `3.10`)
  - `max_python` (string, required, fixed value: `3.14`)
  - `min_pytest` (string, required, fixed value: `6.2.5`)
  - `compatibility_source` (enum: `pytest-matrix`, required)
  - `deprecated_pairs` (array of PairRef, required)
- Validation rules:
  - `min_python <= max_python`
  - Any pair below floor MUST be classified unsupported with EOL reason.

## Entity: CompatibilityMatrixEntry

- Description: One Python/pytest pair with compatibility and support-floor classification.
- Fields:
  - `python_version` (string, required)
  - `pytest_version` (string, required)
  - `is_compatible` (boolean, required)
  - `is_supported` (boolean, required)
  - `reason_code` (enum: `compatible`, `python_not_supported_by_pytest`,
    `pytest_unavailable`, `python_unavailable`, `eol_python`, `eol_pytest`,
    required)
  - `message` (string, required)
  - `tox_env_name` (string, optional; required when `is_supported=true`)
  - `platforms` (array enum: `lin`, `mac`, `win`, required)
- Validation rules:
  - Unique by (`python_version`, `pytest_version`).
  - `is_supported=true` requires `is_compatible=true` and floor compliance.
  - `is_supported=false` for EOL pairs requires `reason_code` in (`eol_python`, `eol_pytest`).

## Entity: ValidationJob

- Description: Executable job that validates one or more matrix entries.
- Fields:
  - `job_id` (string, required, unique)
  - `entries` (array of CompatibilityMatrixEntry references, required)
  - `platform` (enum: `lin`, `mac`, `win`, required)
  - `job_type` (enum: `supported-matrix`, `unsupported-negative`, required)
  - `status` (enum: `pending`, `running`, `passed`, `failed`, required)
- Validation rules:
  - `entries` cannot be empty.
  - `unsupported-negative` jobs MUST contain only `is_supported=false` entries.

## Entity: SupportDeclaration

- Description: Contributor-facing statement of supported and unsupported version ranges.
- Fields:
  - `document_path` (string, required, unique)
  - `supported_python_range` (string, required, expected: `3.10-3.14`)
  - `supported_pytest_floor` (string, required, expected: `>=6.2.5`)
  - `eol_exclusions` (array of strings, required)
  - `last_updated` (date, required)
- Validation rules:
  - Declaration MUST match `CompatibilityPolicy` values.

## Relationships

- `CompatibilityPolicy` governs `CompatibilityMatrixEntry` classification.
- `ValidationJob` references one or more `CompatibilityMatrixEntry` records.
- `SupportDeclaration` summarizes policy and exclusions defined by `CompatibilityPolicy`.
