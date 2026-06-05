---
phase: 18-split-xdist-remote-tests-into-separate-parallel-gha-executor
reviewed: 2026-06-03T07:14:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - Makefile
  - .github/workflows/main.yml
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 18: Code Review Report

**Reviewed:** 2026-06-03T07:14:00Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed `Makefile` and `.github/workflows/main.yml` for CI behavior regressions, security risk, and maintainability defects. The Makefile argument-forwarding path is wired and the workflow matrix statically expands to six xdist-remote cells, but the new CI job introduces a mutable third-party action reference in a workflow that runs on pull requests and pushes.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: New Docker Setup Action Is Not Pinned To An Immutable Revision

**File:** `.github/workflows/main.yml:115`

**Issue:** The newly added `test-xdist-remote` job runs `docker/setup-docker-action@v5` by mutable major-version tag. If that tag is retargeted or compromised, arbitrary code can execute in this repository's CI on `pull_request`, `push`, and `workflow_dispatch` runs. This is a supply-chain security vulnerability in the new executor path, especially because the action runs before tox and receives the default workflow token context.

**Fix:** Pin the action to a reviewed full-length commit SHA, and update it intentionally through dependency maintenance.

```yaml
      - name: Set up Docker
        uses: docker/setup-docker-action@<reviewed-full-commit-sha>
        with:
          version: 29.1.5
```

---

_Reviewed: 2026-06-03T07:14:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
