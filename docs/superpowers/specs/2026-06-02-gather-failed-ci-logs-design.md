# Gather failed-job logs into a workflow artifact

**Status:** Approved (design phase)
**Date:** 2026-06-02
**Scope:** `.github/workflows/main.yml` only

## Problem

When the matrix `test` job in `main.yml` fails on a contributor's machine
configuration we don't own (a specific Python/OS cell), inspecting the failure
today requires opening the GitHub Actions UI, expanding the failing cell, and
scrolling through step output. There is no offline bundle, no easy way to grep
across multiple failed cells, and logs disappear after GitHub's default 90-day
retention. We want failure investigation to be a single artifact download.

## Goals

- After any `main.yml` run that contains one or more failed matrix cells,
  produce a single workflow artifact containing the raw GitHub Actions step
  output for each failed cell.
- Leave the existing `test` job untouched (no `tee`, no per-step wrapping, no
  added dependencies on the hot path).
- Use least-privilege permissions for the new job.

## Non-goals

- Capturing logs from cancelled or skipped jobs.
- Capturing tool-level diagnostic artifacts (pytest junit XML, tox logs,
  coverage data, generated NDJSON). These may be added later under a separate
  spec; see *Future work*.
- Applying the same treatment to `release.yaml` or `messages-baseline-drift.yml`.
- Custom retention overrides; we accept GitHub's default (90 days).

## Design

### New job

Add a single job `collect-failed-logs` to `.github/workflows/main.yml`:

```yaml
  collect-failed-logs:
    needs: test
    if: failure()
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
    steps:
      - name: Download logs for failed matrix jobs
        uses: actions/github-script@v7
        with:
          script: |
            # see Data flow below
      - name: Upload failed-job logs
        if: hashFiles('failed-job-logs/*.log') != ''
        uses: actions/upload-artifact@v4
        with:
          name: failed-job-logs-run-${{ github.run_number }}-attempt-${{ github.run_attempt }}
          path: failed-job-logs/
          if-no-files-found: ignore
```

### Data flow

1. Matrix `test` jobs run exactly as today.
2. After the matrix completes, `collect-failed-logs` fires because
   `needs: test` resolved and `if: failure()` matched at least one failed cell.
   The `if: failure()` predicate deliberately does not include `cancelled()`.
3. The `github-script` step calls
   `octokit.actions.listJobsForWorkflowRun({ owner, repo, run_id: context.runId })`
   to enumerate every job in the current run.
4. It filters that list to jobs whose `conclusion === 'failure'` and whose
   `name` is not `collect-failed-logs` (defensive: the collector cannot have
   failed yet at this point, but guard anyway).
5. For each failed job it calls
   `octokit.actions.downloadJobLogsForWorkflowRun({ owner, repo, job_id })`,
   which returns the plain-text log body via a redirected URL fetch.
6. The body is written to `failed-job-logs/<sanitized-job-name>.log`, where
   `<sanitized-job-name>` replaces any character outside `[A-Za-z0-9._-]` with
   `_` so cell names like `test (ubuntu-latest, 3.14)` become safe file names
   (e.g. `test__ubuntu-latest__3.14_.log`).
7. The upload step bundles the directory as
   `failed-job-logs-run-${{ github.run_number }}` with default retention.

### Error handling

- If `listJobsForWorkflowRun` itself throws, the collector step fails. This is
  acceptable — without the job list we cannot produce a useful artifact, and
  the failure will surface in the Actions UI.
- If `downloadJobLogsForWorkflowRun` throws for an individual job, the script
  logs the failure to step output (`core.warning(...)`) and continues with the
  next job. Partial logs are more valuable than no logs.
- If, after iterating, zero files were written (no failed jobs found despite
  `if: failure()` — e.g. a non-matrix step in the workflow failed in a future
  edit), the upload step skips via the `hashFiles(...) != ''` guard and the
  `if-no-files-found: ignore` safety net. The collector job still succeeds.

### Permissions

`permissions: { actions: read, contents: read }` on the collector job. No
secrets, no write tokens. `actions: read` is required to call the
`listJobsForWorkflowRun` and `downloadJobLogsForWorkflowRun` endpoints for the
current repository.

### Artifact properties

- **Name:** `failed-job-logs-run-${{ github.run_number }}-attempt-${{ github.run_attempt }}`.
  Including `run_attempt` is required because `run_number` and `run_id` both
  stay the same when a failed run is re-run from the Actions UI; only
  `run_attempt` increments. Without it, the second attempt would collide with
  the first and `actions/upload-artifact@v4` would reject the upload (its
  no-duplicate-names rule).
- **Contents:** One `.log` file per failed matrix cell, named after the cell.
- **Retention:** Default (90 days).
- **Format:** Plain text, identical to what the Actions UI displays.

## Verification plan

A workflow change cannot be unit-tested. Verify manually after merge:

1. Open a throwaway PR that adds a deliberately failing step to the `test`
   job (e.g. `- run: exit 1`).
2. Wait for the workflow to run. Confirm:
   - All matrix cells fail at the injected step.
   - `collect-failed-logs` runs and succeeds.
   - The artifact `failed-job-logs-run-<N>` is attached to the run.
   - Downloading and unzipping it yields one `.log` file per matrix cell,
     each containing the step output ending with the `exit 1` failure.
3. Close the throwaway PR without merging.

Record the verification result in the PR description or a follow-up comment so
future maintainers can find evidence the mechanism works.

## Out of scope / future work

- Bundling tool-level diagnostics (junit XML, coverage data, tox logs,
  generated NDJSON). Tracked as a possible follow-up; would likely use a
  per-matrix-cell artifact uploaded with `if: failure()` then aggregated by
  the same collector job.
- Applying the same gathering to `release.yaml` or
  `messages-baseline-drift.yml`. Out of scope per user direction.
- Custom retention windows or off-GitHub log archiving (e.g. S3, GCS).

## Open questions

None at design time. Any operational surprises (e.g. log size limits,
rate limits on `downloadJobLogsForWorkflowRun` when many cells fail) will be
addressed reactively if they appear during verification.
