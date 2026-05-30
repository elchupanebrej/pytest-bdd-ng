# Implementation Plan: Template-Driven Feature Documentation Ordering

**Branch**: `010-order-rst-docs` | **Date**: 2026-03-08 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/spec.md`
**Input**: Feature specification from `/specs/010-order-rst-docs/spec.md`

**Documentation Language Rule**: This plan and generated feature artifacts MUST be written in English.

## Summary

Refactor feature-documentation generation so
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/script/bdd_tree_to_rst.py`
stays a traversal/data-preparation coordinator while template-owned rendering
drives the RST output structure. Ordering will come from required numeric
prefixes in sibling file and directory names, those prefixes will be hidden from
reader-facing labels, generated page paths will keep the prefixes, and missing
or duplicate sibling prefixes will fail generation with deterministic errors.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: `pytest`, `Jinja2`, `pypandoc`, `pathlib2`, `tox`,
`pre-commit`
**Storage**: Filesystem-only artifacts under `features/`, `docs/features/`, and
temporary output directories
**Testing**: `pytest` doc/contract/generation suites, targeted `tox` slices,
strict Sphinx build, `pre-commit`
**Target Platform**: Cross-platform Python development and CI environments;
doc-output assertions are primarily exercised on Linux/Python 3.13-targeted
test slices
**Project Type**: Single Python library and CLI/plugin tooling repository
**Performance Goals**: Preserve one-pass tree traversal, deterministic output,
and contributor-feedback-loop execution time for feature-doc regeneration
**Constraints**: Keep script responsibilities limited to discovery, traversal,
path preparation, and validation; move presentation logic into templates as far
as practical; require unique numeric prefixes for every sibling in an ordered
scope; keep reader-facing labels prefix-free; preserve generated page paths and
manual index content outside the auto-generated block
**Scale/Scope**:
`src/pytest_bdd/script/bdd_tree_to_rst.py`,
`src/pytest_bdd/template/*.jinja2`,
`docs/features/features.rst`,
`tests/doc/test_doc.py`,
`tests/contract/`,
`tests/generation/test_template_packaging.py`,
and ordered source trees under `features/`

**Cross-Platform Validation Rule**: Non-native platform test environments MUST
use the Docker skill, except Windows targets which MAY use non-Docker execution
paths.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Gate Assessment

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | Spec and clarifications in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/spec.md` define the ordering model, template boundary, `pandoc` preference, and deterministic error policy. |
| II. Independent Story Increments | PASS | Stories remain independently testable across reader ordering, lightweight curation, and deterministic regeneration behavior. |
| III. Validation-First Changes | PASS | Plan includes targeted doc, contract, generation, strict-build, and pre-commit validation before implementation completion. |
| IV. Deterministic Compatibility and Contracts | PASS | Ordering policy, label/path policy, and validation error behavior will be captured in a versioned contract artifact under `contracts/`. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | PASS | No planning-time exception is needed; implementation will remain responsible for task-linked commits and passing pre-commit hooks. |
| Additional Constraint: English-only artifacts | PASS | All planning artifacts are written in English. |
| Additional Constraint: No normal-control `None` returns outside hooks | PASS | Planned validation behavior is deterministic error reporting, not `None`-based control flow. |

**Gate Result (Pre-Design)**: PASS

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── feature-doc-ordering.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/
├── src/pytest_bdd/
│   ├── script/
│   │   └── bdd_tree_to_rst.py
│   └── template/
│       ├── feature_include.rst.jinja2
│       └── features_section.rst.jinja2
├── docs/
│   └── features/
│       └── features.rst
├── features/
└── tests/
    ├── contract/
    ├── doc/
    └── generation/
```

**Structure Decision**: Keep the existing single-project Python layout. The
feature is confined to documentation generation and validation, so the plan
centers the work around the existing script/template pair, generated feature-doc
index, and focused doc/contract/generation tests instead of introducing new
packages.

## Phase 0: Outline & Research

Research tasks generated from dependencies and integration scope:

1. Confirm the minimal coordinator/render boundary for
   `bdd_tree_to_rst.py` versus template files.
2. Confirm the ordering model for sibling scopes, including display-label and
   generated-path behavior for numeric prefixes.
3. Confirm how existing `pypandoc` heading shifting should remain the preferred
   normalization path without expanding script-side presentation logic.
4. Confirm the contract and validation pattern that fits existing
   docs-generation governance in this repository.

**Phase 0 Output**:
`/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/research.md`

## Phase 1: Design & Contracts

1. Model ordered source topics, navigation scopes, template render payloads,
   generated pages, and deterministic ordering errors in `data-model.md`.
2. Define a design-time contract in
   `contracts/feature-doc-ordering.openapi.yaml` for template responsibilities,
   ordered-scope validation, generated-index rendering, and markdown heading
   normalization.
3. Define reproducible validation scenarios in `quickstart.md` covering ordered
   generation, deterministic validation errors, contract checks, and
   contributor workflow gates.
4. Update agent context via
   `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/.specify/scripts/bash/update-agent-context.sh codex`.

**Phase 1 Outputs**:

- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/data-model.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/contracts/feature-doc-ordering.openapi.yaml`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/010-order-rst-docs/quickstart.md`

## Post-Design Constitution Check

| Gate | Status | Evidence |
|------|--------|----------|
| I. Spec-Driven Delivery | PASS | `research.md`, `data-model.md`, `quickstart.md`, and `contracts/feature-doc-ordering.openapi.yaml` map directly to FR-001..FR-017 and SC-001..SC-010. |
| II. Independent Story Increments | PASS | Design keeps reader-ordering behavior, maintainer numbering workflow, and deterministic regeneration validation separable and testable. |
| III. Validation-First Changes | PASS | `quickstart.md` defines targeted commands for doc generation, contract validation, strict docs build, and pre-commit enforcement. |
| IV. Deterministic Compatibility and Contracts | PASS | The contract artifact defines deterministic ordering validation, template-owned presentation output, and prefix visibility rules. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | PASS | No constitution violation was introduced in planning artifacts; task-linked commits remain an implementation-phase requirement. |
| Additional Constraint: English-only artifacts | PASS | All generated planning artifacts remain in English. |
| Additional Constraint: No normal-control `None` returns outside hooks | PASS | Design records deterministic validation errors instead of `None`-return fallbacks. |

**Gate Result (Post-Design)**: PASS

## Complexity Tracking

No constitution violations detected. No exceptions required.
