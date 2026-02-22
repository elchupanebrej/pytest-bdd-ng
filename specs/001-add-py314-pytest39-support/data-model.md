# Data Model: Compatibility Matrix Validation

## Entity: CompatibilityMatrixEntry

- Description: One Python/pytest pair with compatibility metadata and runnable mapping.
- Fields:
  - `python_version` (string, required)
  - `pytest_version` (string, required)
  - `is_compatible` (boolean, required)
  - `compatibility_source` (enum: `pytest-matrix`, required)
  - `reason_code` (enum: `compatible`, `python_not_supported_by_pytest`, `pytest_unavailable`, `python_unavailable`, required)
  - `tox_env_name` (string, optional; required when `is_compatible=true`)
  - `platforms` (array enum: `lin`, `mac`, `win`, required)

- Validation rules:
  - Unique by (`python_version`, `pytest_version`).
  - Compatible entries require `reason_code=compatible`.
  - `tox_env_name` is unique when present.

## Entity: ValidationJob

- Description: One executable validation unit for matrix coverage.
- Fields:
  - `job_id` (string, required, unique)
  - `entries` (array of CompatibilityMatrixEntry references, required)
  - `platform` (enum: `lin`, `mac`, `win`, required)
  - `status` (enum: `pending`, `running`, `passed`, `failed`, `skipped`, required)

- Validation rules:
  - `entries` cannot be empty.
  - `skipped` requires explicit compatibility or runtime unavailability reason.

## Entity: SupportDeclaration

- Description: Contributor-facing policy that describes supported compatibility pairs.
- Fields:
  - `document_path` (string, required, unique)
  - `source_of_truth` (enum: `pytest-matrix`, required)
  - `last_updated` (date, required)

- Validation rules:
  - Declaration must match the matrix logic used in validation tooling.

## Relationships

- `ValidationJob` references one or more `CompatibilityMatrixEntry` records.
- `SupportDeclaration` summarizes coverage represented by `CompatibilityMatrixEntry` records.
