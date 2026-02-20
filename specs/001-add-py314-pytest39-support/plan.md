<!-- markdownlint-disable MD013 -->

# Implementation Plan: Python and Pytest Compatibility Alignment

**Branch**: `001-add-py314-pytest39-support` | **Date**: 2026-02-20 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/spec.md`
**Input**: Feature specification from `/specs/001-add-py314-pytest39-support/spec.md`

## Summary

Align project compatibility behavior and validation so support is defined by pytest's Python/pytest compatibility matrix, including Python 3.14 and pytest 9.0, without adding project-level caps that conflict with pytest compatibility. Ensure tox matrix coverage exists for all compatible pairs, document execution paths, and include all currently uncommitted files as part of the feature deliverable scope.

## Technical Context

**Language/Version**: Python 3.9-3.14 (including Python 3.14 from conda-forge for local validation)
**Primary Dependencies**: pytest, tox>=4.2, pre-commit, mypy, ruff, packaging
**Storage**: N/A (repository configuration and documentation artifacts only)
**Testing**: tox matrix execution, pytest suite, mypy checks, ruff checks, pre-commit hooks
**Target Platform**: Linux, macOS, Windows (tox platform factors and CI mapping)
**Project Type**: Python library and CLI tooling
**Performance Goals**: Any selected compatible Python/pytest pair can be invoked via documented command path in under 10 minutes from clean checkout (SC-002)
**Constraints**:
- Follow pytest compatibility matrix as source of truth (FR-001)
- Do not impose additional project-specific caps on compatible pairs (FR-002)
- Provide matrix coverage for all compatible pairs (FR-003)
- Include all currently uncommitted files in feature scope (FR-008)
- Pre-commit hooks must pass before commit per constitution v1.1.0
**Scale/Scope**: Dozens of tox environments spanning Python runtimes, pytest versions, platforms, and validation modes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Spec-Driven Delivery**: PASS
  - Plan, research, data model, contracts, and quickstart are generated from `spec.md` requirements and clarifications.
- **II. Independent Story Increments**: PASS
  - Plan supports independent validation for P1 (pair execution), P2 (matrix completeness), and P3 (regression prevention).
- **III. Validation-First Changes**: PASS
  - tox matrix, compatibility checks, mypy/ruff, and pre-commit checks are part of the planned validation path.
- **IV. Deterministic Compatibility and Contracts**: PASS
  - Compatibility policy and contract artifacts are explicit and versioned in `specs/001-add-py314-pytest39-support/contracts/`.
- **V. Task-Traceable Commits and Pre-Commit Enforcement**: PASS
  - Tasks and commit hygiene are enforced by constitution; implementation phase must keep task-ID commits and pre-commit clean runs.

**Post-Design Re-check**: PASS
- Phase 0 and Phase 1 artifacts define deterministic compatibility rules, testable contracts, and explicit quickstart validation commands.
- No constitution violations or unresolved clarifications remain in planning artifacts.

## Project Structure

### Documentation (this feature)

```text
specs/001-add-py314-pytest39-support/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── compatibility-matrix.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
src/pytest_bdd/
├── script/
│   └── compatibility_matrix.py
└── ...

tests/
├── ...

docs/
├── ...

tox.ini
pyproject.toml
README.rst
.specify/
.codex/skills/
```

**Structure Decision**: Use existing single Python package repository layout and add/update compatibility behavior through tox configuration, script utilities, tests, docs, and supporting feature artifacts under `specs/001-add-py314-pytest39-support/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
