---
phase: 18-split-xdist-remote-tests-into-separate-parallel-gha-executor
verified: 2026-06-02T22:07:46Z
status: human_needed
score: 14/14 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Post-push GitHub Actions UI/log check for the Main testing workflow"
    expected: "The `test` job and six `test-xdist-remote` matrix cells start without a `needs:` dependency, the six cells cover socket/via/ssh on ubuntu-latest and windows-latest, and no `py314-pytestlatest-xdist-remote-*` env appears in the main `test` job logs."
    why_human: "Local YAML and tox checks prove static wiring, but only a real pushed workflow run proves GitHub-hosted runner scheduling, UI parallelism, and per-cell log behavior."
---

# Phase 18: Split xdist-remote Tests Verification Report

**Phase Goal:** Split the six long-running Docker-backed xdist-remote tox environments out of the existing GitHub Actions test job into a dedicated parallel test-xdist-remote job, while preserving the Phase 17 Makefile command boundary.
**Verified:** 2026-06-02T22:07:46Z
**Status:** human_needed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | D-01: Fold the todo into Phase 18 | VERIFIED | Phase 18 roadmap entry exists; phase context and plan use the split-xdist-remote todo as scope. |
| 2 | D-02: Preserve Phase 17 Makefile command boundary in GitHub Actions | VERIFIED | `.github/workflows/main.yml:65` and `:135` invoke `make tox`, not tox directly. |
| 3 | D-03: Use Makefile support for tox arguments | VERIFIED | `Makefile:51` defines `TOX_ARGS ?=`; `Makefile:414` runs `$(TOX) $(TOX_ARGS)`. |
| 4 | D-04: Do not change tox env definitions or remove xdist-remote from default tox list | VERIFIED | `tox.ini:11`, `:84`, `:92` still define xdist-remote envs; `uvx --with tox-uv tox -l` lists all six target envs. |
| 5 | D-05: Add dedicated `test-xdist-remote` GHA job with exactly six matrix cells | VERIFIED | `.github/workflows/main.yml:83`, `:91-97` define two OS values and three mode values. |
| 6 | D-06: `test-xdist-remote` runs parallel with `test` | VERIFIED | Job is sibling to `test`; no `needs:` key found in `.github/workflows/main.yml`. |
| 7 | D-07: Use `fail-fast: false` on the xdist-remote matrix | VERIFIED | `.github/workflows/main.yml:89` has `fail-fast: false` in `test-xdist-remote`. |
| 8 | D-08: Each matrix cell runs matching existing tox env | VERIFIED | `.github/workflows/main.yml:128-135` maps Ubuntu to `lin`, other OS to `win`, builds `py314-pytestlatest-xdist-remote-${{ matrix.mode }}-${platform}`, and passes it via `TOX_ARGS="-e ${target_env}"`. |
| 9 | D-09: Docker provisioned through GitHub CI setup capabilities | VERIFIED | `.github/workflows/main.yml:115-117` uses `docker/setup-docker-action@v5` with version `29.1.5`. |
| 10 | D-10: Verify Docker availability before tox | VERIFIED | `.github/workflows/main.yml:118-122` runs `docker --version`, `docker compose version`, and `docker info` before tox. |
| 11 | D-11: Use explicit Docker setup action | VERIFIED | `.github/workflows/main.yml:115` uses `docker/setup-docker-action@v5`. |
| 12 | D-12: Local verification uses act when feasible | VERIFIED | `Makefile:418-420` defines `validate-github-actions` with `act --validate`; local `act --version` failed with `command not found`, so act execution was not feasible in this verifier environment. |
| 13 | D-13: Local preflight proves YAML parses and six tox envs match | VERIFIED | YAML parse command returned `yaml_parse=ok`; filtered `uvx --with tox-uv tox -l` returned exactly 6 `py314-pytestlatest-xdist-remote-*` envs. |
| 14 | D-14: Plan includes post-push GHA UI check | VERIFIED | `.planning/phases/.../18-VALIDATION.md:58` and `18-RESEARCH.md:180-182` describe UI/log confirmation for parallelism, six cells, and main-job skip. |

**Score:** 14/14 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `Makefile` | Tox argument forwarding | VERIFIED | `gsd-sdk verify.artifacts` passed; `TOX_ARGS ?=` and `$(TOX) $(TOX_ARGS)` present. |
| `.github/workflows/main.yml` | Parallel GHA test workflow with split xdist-remote execution | VERIFIED | `gsd-sdk verify.artifacts` passed; `test-xdist-remote` job present and wired. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| Main `test` job | Makefile tox target | `make tox TOX_ARGS='--skip-env "xdist-remote-.*"'` | WIRED | `.github/workflows/main.yml:65` preserves Makefile boundary and skips target envs. |
| `test-xdist-remote` job | Makefile tox target | `make tox TOX_ARGS="-e ${target_env}"` | WIRED | `.github/workflows/main.yml:133-135` builds one env per matrix cell and passes it through Makefile. |
| Docker setup | Docker diagnostics | setup action before diagnostic step | WIRED | `.github/workflows/main.yml:115-122` provisions Docker before verification and tox. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `.github/workflows/main.yml` | `matrix.os`, `matrix.mode`, `platform`, `target_env` | GitHub Actions matrix and bash step | Yes | FLOWING - matrix values construct concrete tox env names. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Workflow YAML parses | `rtk uvx --with ruamel.yaml python -c "from ruamel.yaml import YAML; YAML(typ='safe').load(open('.github/workflows/main.yml', encoding='utf-8'))"` | `yaml_parse=ok` | PASS |
| Six target tox envs exist | `rtk bash -lc 'uvx --with tox-uv tox -l | grep -E "^py314-pytestlatest-xdist-remote-" | wc -l'` | `6` | PASS |
| Default Makefile tox boundary unchanged | `rtk bash -lc 'make -n tox'` | dry-run ends with `uvx --with tox-uv tox` and no extra args | PASS |
| act validation feasibility | `rtk bash -lc 'command -v act; act --version'` | `/bin/bash: line 1: act: command not found` | SKIP - act unavailable locally |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| None declared | N/A | No `probe-*.sh` paths declared for this phase | SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| None | `18-01-PLAN.md` | Plan frontmatter has `requirements: []`; D-01 through D-14 are must-haves, not requirement IDs in `.planning/REQUIREMENTS.md`. | SATISFIED | `.planning/REQUIREMENTS.md` has no Phase 18 requirement mapping. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | N/A | No TODO/FIXME/XXX/HACK/PLACEHOLDER/stub patterns found in `Makefile` or `.github/workflows/main.yml`. | N/A | N/A |

### Human Verification Required

### 1. Post-push GitHub Actions UI/log check

**Test:** Push branch or open a run of `Main testing workflow`, then inspect the Actions graph and logs.
**Expected:** `test` and six `test-xdist-remote` matrix cells run without a `needs:` dependency; cells cover socket/via/ssh on ubuntu-latest and windows-latest; main `test` logs show tox was run with `--skip-env "xdist-remote-.*"` and do not execute any `py314-pytestlatest-xdist-remote-*` env.
**Why human:** Local checks cannot prove GitHub-hosted runner scheduling or UI/log behavior after push.

### Gaps Summary

No automated verification gaps found. Status is `human_needed` only because post-push GitHub Actions UI/log confirmation is required by D-14 and cannot be proven from local static checks.

---

_Verified: 2026-06-02T22:07:46Z_
_Verifier: the agent (gsd-verifier)_
