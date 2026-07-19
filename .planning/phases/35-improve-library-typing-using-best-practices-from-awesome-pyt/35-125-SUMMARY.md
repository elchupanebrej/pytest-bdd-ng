---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 125
subsystem: typing
tags: [mypy, strict-typing, pylint, astroid, unit-tests]
requires: []
provides:
  - isolated strict-mypy evidence for the remaining pylint checker modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-125.md
  modified:
    - src/pytest_bdd_toolchain/pylint_plugin/checkers/module_api_rules.py
    - src/pytest_bdd_toolchain/pylint_plugin/checkers/quality_gates.py
key-decisions:
  - "Use typed protocol and cast boundaries for Astroid's runtime manager export and optional Pylint linter construction."
  - "Leave checker-convention strings as documentation/data rather than treating them as active suppressions."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five remaining pylint checker modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/pylint_plugin/checkers/module_api_rules.py src/pytest_bdd_toolchain/pylint_plugin/checkers/noqa_rules.py src/pytest_bdd_toolchain/pylint_plugin/checkers/plugin_patterns.py src/pytest_bdd_toolchain/pylint_plugin/checkers/quality_gates.py src/pytest_bdd_toolchain/pylint_plugin/checkers/responsibility_docs.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions without active suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-125.md"
        status: pass
    human_judgment: false
  - id: D3
    description: "Modified checker behavior remains covered by runtime tests."
    verification:
      - kind: other
        ref: "uv run pytest -q src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py"
        status: pass
    human_judgment: false
duration: 25 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 125: Strict-mypy evidence for remaining pylint checkers

**The five targeted pylint checker modules pass focused strict mypy and Ruff after replacing the remaining Astroid/linter type suppressions and a local exception suppression with typed boundaries.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced Astroid manager and optional-Pylint-linter suppressions with typed protocol/cast boundaries.
- Removed the local quality-gates exception suppression.
- Checker integration tests passed: 38 passed, 85 skipped.
- Focused Ruff passed and no active suppression comments remain.
- Committed isolated evidence as `f4196c0`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-125 is complete; Plan 35-126 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-125.md`.
- Evidence commit `f4196c0` is present in Git history.
