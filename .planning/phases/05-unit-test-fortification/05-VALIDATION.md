---
phase: 05
slug: unit-test-fortification
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-14
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=7.0.0 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run python -m pytest tests/unit/ -q` |
| **Full suite command** | `uv run python -m pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds (unit tests), ~120 seconds (full suite) |

---

## Sampling Rate

- **After every task commit:** Run `uv run python -m pytest tests/unit/ -x -q`
- **After every plan wave:** Run `uv run python -m pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 0 | TEST-01 | — | N/A | config | `uv run python -m pytest tests/unit/ -q` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 0 | TEST-01 | — | N/A | config | `uv run python -m pytest --markers` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 0 | TEST-01 | — | N/A | config | `uv run python -m pytest --cov --cov-report=term` | ❌ W0 | ⬜ pending |
| 05-01-04 | 01 | 0 | TEST-01 | — | N/A | migration | `uv run python -m pytest tests/unit/ -m unit -q` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 1 | TEST-01 | — | N/A | unit | `uv run python -m pytest tests/unit/model/test_run.py -x` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 1 | TEST-01 | — | N/A | unit | `uv run python -m pytest tests/unit/model/test_scenario_run.py -x` | ❌ W0 | ⬜ pending |
| 05-02-03 | 02 | 1 | TEST-01 | — | N/A | unit | `uv run python -m pytest tests/unit/model/test_feature_binding.py -x` | ❌ W0 | ⬜ pending |
| 05-03-01 | 03 | 2 | TEST-01 | T05-01 | No regex DoS via crafted patterns | integration | `uv run python -m pytest tests/unit/test_steps.py -x` | ❌ W0 | ⬜ pending |
| 05-04-01 | 04 | 3 | TEST-01 | — | N/A | unit | `uv run python -m pytest tests/args/ -x` | ❌ W0 | ⬜ pending |
| 05-04-02 | 04 | 3 | TEST-01 | — | N/A | audit | N/A — code review step | N/A | ⬜ pending |

| Status | ⬜ pending · ✅ green · ❌ red · ⚠️ flaky |

---

## Wave 0 Requirements

- [ ] `tests/unit/model/test_run.py` — stubs for Run class tests (TEST-01)
- [ ] `tests/unit/model/test_scenario_run.py` — stubs for ScenarioRun + RunNode tests (TEST-01)
- [ ] `tests/unit/model/test_feature_binding.py` — stubs for FeatureRuntimeBinding tests (TEST-01)
- [ ] `tests/unit/test_steps.py` — stubs for step definition tests (TEST-01)
- [ ] `tests/unit/conftest.py` — shared fixtures: run, scenario_run, feature_binding, gherkin_document
- [ ] `uv add --dev pytest-cov` — coverage tooling not installed
- [ ] `@pytest.mark.unit` marker registered in `pyproject.toml`
- [ ] `fail_under = 70` added to `.coveragerc`
- [ ] Migration of 19 existing tests from `tests/hook/`, `tests/model/`, `tests/steps/` into `tests/unit/`
- [ ] Stubs in `tests/args/regex/`, `tests/args/parse_/`, `tests/args/cfparse/`, `tests/args/cucumber_expression/`, `tests/args/heuristic/` for parser edge cases

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `# pragma: no cover` justification audit (13 instances in parsers.py) | TEST-01 (D-10, D-11) | Code review — each pragma must have inline justification comment | Open `src/pytest_bdd/parsers.py`, verify each `# pragma: no cover` has `— reason:` comment |
| Test migration deduplication | TEST-01 (D-07) | Manual review of migrated test function names for collisions | `uv run python -m pytest --co tests/unit/` and verify no name collisions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
