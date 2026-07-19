---
phase: 31
slug: add-tracebackhide-true-module-level-to-all-src-pytest-bdd-mo
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-08
---

# Phase 31 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | pyproject.toml |
| **Quick run command** | `.venv/bin/pytest src/pytest_bdd_toolchain/case/unit/test_utils.py` |
| **Full suite command** | `.venv/bin/pytest src/pytest_bdd_toolchain/case/unit -n auto` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest src/pytest_bdd_toolchain/case/unit/test_utils.py`
- **After every plan wave:** Run `.venv/bin/pytest src/pytest_bdd_toolchain/case/unit -n auto`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 31-01-01 | 01 | 1 | D-06 | T-31-01 | Scaffold traceback hide test | integration | `.venv/bin/python -m py_compile src/pytest_bdd_toolchain/case/integration/test_tracebackhide.py` | ❌ W0 | ⬜ pending |
| 31-02-01 | 02 | 2 | D-01 / D-03 / D-04 / D-05 / D-08 / D-09 | T-31-02 | Run insertion script | unit | git diff --name-only \| grep -q "src/pytest_bdd/" | ✅ | ⬜ pending |
| 31-02-02 | 02 | 2 | D-02 | T-31-02 | Remove redundant variables | unit | `grep -E '^[[:space:]]+__tracebackhide__[[:space:]]*=' src/pytest_bdd/compatibility/pytest.py src/pytest_bdd/plugin/pickle_runner/plugin/runner_plugin.py; [ $? -eq 1 ]` | ✅ | ⬜ pending |
| 31-02-03 | 02 | 2 | D-05 | T-31-02 | Format imports and variables spacing | unit | ruff format --check src/pytest_bdd/ | ✅ | ⬜ pending |
| 31-03-01 | 03 | 3 | D-07 | T-31-03 | Run test suite and adapt checking | unit | `.venv/bin/pytest src/pytest_bdd_toolchain/case/unit/ -n auto` | ✅ | ⬜ pending |
| 31-03-02 | 03 | 3 | D-06 | T-31-03 | Verify integration test passes | integration | `.venv/bin/pytest src/pytest_bdd_toolchain/case/integration/test_tracebackhide.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/pytest_bdd_toolchain/case/integration/test_tracebackhide.py` — integration test to verify frame hiding.

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved
