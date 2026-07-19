---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 64
subsystem: typing
tags: [mypy, strict-typing, contract-tests, allure]
requires: []
provides:
  - isolated strict-mypy evidence for five Allure formatter parity and contract tests
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-64.md
  modified: []
key-decisions:
  - "Record the clean five-module verification as isolated evidence without source changes."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five Allure formatter parity and contract tests pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_converter_contract.py src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_golden_parity.py src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_hypothesis.py src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_mapping_contract.py src/pytest_bdd_toolchain/case/contract/formatters/allure_formatter/test_native_parity_and_xdist.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-64.md"
        status: pass
    human_judgment: false
duration: 15 min
completed: 2026-07-18
status: complete
---
# Phase 35 Plan 64: Strict-mypy evidence for Allure parity tests

**The five Allure formatter parity and contract tests pass focused strict mypy without source changes or target-slice suppressions.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Confirmed the target slice contains no typing suppressions and committed isolated evidence as `1890000`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-64 is complete; Plan 35-65 is next in Phase 35.
