---
phase: 34
slug: move-remaining-cck-testing-utilities-out-of-pytest-bdd-testi
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-12
---

# Phase 34 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -c "from pytest_bdd_toolchain.case.contract.cck.cck import CCK_SAMPLE_NAMES; print('OK')"` |
| **Full suite command** | `python -m pytest src/pytest_bdd_toolchain/case/contract/cck/ -x --no-header -q -m "not docker and not browser"` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run import smoke test
- **After every plan wave:** Run full CCK contract test suite
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 34-01-01 | 01 | 1 | Move cck.py | integration | `python -c "from pytest_bdd_toolchain.case.contract.cck.cck import CCK_SAMPLE_NAMES; print('OK')"` | ⬜ pending |
| 34-01-02 | 01 | 1 | Update imports | integration | `python -m pytest src/pytest_bdd_toolchain/case/contract/cck/ -x -q -m "not docker and not browser"` | ⬜ pending |
| 34-01-03 | 01 | 1 | Delete testing/ | shell | `test ! -d src/pytest_bdd/testing && echo PASS` | ⬜ pending |
| 34-01-04 | 01 | 1 | Negative import | shell | `python -c "from pytest_bdd.testing.cck import CCK_SAMPLE_NAMES" 2>&1 \| grep -q ModuleNotFoundError && echo PASS` | ⬜ pending |
| 34-01-05 | 01 | 1 | Lint clean | lint | `ruff check src/pytest_bdd_toolchain/case/contract/cck/ src/pytest_bdd_toolchain/step/steps_cck_allure.py` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test files or fixtures needed.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have automated verify
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-12
