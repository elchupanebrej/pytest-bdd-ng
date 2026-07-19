# Phase 33: Gather Failed CI Logs into Workflow Artifact - Context

**Gathered:** 2026-07-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a `collect-failed-logs` job to `.github/workflows/main.yml` that downloads raw step output for failed matrix test cells via `actions/github-script@v7` and uploads them as a single workflow artifact. Covers both `test` and `test-xdist-remote` jobs. Implementation follows the approved design spec at `docs/superpowers/specs/2026-06-02-gather-failed-ci-logs-design.md`.

The existing `test` and `test-xdist-remote` jobs are not modified — the collector job is a downstream consumer that fires on failure. Logs are downloadable as a single artifact bundle for offline investigation, grep, and long-term retention beyond GitHub's 90-day default.

</domain>

<decisions>
## Implementation Decisions

### Scope
- **D-01:** `needs: [test, test-xdist-remote]` — the collector job waits for both matrix jobs. If either fails, the collector runs. Both matrices produce downloadable logs in the same artifact bundle.

### Log Output Format
- **D-02:** Prepend a metadata header to each `.log` file before the raw step output body. Header includes: human-readable job name, run URL (`https://github.com/{owner}/{repo}/actions/runs/{run_id}`), and ISO 8601 timestamp. The raw output follows after a blank line.

### Design Decisions (from approved spec)
- **D-03:** `actions/github-script@v7` for API calls — `octokit.actions.listJobsForWorkflowRun` to enumerate jobs, filter by `conclusion === 'failure'`, then `octokit.actions.downloadJobLogsForWorkflowRun` per failed job.
- **D-04:** File name sanitization: replace any character outside `[A-Za-z0-9._-]` with `_`. Matrix cell names like `test (ubuntu-latest, 3.14)` become `test__ubuntu-latest__3.14_.log`.
- **D-05:** Artifact name: `failed-job-logs-run-${{ github.run_number }}-attempt-${{ github.run_attempt }}`. Includes `run_attempt` to avoid collision on UI re-runs.
- **D-06:** Permissions: `actions: read, contents: read`. No secrets, no write tokens.
- **D-07:** Error handling: if `downloadJobLogsForWorkflowRun` throws for an individual job, log via `core.warning` and continue with next job. Partial logs are more valuable than no logs.
- **D-08:** No-files guard: `hashFiles('failed-job-logs/*.log') != ''` check before upload, plus `if-no-files-found: ignore` on the upload step.
- **D-09:** Scope boundary: `main.yml` only. `release.yaml` and `messages-baseline-drift.yml` are out of scope.
- **D-10:** No modification to existing `test` or `test-xdist-remote` jobs.

### the agent's Discretion
- The planner decides exact implementation of the metadata header formatting within the github-script body.
- The planner decides whether the header should use `core.info` or be written directly into the log file content.
- The planner decides any helper function extraction within the script for DRY log collection.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design & Requirements
- `docs/superpowers/specs/2026-06-02-gather-failed-ci-logs-design.md` — **Approved design spec.** Job structure, data flow, error handling, permissions, artifact naming, verification plan. Authoritative for all implementation details not overridden by decisions above.
- `.planning/todos/done/2026-06-02-gather-failed-ci-logs-into-workflow-artifact.md` — Todo item with problem statement, solution summary, and implementation points.

### Workflow Target
- `.github/workflows/main.yml` — The workflow to modify. Contains `test` (matrix: 18 OS×Python cells) and `test-xdist-remote` (matrix: socket/via/ssh modes) jobs. New `collect-failed-logs` job is added here.

### Existing Patterns to Follow
- `.github/workflows/messages-baseline-drift.yml` — Example of `actions/upload-artifact@v4` usage (line 84) with name and path configuration. Existing artifact upload pattern.

### Project Conventions
- `.planning/PROJECT.md` — Project context and constraints.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `actions/upload-artifact@v4` already used in `messages-baseline-drift.yml` (line 84) — established pattern for artifact name + path + retention.
- `actions/github-script@v7` is a standard GitHub Action for authenticated API calls within a workflow run.
- `main.yml` already uses `actions/checkout@v5` and `astral-sh/setup-uv@v8.2.0` — the collector job only needs `actions/github-script@v7` and `actions/upload-artifact@v4`, no checkout or language setup required.

### Established Patterns
- Job dependencies: `test-xdist-remote` in `main.yml` already shows top-level dependency on nothing — it runs in parallel with `test`. The collector's `needs: [test, test-xdist-remote]` waits for both.
- `if: failure()` is standard GHA conditional for running cleanup/notification jobs after a failure.
- `permissions:` block per-job is used in `release.yml` and `main.yml` (implicit default). Explicit `permissions: { actions: read, contents: read }` follows least-privilege.

### Integration Points
- `.github/workflows/main.yml` — New `collect-failed-logs` job added after the `test-xdist-remote` job definition. No other files modified.
- No changes to `test` or `test-xdist-remote` jobs — they run unchanged.

</code_context>

<specifics>
## Specific Ideas

### Acceptance Criteria (from todo)
1. After any `main.yml` run with failed matrix cells, a single workflow artifact is produced
2. Artifact contains one `.log` file per failed matrix cell
3. Log content matches the raw step output shown in the GitHub Actions UI
4. No modification to the `test` or `test-xdist-remote` job definitions
5. Verification via throwaway PR with intentional failure confirmed (per spec verification plan)

### Design Spec Overrides
- Spec originally scoped to `needs: test` only → **D-01** expands to `needs: [test, test-xdist-remote]`
- Spec said raw output only → **D-02** adds a metadata header to each log file

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 33-gather-failed-ci-logs-into-workflow-artifact*
*Context gathered: 2026-07-10*
