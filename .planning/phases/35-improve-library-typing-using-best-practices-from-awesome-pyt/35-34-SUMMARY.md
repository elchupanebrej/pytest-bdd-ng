---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 34
subsystem: typing
tags: [mypy, strict-typing, gherkin-message-reporter, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five reporter resource and runtime modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Keep framework Config and plugin-manager types explicit at the runtime contract boundary."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-34.md
  modified:
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_contract.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Use direct pytest framework types for the runtime contract's type-only boundary where the refactored compatibility namespace is ambiguous."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five-module reporter resource/runtime slice passes focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/plugin/gherkin_message_reporter/resources/__init__.py src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/__init__.py src/pytest_bdd/plugin/gherkin_message_reporter/resources/templates/formatters/__init__.py src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py src/pytest_bdd/plugin/gherkin_message_reporter/runtime_contract.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-34.md"
        status: pass
    human_judgment: false
duration: 30 min
completed: 2026-07-18
status: complete
---

# Phase 35 Plan 34: Strict-mypy evidence for resource/runtime modules

**The five reporter resource and runtime modules pass focused strict mypy with isolated evidence.**

## Accomplishments

- The exact five-file strict mypy command passed with exit status 0.
- Replaced the ambiguous compatibility-module type import in `runtime_contract.py` with direct pytest framework types at the type boundary.
- Recorded one disposition for each affected source path without editing the shared typing inventory.
- Committed isolated evidence as `8240750`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; the source fix remains in that existing working-tree refactor.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 2 environment/scope deviations; the focused Plan 35-34 verification passed.

## Next Phase Readiness

- Plan 35-34 is complete; Plan 35-35 is next in Phase 35.
