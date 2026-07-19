---
phase: 10
slug: pattern-unification
status: final
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-18
updated: 2026-05-18
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for plugin pattern unification enforcement.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run python -m pytest tests/unit/test_plugin_patterns.py tests/unit/test_quality_gates.py tests/contract/test_plugin_patterns_contract.py -q` |
| **Full suite command** | `uv run python -m pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds (unit), ~120 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `uv run python -m pytest tests/unit/test_plugin_patterns.py tests/unit/test_quality_gates.py -q`
- **After every plan wave:** Run `uv run python -m pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds (unit), ~120 seconds (full)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | SIM-02 | T-10-02 | Empty dirs removed, no import breakage | contract | `uv run python -m pytest tests/contract/test_plugin_patterns_contract.py::test_empty_plugin_directories_removed -q` | ✅ | ✅ green |
| 10-01-02 | 01 | 1 | SIM-02 | T-10-01 | `check_required_files()` detects missing entrypoint/hook/plugin | unit | `uv run python -m pytest tests/unit/test_plugin_patterns.py -q -k "required_files"` | ✅ | ✅ green |
| 10-01-02 | 01 | 1 | SIM-02 | T-10-01 | `check_cross_plugin_imports()` detects cross-plugin imports | unit | `uv run python -m pytest tests/unit/test_plugin_patterns.py -q -k "cross_plugin"` | ✅ | ✅ green |
| 10-01-02 | 01 | 1 | SIM-02 | T-10-01 | `check_stashbound_coverage()` detects unauthorized stash access | unit | `uv run python -m pytest tests/unit/test_plugin_patterns.py -q -k "stashbound"` | ✅ | ✅ green |
| 10-01-02 | 01 | 1 | SIM-02 | T-10-01 | `check_plugin_patterns()` combines all checks correctly | unit | `uv run python -m pytest tests/unit/test_plugin_patterns.py -q -k "CheckPluginPatterns"` | ✅ | ✅ green |
| 10-01-02 | 01 | 1 | SIM-02 | T-10-01 | `main()` returns correct exit codes (0 success, 1 failure, 1 nonexistent dir) | unit | `uv run python -m pytest tests/unit/test_plugin_patterns.py -q -k "Main"` | ✅ | ✅ green |
| 10-01-03 | 01 | 1 | SIM-02 | T-10-01 | quality_gates includes plugin_patterns; real codebase passes clean | unit | `uv run python -m pytest tests/unit/test_quality_gates.py -q -k "PluginPatternsIntegration"` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers all phase requirements.
- No `@dataclass` decorator usage in production code (verified by `tests/contract/test_plugin_patterns_contract.py::test_no_dataclass_in_production_code`).

---

## Manual-Only Verifications

*No manual-only items — all gaps resolved via automated tests.*

---

## Validation Audit 2026-05-18

| Metric | Count |
|--------|-------|
| Gaps found | 7 |
| Resolved | 7 |
| Escalated | 0 |

### Test Files Generated

| File | Tests | Coverage |
|------|-------|----------|
| `tests/unit/test_plugin_patterns.py` | 33 | `check_required_files`, `check_cross_plugin_imports`, `check_stashbound_coverage`, `check_plugin_patterns`, `main` |
| `tests/unit/test_quality_gates.py` | +2 | `quality_gates.main` plugin_patterns integration, real codebase pass |
| `tests/contract/test_plugin_patterns_contract.py` | 2 | `@dataclass` enforcement, empty directory removal |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** final — all 7 gaps resolved, 51 new test assertions (2026-05-18)
