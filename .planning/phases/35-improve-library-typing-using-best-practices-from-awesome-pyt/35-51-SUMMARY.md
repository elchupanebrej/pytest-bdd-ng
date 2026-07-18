---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 51
subsystem: typing
tags: [mypy, strict-typing, cucumber-formatters, data-table]
requires: []
provides:
  - isolated strict-mypy evidence for formatter-support and data-table utilities
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns:
    - "Use direct pytest types when compatibility re-export attributes are not visible to mypy."
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-51.md
  modified:
    - src/pytest_bdd/util/cucumber_formatter_support/base.py
    - src/pytest_bdd/util/cucumber_formatters.py
key-decisions:
  - "Use direct _pytest Config and Parser types for formatter integration annotations because mypy cannot resolve the compatibility shim attributes."
  - "Record evidence independently and leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five formatter-support and data-table modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd/util/cucumber_formatter_support/base.py src/pytest_bdd/util/cucumber_formatter_support/registry.py src/pytest_bdd/util/cucumber_formatter_support/standalone.py src/pytest_bdd/util/cucumber_formatters.py src/pytest_bdd/util/data_table.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-51.md"
        status: pass
    human_judgment: false
duration: 15 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 51: Strict-mypy evidence for formatter utilities

**The five formatter-support and data-table modules pass focused strict mypy with direct pytest parser types and isolated evidence.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced compatibility-shim `Config` and `Parser` annotations with direct pytest types in the formatter integration modules.
- Confirmed the target slice contains no typing suppressions and committed isolated evidence as `5848596`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-51 is complete; Plan 35-52 is next in Phase 35.
