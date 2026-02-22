<!-- markdownlint-disable MD013 -->

# Implementation Plan: Python and Pytest Compatibility Alignment

**Branch**: `001-add-py314-pytest39-support` | **Date**: 2026-02-22 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/spec.md`
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/001-add-py314-pytest39-support/spec.md`

## Summary

Align project compatibility policy to support Python 3.10-3.14 and pytest>=6.2.5, remove EOL combinations (Python 3.9 and pytest<6.2.5) from supported matrix execution, and add explicit negative validation for deprecated combinations with fail-fast actionable diagnostics.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: pytest>=6.2.5, tox>=4.2, pre-commit, packaging
**Storage**: N/A (repository configuration and documentation only)
**Testing**: pytest suites in `tests/compatibility` and `tests/contract`, tox matrix envs, pre-commit hooks
**Target Platform**: Linux, macOS, Windows
**Project Type**: Python library and CLI tooling
**Performance Goals**: Any selected supported Python/pytest pair runnable via documented workflow in under 10 minutes from clean checkout (SC-002)
**Constraints**:
- Compatibility source of truth MUST follow pytest compatibility matrix with explicit EOL floors from spec (FR-001, FR-009, FR-010)
- CI/tox MUST exclude Python 3.9 and pytest<6.2.5 matrix entries (FR-011)
- Validation MUST include explicit negative checks for deprecated EOL combinations (FR-012)
- Pre-commit hooks MUST pass before commit (Constitution Principle V)
- Non-native platform validation MUST use Docker skill except Windows targets (Constitution Principle III)
**Scale/Scope**: Update matrix logic, tox/CI configuration, compatibility tests, contract tests, and contributor-facing documentation under repo root

**Cross-Platform Validation Rule**: Non-native platform test environments MUST use the Docker skill, except Windows targets which MAY use non-Docker execution paths.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-design gate status:
- **I. Spec-Driven Delivery**: PASS - Spec includes clarified support floor, deprecation scope, and measurable outcomes.
- **II. Independent Story Increments**: PASS - Plan maps changes to matrix behavior (P1), CI coverage (P2), and regression protection (P3).
- **III. Validation-First Changes**: PASS - Adds positive matrix validation plus explicit negative checks and pre-commit requirement.
- **IV. Deterministic Compatibility and Contracts**: PASS - Matrix policy and contract artifacts remain explicit and versioned.
- **V. Task-Traceable Commits and Pre-Commit Enforcement**: PASS - Implementation requires task-ID commit discipline and clean pre-commit.

Post-design gate status (after Phase 1 artifacts):
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
│   ├── compatibility/
│   └── script/
├── tests/
│   ├── compatibility/
│   └── contract/
├── docs/
├── tox.ini
├── pyproject.toml
└── .github/workflows/
```

**Structure Decision**: Keep compatibility logic in existing `src/pytest_bdd/script` and `src/pytest_bdd/compatibility`, enforce behavior through `tests/compatibility` and `tests/contract`, and keep policy docs under `docs/` and spec artifacts.

## Complexity Tracking

No constitution violations requiring justification.
