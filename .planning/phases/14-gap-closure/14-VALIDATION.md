---
phase: 14
slug: gap-closure
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-20
revised: 2026-05-20
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=7.0.0 |
| **Config file** | pyproject.toml (pytest markers, test_group_paths, coverage) |
| **Quick run command** | `uv run python -m pytest tests/cases/unit/ -q --no-header` |
| **Full suite command** | `uv run python -m pytest tests/cases/ --cov=pytest_bdd --cov-report=term` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run python -m pytest tests/cases/unit/ -q --no-header`
- **After every plan wave:** Run `uv run python -m pytest tests/cases/ --cov=pytest_bdd --cov-report=term`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | TEST-01 | — | N/A | analysis | `grep -c "per-module\|top uncovered\|prioritized\|CLI command" .planning/phases/14-gap-closure/coverage-gap-report.md` (>=3 hits) | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 1 | TEST-02 | — | N/A | analysis | `grep -c "StepNotFound\|AssertionError\|ImportError\|FixtureLookupError\|Infrastructure\|ProductionBug" .planning/phases/14-gap-closure/bdd-triage-report.md` (>=3 hits) | ❌ W0 | ⬜ pending |
| 14-02-01 | 02 | 2 | TEST-01 | — | N/A | unit | `uv run python -m pytest tests/cases/unit/unit/test_tag_expression.py tests/cases/unit/unit/test_scenario_locator.py tests/cases/unit/unit/test_scenario.py tests/cases/unit/unit/test_parser.py tests/cases/unit/unit/test_collector.py -v --no-header` | ❌ W0 | ⬜ pending |
| 14-02-02 | 02 | 2 | TEST-01 | — | N/A | unit+integration | `uv run python -m pytest tests/cases/unit/unit/model/test_run.py tests/cases/unit/unit/model/test_scenario_run.py tests/cases/unit/unit/model/test_run_access.py tests/cases/unit/unit/model/test_run_refs.py tests/cases/unit/unit/test_parsers_unit.py tests/cases/unit/unit/parser/test_parsers.py tests/cases/unit/unit/test_steps.py tests/cases/unit/unit/test_step_internals.py tests/cases/integration/feature/test_steps.py -v --no-header` | ❌ W0 | ⬜ pending |
| 14-02-03 | 02 | 2 | TEST-01 | — | N/A | unit (marker audit) | `uv run python -m pytest tests/cases/unit/unit/test_marker_audit.py -v --no-header; uv run python -m pytest tests/cases/unit/ -q --no-header` | ❌ W0 | ⬜ pending |
| 14-03-01 | 03 | 2 | TEST-02 | — | N/A | e2e | `uv run python -m pytest tests/cases/e2e/e2e/test_e2e.py -v --tb=short --no-header` | ✅ | ⬜ pending |
| 14-03-02 | 03 | 2 | TEST-02 | — | N/A | e2e (split) | `uv run python -m pytest tests/cases/e2e/e2e/ -v --tb=short --no-header` | ❌ W0 | ⬜ pending |
| 14-03-03 | 03 | 2 | TEST-02 | — | N/A | e2e (new features) | `uv run python -m pytest tests/cases/e2e/e2e/ -v --tb=short --no-header` | ❌ W0 | ⬜ pending |
| 14-04-01 | 04 | 3 | TEST-01 | — | N/A | full suite + coverage | `uv run python -m pytest tests/cases/ -q --no-header --cov=pytest_bdd --cov-branch --cov-report=term --cov-fail-under=70` | ✅ | ⬜ pending |
| 14-04-02 | 04 | 3 | TEST-02 | — | N/A | e2e + integration final | `uv run python -m pytest tests/cases/e2e/e2e/ tests/cases/integration/ -v --tb=short --no-header` | ❌ W0 | ⬜ pending |
| 14-04-03 | 04 | 3 | TEST-01, TEST-02 | — | N/A | summary | `grep -c "Requirements status" .planning/phases/14-gap-closure/14-04-SUMMARY.md` returns 1, `grep -c "before/after" .planning/phases/14-gap-closure/14-04-SUMMARY.md` returns >=1 | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Baseline coverage report: `uv run python -m pytest tests/cases/unit/ tests/cases/integration/ --cov=pytest_bdd --cov-report=term` to establish current coverage per module
- [x] BDD triage run: `uv run python -m pytest tests/cases/e2e/e2e/ -k "not allure and not docker and not slow and not xdist" --no-header` to categorize failures
- [x] Existing infrastructure covers all phase requirements (pytest, pytest-cov, pytest-order, pytest-xdist already installed)
- [ ] 14-01 creates coverage-gap-report.md and bdd-triage-report.md (analysis artifacts, not test files)
- [ ] 14-02 Task 3 creates tests/cases/unit/unit/test_marker_audit.py (marker compliance gate)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Per-module coverage threshold verification | TEST-01 | Per-module enforcement needs script/plugin; aggregate check automated | Run coverage report per module, verify each >=70% |
| Pragma audit justification review | TEST-01 | Human judgment required to classify pragma as justified/unjustified | Review each `# pragma: no cover`, tag justified or remove |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
