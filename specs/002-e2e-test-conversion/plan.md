<!-- markdownlint-disable MD013 -->

# Implementation Plan: E2E Test Conversion to Feature Documentation

**Branch**: `002-e2e-spec-remediation` | **Date**: 2026-02-22 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/002-e2e-test-conversion/spec.md`
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/002-e2e-test-conversion/spec.md`

## Summary

Convert user-facing pytest scenarios into executable feature documentation in `features/`, retain technical scenarios in `tests/` with canonical markers, and enforce per-conversion parity auditing with follow-up fixes only.

## Technical Context

**Language/Version**: Python 3.10-3.14 (feature-level validation scope)
**Primary Dependencies**: pytest, pytest-bdd, pre-commit, markdownlint
**Storage**: Repository files (`specs/002-e2e-test-conversion/*.md`, `features/`, `tests/`)
**Testing**: `python -m pytest tests/e2e -q`, targeted feature/compatibility checks, pre-commit hooks
**Target Platform**: Linux/macOS local development + CI matrix
**Project Type**: Python library + test/documentation conversion workflow
**Performance Goals**: Deterministic conversion checks complete within standard CI test window
**Constraints**:
- No history rewrite for conversion parity remediation
- Commit messages must include task IDs for completed work
- Canonical markers must be registered in `pytest.ini`
**Scale/Scope**: High/medium-priority conversion set tracked in `tasks.md` (T010-T038 + parity tasks)

**Cross-Platform Validation Rule**: Non-native platform test environments MUST use the Docker skill, except Windows targets which MAY use non-Docker execution paths.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Spec-driven delivery: PASS (spec, clarifications, and task mapping exist)
- Independent story increments: PASS (US1 conversion, US2 retention policy, US3 parity audit)
- Validation-first changes: PASS (pre-commit + pytest/e2e validations required)
- Deterministic compatibility/contracts: PASS (marker policy + conversion contract specified)
- Task-traceable commits/pre-commit enforcement: PASS (explicitly required by FR-007/FR-008 and constitution)
- Cross-platform Docker rule: PASS (captured in this plan and constitution)

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/002-e2e-test-conversion/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── e2e-conversion.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/
├── src/pytest_bdd/
├── features/
├── tests/
│   ├── e2e/
│   ├── feature/
│   ├── compatibility/
│   └── contract/
└── specs/002-e2e-test-conversion/
```

**Structure Decision**: Single Python project. This feature updates documentation/tests/contracts artifacts; no new runtime package layout is required.

## Phase 0: Research Output

Research decisions are captured in `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/002-e2e-test-conversion/research.md` with explicit rationale and alternatives for:
- conversion classification model,
- deferred conversion handling,
- parity auditing enforcement,
- retention-marker lifecycle in CI.

## Phase 1: Design Output

Design artifacts are captured in:
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/002-e2e-test-conversion/data-model.md`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/002-e2e-test-conversion/contracts/e2e-conversion.openapi.yaml`
- `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/002-e2e-test-conversion/quickstart.md`

## Post-Design Constitution Re-Check

- All gates remain PASS.
- No constitution violations require complexity exceptions.

## Complexity Tracking

No constitutional violations or justified exceptions.
