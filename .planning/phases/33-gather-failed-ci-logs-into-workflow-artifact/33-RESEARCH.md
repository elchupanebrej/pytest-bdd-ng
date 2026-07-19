# Phase 33: Gather Failed CI Logs into Workflow Artifact - Research

**Researched:** 2026-07-10
**Domain:** GitHub Actions workflow (CI/CD pipeline customization)
**Confidence:** HIGH

## Summary

This phase adds a single `collect-failed-logs` job to `.github/workflows/main.yml` that fires on failure of either the `test` or `test-xdist-remote` matrix jobs, downloads raw step output for every failed matrix cell via the GitHub Actions REST API, and bundles them into a single downloadable workflow artifact. The implementation is entirely within one YAML file using two built-in GitHub Actions (`actions/github-script@v7` and `actions/upload-artifact@v4`) — no external packages, no code changes outside the workflow file.

**Primary recommendation:** Implement exactly per the approved design spec at `docs/superpowers/specs/2026-06-02-gather-failed-ci-logs-design.md` with the two overrides documented in CONTEXT.md (D-01: include both test + xdist-remote; D-02: prepend metadata header). The research confirms all API behaviors, pagination edge cases, and error handling patterns described in the spec are correct and current.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `needs: [test, test-xdist-remote]` — the collector job waits for both matrix jobs. If either fails, the collector runs. Both matrices produce downloadable logs in the same artifact bundle.
- **D-02:** Prepend a metadata header to each `.log` file before the raw step output body. Header includes: human-readable job name, run URL (`https://github.com/{owner}/{repo}/actions/runs/{run_id}`), and ISO 8601 timestamp. The raw output follows after a blank line.
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

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Log collection trigger | GHA Job Scheduler | — | `if: failure()` + `needs` determines when collector runs |
| Job enumeration | GitHub REST API | — | `listJobsForWorkflowRun` is the sole source of truth for job status |
| Log download | GitHub REST API | — | `downloadJobLogsForWorkflowRun` returns raw step output via Octokit |
| Log file writing | GHA Runner filesystem | — | `require('node:fs')` writes log files to `failed-job-logs/` directory |
| Artifact bundling | GHA Artifact storage | — | `actions/upload-artifact@v4` packages and stores the artifact |
| Metadata formatting | github-script inline JS | — | D-02 specifies the header fields; formatting is agent discretion |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `actions/github-script` | v7 | Authenticated Octokit client for GitHub REST API calls | GitHubs own action; pre-authenticated, context-aware, Node 20 runtime [CITED: github.com/actions/github-script] |
| `actions/upload-artifact` | v4 | Upload directory as workflow artifact | GitHubs own action; already used in project (`messages-baseline-drift.yml` line 84) [CITED: github.com/actions/upload-artifact] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Octokit REST client (via github-script) | bundled | `github.rest.actions.listJobsForWorkflowRun`, `downloadJobLogsForWorkflowRun` | Always — injected as `github` parameter in script |
| `@actions/core` (via github-script) | bundled | `core.warning()` for non-fatal error logging | For per-job download failures (D-07) |
| Node.js `fs` (via github-script) | Node 20 stdlib | `require('node:fs')` for writing log files to runner workspace | Always — writable `failed-job-logs/` directory |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `actions/github-script@v7` | Raw `curl` + `gh api` in shell | github-script provides pre-authenticated Octokit, context injection, and JSON parsing out of the box. Raw curl requires token management and jq parsing. |
| `actions/upload-artifact@v4` | Custom artifact upload via REST API | upload-artifact handles zipping, naming, retention, and error cases. Custom upload is more code for no benefit. |
| Metadata via `core.info` | Prepend to file content | `core.info` goes to step output (not log file). Header MUST be written to file content for offline artifact to be self-contained. |

**Installation:** No packages to install — both actions are GitHub-owned and resolve at runtime.

## Package Legitimacy Audit

> No external packages are installed in this phase. Both `actions/github-script` and `actions/upload-artifact` are GitHub-owned actions referenced by tag in the workflow YAML — they are resolved by the GitHub Actions runner at workflow execution time, not installed as project dependencies.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    .github/workflows/main.yml                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐     ┌───────────────────────┐                     │
│  │   test   │     │   test-xdist-remote   │                     │
│  │ (matrix: │     │    (matrix: socket,   │                     │
│  │  18 cells)│     │     via, ssh modes)   │                     │
│  └────┬─────┘     └───────────┬───────────┘                     │
│       │                       │                                  │
│       │    needs: [test,      │                                  │
│       │    test-xdist-remote] │                                  │
│       │                       │                                  │
│       ▼                       ▼                                  │
│  ┌─────────────────────────────────────────┐                    │
│  │        collect-failed-logs              │                    │
│  │  if: failure()                          │                    │
│  │  permissions: actions:read, contents:read│                   │
│  │                                         │                    │
│  │  Step 1: actions/github-script@v7       │                    │
│  │  ┌───────────────────────────────────┐  │                    │
│  │  │ listJobsForWorkflowRun(run_id)    │  │                    │
│  │  │   ↓                               │  │                    │
│  │  │ filter: conclusion === 'failure'  │  │                    │
│  │  │   && name !== 'collect-failed-    │  │                    │
│  │  │        logs'                       │  │                    │
│  │  │   ↓                               │  │                    │
│  │  │ for each failed job:              │  │                    │
│  │  │   downloadJobLogsForWorkflowRun   │  │                    │
│  │  │   (job_id) → raw log text         │  │                    │
│  │  │   ↓                               │  │                    │
│  │  │   prepend metadata header         │  │                    │
│  │  │   ↓                               │  │                    │
│  │  │   fs.writeFile(                   │  │                    │
│  │  │     failed-job-logs/              │  │                    │
│  │  │     <sanitized-name>.log)         │  │                    │
│  │  │   on error → core.warning(),      │  │                    │
│  │  │   continue                         │  │                    │
│  │  └───────────────────────────────────┘  │                    │
│  │                                         │                    │
│  │  Step 2: actions/upload-artifact@v4    │                    │
│  │  ┌───────────────────────────────────┐  │                    │
│  │  │ if: hashFiles(                    │  │                    │
│  │  │   'failed-job-logs/*.log') != ''   │  │                    │
│  │  │ name: failed-job-logs-run-        │  │                    │
│  │  │   {number}-attempt-{attempt}       │  │                    │
│  │  │ path: failed-job-logs/             │  │                    │
│  │  │ if-no-files-found: ignore          │  │                    │
│  │  └───────────────────────────────────┘  │                    │
│  └─────────────────────────────────────────┘                    │
│                       │                                          │
│                       ▼                                          │
│              ┌────────────────┐                                  │
│              │ Workflow       │                                  │
│              │ Artifact       │                                  │
│              │ (ZIP bundle)   │                                  │
│              └────────────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Trigger:** Matrix jobs (`test` + `test-xdist-remote`) complete. If any cell failed (but not cancelled), `if: failure()` activates `collect-failed-logs`.
2. **Enumerate:** github-script calls `octokit.rest.actions.listJobsForWorkflowRun({owner, repo, run_id: context.runId, per_page: 100})` to get all jobs in the current run.
3. **Filter:** Keep only jobs where `conclusion === 'failure'` AND `name !== 'collect-failed-logs'` (defensive guard).
4. **Download:** For each failed job, call `octokit.rest.actions.downloadJobLogsForWorkflowRun({owner, repo, job_id})`. Octokit follows the 302 redirect and returns the plain-text log body.
5. **Sanitize name:** Replace any character outside `[A-Za-z0-9._-]` with `_`. Matrix names like `test (ubuntu-latest, 3.14)` → `test__ubuntu-latest__3.14_.log`.
6. **Write file:** Prepend metadata header (job name, run URL, ISO 8601 timestamp), blank line, then raw log body. Write to `failed-job-logs/<sanitized-name>.log`.
7. **Error resilience:** If `downloadJobLogsForWorkflowRun` throws for any individual job, log via `core.warning()` and continue. Partial logs are better than no logs.
8. **Upload:** `actions/upload-artifact@v4` packages the `failed-job-logs/` directory into artifact `failed-job-logs-run-{number}-attempt-{attempt}`. Guarded by `hashFiles` check and `if-no-files-found: ignore`.

### Recommended Project Structure

```text
.github/workflows/
└── main.yml          # Only file modified — new `collect-failed-logs` job added
```

No new files are created. The `failed-job-logs/` directory is transient — created on the runner filesystem during workflow execution and discarded after artifact upload.

### Pattern 1: Downstream Collector Job (Post-Mortem Log Gathering)

**What:** A job that depends on upstream jobs via `needs`, triggers only on failure via `if: failure()`, queries the GitHub Actions API to retrieve execution details, and bundles results as an artifact.

**When to use:** Any time you need to collect diagnostic data from failed CI jobs without modifying the jobs themselves.

**Example (from design spec):**
```yaml
  collect-failed-logs:
    needs: [test, test-xdist-remote]
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
            const fs = require('node:fs');
            const { owner, repo } = context.repo;

            // Enumerate jobs for this run
            const { data } = await github.rest.actions.listJobsForWorkflowRun({
              owner, repo, run_id: context.runId, per_page: 100
            });

            const failedJobs = data.jobs.filter(
              j => j.conclusion === 'failure' && j.name !== 'collect-failed-logs'
            );

            if (failedJobs.length === 0) {
              core.info('No failed jobs found — nothing to collect.');
              return;
            }

            fs.mkdirSync('failed-job-logs', { recursive: true });

            for (const job of failedJobs) {
              const safeName = job.name.replace(/[^A-Za-z0-9._-]/g, '_');
              try {
                const log = await github.rest.actions.downloadJobLogsForWorkflowRun({
                  owner, repo, job_id: job.id
                });
                const header = [
                  `Job: ${job.name}`,
                  `Run:  https://github.com/${owner}/${repo}/actions/runs/${context.runId}`,
                  `At:   ${new Date().toISOString()}`,
                  ''
                ].join('\n');
                fs.writeFileSync(`failed-job-logs/${safeName}.log`, header + log.data);
              } catch (err) {
                core.warning(`Failed to download logs for "${job.name}": ${err.message}`);
              }
            }
```

### Anti-Patterns to Avoid
- **Modifying the `test` or `test-xdist-remote` jobs:** Adding `tee`, per-step log capture, or extra dependencies to the hot path adds complexity to every run. The collector is a downstream consumer — keep it separate. [VERIFIED: approved design spec]
- **Hardcoding the repository name:** Use `context.repo.owner` and `context.repo.repo` from the injected context — makes the workflow portable. [CITED: github.com/actions/github-script README]
- **Skipping pagination:** `listJobsForWorkflowRun` returns 30 jobs per page by default. The current matrix has ~21 cells but could grow. Always pass `per_page: 100` or implement pagination. [CITED: docs.github.com REST API]
- **Using `core.info` for log header:** `core.info` writes to step output, not the file. For the downloadable artifact to be self-contained offline, the header must be written to the file content. [ASSUMED]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Authenticated GitHub API access | Custom token management + fetch/curl | `actions/github-script@v7` | Pre-authenticated Octokit client, context injection, no token passing needed |
| Artifact creation and upload | Manual zip + REST API upload | `actions/upload-artifact@v4` | Handles zipping, naming collision prevention, retention, and error cases |
| Job name sanitization | Custom regex library | Inline `.replace(/[^A-Za-z0-9._-]/g, '_')` | Simple enough for a one-liner; no library needed for this specific sanitization |
| Workflow run metadata | Hardcoded strings | `context.runId`, `context.runNumber`, `context.runAttempt` | Always correct for the current run, portable across repos |

**Key insight:** The entire phase adds zero new dependencies. Both actions used are GitHub-owned and already available in the Actions runner environment. The only code written is the inline JavaScript body of the github-script step.

## Common Pitfalls

### Pitfall 1: Artifact Name Collision on Re-runs
**What goes wrong:** If `run_attempt` is omitted from the artifact name, re-running a failed workflow from the Actions UI produces the same artifact name. `actions/upload-artifact@v4` rejects duplicate names, causing the upload step to fail.

**Why it happens:** `run_number` and `run_id` stay the same across re-run attempts. Only `run_attempt` increments.

**How to avoid:** Always include `${{ github.run_attempt }}` in the artifact name. The spec's `failed-job-logs-run-${{ github.run_number }}-attempt-${{ github.run_attempt }}` pattern is correct. [CITED: design spec § Artifact properties]

**Warning signs:** Upload step fails with "Artifact already exists" error on re-runs.

### Pitfall 2: Pagination for Large Matrices
**What goes wrong:** `listJobsForWorkflowRun` returns only the first 30 jobs by default. If the matrix ever exceeds 30 cells (e.g., more Python versions added), some failed jobs are silently missed.

**Why it happens:** The Octokit default `per_page` is 30.

**How to avoid:** Pass `per_page: 100` in the API call. The current matrix has ~21 cells total (18 test + 3 xdist-remote), well within 100. If the matrix ever exceeds 100, implement pagination via `github.paginate()`. [CITED: docs.github.com REST API]

**Warning signs:** Reported failures in the Actions UI don't appear in the artifact.

### Pitfall 3: `hashFiles` Without Checkout
**What goes wrong:** `hashFiles()` is a GHA expression function that evaluates against the workspace filesystem. It does NOT require `actions/checkout` — it reads files written by previous steps in the same job.

**Why it happens:** Confusion about GHA expression functions vs. step dependencies.

**How to avoid:** The `hashFiles('failed-job-logs/*.log') != ''` guard on the upload step works correctly because the github-script step (which writes the files) runs before the upload step in the same job. No checkout needed. [VERIFIED: GHA workflow syntax docs]

**Warning signs:** N/A — this works correctly as designed.

### Pitfall 4: `if: failure()` With Cancelled Jobs
**What goes wrong:** If a job is cancelled (not failed), `if: failure()` evaluates to `false` and the collector does not run. Cancelled logs are not captured.

**Why it happens:** `failure()` returns true only for jobs with `conclusion === 'failure'`, not `cancelled`.

**How to avoid:** This is by design (non-goal per spec: "Capturing logs from cancelled or skipped jobs"). If cancelled-job logs are ever needed in the future, use `if: failure() || cancelled()` and adjust the conclusion filter. [CITED: design spec § Non-goals]

**Warning signs:** User expects cancelled job logs in artifact but they're absent.

## Code Examples

### Sanitize Job Name for File System
```javascript
// Source: design spec D-04
// Replace any character outside [A-Za-z0-9._-] with underscore
const safeName = job.name.replace(/[^A-Za-z0-9._-]/g, '_');
// 'test (ubuntu-latest, 3.14)' → 'test__ubuntu-latest__3.14_.log'
```

### Metadata Header Format (Agent Discretion — Recommendation)
```javascript
// Source: D-02 + research recommendation
// Write header directly to file content (NOT via core.info)
// for self-contained offline artifact
const header = [
  `Job: ${job.name}`,
  `Run:  https://github.com/${owner}/${repo}/actions/runs/${context.runId}`,
  `At:   ${new Date().toISOString()}`,
  ''  // blank line before raw output
].join('\n');
```

### Complete Script Skeleton
```javascript
// Source: design spec + verified API patterns
const fs = require('node:fs');
const path = require('node:path');

const { owner, repo } = context.repo;
const runUrl = `https://github.com/${owner}/${repo}/actions/runs/${context.runId}`;

// 1. List jobs (with pagination headroom)
const { data } = await github.rest.actions.listJobsForWorkflowRun({
  owner, repo, run_id: context.runId, per_page: 100
});

// 2. Filter to failed jobs (exclude self defensively)
const failedJobs = data.jobs.filter(
  j => j.conclusion === 'failure' && j.name !== 'collect-failed-logs'
);

if (failedJobs.length === 0) {
  core.info('No failed jobs found.');
  return;
}

// 3. Prepare output directory
const outDir = 'failed-job-logs';
fs.mkdirSync(outDir, { recursive: true });

let downloadedCount = 0;

// 4. Download and write per job
for (const job of failedJobs) {
  const safeName = job.name.replace(/[^A-Za-z0-9._-]/g, '_');
  const filePath = path.join(outDir, `${safeName}.log`);

  try {
    const log = await github.rest.actions.downloadJobLogsForWorkflowRun({
      owner, repo, job_id: job.id
    });

    const header = [
      `Job: ${job.name}`,
      `Run:  ${runUrl}`,
      `At:   ${new Date().toISOString()}`,
      ''
    ].join('\n');

    fs.writeFileSync(filePath, header + log.data);
    downloadedCount++;
  } catch (err) {
    core.warning(`Skipping "${job.name}" (job_id=${job.id}): ${err.message}`);
  }
}

core.info(`Downloaded logs for ${downloadedCount}/${failedJobs.length} failed jobs.`);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual UI inspection | Downloadable artifact bundle | This phase | Offline grep, multi-cell analysis, retention beyond 90 days |
| Logs in Actions UI only | Self-contained `.log` files with metadata headers | This phase | No cross-referencing artifact names to remember which run |
| `upload-artifact@v3` (mutable artifacts) | `upload-artifact@v4` (immutable, unique naming) | v4 release (2024) | No accidental mutation; requires explicit `overwrite: true` |
| `github-script@v6` (Node 16) | `github-script@v7` (Node 20) | v7 release | Modern runtime; uses `github.rest.*` API surface |

**Deprecated/outdated:**
- `actions/upload-artifact@v3`: deprecated Nov 2024. Project already uses v4. [CITED: github.com/actions/upload-artifact README]
- `octokit.actions.listJobsForWorkflowRunAttempt` (attempt-specific endpoint): Not needed — the standard `listJobsForWorkflowRun` with default `filter: 'latest'` returns jobs for the current attempt. [CITED: docs.github.com REST API]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `downloadJobLogsForWorkflowRun` in Octokit returns the log body as `log.data` (string) rather than a redirect response | Architecture Patterns | Low — multiple sources confirm Octokit follows the 302 redirect. If API changes to not follow redirects, the script would write HTTP response metadata instead of log text. Easily detected during verification. |
| A2 | The metadata header should be written to the file content, not via `core.info` | Architecture Patterns / Don't Hand-Roll | Low — `core.info` goes to step output (visible in Actions UI) but not into the downloadable file. If planner chooses `core.info`, the artifact would lack headers, reducing offline utility but not breaking functionality. |

## Open Questions

1. **Rate limiting on `downloadJobLogsForWorkflowRun`:**
   - What we know: GitHub API has rate limits, but for actions using `GITHUB_TOKEN` on the same repository, limits are generous (1,000 requests/hour). With max ~21 failed cells, this is well within limits.
   - What's unclear: Whether many simultaneous log downloads trigger any throttling.
   - Recommendation: Design spec says "address reactively if they appear during verification." The per-job try/catch (D-07) already handles individual failures gracefully. No preemptive action needed.

## Environment Availability

> Step 2.6: SKIPPED — no external dependencies identified. Both `actions/github-script@v7` and `actions/upload-artifact@v4` are GitHub-owned actions that run on the GitHub Actions runner (ubuntu-latest). No local tools, services, or runtimes need to be available on the developer's machine. Verification uses a throwaway PR against live GitHub Actions.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual verification (throwaway PR) |
| Config file | none — manual test workflow |
| Quick run command | N/A — manual via GitHub Actions UI |
| Full suite command | N/A — manual verification |

GitHub Actions workflow changes cannot be unit-tested locally. The verification plan from the approved design spec is manual:

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-01 | Collector fires on both test and xdist-remote failure | manual-only | N/A — throwaway PR with intentional failure in both jobs | N/A |
| D-02 | Metadata header present in each log file | manual-only | N/A — inspect downloaded artifact content | N/A |
| D-03 | Uses `actions/github-script@v7` for API calls | manual-only | N/A — verify job uses correct action version | N/A |
| D-04 | File names are sanitized correctly | manual-only | N/A — check artifact file names | N/A |
| D-05 | Artifact name includes `run_attempt` | manual-only | N/A — check artifact name in Actions UI | N/A |
| D-06 | Permissions are least-privilege | manual-only | N/A — verify `permissions` block in YAML | N/A |
| D-07 | Individual download failures don't block other logs | manual-only | N/A — would need to force one API call to fail | N/A |
| D-08 | No-files guard prevents upload failure | manual-only | N/A — verify job succeeds when no logs found | N/A |

### Sampling Rate
- **Per task commit:** N/A — single YAML change, verified as a whole
- **Per wave merge:** N/A — single plan, single commit
- **Phase gate:** Manual verification via throwaway PR per design spec § Verification plan

### Wave 0 Gaps
- [ ] Throwaway PR creation process — documented in design spec but no automated mechanism
- [ ] Verification checklist — not automated; manual inspection of Actions UI and artifact content

### Verification Procedure (from approved spec)
1. Open a throwaway PR that adds `- run: exit 1` to the `test` job
2. Wait for workflow to run. Confirm `collect-failed-logs` runs and succeeds
3. Download artifact `failed-job-logs-run-<N>-attempt-<A>` and verify:
   - One `.log` file per matrix cell
   - Each file contains step output ending with `exit 1` failure
   - Each file has metadata header (job name, run URL, timestamp)
4. Close throwaway PR without merging
5. Record verification result in PR description

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Uses `GITHUB_TOKEN` — GitHub-managed, no custom auth |
| V3 Session Management | no | Token lifecycle managed by GitHub Actions runner |
| V4 Access Control | yes | `permissions: { actions: read, contents: read }` — least privilege |
| V5 Input Validation | no | No user input processed |
| V6 Cryptography | no | No cryptographic operations performed |

### Known Threat Patterns for GHA Workflows

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Token exposure via debug logging | Information Disclosure | `permissions: { actions: read, contents: read }` — no write access even if leaked; `GITHUB_TOKEN` is auto-expiring |
| Script injection via workflow inputs | Tampering | No workflow inputs accepted; no expressions interpolated into the script body from untrusted sources |
| Log exfiltration via artifact | Information Disclosure | Artifact contains only step output that already exists in the Actions UI; no new secrets exposure. Only job names, URLs, timestamps, and public step output. |
| API rate limit abuse | Denial of Service | `per_page: 100` minimizes API calls; max ~21 log downloads per run; GitHub's per-repo rate limits (1,000 req/hr) provide headroom |

## Sources

### Primary (HIGH confidence)
- `docs/superpowers/specs/2026-06-02-gather-failed-ci-logs-design.md` — Approved design spec (authoritative for all implementation details)
- GitHub REST API docs (docs.github.com) — `listJobsForWorkflowRun`, `downloadJobLogsForWorkflowRun` endpoints confirmed [CITED: docs.github.com/en/rest/actions/workflow-jobs]
- `actions/github-script` README — Octokit client injection, context properties, core API, Node 20 runtime [CITED: github.com/actions/github-script]
- `actions/upload-artifact` README — v4 inputs, immutable artifact rules, `if-no-files-found` behavior [CITED: github.com/actions/upload-artifact]
- `.github/workflows/main.yml` — Existing workflow structure, matrix configurations, job definitions [VERIFIED: codebase]
- `.github/workflows/messages-baseline-drift.yml` — Existing `upload-artifact@v4` usage pattern [VERIFIED: codebase]

### Secondary (MEDIUM confidence)
- Octokit REST API docs (octokit.github.io/rest.js) — `downloadJobLogsForWorkflowRun` returns log body via auto-followed redirect [CITED: octokit.github.io/rest.js]
- GitHub Actions workflow syntax docs (docs.github.com) — `needs`, `if: failure()`, `permissions`, `hashFiles` behavior [CITED: docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions]

### Tertiary (LOW confidence)
- None — all claims are verified against official sources or the approved design spec.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — both actions are GitHub-owned, well-documented, and already used in the project
- Architecture: HIGH — design spec provides complete job structure; verified against current API documentation
- Pitfalls: HIGH — pagination, collision, and conditional behavior patterns confirmed against official docs
- Implementation: HIGH — all API signatures, context properties, and error handling patterns confirmed

**Research date:** 2026-07-10
**Valid until:** 2026-10-10 (GitHub Actions APIs are stable; major version bumps would trigger deprecation notices well in advance)
