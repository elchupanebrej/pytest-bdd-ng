# Implementation Plan: Maximize Messages Capability Coverage

**Branch**: `007-maximize-messages-coverage` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-maximize-messages-coverage/spec.md`

## Summary

The feature mandates 100% field-level coverage of the `cucumber-messages` capabilities within the `pytest-bdd-ng` plugin. The technical approach involves automatically extracting a `CapabilityInventory` from the upstream `Envelope.json` schema, validating runtime message payloads against that schema using `jsonschema` with a strict failure mode for any missing coverage, dynamically tracking populated fields across runs to surface white spots, and generating a formal governance checklist (`governance.json`) for missing components.

## Technical Context

**Language/Version**: Python 3.10-3.14
**Primary Dependencies**: `pytest`, `cucumber-messages`, `pluggy`, `jsonschema`
**Storage**: N/A (in-repo json artifacts only)
**Testing**: `pytest`, `tox>=4.2`
**Target Platform**: pytest execution environments
**Project Type**: Python library/plugin
**Performance Goals**: Opt-in dynamic tracing via CLI flag to avoid degrading default test run performance.
**Constraints**: Relative path resolution based on module location is prohibited. `importlib.resources` or `git` must be used for locating artifacts like the JSON schema.
**Scale/Scope**: ~130 line schema definition to map accurately to `Envelope` structures.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Spec-Driven Delivery**: Yes, spec is fully defined in `/specs/007-maximize-messages-coverage/spec.md`.
- [x] **Independent Story Increments**: Yes, User Stories 1 (Inventory), 2 (Consistent Coverage Validation), and 3 (Governance) are isolated.
- [x] **Validation-First Changes**: Yes, unit, integration, and release matrix tests are required.
- [x] **Deterministic Compatibility and Contracts**: Yes, contracts are versioned in `governance.json` and schema validation profile.

## Project Structure

### Documentation (this feature)

```text
specs/007-maximize-messages-coverage/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
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
├── message_extension.py
└── message_status_governance.py

src/pytest_bdd/plugin/
└── gherkin_message_reporter/
    └── plugin.py

src/pytest_bdd/script/
└── message_capability_governance.py

tests/messages/
├── test_coverage.py
├── test_governance.py
└── test_message_validation.py
```

**Structure Decision**: Code lives within the core `pytest-bdd` model and plugin boundaries, with coverage models housed in their own nested namespace (`pytest_bdd.model.coverage`) for cleanliness.
