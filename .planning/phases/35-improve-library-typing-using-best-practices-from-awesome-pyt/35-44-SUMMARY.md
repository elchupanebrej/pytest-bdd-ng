---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 44
subsystem: typing
tags: [mypy, strict-typing, scenario-locator, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five scenario-locator and script modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use direct pytest types at scenario-locator configuration boundaries."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-44.md
  modified:
    - src/pytest_bdd/scenario_locator/base.py
    - src/pytest_bdd/scenario_locator/file_locator.py
    - src/pytest_bdd/scenario_locator/url_locator.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Use direct pytest Config types while retaining locator runtime behavior."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five scenario-locator and script modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/scenario_locator/__init__.py src/pytest_bdd/scenario_locator/base.py src/pytest_bdd/scenario_locator/file_locator.py src/pytest_bdd/scenario_locator/url_locator.py src/pytest_bdd/script/__init__.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-44.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 44: Strict-mypy evidence for scenario locators

**The five scenario-locator and script modules pass focused strict mypy with direct pytest configuration types and isolated evidence.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced compatibility-layer `Config` imports in the locator modules with the direct pytest type.
- Removed duplicate compatibility-only typing imports from the locator modules.
- Recorded one disposition for each affected source path without editing the shared typing inventory.
- Committed isolated evidence as `63793ee`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-44 is complete; Plan 35-45 is next in Phase 35.
