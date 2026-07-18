---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 50
subsystem: typing
tags: [mypy, strict-typing, types, cucumber-formatter]
requires: []
provides:
  - isolated strict-mypy evidence for five type and formatter-support modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use canonical _pytest types when a compatibility re-export is not visible to mypy."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-50.md
  modified:
    - src/pytest_bdd/types/protocol.py
key-decisions:
  - "Use _pytest.stash.Stash directly for the structural protocol annotation because mypy cannot resolve the compatibility shim attribute."
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five type and formatter-support modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/types/failure_reasons.py src/pytest_bdd/types/json.py src/pytest_bdd/types/protocol.py src/pytest_bdd/types/warning.py src/pytest_bdd/util/cucumber_formatter_support/__init__.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-50.md"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 50: Strict-mypy evidence for type contracts

**The five-module type and formatter-support slice passes focused strict mypy with a canonical pytest stash type and isolated evidence.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced the unresolved compatibility-shim `Stash` annotation with the canonical `_pytest.stash.Stash` type.
- Confirmed the target slice contains no typing suppressions and committed isolated evidence as `93c2670`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-50 is complete; Plan 35-51 is next in Phase 35.
