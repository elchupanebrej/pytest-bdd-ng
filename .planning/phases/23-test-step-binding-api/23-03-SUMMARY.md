---
phase: 22-test-step-binding-api
plan: 03
subsystem: reporter
tags: [step-binding, missing-step, ambiguous-step, mock-run]
requires:
  - phase: 22-test-step-binding-api
    provides: Plan 02 IDE binding service and launch metadata.
provides:
  - Matched step binding attachments.
  - Missing step diagnostics with scoped available definitions.
  - Ambiguous step diagnostics with scoped candidate definitions.
affects: [gherkin-message-reporter, pickle-runner, step-matcher]
tech-stack:
  added: []
  patterns: [scoped registry serialization, mock-run binding verification]
key-files:
  modified:
    - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py
    - src/pytest_bdd/plugin/pickle_runner/plugin.py
    - tests/cases/integration/messages/test_ide_step_bindings.py
requirements-completed: [P23-01, P22-07, P22-08]
duration: 1h
completed: 2026-06-06
---

# Phase 23 Plan 03 Summary

**Matcher-derived step binding attachments and mock-run diagnostics for missing and ambiguous steps**

## Accomplishments
- Emitted `application/vnd.pytest-bdd.step-binding+json` attachments for matched pickle steps.
- Added missing-step diagnostic payloads containing unmatched text and scoped available step definitions.
- Added ambiguous-step diagnostic payloads containing scoped candidate source references.
- Preserved mock-run no-execution behavior while still verifying binding correctness.

## Verification
- `rtk proxy uv run pytest tests/cases/integration/messages/test_ide_binding_contract.py tests/cases/integration/messages/test_ide_binding_diagnostics.py tests/cases/integration/messages/test_ide_step_bindings.py tests/cases/integration/feature/test_mock_run.py tests/cases/integration/feature/test_step_matching_ambiguous.py -q`

## Deviations from Plan
- Ambiguous duplicate step definitions remain a warning/pass path in existing runtime behavior; diagnostics are emitted without changing that existing outcome.

## Issues Encountered
- Runner lookup failure output changed from collection-time zero-binding usage text to runtime step lookup text for mock-run missing steps; regression assertion was updated.

## User Setup Required
None.
