# Implementation Plan: Execution Context Reporting Consistency

**Branch**: `009-execution-context-reporting` | **Date**: 2026-03-05 | **Spec**: [/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/spec.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/spec.md)
**Input**: Feature specification from `/specs/009-execution-context-reporting/spec.md`

## Summary

Refactor reporting and runtime boundaries so `ExecutionContext` remains the only runtime state source, reporting uses a dedicated execution<->message adapter layer, and all reference reconstruction is deterministic through context-owned registries and IDs. Preserve external message/report behavior while enforcing strict read/write ownership, runtime-true coverage gating, and deterministic diagnostics (no synthetic fabrication).

## Technical Context

**Language/Version**: Python 3.10-3.14  
**Primary Dependencies**: `pytest>=6.2.5`, `pluggy`, `cucumber-messages`, `jsonschema`, existing `message_converter`  
**Storage**: In-memory runtime context state (`ExecutionContext`, `SessionExecutionContext`) + file artifacts (NDJSON, JSON governance reports under `artifacts/` and `specs/`)  
**Testing**: `pytest`, `tox>=4.2`, targeted hook/messages/messages_coverage suites, `pre-commit`, `ruff`, `mypy`  
**Target Platform**: Cross-platform Python package (Linux/macOS/Windows CI matrix; worker-aware behavior for xdist)  
**Project Type**: Python library + pytest plugin stack  
**Performance Goals**: No observable regression in reporting throughput for existing messages suites; retain deterministic emission/validation behavior and current CI runtime envelope  
**Constraints**: Reporter plugins are read-only over context; execution plugins are exclusive context writers; no synthetic event/state fabrication; deterministic ID/reference resolution via adapter+registry; `config.stash` as canonical shared context transport  
**Scale/Scope**: Runtime/reporting/model layers in `src/pytest_bdd` plus hook/reporting/governance tests in `tests/`; contract and governance artifacts under `specs/009-execution-context-reporting/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Gate Review

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Delivery | PASS | Spec + clarifications define runtime ownership split, adapter boundary, and deterministic diagnostics (`FR-001..FR-019`). |
| II. Independent Story Increments | PASS | US1 (context ownership), US2 (registry ownership), US3 (reference/adapter/governance) remain independently testable. |
| III. Validation-First Changes | PASS | Validation strategy defined via hook/message/messages_coverage and governance regression suites; quickstart scenarios are executable. |
| IV. Deterministic Compatibility and Contracts | PASS | Contract artifacts define runtime ownership, adapter conversion contract, and CI governance gate semantics. |
| V. Task-Traceable Commits and Pre-Commit | PASS | Implementation plan preserves requirement for task-linked commits and pre-commit pass before commit. |

### Post-Phase 1 Gate Review

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Delivery | PASS | `research.md`, `data-model.md`, `contracts/`, `quickstart.md` map directly to FR/SC requirements and clarifications. |
| II. Independent Story Increments | PASS | Data/contract decomposition supports phased implementation by story and independent validation paths. |
| III. Validation-First Changes | PASS | Quickstart includes independent US1/US2/US3 executable checks plus strict governance gate flow. |
| IV. Deterministic Compatibility and Contracts | PASS | Adapter and governance contracts explicitly define deterministic ID/reference behavior and failure modes. |
| V. Task-Traceable Commits and Pre-Commit | PASS | No exceptions required; no constitution violation or complexity override introduced. |

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── execution-context-boundary.md
│   ├── execution-message-adapter.md
│   └── governance-gate-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/
├── src/pytest_bdd/
│   ├── model/
│   │   ├── execution_context.py
│   │   ├── gherkin_document/
│   │   └── message_converter.py
│   └── plugin/
│       ├── scenario_runner/
│       ├── gherkin_message_reporter/
│       ├── scenario_reporter/
│       └── scenario_test_collector/
└── tests/
    ├── hook/
    ├── model/
    ├── messages/
    ├── messages_coverage/
    ├── generation/
    └── struct_bdd/
```

**Structure Decision**: Keep existing single-package plugin architecture. Introduce adapter layer and registry/index abstractions inside existing runtime/reporting modules without creating a new top-level project.

## Phase 0: Research Output

Research decisions are consolidated in:
- [/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/research.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/research.md)

Resolved topics include:
- Strict execution-plugin write vs reporter read ownership.
- Adapter-only message conversion boundary.
- Deterministic serialize/deserialize round-trip via context-owned registries.
- Worker-safe ID/reference keying and missing-context failure handling.
- Governance classification evidence rules for runtime-required vs non-runtime-required capabilities.

## Phase 1: Design & Contracts Output

Generated artifacts:
- Data model: [/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/data-model.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/data-model.md)
- Contracts:
  - [/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/contracts/execution-context-boundary.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/contracts/execution-context-boundary.md)
  - [/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/contracts/execution-message-adapter.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/contracts/execution-message-adapter.md)
  - [/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/contracts/governance-gate-contract.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/contracts/governance-gate-contract.md)
- Quickstart: [/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/quickstart.md](/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/quickstart.md)

## Validation Evidence (2026-03-05)

- `PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 conda run -n pytest-bdd-ng-py314 python -m pytest tests/hook/test_gherkin_reporter_context_lifecycle.py tests/messages/test_message_emission_points.py tests/model/gherkin_document/test_feature_context_lookup.py tests/hook/test_scenario_reference_resolution.py tests/messages/test_execution_message_adapter.py tests/messages/test_execution_message_adapter_roundtrip.py tests/messages/test_governance.py tests/messages_coverage/test_execution_context_governance_regression.py tests/messages_coverage/test_full_capability_governance.py -q`  
  Result: `45 passed`.
- `conda run -n pytest-bdd-ng-py314 python -m pytest tests/hook/test_execution_context_store_unit.py tests/hook/test_execution_context_transitions.py tests/feature/test_report_context_hierarchy.py tests/generation/test_generate_missing.py -q`  
  Result: `17 passed`.
- `conda run -n pytest-bdd-ng-py314 python -m pytest tests/struct_bdd/test_steps.py -q`  
  Result: optional parser dependency gap in local env (`pyhocon`, `hjson`, `json5` missing), no execution-context regressions observed.
- `conda run -n pytest-bdd-ng-py314 ruff check src/pytest_bdd/model/execution_message_adapter.py src/pytest_bdd/model/execution_context.py src/pytest_bdd/model/message_validation.py src/pytest_bdd/plugin/scenario_runner/context_access.py src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py tests/messages/test_execution_message_adapter.py tests/messages/test_execution_message_adapter_roundtrip.py`  
  Result: `All checks passed`.
- `conda run -n pytest-bdd-ng-py314 pre-commit run --files <changed-files>`  
  Result: command completed; hooks skipped by current matcher configuration for the provided file set.

## Complexity Tracking

No constitution violations or justified exceptions required.
