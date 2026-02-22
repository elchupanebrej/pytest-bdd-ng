<!-- markdownlint-disable MD013 -->

# Implementation Plan: Python and Pytest Compatibility Alignment

**Branch**: `001-add-py314-pytest39-support` | **Date**: 2026-02-22 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/spec.md`
**Input**: Feature specification from `/specs/001-add-py314-pytest39-support/spec.md`

## Summary

Implement compatibility behavior that follows pytest's Python/pytest compatibility matrix (including Python 3.14), provide full compatible-pair validation coverage, and keep contributor workflow/documentation aligned with this policy.

## Technical Context

**Language/Version**: Python 3.9-3.14
**Primary Dependencies**: pytest, tox>=4.2, pre-commit, packaging
**Storage**: N/A (repository config, docs, matrix metadata)
**Testing**: tox matrix execution, pytest compatibility checks, contract checks, pre-commit hooks
**Target Platform**: Linux, macOS, Windows
**Project Type**: Python library
**Performance Goals**: Any selected compatible Python/pytest pair runnable in under 10 minutes from clean checkout (SC-002)
**Constraints**:
- Compatibility source of truth is pytest compatibility matrix (FR-001)
- No extra project-specific caps on compatible pairs (FR-002)
- Full compatible-pair matrix validation coverage (FR-003)
- Existing documented supported combinations must stay valid (FR-005)
- Pre-commit must pass before commits (constitution)
**Scale/Scope**: Matrix and workflow updates across `tox.ini`, CI, docs, compatibility scripts, and validation suites

## Constitution Check

- **I. Spec-Driven Delivery**: PASS
- **II. Independent Story Increments**: PASS
- **III. Validation-First Changes**: PASS
- **IV. Deterministic Compatibility and Contracts**: PASS
- **V. Task-Traceable Commits and Pre-Commit Enforcement**: PASS

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/
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
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/
├── src/pytest_bdd/
│   └── compatibility/
├── tests/
│   ├── compatibility/
│   └── contract/
├── docs/
├── tox.ini
├── pyproject.toml
└── .github/workflows/
```

**Structure Decision**: Keep compatibility implementation and validation in existing compatibility and contract locations. E2E conversion work is out of scope and tracked in `specs/002-e2e-test-conversion/`.
