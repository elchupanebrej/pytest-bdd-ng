---
phase: 28-extract-pytest-bdd-toolchain
verified: 2026-07-02T13:23:29Z
status: passed
score: 6/6 acceptance criteria verified locally or accounted for
mode: forensic
runner: generic-agent workaround
typed_gsd_dispatch: unavailable
human_verification:
  - test: "Python 3.10-3.14 tox matrix"
    expected: "`tox -e py310,py311,py312,py313,py314` passes in CI or a local environment with all target interpreters."
    why_human: "The Phase 28 validation already classifies the tox matrix as manual/CI-only; this forensic verifier did not provision every interpreter locally."
---

# Phase 28 Verification - Extract pytest_bdd_toolchain

## Dispatch Note

This report was produced through the generic-agent workaround requested by the orchestrator because typed GSD verifier dispatch failed in the parent session with child model/service-tier resolution errors. This is not a typed `gsd-verifier`/GSD subagent run. In this session, `tool_search` found no `spawn_agent` tool, so verification was performed inline and labeled accordingly.

## Result

Passed for the active code/config/docs surfaces checked by the Phase 28 closure prompt.

No implementation files were modified. No commit was made. Historical planning/proposal records were not treated as active command surfaces.

## Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | `src/pytest_bdd_toolchain` exists | PASS | `test -d src/pytest_bdd_toolchain` passed. |
| 2 | `src/pytest_bdd_testing` does not exist | PASS | `test ! -e src/pytest_bdd_testing` passed. `importlib.util.find_spec("pytest_bdd_testing")` returned `None`. |
| 3 | Top-level `scripts/` does not exist | PASS | `test ! -e scripts` passed. |
| 4 | All 11 `pbt-*` entrypoints work | PASS | Every `pbt-* --help` command exited 0 from `.venv/bin`. |
| 5 | Active workflows/config/docs no longer call `scripts/` or `pytest_bdd_testing` | PASS | Focused active-surface scans over `.github`, `pyproject.toml`, `AGENTS.md`, `DEVELOPMENT.rst`, `CONTRIBUTING.md`, `docs/TESTING.md`, `docs/guides`, `docs/features`, `features`, and `src` found no active `pytest_bdd_testing` references and no active `python scripts/`, `uv run python scripts/`, `./scripts/`, or `bash scripts/` command invocations. |
| 6 | Current E2E/contract commands use `pytest_bdd_toolchain` paths | PASS | Active references in `.github/workflows/tests.yml`, `pyproject.toml`, `DEVELOPMENT.rst`, `docs/guides/06-ai-parallel-regression-testing.md`, `features/18 Development/11 Tests.feature.md`, and `src/pytest_bdd_toolchain/tool/run_messages_coverage_audit.py` use `src/pytest_bdd_toolchain/case/e2e` and/or `src/pytest_bdd_toolchain/case/contract`. |

## Commands Run

| Command | Result |
|---------|--------|
| `sed -n '1,260p' /home/elchupanebrej/.codex/skills/gsd-verify-work/SKILL.md` | Read required skill instructions. |
| `sed -n '1,1120p' "$HOME/.codex/gsd-core/workflows/verify-work.md"` | Read required workflow instructions. |
| `sed -n '1,260p' "$HOME/.codex/gsd-core/templates/UAT.md"` | Read required UAT template. |
| `sed -n '1,260p' .planning/v1.0-AUDIT-CLOSURE-COMMANDS.md` | Read closure sequence and Phase 28 subprompt. |
| `sed -n '1,260p' .planning/phases/28-extract-pytest-bdd-toolchain/28-01-SUMMARY.md` | Read Phase 28 implementation summary. |
| `sed -n '1,320p' .planning/phases/28-extract-pytest-bdd-toolchain/28-VALIDATION.md` | Read existing Phase 28 validation result. |
| `git status --short` | Confirmed known dirty state; left unrelated edits untouched. |
| `node "$HOME/.codex/gsd-core/bin/gsd-tools.cjs" query init.verify-work "28 --forensic"` | Phase found; implementation complete; prior canonical verification missing. |
| `find .planning/phases -name '*-UAT.md' -type f \| sort` | No Phase 28 UAT session exists. |
| `tool_search` for `spawn_agent multi_agent` | Found 0 tools; typed or generic subagent dispatch unavailable in this session. |
| `test -d src/pytest_bdd_toolchain && test ! -e src/pytest_bdd_testing && test ! -e scripts` | Passed. |
| `uv run python - <<'PY' ... all pbt-* --help ... PY` | All 11 entrypoints exited 0. |
| `uv run python -m pytest src/pytest_bdd_toolchain/case/contract/test_phase28_rename.py -q --tb=short --no-header` | Passed: `37 passed in 17.36s`. |
| `rg -n "pytest_bdd_testing" ...active surfaces... || true` | No active-surface hits outside the Phase 28 contract test when excluded from the scan. |
| `rg -n "(uv run python scripts/\|python scripts/\|\\./scripts/\|bash scripts/\| scripts/[A-Za-z0-9_.-]+\\.py\|src/pytest_bdd_testing)" ...active surfaces... || true` | No active command invocation hits. |
| `rg -n "src/pytest_bdd_toolchain/case/(e2e\|contract)\|pytest_bdd_toolchain/case/(e2e\|contract)" ...active surfaces... || true` | Confirmed current E2E/contract command and path references use toolchain paths. |
| `uv run python - <<'PY' ... importlib.util.find_spec ... PY` | `pytest_bdd_toolchain spec: True`; `pytest_bdd_testing spec: None`. |
| `node "$HOME/.codex/gsd-core/bin/gsd-tools.cjs" query audit-open --json` | Open items exist elsewhere; none are Phase 28 UAT/verification/context blockers after this report is written. |

## Entrypoint Evidence

All commands below exited 0 with `--help`:

- `pbt-analyze-responsibility-zones`
- `pbt-arch`
- `pbt-collect-arch-scores`
- `pbt-collect-test-scores`
- `pbt-fill-arch-scores`
- `pbt-fill-test-docstrings`
- `pbt-fix-incomplete-scores`
- `pbt-fix-long-lines`
- `pbt-inject-responsibility-docstrings`
- `pbt-inject-test-docstrings`
- `pbt-run-messages-coverage-audit`

## Reference Scan Notes

The broad scan surfaced historical/proposal references under `docs/superpowers/plans/*` and `docs/superpowers/specs/*`, plus intentional Phase 28 contract-test assertions about the old package being absent. These were not counted as active command surfaces because the closure prompt says to check active code/config/docs only, not historical planning records, and the existing Phase 28 validation explicitly preserved historical planning/spec references for traceability.

The only `AGENTS.md` `scripts/` hit is the project-structure label for the now-absent directory; it is not a command invocation. The stricter command-invocation scan found no active `scripts/` calls.

## Pre-Existing Failures / Manual-Only Items

- No new implementation failures were observed in this focused forensic pass.
- The existing Phase 28 validation reported `37 passed` for the focused contract suite and all 11 `pbt-* --help` checks passing; this run refreshed those checks with `37 passed in 17.36s`.
- The Phase 28 summary previously recorded local full-suite issues caused by missing optional/local dependencies (`allure_commons` and `hypothesis`) as pre-existing/unrelated. This forensic pass did not rerun the full suite.
- Python 3.10-3.14 tox matrix remains manual/CI-only.
- Historical document retention remains a manual judgment item, not an implementation blocker for the active rename surfaces.

## Final Status

Phase 28 forensic verification is passed. It is safe for the orchestrator to proceed to `$gsd-validate-phase 26`, subject to the manual/CI-only tox matrix remaining tracked as external verification debt.
