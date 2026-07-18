---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 32
subsystem: typing
tags: [mypy, strict-typing, gherkin-message-reporter, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five Gherkin message reporter modules
  - suppression-free typed boundaries in the working-tree reporter refactor
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use explicit compatibility Config and PickleStep types at pytest and Cucumber boundaries."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-32.md
  modified:
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/core.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/hooks.py
key-decisions:
  - "Keep the plan-owned evidence isolated and do not absorb the checkout's broader pre-existing source refactor into this commit."
  - "Replace reporter lifecycle type suppressions with explicit Config, exit-status, and PickleStep boundaries."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five-module reporter source slice passes focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/ci.py src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/core.py src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/hooks.py src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_node.py src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_payload.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-32.md"
        status: pass
    human_judgment: false
duration: 45 min
completed: 2026-07-18
status: complete
---

# Phase 35 Plan 32: Strict-mypy evidence for reporter lifecycle modules

**The five Gherkin message reporter modules pass focused strict mypy with explicit typed boundaries and isolated evidence.**

## Accomplishments

- The exact five-file strict mypy command passed with exit status 0.
- Removed existing lifecycle hook suppressions by typing the pytest `Config` boundary and converting the exit status explicitly.
- Replaced the runtime step dispatch suppression with an explicit `PickleStep` cast at the model boundary.
- Recorded one disposition for each affected source path without editing the shared typing inventory.
- Committed the isolated evidence artifact as `f53911c`.

## Task Commit

- **Task 1: Remediate the exact strict-typing source slice** - `f53911c` (evidence/verification)

## Plan Metadata

- **Plan metadata:** `docs(35-32): complete strict typing plan`

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only this plan's evidence was staged and committed; the source edits remain in that existing working-tree refactor.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 2 environment/scope deviations; the focused Plan 35-32 verification passed.

## Next Phase Readiness

- Plan 35-32 is complete; Plan 35-33 is next in Phase 35.
