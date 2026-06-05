---
created: 2026-06-02T19:47:26.270Z
title: Gather failed CI logs into workflow artifact
area: tooling
files:
  - .github/workflows/main.yml:38
  - docs/superpowers/specs/2026-06-02-gather-failed-ci-logs-design.md:1
---

## Problem

When the matrix `test` job in `.github/workflows/main.yml` fails on a
contributor's Python/OS cell, today the only way to inspect the failure is to
open the GitHub Actions UI, expand the failing cell, and scroll through step
output. There is no offline bundle, no way to grep across multiple failed
cells at once, and logs disappear after GitHub's default 90-day retention.
A single design spec is approved (2026-06-02) and ready to implement.

## Solution

Add a single new job `collect-failed-logs` to `.github/workflows/main.yml` per
the approved spec at `docs/superpowers/specs/2026-06-02-gather-failed-ci-logs-design.md`.

Key implementation points (from the spec):

- New job `collect-failed-logs` with `needs: test`, `if: failure()`,
  `runs-on: ubuntu-latest`, `permissions: { actions: read, contents: read }`.
- Uses `actions/github-script@v7` to call
  `octokit.actions.listJobsForWorkflowRun(...)` filtered to
  `conclusion === 'failure'` and `name !== 'collect-failed-logs'`, then
  `octokit.actions.downloadJobLogsForWorkflowRun(...)` per failed job.
- Writes one `.log` per failed cell to `failed-job-logs/<sanitized-name>.log`
  (sanitize any char outside `[A-Za-z0-9._-]` to `_`).
- Uploads via `actions/upload-artifact@v4` named
  `failed-job-logs-run-${{ github.run_number }}-attempt-${{ github.run_attempt }}`
  (must include `run_attempt` to avoid collision on UI re-runs).
- `if-no-files-found: ignore` plus `hashFiles(...) != ''` guard so a no-failure
  edge case doesn't break the job.
- Do NOT modify the `test` job itself — no `tee`, no per-step wrapping.

Verification: open a throwaway PR injecting `run: exit 1` into `test`, confirm
`collect-failed-logs` succeeds and the artifact has one `.log` per cell, then
close the throwaway PR without merging. Record the verification in the PR
description.
