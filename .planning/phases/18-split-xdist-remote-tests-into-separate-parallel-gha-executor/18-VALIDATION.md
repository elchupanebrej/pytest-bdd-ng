---
phase: 18
slug: split-xdist-remote-tests-into-separate-parallel-gha-executor
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-02
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | GitHub Actions YAML / Tox validation / act |
| **Config file** | `.github/workflows/main.yml` |
| **Quick run command** | `uvx --with ruamel.yaml python -c "import yaml; yaml.safe_load(open('.github/workflows/main.yml'))"` |
| **Full suite command** | `make validate-github-actions` (if `act` is installed) |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run YAML syntax verification: `uvx --with ruamel.yaml python -c "import yaml; yaml.safe_load(open('.github/workflows/main.yml'))"`
- **After every plan wave:** Verify targets match: `uvx --with tox-uv tox -l | rg xdist-remote`
- **Before `/gsd-verify-work`:** Run full validation using `make validate-github-actions` (or `act`) and manually review the pushed GitHub Actions workflow run in the GitHub UI.
- **Max feedback latency:** 10 seconds (local)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | CI-SPLIT-01 | — | N/A | syntax | `uvx --with ruamel.yaml python -c "import yaml; yaml.safe_load(open('.github/workflows/main.yml'))"` | ✅ | ⬜ pending |
| 18-01-02 | 01 | 1 | CI-SPLIT-02 | — | N/A | integration | `make validate-github-actions` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GitHub UI Execution Run | CI-SPLIT-03 | Requires real GHA runners to verify parallelism | Push to a branch, open the GHA Actions UI, verify the parallel `test-xdist-remote` job executes all 6 matrix cells, and the main `test` job skips them. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending 2026-06-02
