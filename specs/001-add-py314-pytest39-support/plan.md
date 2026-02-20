# Implementation Plan: Python and Pytest Compatibility Alignment

**Branch**: `001-add-py314-pytest39-support` | **Date**: 2026-02-20 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/spec.md`
**Input**: Feature specification from `/specs/001-add-py314-pytest39-support/spec.md`

## Summary

Align project support policy with pytest-to-python compatibility rules, remove library-specific caps, and ensure automated validation covers all compatible Python/pytest pairs. The implementation will centralize compatibility generation from authoritative version metadata, produce deterministic tox environment expansion, and keep support documentation synchronized.

## Technical Context

**Language/Version**: Python 3.9+ runtime for tooling; validation must include all interpreter versions available in CI that satisfy pytest compatibility rules  
**Primary Dependencies**: tox 4.x, pytest (multiple versions), packaging, Python standard library (`importlib.metadata`, `json`, `pathlib`)  
**Storage**: Files in repository (`tox.ini`, `pyproject.toml`, docs, generated compatibility manifest under specs/docs)  
**Testing**: pytest + tox matrix validation + integration checks that verify matrix expansion output  
**Target Platform**: Cross-platform CI targets already used by project (linux/mac/win), local developer machines with Conda or system Python
**Project Type**: Single Python package/library with test matrix orchestration  
**Performance Goals**: Generate compatibility matrix in under 30 seconds and start selected tox jobs within 10 minutes from clean checkout  
**Constraints**: No additional project-level version cap beyond pytest compatibility constraints; maintain existing supported combinations; deterministic matrix generation and failure messaging  
**Scale/Scope**: Full Cartesian coverage of compatible Python/pytest pairs for supported window; expected to produce dozens to low hundreds of tox env combinations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.specify/memory/constitution.md` currently contains placeholder tokens and no enforceable principles. No concrete constitutional gates can be evaluated.

Gate result (pre-research): PASS (no enforceable rules present).

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
├── tests/
├── tox.ini
├── pyproject.toml
└── docs/
```

**Structure Decision**: Use the existing single-project Python package structure and update compatibility policy, matrix generation, and tests in-place.

## Phase 0: Research Output

- Documented compatibility source-of-truth selection and matrix expansion strategy in `research.md`.
- Resolved uncertainty around "all compatible pairs" by defining generation from pytest compatibility metadata intersected with available interpreters.

## Phase 1: Design & Contracts Output

- Defined compatibility entities, validation rules, and transitions in `data-model.md`.
- Defined REST contract for matrix query and compatibility validation in `contracts/compatibility-matrix.openapi.yaml`.
- Added execution workflow and verification commands in `quickstart.md`.

## Post-Design Constitution Check

Gate result (post-design): PASS (constitution remains template-only with no enforceable constraints).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
