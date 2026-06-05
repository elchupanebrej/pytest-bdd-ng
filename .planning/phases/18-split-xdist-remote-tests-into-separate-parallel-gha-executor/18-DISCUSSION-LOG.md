# Phase 18: Split xdist-remote tests into separate parallel GHA executor job - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-02
**Phase:** 18-split-xdist-remote-tests-into-separate-parallel-gha-executor
**Areas discussed:** todo folding, adjacent CI logs todo, discussion depth, main test job boundary, remote executor job, Docker runner setup, verification

---

## Todo Folding

| Option | Description | Selected |
|--------|-------------|----------|
| Fold it | Treat approved xdist-remote design spec as locked scope for downstream planner. | yes |
| Review only | Mention it as context but do not lock all todo details. | |
| Skip it | Ignore todo and discuss from roadmap only. | |

**User's choice:** Fold it.
**Notes:** Exact xdist-remote split todo is Phase 18 scope.

---

## Adjacent CI Logs Todo

| Option | Description | Selected |
|--------|-------------|----------|
| Defer | Keep Phase 18 focused on xdist-remote executor split. | yes |
| Fold it | Make log artifact part of this phase too, increasing workflow scope. | |
| Review only | Mention as adjacent future work without planning it. | |

**User's choice:** Defer.
**Notes:** Failed-CI-logs artifact todo is adjacent but separate capability.

---

## Discussion Depth

| Option | Description | Selected |
|--------|-------------|----------|
| All areas | Cover skip command boundary, new job shape, Docker setup, and verification. | yes |
| Critical only | Discuss only choices likely to change implementation. | |
| Use spec | Treat approved spec as locked and write context with agent discretion. | |

**User's choice:** All areas.
**Notes:** User wanted all meaningful implementation decision points clarified.

---

## Main Test Job Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Keep raw tox command | Replace `make tox` with raw `uvx --with tox-uv tox --skip-env ...`, as approved spec says. | |
| Preserve Makefile boundary | Use `make tox -- --skip-env ...` or add Makefile support if needed. | yes |
| Let planner choose | Require no duplicate xdist-remote execution, but leave command form flexible. | |

**User's choice:** Preserve Makefile boundary.
**Notes:** Phase 17 decision remains active. Planner may add minimal Makefile forwarding if current target cannot carry tox args cleanly.

---

## Remote Executor Job

| Option | Description | Selected |
|--------|-------------|----------|
| Exact 6-cell parallel job | `os=[ubuntu-latest, windows-latest]`, `mode=[socket, via, ssh]`, no `needs: test`, `fail-fast: false`. | yes |
| Add dependency on test | Avoid spending remote job time if main matrix fails, but lose parallel speedup. | |
| Let planner choose | Require six remote envs not run inside main `test` job. | |

**User's choice:** Exact 6-cell parallel job.
**Notes:** New job must start parallel with main `test`.

---

## Docker Runner Setup

| Option | Description | Selected |
|--------|-------------|----------|
| Pinned Docker action + verify | Use approved spec's `docker/setup-docker-action@v5` pin and Docker verification. | |
| Runner Docker as-is, verify only | Rely on GitHub-hosted runner Docker and verify before tox. | initial |
| CI-provisioned Docker before tests | Use GitHub CI setup capabilities so tests do not own Docker setup or image-loading orchestration. | yes |

**User's choice:** CI-provisioned Docker before tests.
**Notes:** User revised Area 3: "I need a runner with pre-setup docker (tests must not setup docker env and load images). It must be done via github ci setup possibilities." Context captures this as CI-owned setup before tox, with explicit Docker verification.

---

## Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Local only | Workflow YAML parses, six xdist-remote envs exist, main job skip expression validated. | |
| Local + GitHub UI required | Also require branch run showing six remote jobs parallel with main test and no duplicate envs. | |
| Local via act if possible | Prefer `act`/`make validate-github-actions` locally, plus post-push UI check for real parallelism. | yes |

**User's choice:** Local via act if possible.
**Notes:** User revised Area 4: "Verification locally - via act if possible." Context requires local `act` validation when feasible and keeps GitHub UI check for behavior local tools cannot prove.

---

## the agent's Discretion

- Exact Makefile forwarding implementation.
- Exact GitHub Actions expression syntax for platform mapping.
- Exact Docker CI setup mechanism, as long as setup is CI-owned before tests and verification is visible.
- Exact validation command sequence, as long as `act` is preferred when feasible and six-env skip behavior is checked.

## Deferred Ideas

- Failed-CI-logs artifact collection remains separate future CI work.
