---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 36
subsystem: typing
tags: [mypy, strict-typing, gherkin-message-reporter, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five step catalog and transport modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use direct pytest types and explicit sentinel/document casts at dynamic runtime boundaries."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-36.md
  modified:
    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/core.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/static_helpers.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Model missing previous steps with the existing NoPreviousStep sentinel instead of suppressing the assignment."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five-module step catalog/transport slice passes focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/__init__.py src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/core.py src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/static_helpers.py src/pytest_bdd/plugin/gherkin_message_reporter/stream_relay.py src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-36.md"
        status: pass
    human_judgment: false
duration: 30 min
completed: 2026-07-18
status: complete
---

# Phase 35 Plan 36: Strict-mypy evidence for step catalog/transport modules

**The five step catalog and transport modules pass focused strict mypy with explicit boundaries and isolated evidence.**

## Accomplishments

- The exact five-file strict mypy command passed with exit status 0.
- Replaced compatibility imports with direct pytest framework types across the step catalog and transport boundaries.
- Replaced the previous-step assignment suppression with the existing `NoPreviousStep` sentinel and narrowed the document boundary explicitly.
- Recorded one disposition for each affected source path without editing the shared typing inventory.
- Committed isolated evidence as `33748ee`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 2 environment/scope deviations; the focused Plan 35-36 verification passed.

## Next Phase Readiness

- Plan 35-36 is complete; Plan 35-37 is next in Phase 35.
