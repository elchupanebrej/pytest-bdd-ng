---
phase: 06
slug: integration-testing
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-14
updated: 2026-05-17
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=7.0.0 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run python -m pytest tests/feature/test_step_matching_priority.py tests/feature/test_step_matching_ambiguous.py -q` |
| **Full phase run** | `uv run python -m pytest tests/feature/test_step_matching_*.py tests/feature/test_run_lifecycle_integration.py tests/feature/test_scenario_execution_edge_cases.py tests/feature/test_run_access_and_errors.py -q` |
| **xdist run** | `uv run python -m pytest tests/feature/test_xdist_parallel_integration.py -q` |
| **Estimated runtime** | ~60 seconds (phase core), ~30 seconds (xdist only) |

---

## Sampling Rate

- **After every task commit:** Run the specific test file for that task via `testdir`
- **After every plan wave:** Run all Phase 6 integration tests (excluding xdist)
- **Before `/gsd-verify-work`:** Full phase suite including xdist must be green
- **Max feedback latency:** 60 seconds (testdir subprocess overhead)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 0 | TEST-03 | T-06-01 | Correct matcher priority end-to-end | testdir | `pytest tests/feature/test_step_matching_priority.py -q` | ✅ | ✅ green |
| 06-01-02 | 01 | 0 | TEST-03 | T-06-03 | Import-order independence | testdir | `pytest tests/feature/test_step_matching_priority.py -q` | ✅ | ✅ green |
| 06-02-01 | 02 | 0 | TEST-03 | — | Ambiguous match resolution | testdir | `pytest tests/feature/test_step_matching_ambiguous.py -q` | ✅ | ✅ green |
| 06-02-02 | 02 | 0 | TEST-03 | — | Undefined step detection | testdir | `pytest tests/feature/test_step_matching_ambiguous.py -q` | ✅ | ✅ green |
| 06-02-03 | 02 | 0 | TEST-03 | — | Liberal steps ini option | testdir | `pytest tests/feature/test_step_matching_ambiguous.py -q` | ✅ | ✅ green |
| 06-03-01 | 03 | 0 | TEST-03 | T-06-04 | All RunStage transitions | testdir | `pytest tests/feature/test_run_lifecycle_integration.py -q` | ✅ | ✅ green |
| 06-03-02 | 03 | 0 | TEST-03 | — | Hook invocation order | testdir | `pytest tests/feature/test_run_lifecycle_integration.py -q` | ✅ | ✅ green |
| 06-03-03 | 03 | 0 | TEST-03 | — | xdist parallel lifecycle | testdir | `pytest tests/feature/test_run_lifecycle_integration.py -q -n 2` | ✅ | ✅ green |
| 06-04-01 | 04 | 0 | TEST-03 | — | Empty scenario handling | testdir | `pytest tests/feature/test_scenario_execution_edge_cases.py -q` | ✅ | ✅ green |
| 06-04-02 | 04 | 0 | TEST-03 | — | Unicode + data tables | testdir | `pytest tests/feature/test_scenario_execution_edge_cases.py -q` | ✅ | ✅ green |
| 06-04-03 | 04 | 0 | TEST-03 | — | Scenario Outline + Examples | testdir | `pytest tests/feature/test_scenario_execution_edge_cases.py -q` | ✅ | ✅ green |
| 06-05-01 | 05 | 0 | TEST-03 | T-06-08 | Step error hook pipeline | testdir | `pytest tests/feature/test_run_access_and_errors.py -q` | ✅ | ✅ green |
| 06-05-02 | 05 | 0 | TEST-03 | — | Missing binding error messages | testdir | `pytest tests/feature/test_run_access_and_errors.py -q` | ✅ | ✅ green |
| 06-05-03 | 05 | 0 | TEST-03 | T-06-09 | Scenario cleanup / state isolation | testdir | `pytest tests/feature/test_run_access_and_errors.py -q` | ✅ | ✅ green |
| 06-06-01 | 06 | 1 | TEST-03 | T-06-10 | xdist worker isolation | testdir | `pytest tests/feature/test_xdist_parallel_integration.py -q` | ✅ | ✅ green |
| 06-06-02 | 06 | 1 | TEST-03 | — | Report correctness under xdist | testdir | `pytest tests/feature/test_xdist_parallel_integration.py -q` | ✅ | ✅ green |

| Status | ⬜ pending · ✅ green · ❌ red · ⚠️ flaky |

---

## Wave 0 Requirements

- [x] `tests/feature/test_step_matching_priority.py` — 12 matching priority tests
- [x] `tests/feature/test_step_matching_ambiguous.py` — 8 ambiguity/error tests
- [x] `tests/feature/test_run_lifecycle_integration.py` — 8 lifecycle + hook order tests
- [x] `tests/feature/test_scenario_execution_edge_cases.py` — 12 edge case tests
- [x] `tests/feature/test_run_access_and_errors.py` — 10 error path tests
- [x] All new tests pass via `testdir` execution pattern
- [x] No regressions in existing `tests/feature/` suite

## Wave 1 Requirements

- [x] `tests/feature/test_xdist_parallel_integration.py` — 5 parallel execution tests
- [x] Full phase suite passes under `-n 2`
- [x] No cross-worker state contamination

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Existing test suite regression check | TEST-03 | Must run full suite | `uv run python -m pytest tests/ -q` and compare to baseline |
| Step matching determinism under load | TEST-03 | Non-deterministic failures only appear under stress | Run `pytest tests/feature/test_step_matching_priority.py -q` 50x via loop |

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all test files listed above
- [x] No watch-mode flags
- [x] Feedback latency < 60s per test file
- [x] `nyquist_compliant: true` set in frontmatter after Wave 0 pass

**Approval:** approved

## Validation Audit 2026-05-17

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Total tests | 55 (12 + 8 + 8 + 12 + 10 + 5) |
| All green | Yes |
| xdist pass | Yes (`-n 2`) |

**Audit notes:** All 16 verification tasks mapped to 6 test files. 55/55 tests pass. No gaps detected. Phase is Nyquist-compliant.
