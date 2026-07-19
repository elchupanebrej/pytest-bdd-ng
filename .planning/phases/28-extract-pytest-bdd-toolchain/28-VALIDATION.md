---
phase: 28
slug: extract-pytest-bdd-toolchain
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-26
validated: 2026-07-02
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `uv run python -m pytest src/pytest_bdd_toolchain/case/unit -q --tb=short --no-header` |
| **Full suite command** | `uvx --with tox-uv tox` |
| **Estimated runtime** | ~120 seconds (unit), ~600 seconds (full tox) |

---

## Sampling Rate

- **After every task commit:** Run `uv run python -m pytest src/pytest_bdd_toolchain/case/unit -q --tb=short --no-header`
- **After every plan wave:** Run `uvx --with tox-uv tox`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 28-01-T1 | 01 | 1 | — (inventory) | — | N/A | manual | `test -d src/pytest_bdd_toolchain && test ! -d src/pytest_bdd_testing && test ! -d scripts` | ✅ | ✅ green |
| 28-01-T2 | 01 | 1 | REQ-R2 | — | Scripts in package | contract | `test -d src/pytest_bdd_toolchain/tool` | ✅ | ✅ green |
| 28-01-T3 | 01 | 1 | REQ-R1 | — | Clean break | contract | `import pytest_bdd_toolchain` / `import pytest_bdd_testing` fails | ✅ | ✅ green |
| 28-01-T4 | 01 | 1 | REQ-R2, R6 | — | Entrypoints registered | contract | `pbt-* --help` exit 0 | ✅ | ✅ green |
| 28-01-T5 | 01 | 1 | REQ-R3 | — | Workflows updated | contract | `rg -n pytest_bdd_testing .github/workflows` | ✅ | ✅ green |
| 28-01-T6 | 01 | 1 | REQ-R3 | — | Docs updated | contract | `rg -n pytest_bdd_testing AGENTS.md ...` | ✅ | ✅ green |
| 28-01-T7 | 01 | 1 | — (fix-forward) | — | N/A | manual | No implementation fix-forward required by 2026-07-02 validation; dirty worktree items are unrelated planning/artifact changes | ✅ | ✅ green |
| 28-01-T8 | 01 | 1 | REQ-R1-R6 | — | Full validation | integration | `pytest src/pytest_bdd_toolchain/case` + `ruff` + `mypy` + `pylint` + `uv build` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `src/pytest_bdd_toolchain/case/contract/test_python_scripts.py` — script structure contracts (R2)
- [x] `src/pytest_bdd_toolchain/case/contract/test_phase28_rename.py` — NEW: package rename validation (R1, R2, R6)

*Existing infrastructure covers most phase requirements; new test file fills remaining gaps.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Python 3.10-3.14 matrix | REQ-R4 | Requires tox-uv + multiple interpreters not available locally | Run `tox -e py310,py311,py312,py313,py314` in CI |
| Historical doc retention | D-10 | Requires judgment about what counts as "historical" | Review `.planning/phases/*` manually |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-26

---

## Validation Audit 2026-07-02

**Runner:** generic-worker workaround. Typed `gsd-nyquist-auditor` dispatch was not available in this Codex session (`tool_search` found no `spawn_agent` tool), so this audit is explicitly not a typed GSD Nyquist auditor run.

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 2 pending rows refreshed |
| Escalated | 0 |

### Current Evidence

- `src/pytest_bdd_toolchain` exists.
- `src/pytest_bdd_testing` does not exist.
- Top-level `scripts/` does not exist.
- All 11 `pbt-* --help` entrypoints exit 0:
  `pbt-analyze-responsibility-zones`,
  `pbt-arch`,
  `pbt-collect-arch-scores`,
  `pbt-collect-test-scores`,
  `pbt-fill-arch-scores`,
  `pbt-fill-test-docstrings`,
  `pbt-fix-incomplete-scores`,
  `pbt-fix-long-lines`,
  `pbt-inject-responsibility-docstrings`,
  `pbt-inject-test-docstrings`,
  `pbt-run-messages-coverage-audit`.
- Focused contract suite passed: `uv run python -m pytest src/pytest_bdd_toolchain/case/contract/test_phase28_rename.py -q --tb=short --no-header` -> `37 passed in 22.31s`.
- Active workflow/config command references use `src/pytest_bdd_toolchain/case` and `pbt-*` entrypoints.
- No active workflow/config/doc command invocation of `python scripts/`, `uv run python scripts/`, `./scripts/`, or `pytest_bdd_testing` was found. The remaining active-doc `scripts/` hit is a project-structure note in `AGENTS.md`, not a command invocation; historical planning/spec records were excluded from this audit per closure instructions.
- Current E2E and contract command references use `src/pytest_bdd_toolchain/case/e2e` and `src/pytest_bdd_toolchain/case/contract`.

### Pre-Existing / Manual-Only

- Python 3.10-3.14 tox matrix remains manual/CI-only.
- Historical document retention remains manual judgment.
- No new implementation failures were observed in this focused validation pass.
