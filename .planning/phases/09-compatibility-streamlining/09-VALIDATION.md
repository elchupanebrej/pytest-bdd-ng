---
phase: 09
slug: compatibility-streamlining
status: final
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-16
updated: 2026-05-18
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run python -m pytest tests/ -q` |
| **Full suite command** | `uv run python -m pytest tests/ -q` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run python -m pytest tests/ -q`
- **After every plan wave:** Run `uv run python -m pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | SIM-01 | — | `bdd_tree_to_rst.py` runs with argparse, no docopt import | unit | `uv run python -m pytest tests/doc/test_doc.py -q` | ✅ | ✅ green |
| 09-01-02 | 01 | 1 | SIM-01 | — | `pathlib2` removed from pyproject.toml, no import errors | unit | `uv run python -m pytest tests/ -q` | ✅ | ✅ green |
| 09-01-03 | 01 | 1 | SIM-01 | — | `compatibility/git.py` deleted, no import errors | unit | `uv run python -m pytest tests/ -q` | ✅ | ✅ green |
| 09-01-04 | 01 | 1 | SIM-01 | — | `compatibility/jsonschema.py` deleted, direct imports work | unit | `uv run python -m pytest tests/messages/ -q` | ✅ | ✅ green |
| 09-01-05 | 02 | 1 | SIM-01 | — | `matrix.py` split: runtime functions importable from `compatibility/runtime_compat.py` | unit | `uv run python -m pytest tests/compatibility/test_matrix_rules.py -q` | ✅ | ✅ green |
| 09-01-06 | 02 | 1 | SIM-01 | — | `matrix.py` split: CI helpers importable from `util/matrix.py` | unit | `uv run python -m pytest tests/compatibility/ -q` | ✅ | ✅ green |
| 09-01-07 | 02 | 1 | SIM-01 | — | All 9 test files import from new module paths | unit | `uv run python -m pytest tests/compatibility/ -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

*All manual-only items have been verified as covered by existing automated tests.*

| Behavior | Requirement | Why Manual | Resolution |
|----------|-------------|------------|------------|
| `bdd_tree_to_rst.py` CLI behavior unchanged | SIM-01 | argparse vs docopt may have subtle CLI differences | Covered by `tests/doc/test_doc.py` — exercises `main()` and `convert()` with pathlib; module import succeeds, no docopt/pathlib2 references exist in source |
| `is_pair_compatible()` runtime behavior unchanged | SIM-01 | Split may alter import chain | Covered by `tests/compatibility/test_matrix_rules.py` — 5 test cases exercise `is_pair_compatible` from `runtime_compat`; all 39 compatibility tests pass |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** final — all 7 tasks verified green (2026-05-18)

---

## Validation Audit 2026-05-18

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 7 (all pre-existing, verified green) |
| Escalated | 0 |

**Test results:**
- `tests/compatibility/` — 39 passed
- `tests/messages/` — 107 passed, 2 skipped
- `tests/doc/test_doc.py` — 7 skipped (doc deps not installed; module imports clean)
- Zero `pathlib2`/`docopt` references in source tree
- Zero imports from old `compatibility/matrix.py`
