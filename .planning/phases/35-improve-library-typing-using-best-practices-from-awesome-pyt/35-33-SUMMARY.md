---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 33
subsystem: typing
tags: [mypy, strict-typing, gherkin-message-reporter, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five live formatter and reporter modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use concrete generics and setattr at dynamic framework monkeypatch boundaries."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-33.md
  modified:
    - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py
key-decisions:
  - "Keep the plan-owned evidence isolated and do not absorb the checkout's broad pre-existing refactor into this plan commit."
  - "Replace the xdist assignment suppression with setattr and use concrete TemporaryDirectory and plugin-manager call types."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five-module live formatter source slice passes focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_process.py src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-33.md"
        status: pass
    human_judgment: false
duration: 45 min
completed: 2026-07-18
status: complete
---

# Phase 35 Plan 33: Strict-mypy evidence for live formatter modules

**The five live formatter and reporter modules pass focused strict mypy with explicit local boundaries and isolated evidence.**

## Accomplishments

- The exact five-file strict mypy command passed with exit status 0.
- Parameterized the live formatter temporary directory and supplied the required plugin-manager positional argument.
- Replaced the intentional xdist monkeypatch assignment suppression with `setattr`.
- Recorded one disposition for each affected source path without editing the shared typing inventory.
- Committed isolated evidence as `a2cff4e` and corrected its dispositions as `eb1f60e`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so normal evidence commits used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 2 environment/scope deviations; the focused Plan 35-33 verification passed.

## Next Phase Readiness

- Plan 35-33 is complete; Plan 35-34 is next in Phase 35.
