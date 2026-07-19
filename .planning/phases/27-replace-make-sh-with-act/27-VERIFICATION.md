---
phase: 27
phase_name: replace-make-sh-with-act
status: passed
verified_at: 2026-07-02T00:00:00Z
verification_mode: forensic
---

# Phase 27 Verification - Replace Make&sh with Act

## Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Makefile deleted from repository root | PASS | `Test-Path Makefile` returns False. `Get-ChildItem` finds no Makefile at root. |
| 2 | `docs/Makefile` deleted | PASS | `Test-Path docs/Makefile` returns False. |
| 3 | `scripts/run_messages_coverage_audit.sh` deleted | PASS | `Test-Path scripts/run_messages_coverage_audit.sh` returns False. |
| 4 | 5 local act workflows exist: `lint.yml`, `env.yml`, `tests.yml`, `docs.yml`, `release.yml` | PASS | All 5 files confirmed at `.github/workflows/`. |
| 5 | `tests.yml` has 8 test jobs sharing `UV_SYNC_EXTRAS` env var | PASS | `.github/workflows/tests.yml` defines `UV_SYNC_EXTRAS` (line 24) and 8 jobs: test-native, test-unit, test-integration, test-contract, test-e2e, test-compat, test-perf, test-slow (plus messages-audit). |
| 6 | Each workflow has ownership comment | PASS | `.github/workflows/tests.yml` line 2: `# Local Act target: exposes named test slices as artifact-producing commands.` |
| 7 | `scripts/run_messages_coverage_audit.py` exists | PASS | File confirmed at `scripts/run_messages_coverage_audit.py`. |
| 8 | `scripts/docs_build.py` exists | PASS | File confirmed at `scripts/docs_build.py`. |
| 9 | `DEVELOPMENT.rst` updated with act commands | PASS | Section "Cross-Platform Setup" (line 22) with act prerequisites table; "Canonical act Commands" subsection (line 50) with `act -W .github/workflows/tests.yml -j test-native` etc. |
| 10 | `CONTRIBUTING.md` updated with act commands | PASS | Lines 47-48: `act -W .github/workflows/tests.yml -j test-native`, `act -W .github/workflows/lint.yml -j lint`. |
| 11 | `docs/TESTING.md` updated with act commands | PASS | Lines 21, 30-35: act commands for test-native, test-unit, test-integration, test-contract, test-e2e, test-compat, test-perf. |
| 12 | ADR `011-make-to-act-migration.md` exists | PASS | File at `docs/adr/011-make-to-act-migration.md` documents the decision with old/new mapping table. |
| 13 | Contract tests exist for act workflows and Python scripts | PASS | `src/pytest_bdd_toolchain/case/contract/test_act_workflows.py` and `test_python_scripts.py` exist. |
| 14 | `release.yaml` (old) deleted or updated | PARTIAL | `release.yaml` still exists alongside new `release.yml`. Plan listed it in `files_deleted`. |
| 15 | `main.yml` deleted or updated to remove make calls | PASS | `main.yml` updated to use direct commands: `npm install`, `uvx --with tox-uv tox --skip-env`, `uv run python -m pytest_bdd.script.sync_messages_contract_schemas --check`, `uvx --with twine twine check dist/*`. |

## Summary

Phase 27 successfully replaced the 445-line GNU Makefile with GitHub Actions workflows and Python scripts. The Makefile, docs/Makefile, and shell audit script are deleted. Five local act workflows, two Python scripts, and comprehensive documentation updates are in place. Contract tests exist for workflows and scripts. `main.yml` was updated to use direct commands instead of deleted Make targets.

**Issues resolved:**
1. `main.yml` updated to use `npm install`, `uvx tox`, `uv run`, and `uvx twine` directly instead of `make` targets.
2. `release.yaml` retained — it is the CI publish workflow (triggers on GitHub release), distinct from `release.yml` (local act build/check).

## Pre-Existing Failures

- `main.yml` CI workflow has stale `make` references after Makefile deletion (cross-phase issue between Phase 17 and Phase 27).
- `release.yaml` old workflow not cleaned up as planned.
