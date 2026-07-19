---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 124
subsystem: typing
tags: [mypy, strict-typing, pylint, unit-tests, toml]
requires: []
provides:
  - isolated strict-mypy evidence for utility and pylint checker modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-124.md
  modified:
    - src/pytest_bdd_toolchain/case/unit/test_utils.py
    - src/pytest_bdd_toolchain/pylint_plugin/checkers/layer_rules.py
key-decisions:
  - "Replace the untyped tomli import suppression with a typed dynamic TOML boundary and explicit parsed-value casts."
  - "Remove local test lint suppressions by extracting the intentional raise and directly exercising the expected TypeError."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five utility and pylint checker modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/unit/test_utils.py src/pytest_bdd_toolchain/pylint_plugin/__init__.py src/pytest_bdd_toolchain/pylint_plugin/checkers/__init__.py src/pytest_bdd_toolchain/pylint_plugin/checkers/file_size_rules.py src/pytest_bdd_toolchain/pylint_plugin/checkers/layer_rules.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions without suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-124.md"
        status: pass
    human_judgment: false
  - id: D3
    description: "Modified utility and checker behavior remains covered by runtime tests."
    verification:
      - kind: other
        ref: "uv run pytest -q src/pytest_bdd_toolchain/case/unit/test_utils.py src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py"
        status: pass
    human_judgment: false
duration: 30 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 124: Strict-mypy evidence for utility and pylint checker modules

**The five targeted utility and pylint checker modules pass focused strict mypy and Ruff after replacing the untyped TOML import boundary and two local test suppressions.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced the untyped `tomli` import suppression with a typed dynamic TOML boundary and parsed-value casts.
- Removed two local test lint suppressions while preserving the intentional failure-path behavior.
- Focused runtime checks passed: 71 passed, 85 skipped.
- Focused Ruff passed and the precise suppression scan is empty.
- Committed isolated evidence as `b92dd7f`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-124 is complete; Plan 35-125 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-124.md`.
- Evidence commit `b92dd7f` is present in Git history.
