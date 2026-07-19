---
phase: 32
slug: implement-unbound-feature-detection
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-09
---

# Phase 32 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/unit/test_unbound.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick suite
- **After every plan wave:** Run full suite
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | TBD | — | N/A | unit | `pytest tests/unit/test_unbound.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_unbound.py` — stubs for UnboundFeatureItem and _detect_unbound_features
- [ ] `tests/feature/test_feature_detection.py` — integration tests for unbound feature detection

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| xdist worker gating | D-03 | Multi-process collection timing | Run `pytest -n 2` and verify no duplicate skip items |
| CLI/INI config round-trip | D-05 | Config string format | Run `pytest --help`, verify `--unbound-features` appears; check `pytest -h` output |
| Shortcut file resolution | D-14 | Requires .url/.desktop fixtures on disk | Create test fixture shortcuts, verify detection behavior |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
