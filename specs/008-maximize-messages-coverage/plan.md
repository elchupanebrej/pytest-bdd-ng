# Implementation Plan: Maximize Messages Capability Coverage

**Branch**: `008-maximize-messages-coverage` | **Date**: 2026-03-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/Users/goloveshkokonstantin/Projects/pytest-bdd-ng/specs/008-maximize-messages-coverage/spec.md`

## Summary

Deliver complete, auditable capability governance for `messages` usage in `pytest-bdd-ng` by:
- maintaining a canonical capability inventory from approved upstream baseline artifacts,
- enforcing deterministic runtime outcome mapping and consistent status vocabulary,
- requiring explicit evidence for non-implemented/state-dependent coverage,
- publishing a governance checklist artifact for release sign-off,
- and running scheduled baseline drift comparisons that fail governance gates on unreviewed changes.

## Technical Context

**Language/Version**: Python 3.10-3.14  
**Primary Dependencies**: `pytest`, `pluggy`, `cucumber-messages`, `jsonschema`  
**Storage**: In-repo NDJSON + JSON artifacts (no persistent database)  
**Testing**: `pytest` (unit/integration/contract), `tox>=4.2`, `pre-commit`  
**Target Platform**: Pytest execution environments on Linux/macOS/Windows (Docker required for non-native execution targets per constitution)  
**Project Type**: Python library + pytest plugin + CLI governance tooling  
**Performance Goals**: Near-zero behavioral overhead when coverage tracing is disabled; strict validation and tracing only when explicitly enabled  
**Constraints**: No relative module-path schema resolution; deterministic mapping rules; hard-failure on invalid or missing required evidence; weekly baseline-diff governance signal; feature artifacts in English with ISO dates  
**Scale/Scope**: Full relevant `Envelope` capability surface, fixed release-readiness matrix outcomes, and release-scoped governance artifacts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate

- [x] **I. Spec-Driven Delivery**: Feature spec exists at `specs/008-maximize-messages-coverage/spec.md`; plan derives only from this spec.
- [x] **II. Independent Story Increments**: Inventory, runtime mapping/coverage, and governance sign-off remain independently testable story slices.
- [x] **III. Validation-First Changes**: Plan requires executable validation across unit/integration/contract layers and fail-fast diagnostics.
- [x] **IV. Deterministic Compatibility and Contracts**: Plan includes explicit contract artifacts and deterministic mapping/baseline policies.
- [x] **V. Task-Traceable Commits and Pre-Commit Enforcement**: Implementation phase will require task-linked commits and clean pre-commit execution; this is carried into tasks design.

**Pre-Research Gate Status**: PASS

### Post-Design Re-Check

- [x] `research.md` resolves all technical clarifications with explicit decisions and alternatives.
- [x] `data-model.md` defines entities, validation rules, and state transitions aligned to spec requirements.
- [x] `contracts/` defines versioned OpenAPI + JSON Schema governance interfaces.
- [x] `quickstart.md` defines executable validation flow from inventory to governance and baseline drift checks.
- [x] No constitution violations require complexity exemptions.

**Post-Design Gate Status**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/008-maximize-messages-coverage/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── messages-capability-governance.openapi.yaml
│   └── governance-report.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
src/pytest_bdd/model/
├── coverage/
│   ├── __init__.py
│   ├── inventory.py
│   └── tracker.py
├── message_validation.py
├── message_outcome_mapping.py
├── message_status_governance.py
├── message_governance_checklist.py
└── message_baseline_diff.py

src/pytest_bdd/plugin/gherkin_message_reporter/
├── entrypoint.py
├── hook.py
└── plugin.py

src/pytest_bdd/script/
└── message_capability_governance.py

tests/messages/
├── test_message_capability_inventory.py
├── test_message_validation.py
├── test_message_outcome_mapping.py
├── test_message_governance_checklist.py
├── test_message_baseline_diff.py
├── test_coverage.py
└── test_governance.py

tests/contract/
└── test_messages_capability_coverage_contract.py
```

**Structure Decision**: Extend the existing `pytest_bdd` message model/plugin/script boundaries. Keep contract validation in `tests/contract`, behavior validation in `tests/messages`, and feature governance documents under `specs/008-maximize-messages-coverage`.

## Complexity Tracking

No constitution violations detected; no complexity exemptions are required.
