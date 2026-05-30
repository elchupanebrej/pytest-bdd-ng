---
phase: 17
slug: adapt-github-ci-to-use-make-and-validate-with-act
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-27
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest via tox/make; GitHub Actions workflow validation via act |
| **Config file** | `pyproject.toml`, `tox.ini`, `.github/workflows/main.yml`, `Makefile` |
| **Quick run command** | `make validate-github-actions` |
| **Full suite command** | `make tox` |
| **Estimated runtime** | ~30 seconds for workflow validation; tox runtime varies by matrix selection |

---

## Sampling Rate

- **After every task commit:** Run `make validate-github-actions`
- **After every plan wave:** Run `make validate-github-actions` and targeted contract tests if workflow command assertions change
- **Before `$gsd-verify-work`:** `make validate-github-actions`, `make -n tox`, `GITHUB_ACTIONS=true make -n tox`, and changed-file-focused tests must be green
- **Max feedback latency:** 60 seconds for workflow syntax and dry-run checks

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 17-01-01 | 01 | 1 | D-04/D-05/D-06 | T-17-01 | CI tox command includes `tox-gh-actions` only under `GITHUB_ACTIONS=true` | smoke | `make -n tox` and `GITHUB_ACTIONS=true make -n tox` | no W0 | pending |
| 17-01-02 | 01 | 1 | D-07/D-08/D-10/D-11/D-12/D-13 | T-17-02 | Makefile targets are static commands with clear missing-tool failure for `act` | smoke | `make validate-github-actions` | no W0 | pending |
| 17-02-01 | 02 | 2 | D-01/D-02/D-03/D-09 | T-17-03 | Workflow preserves secret env and setup actions while calling Makefile targets | workflow validation | `make validate-github-actions` | no W0 | pending |
| 17-02-02 | 02 | 2 | D-10 | — | Message schema check still invokes existing sync script in check mode | contract | `uv run python -m pytest tests/cases/contract/generation/test_template_packaging.py -q` | yes | pending |

---

## Wave 0 Requirements

- [ ] No new test framework required; existing Makefile, tox, pytest, and act commands cover phase validation.
- [ ] Update contract coverage only if existing workflow-command assertions break after moving commands behind Makefile targets.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Npm package legitimacy | D-08 | npm packages are locked by phase context but slopcheck only checked PyPI ecosystem | Confirm `@cucumber/html-formatter` and `cucumber-html-reporter` remain intended dependencies before changing install semantics |
| First real GitHub Actions run | D-05 | tox-gh-actions behavior depends on runner matrix environment | Inspect first CI run for expected tox env selection and absence of unexpected platform skips |

---

## Validation Sign-Off

- [x] All tasks have automated verify or justified manual verification
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers missing references
- [x] No watch-mode flags
- [x] Feedback latency < 60s for workflow syntax and dry-run checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-27
