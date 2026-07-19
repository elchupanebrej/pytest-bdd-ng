---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 38
subsystem: typing
tags: [mypy, strict-typing, pickle-runner, pytest]
requires: []
provides:
  - isolated strict-mypy evidence for five pickle-runner modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use direct pytest types and a typed local decorator boundary when framework stubs are insufficient."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-38.md
  modified:
    - src/pytest_bdd/plugin/pickle_runner/entrypoint.py
    - src/pytest_bdd/plugin/pickle_runner/hook.py
key-decisions:
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
  - "Use direct pytest implementation types and a typed fixture decorator boundary instead of mypy suppressions."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five pickle-runner modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/plugin/pickle_runner/__init__.py src/pytest_bdd/plugin/pickle_runner/api_compatibility.py src/pytest_bdd/plugin/pickle_runner/const.py src/pytest_bdd/plugin/pickle_runner/entrypoint.py src/pytest_bdd/plugin/pickle_runner/hook.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-38.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 38: Strict-mypy evidence for pickle runner

**The five pickle-runner modules pass focused strict mypy with direct pytest types, an explicit fixture boundary, and isolated evidence.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced compatibility-layer imports with direct pytest framework types in the entrypoint and hook modules.
- Replaced the untyped session fixture decorator suppression with a local typed decorator boundary.
- Recorded one disposition for each affected source path without editing the shared typing inventory.
- Committed isolated evidence as `7874877`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-38 is complete; Plan 35-39 is next in Phase 35.
