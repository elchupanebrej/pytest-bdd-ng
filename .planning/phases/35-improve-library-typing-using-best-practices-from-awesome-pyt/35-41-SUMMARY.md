---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 41
subsystem: typing
tags: [mypy, strict-typing, scenario-test-collector, struct-bdd, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five collector and struct-BDD modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use direct pytest types and narrow dynamic collection payloads at local boundaries."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-41.md
  modified:
    - src/pytest_bdd/plugin/scenario_test_collector/helpers.py
    - src/pytest_bdd/plugin/scenario_test_collector/hook.py
    - src/pytest_bdd/plugin/scenario_test_collector/plugin.py
    - src/pytest_bdd/plugin/scenario_test_collector/unbound.py
    - src/pytest_bdd/plugin/struct_bdd/entrypoint.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Use direct pytest types and explicit casts or callable adapters instead of type suppressions for dynamic collection APIs."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five collector and struct-BDD modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/plugin/scenario_test_collector/helpers.py src/pytest_bdd/plugin/scenario_test_collector/hook.py src/pytest_bdd/plugin/scenario_test_collector/plugin.py src/pytest_bdd/plugin/scenario_test_collector/unbound.py src/pytest_bdd/plugin/struct_bdd/entrypoint.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-41.md"
        status: pass
    human_judgment: false
duration: 35 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 41: Strict-mypy evidence for collector and struct BDD

**The five collector and struct-BDD modules pass focused strict mypy with direct pytest types, explicit dynamic boundaries, and isolated evidence.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced compatibility-layer pytest imports with direct typed framework imports.
- Replaced collection and matcher type suppressions with casts, typed callable adapters, and dynamic marker lookup.
- Recorded one disposition for each affected source path without editing the shared typing inventory.
- Committed isolated evidence as `3d3bf59`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-41 is complete; Plan 35-42 is next in Phase 35.
