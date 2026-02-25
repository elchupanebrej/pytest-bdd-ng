<!-- markdownlint-disable MD013 -->

# Implementation Plan: Migrate Documentation Generation to Jinja2

**Branch**: `004-migrate-jinja2-docs` | **Date**: 2026-02-25 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/004-migrate-jinja2-docs/spec.md`
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/004-migrate-jinja2-docs/spec.md`

**Documentation Language Rule**: This plan and generated feature artifacts MUST be written in English.

## Summary

Migrate documentation and code generation templates from Mako to Jinja2 while preserving semantic output parity, preserving manual documentation content during regeneration, enforcing stale-doc detection in pre-commit, and keeping `docs/features/features.rst` limited to feature-file-driven generated documentation context.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: pytest>=6.2.5, Jinja2, pluggy hooks, pre-commit, tox>=4.2, ruff, packaging
**Storage**: N/A (in-repo files only)
**Testing**: pytest (unit/contract/doc/generation), tox matrix, pre-commit hooks
**Target Platform**: macOS/Linux local development; compatibility validation includes Windows-target tox environment behavior
**Project Type**: Python library and CLI tooling
**Performance Goals**: Deterministic generation output and no additional contributor workflow steps; regeneration and verification complete within normal pre-commit execution window
**Constraints**: Preserve semantic output parity; preserve manual docs blocks; enforce pre-commit stale-doc failure; keep `docs/features/features.rst` free of internal implementation/change-history details
**Scale/Scope**: Migration of generator templates and documentation-generation pipeline under `src/pytest_bdd/`, synchronized docs under `docs/features/`, and validation coverage under `tests/`

**Cross-Platform Validation Rule**: Non-native platform test environments MUST use the Docker skill, except Windows targets which MAY use non-Docker execution paths.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate Review

- **I. Spec-Driven Delivery**: PASS
  - Active spec exists at `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/004-migrate-jinja2-docs/spec.md` with accepted clarifications.
- **II. Independent Story Increments**: PASS
  - Stories are separated into parity, manual-doc preservation, and contributor workflow stability.
- **III. Validation-First Changes**: PASS
  - Plan includes contract, generation, docs, and pre-commit validation artifacts.
- **IV. Deterministic Compatibility and Contracts**: PASS
  - Compatibility scope and contract artifact are explicit and versioned in feature docs.
- **V. Task-Traceable Commits and Pre-Commit Enforcement**: PASS (planning scope)
  - Plan preserves requirement for task-linked commits and mandatory pre-commit in implementation phase.

**Gate Result (Pre-Design)**: PASS

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/004-migrate-jinja2-docs/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── jinja2-doc-generation.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/
├── src/pytest_bdd/
│   ├── plugin/code_generator/
│   ├── script/
│   └── template/
├── docs/
│   ├── features/
│   └── internal/
└── tests/
    ├── contract/
    ├── doc/
    └── generation/
```

**Structure Decision**: Use the existing single-project Python library layout and limit changes to generator, templates, docs, and focused validation suites.

## Phase 0: Research Plan

- Confirm Mako->Jinja2 migration strategy that preserves semantic output parity.
- Define marker-based regeneration strategy to preserve manual documentation content.
- Define pre-commit stale-doc enforcement approach.
- Define packaging rules for new `.jinja2` assets and legacy `.mak` removal.
- Define documentation boundary policy: `docs/features/features.rst` contains feature-file-generated navigation/context only; internal implementation notes moved to separate documentation.

**Phase 0 Output**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/004-migrate-jinja2-docs/research.md`

## Phase 1: Design & Contracts Plan

- Model template assets, render contexts, doc blocks, parity validation cases, sync checks, packaging manifest, and documentation boundary rules.
- Define contract surfaces for rendering, synchronization validation, parity validation, packaging checks, and docs-boundary validation.
- Provide reproducible quickstart validation commands for local execution.

**Phase 1 Outputs**:
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/004-migrate-jinja2-docs/data-model.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/004-migrate-jinja2-docs/contracts/jinja2-doc-generation.openapi.yaml`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/004-migrate-jinja2-docs/quickstart.md`

## Post-Design Constitution Check

- **I. Spec-Driven Delivery**: PASS (design artifacts trace to FR-001..FR-012).
- **II. Independent Story Increments**: PASS (artifact structure supports per-story validation).
- **III. Validation-First Changes**: PASS (quickstart and contract artifacts define executable checks).
- **IV. Deterministic Compatibility and Contracts**: PASS (semantic parity and explicit OpenAPI design-time contract maintained).
- **V. Task-Traceable Commits and Pre-Commit Enforcement**: PASS (design includes pre-commit enforcement requirement and task-traceability expectation).

**Gate Result (Post-Design)**: PASS

## Complexity Tracking

No constitution violations requiring justification.
