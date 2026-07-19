---
phase: 33
slug: gather-failed-ci-logs-into-workflow-artifact
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-10
---

# Phase 33 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | GitHub Actions workflow validation (no test framework) |
| **Config file** | `.github/workflows/main.yml` |
| **Quick run command** | `act -j collect-failed-logs` (local GHA runner) or push to throwaway PR branch |
| **Full suite command** | N/A — CI infrastructure change; validated via manual PR workflow run |
| **Estimated runtime** | ~120 seconds (CI run) |

---

## Sampling Rate

- **After every task commit:** Validate YAML syntax (`yamllint .github/workflows/main.yml`)
- **After every plan wave:** Push to throwaway PR and verify artifact generation on intentional failure
- **Before `/gsd-verify-work`:** Full verification per approved design spec plan
- **Max feedback latency:** 300 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 33-01-01 | 01 | 1 | AC-01 | — | N/A | yamllint | `yamllint .github/workflows/main.yml` | ⬜ pending | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.github/workflows/main.yml` — validates collect-failed-logs job YAML syntax
- [ ] No test framework install needed — CI infrastructure phase

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Artifact produced on matrix failure | AC-01 | Requires live GHA environment; cannot simulate `failure()` condition locally | Push intentional failure to throwaway PR, confirm artifact appears with correct logs |
| Log metadata headers present | AC-03 (D-02) | Header content verification requires reading artifact contents | Download artifact, inspect `.log` files for metadata header format |
| Raw step output matches Actions UI | AC-03 | Requires side-by-side comparison between artifact and UI | Compare downloaded log content against Actions UI step output |
| No modification to existing jobs | AC-04 | Diff verification | `git diff` confirms only new `collect-failed-logs` job added |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 300s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
