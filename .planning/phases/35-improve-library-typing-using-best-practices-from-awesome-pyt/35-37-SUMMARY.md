---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 37
subsystem: typing
tags: [mypy, strict-typing, gherkin-message-reporter, gherkin-terminal-reporter, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five xdist/terminal reporter modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use direct pytest types and explicit dynamic boundaries for xdist and terminal reporter APIs."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-37.md
  modified:
    - src/pytest_bdd/plugin/gherkin_message_reporter/xdist_worker.py
    - src/pytest_bdd/plugin/gherkin_terminal_reporter/entrypoint.py
    - src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Use getattr for dynamic xdist/parser framework methods where upstream stubs do not describe runtime attributes."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five xdist/terminal reporter modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/plugin/gherkin_message_reporter/xdist_worker.py src/pytest_bdd/plugin/gherkin_terminal_reporter/entrypoint.py src/pytest_bdd/plugin/gherkin_terminal_reporter/exception.py src/pytest_bdd/plugin/gherkin_terminal_reporter/hook.py src/pytest_bdd/plugin/gherkin_terminal_reporter/plugin.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-37.md"
        status: pass
    human_judgment: false
duration: 30 min
completed: 2026-07-18
status: complete
---

# Phase 35 Plan 37: Strict-mypy evidence for xdist/terminal reporters

**The five xdist and terminal reporter modules pass focused strict mypy with explicit boundaries and isolated evidence.**

## Accomplishments

- The exact five-file strict mypy command passed with exit status 0.
- Replaced compatibility imports with direct pytest framework types in the xdist and terminal reporter boundaries.
- Replaced dynamic xdist/parser and terminal superclass suppressions with explicit runtime boundaries and returns.
- Recorded one disposition for each affected source path without editing the shared typing inventory.
- Committed isolated evidence as `54b0f79`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 2 environment/scope deviations; the focused Plan 35-37 verification passed.

## Next Phase Readiness

- Plan 35-37 is complete; Plan 35-38 is next in Phase 35.
