---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 40
subsystem: typing
tags: [mypy, strict-typing, scenario-reporter, scenario-test-collector, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five reporter and collector modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use direct pytest implementation types at plugin boundaries."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-40.md
  modified:
    - src/pytest_bdd/plugin/pickle_runner/status_policy.py
    - src/pytest_bdd/plugin/scenario_reporter/entrypoint.py
    - src/pytest_bdd/plugin/scenario_reporter/plugin.py
    - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Use direct pytest types for reporter and collector plugin boundaries where the compatibility module is shadowed by the active refactor."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five reporter and collector modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/plugin/pickle_runner/status_policy.py src/pytest_bdd/plugin/scenario_reporter/entrypoint.py src/pytest_bdd/plugin/scenario_reporter/hook.py src/pytest_bdd/plugin/scenario_reporter/plugin.py src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-40.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 40: Strict-mypy evidence for reporters and collector

**The five reporter and collector modules pass focused strict mypy with direct pytest types and isolated evidence.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced compatibility-layer pytest imports with direct typed framework imports in status policy, scenario reporter, and scenario collector boundaries.
- Confirmed the scenario reporter hook remains clean without suppressions.
- Recorded one disposition for each affected source path without editing the shared typing inventory.
- Committed isolated evidence as `80e24eb`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-40 is complete; Plan 35-41 is next in Phase 35.
