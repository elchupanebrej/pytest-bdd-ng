---
phase: 01-foundation-cleanup
slug: foundation-cleanup
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-18
updated: 2026-05-18
---

# Phase 01 — Validation Strategy

> Reconstructed from Phase 01 plan and summary artifacts.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run --extra test python -m pytest tests/feature/test_foundation_cleanup.py -q` |
| **Full suite command** | `uv run --extra test python -m pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds quick / project suite dependent |

---

## Sampling Rate

- **After every task commit:** Run `uv run --extra test python -m pytest tests/feature/test_foundation_cleanup.py -q`
- **After every plan wave:** Run `uv run --extra test python -m pytest tests/ -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds for Phase 01-specific checks

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | STAB-01 | — | Dead Allure plugin entrypoint, extra, source, compatibility shim, and tests stay removed | regression | `uv run --extra test python -m pytest tests/feature/test_foundation_cleanup.py::test_allure_plugin_cleanup_remains_complete -q` | yes | green |
| 01-01-02 | 01 | 1 | STAB-01 | — | Allure source/test paths remain absent after cleanup | regression | `uv run --extra test python -m pytest tests/feature/test_foundation_cleanup.py::test_allure_plugin_cleanup_remains_complete -q` | yes | green |
| 01-02-01 | 02 | 1 | STAB-04 | — | Legacy `--cucumberjson` alias is rejected by pytest while plugin import remains intact | regression | `uv run --extra test python -m pytest tests/feature/test_foundation_cleanup.py::test_legacy_cucumberjson_flag_is_rejected -q` | yes | green |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

Existing pytest infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Audit 2026-05-18

| Metric | Count |
|--------|-------|
| Gaps found | 2 |
| Resolved | 2 |
| Escalated | 0 |

Resolved gaps:

- STAB-01: Added regression coverage for complete Allure cleanup across `pyproject.toml`, plugin source, compatibility shim, and deleted tests.
- STAB-04: Added regression coverage that `--cucumberjson` receives pytest's standard unrecognized-argument failure.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s for Phase 01 checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-18
