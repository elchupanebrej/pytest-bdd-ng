---
phase: 22-test-step-binding-api
plan: 02
subsystem: reporter
tags: [cucumber-messages, launch-attachment, source-identity, cardinality]
requires:
  - phase: 22-test-step-binding-api
    provides: Plan 01 contract tests and hook taxonomy.
provides:
  - Launch attachments for each mock-run TestCase.
  - Stable source identity helper for scenarios and examples rows.
  - Source binding cardinality diagnostics.
affects: [gherkin-message-reporter, scenario-test-collector, feature-runtime-binding]
tech-stack:
  added: []
  patterns: [reporter service, JSON attachment payloads, sourceIdentity grouping]
key-files:
  created:
    - src/pytest_bdd/plugin/gherkin_message_reporter/ide_binding_runtime.py
  modified:
    - src/pytest_bdd/model/feature_binding.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime.py
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py
requirements-completed: [P22-02, P22-03, P22-04, P22-05, P22-06]
duration: 1h
completed: 2026-06-06
---

# Phase 22 Plan 02 Summary

**Reporter-owned launch handles and source cardinality diagnostics emitted as Cucumber Message attachments**

## Accomplishments
- Added `IdeBindingService` and wired it into the gherkin message reporter runtime.
- Emitted `application/vnd.pytest-bdd.launch+json` attachments with `testCaseId`, `pickleId`, raw `nodeid`, and stable `sourceIdentity`.
- Added source identity generation on `FeatureRuntimeBinding`, including examples row identity data.
- Added duplicate and unbound source diagnostics through `application/vnd.pytest-bdd.diagnostic+json`.

## Verification
- `rtk proxy uv run pytest tests/cases/integration/messages/test_ide_binding_contract.py tests/cases/integration/messages/test_ide_binding_diagnostics.py tests/cases/integration/messages/test_ide_step_bindings.py -q`
- Included in final 17-test integration gate.

## Deviations from Plan
- None beyond no-commit execution mode.

## Issues Encountered
- Cardinality diagnostics must wait until TestCase IDs exist, so emission happens at session finish with nodeid-to-TestCase mapping collected during setup.

## User Setup Required
None.
