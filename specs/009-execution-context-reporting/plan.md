# Implementation Plan: Execution Context Reporting Consistency

**Branch**: `009-execution-context-reporting` | **Date**: 2026-03-07 | **Spec**: `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/spec.md`
**Input**: Feature specification from `/specs/009-execution-context-reporting/spec.md`

## Summary

Remove `src/pytest_bdd/model/gherkin_document/core.py::Feature` from the runtime and reporting boundary entirely. The design standardizes on `Run` and `ScenarioRun` as the only runtime context owners, stores feature-level registries and derived metadata in run-owned bindings, and uses canonical cucumber message objects (`GherkinDocument`, `Source`, `Pickle`) everywhere else.

This plan enforces four outcomes:
- `Feature` is not constructed or consumed in hooks, fixtures, collector callbacks, or reporting flows.
- Feature-level lookup and registry state moves into `Run` / `ScenarioRun`, with a single run-owned identifiable-object registry.
- Collection, parametrization, and reporting operate on canonical message-model objects plus run-owned bindings.
- The execution/message adapter remains the only protocol conversion boundary, and `pytest_bdd_id_generator` is resolved through `config.stash`.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: `pytest`, `pluggy`, `cucumber-messages`, `gherkin`, `jsonschema`
**Storage**: In-memory runtime state in `Run` / `ScenarioRun` plus `pytest.config.stash`; NDJSON and governance artifacts on disk
**Testing**: `pytest`, `tox`, `ruff`, `mypy`, `pre-commit`
**Target Platform**: Cross-platform Python test environments (Linux/macOS/Windows CI matrix)
**Project Type**: Python library and pytest plugin suite
**Performance Goals**: Preserve current collection and runtime execution characteristics; avoid extra wrapper construction and avoid synthetic reporting passes
**Constraints**: No reporter-side context mutation; no `Feature` adapters in hooks or fixtures; no compatibility shim for executable `scenario`; no synthetic event fabrication; deterministic ID and reference resolution through run-owned registries
**Scale/Scope**: Parser, scenario locator, feature locator, collector, pickle runner, reporters, code generation inputs, hook surface, fixture surface, and message/governance validation across `src/pytest_bdd/*` and matching tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Gate Assessment

| Principle | Gate | Status | Notes |
|-----------|------|--------|-------|
| I. Spec-Driven Delivery | Spec and clarifications are explicit and testable | PASS | `/specs/009-execution-context-reporting/spec.md` now explicitly forbids `Feature` in hooks, fixtures, and adapter APIs and requires migration of feature-level state into `Run` / `ScenarioRun`. |
| II. Independent Story Increments | Stories remain independently testable | PASS | US1 covers reporter/context ownership, US2 covers removal of `Feature` and run-owned feature state, US3 covers adapter/reference resolution. |
| III. Validation-First Changes | Validation strategy is defined before implementation | PASS | Quickstart scenarios cover collection boundary, runtime API surface, reporting, adapter, and full strict audit flow. |
| IV. Deterministic Compatibility and Contracts | Contracts are explicit and versionable | PASS | Contracts define runtime ownership, adapter semantics, and the public hook/fixture boundary without `Feature`. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | Enforceable during implementation | PASS | No design-time exception is required; implementation remains responsible for task-scoped commits and pre-commit compliance. |

### Post-Phase 1 Design Re-Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Delivery | PASS | `research.md`, `data-model.md`, `contracts/`, and `quickstart.md` map directly to FR-001..FR-026 and SC-001..SC-013. |
| II. Independent Story Increments | PASS | Design separates reporter read-only behavior, run-owned feature-state migration, and adapter/governance behavior into independently testable increments. |
| III. Validation-First Changes | PASS | `quickstart.md` provides targeted command groups for collection API, runtime API, reporting, and strict governance validation. |
| IV. Deterministic Compatibility and Contracts | PASS | Contracts cover execution-context ownership, adapter conversion, governance, and runtime hook/fixture surface without `Feature`. |
| V. Task-Traceable Commits and Pre-Commit Enforcement | PASS | No constitution violation introduced in planning artifacts; enforcement remains in implementation/tasks phase. |

## Project Structure

### Documentation (this feature)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/009-execution-context-reporting/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/src/pytest_bdd/
├── parser.py
├── scenario_locator.py
├── feature_locator.py
├── hook.py
├── model/
│   ├── scenario_run.py
│   ├── execution_message_adapter.py
│   ├── message_registry.py
│   └── gherkin_document/
├── plugin/
│   ├── pickle_runner/
│   ├── scenario_test_collector/
│   ├── gherkin_message_reporter/
│   ├── scenario_reporter/
│   └── code_generator/
└── scenario.py

/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/
├── compatibility/
├── hook/
├── feature/
├── messages/
├── messages_coverage/
├── model/
└── struct_bdd/
```

**Structure Decision**: Keep the single-project Python library layout. The refactor spans parser/locator/runtime/reporting boundaries, so the plan centers the work around `parser.py`, `scenario_locator.py`, `feature_locator.py`, `model/scenario_run.py`, `model/message_registry.py`, and plugin integration points rather than introducing a new package.

## Phase 0: Research Summary

Phase 0 resolved the design boundary with no remaining unresolved questions:
- `Feature` is removed from runtime/reporting and collection APIs.
- `Run` owns feature bindings and session-shared registries.
- `ScenarioRun` owns scenario-scoped pointers into the active feature binding.
- Collection emits `Source`, `GherkinDocument`, then `Pickle` read events in order.
- Hooks and fixtures expose only canonical message objects and `Run`.

## Phase 1: Design Summary

Phase 1 artifacts define:
- a run-owned `FeatureRuntimeBinding` model for feature metadata, source, and compiled pickles backed by a shared `Run.identifiable_registry`;
- explicit contracts for hook/fixture APIs without `Feature`;
- quickstart validation that covers API-surface removal, stash-backed ID services, and strict runtime coverage auditing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Implementation Validation

### Completed Validation Commands

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/hook/test_scenario_locator_pipeline.py \
  tests/hook/test_scenario_collection_read_hooks.py \
  tests/hook/test_run_scenario_runtime_unit.py \
  tests/hook/test_gherkin_reporter_context_lifecycle.py -q
```

Result:
- `20 passed in 0.16s`

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/feature/test_report.py \
  tests/messages/test_message_validation.py \
  tests/messages/test_execution_message_adapter.py \
  tests/generation/test_generate.py -q
```

Result:
- `14 passed in 1.85s`

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/e2e/test_e2e.py \
  tests/e2e/allure/test_e2e_allure.py -q
```

Result:
- `95 passed in 56.50s`

```bash
PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 \
conda run -n pytest-bdd-ng-py314 python -m pytest -q --tb=no
```

Result:
- `520 passed, 5 skipped in 100.03s`

```bash
git diff --name-only -- '*.py' | xargs conda run -n pytest-bdd-ng-py314 python -m ruff check
```

Result:
- `All checks passed!`

### Notes

- The final runtime/reporting boundary no longer relies on `src/pytest_bdd/model/gherkin_document/core.py::Feature`.
- `pytest_bdd_id_generator` is now stored and resolved through `pytest config.stash`; runtime and reporter code no longer read `config.pytest_bdd_id_generator`.
- E2E feature examples were updated to the final API surface: `gherkin_document` replaces the removed `feature` fixture, and `pytest_bdd_convert_tag_to_marks` now accepts `gherkin_document`.
