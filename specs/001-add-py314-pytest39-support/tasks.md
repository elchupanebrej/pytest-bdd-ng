<!-- markdownlint-disable MD013 -->

# Tasks: Python and Pytest Compatibility Alignment

**Input**: Design documents from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/compatibility-matrix.openapi.yaml`, `quickstart.md`

## Phase 1: Setup

- [ ] T001 Update compatibility policy text in `docs/` to reference pytest compatibility matrix
- [ ] T002 Add/refresh Python 3.14 setup instructions using conda-forge in `specs/001-add-py314-pytest39-support/quickstart.md`

## Phase 2: Matrix and Tooling

- [ ] T003 Ensure compatibility matrix logic supports Python 3.14 and pytest-compatible pairs in `src/pytest_bdd/script/compatibility_matrix.py`
- [ ] T004 Ensure matrix includes all compatible Python/pytest pairs in `tox.ini`
- [ ] T005 Update CI matrix configuration for full compatible-pair coverage in `.github/workflows/`

## Phase 3: Validation

- [ ] T006 Run compatibility suite in `tests/compatibility/` and capture results
- [ ] T007 Run contract suite in `tests/contract/` and capture results
- [ ] T008 Validate representative tox environment for Python 3.14 in local/CI logs

## Phase 4: Documentation and Governance

- [ ] T009 Update contributor docs with supported-pairs policy and command examples in `docs/`
- [ ] T010 Run `pre-commit run --all-files` and fix all reported issues before commit

## Notes

- E2E conversion is tracked separately in `specs/002-e2e-test-conversion/`.
