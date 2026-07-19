---
phase: 35-improve-library-typing-using-best-practices-from-awesome-pyt
plan: 126
subsystem: typing
tags: [mypy, strict-typing, pylint, toml, allure]
requires: []
provides:
  - isolated strict-mypy evidence for checker and Allure outline modules
affects: [phase-35-typing-inventory]
tech-stack:
  added: []
  patterns: []
key-files:
  created:
    - .planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-126.md
  modified:
    - src/pytest_bdd_toolchain/pylint_plugin/checkers/test_import_rules.py
key-decisions:
  - "Replace the untyped tomli fallback import suppression with a typed dynamic loader boundary and explicit parsed mapping casts."
  - "Leave checker-convention strings as documentation/data rather than treating them as active suppressions."
  - "Leave the checkout's broad pre-existing refactor outside this plan commit."
patterns-established:
  - "Focused typing plans record exact mypy commands and one disposition per source path."
requirements-completed: []
coverage:
  - id: D1
    description: "The five target modules pass focused strict mypy."
    verification:
      - kind: other
        ref: "uv run --all-extras mypy --config-file pyproject.toml src/pytest_bdd_toolchain/pylint_plugin/checkers/test_import_rules.py src/pytest_bdd_toolchain/pylint_plugin/checkers/test_responsibility_docs.py src/pytest_bdd_toolchain/pylint_plugin/checkers/typing_rules.py src/pytest_bdd_toolchain/resource/allure_reporting/outline/conftest.py src/pytest_bdd_toolchain/resource/allure_reporting/outline/test_sample.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plan-owned evidence records affected paths and typing dispositions without active suppressions."
    verification:
      - kind: other
        ref: ".planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-126.md"
        status: pass
    human_judgment: false
  - id: D3
    description: "The changed TOML/config boundary and outline resource path remain importable."
    verification:
      - kind: other
        ref: "uv run python -c 'from pytest_bdd_toolchain.pylint_plugin.checkers.test_import_rules import get_test_paths; from pathlib import Path; assert get_test_paths(); assert Path(\"src/pytest_bdd_toolchain/resource/allure_reporting/outline/test_sample.py\").exists()'"
        status: pass
    human_judgment: false
duration: 20 min
completed: 2026-07-19
status: complete
---
# Phase 35 Plan 126: Strict-mypy evidence for checker and outline modules

**The five targeted checker and Allure outline modules pass focused strict mypy and Ruff after replacing the untyped TOML fallback import with a typed dynamic loader boundary.**

## Accomplishments

- The exact five-module strict mypy check passed with exit status 0.
- Replaced the untyped TOML fallback import suppression with a typed dynamic loader and parsed mapping casts in `test_import_rules.py`.
- Focused Ruff passed; remaining suppression-pattern matches are documentation or diagnostic strings.
- The changed config boundary and Allure outline resource path probe passed.
- Committed isolated evidence as `bca7920`.

## Deviations from Plan

- The checkout contains a much larger pre-existing source and test refactor with repository-wide mypy and pylint failures. To avoid absorbing unrelated work, only the plan evidence was committed; source fixes remain in that existing working-tree refactor.
- The repository-relative verifier could not resolve `pyproject.toml` through the active `rtk uv` wrapper, so verification used the same command with an absolute config path; the focused check passed.
- The repository's installed pre-commit 2.17 could not parse the pinned `pre-commit-hooks v5` manifest, so the normal evidence commit used the temporary pre-commit 4.3.0 runtime established earlier without changing project dependencies.
- **Total deviations:** 3 environment/scope deviations; focused verification passed.

## Next Phase Readiness

- Plan 35-126 is complete; Plan 35-127 is next in Phase 35.

## Self-Check: PASSED

- Evidence file exists at `.planning/phases/35-improve-library-typing-using-best-practices-from-awesome-pyt/35-TYPING-EVIDENCE/35-126.md`.
- Evidence commit `bca7920` is present in Git history.
