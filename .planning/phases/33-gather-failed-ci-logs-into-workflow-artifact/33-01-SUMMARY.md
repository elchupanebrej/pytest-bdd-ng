---
phase: 33-gather-failed-ci-logs-into-workflow-artifact
plan: "01"
subsystem: infra
tags: [github-actions, yaml, octokit, upload-artifact, github-script]

# Dependency graph
requires: []
provides:
  - Failed job logs downloadable as a single artifact named `failed-job-logs-run-{number}-attempt-{attempt}` from the Actions UI after any main.yml run with failures
affects: [CI workflow debugging workflow, future CI pipeline improvements]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Downstream collector job pattern (needs + `if: failure()` trigger for post-mortem log gathering without modifying hot-path jobs)
    - Inline github-script with Octokit for authenticated GitHub REST API calls within a workflow job
    - upload-artifact@v4 with `hashFiles` guard and `if-no-files-found: ignore` for resilient artifact uploads

key-files:
  created: []
  modified:
    - .github/workflows/main.yml

key-decisions:
  - "Metadata header written to log file content (not core.info) for self-contained offline artifacts"
  - "Long inline JS lines broken with string concatenation and chained method calls to satisfy yamllint line-length rule"
  - "Artifact name line uses `# yamllint disable-line rule:line-length` pragma (matching existing `on:` pragma pattern)"
  - "`fs` and `path` imported via `node:` prefix for clarity (Node.js stdlib modules)"

patterns-established:
  - "Pattern: Downstream Collector Job — a job that depends on upstream jobs via `needs`, triggers only on failure via `if: failure()`, queries the GitHub Actions API, and bundles results as an artifact"

requirements-completed: []

# Coverage metadata
coverage:
  - id: D1
    description: "New `collect-failed-logs` job added to main.yml that fires on failure, downloads logs for failed matrix cells via Octokit, prepends metadata headers, and uploads as a single artifact"
    verification:
      - kind: manual_procedural
        ref: "yamllint .github/workflows/main.yml"
        status: pass
    human_judgment: true
    rationale: "GitHub Actions workflow YAML changes cannot be unit-tested locally. Functional verification requires a throwaway PR with intentional failure against live GitHub Actions (per design spec §Verification plan). YAML syntax and formatting are verified locally; runtime behavior requires human UAT."

# Metrics
duration: 7min
completed: 2026-07-10
status: complete
---

# Phase 33 Plan 01: Gather Failed CI Logs into Workflow Artifact Summary

**Add `collect-failed-logs` downstream job to main.yml CI workflow that downloads raw step output for every failed matrix cell via `actions/github-script@v7` and bundles them as a single `actions/upload-artifact@v4` artifact with self-contained metadata headers**

## Performance

- **Duration:** 7 min
- **Started:** 2026-07-10T12:46:49Z
- **Completed:** 2026-07-10T12:54:05Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- New `collect-failed-logs` job appended to `.github/workflows/main.yml` after `test-xdist-remote` with zero changes to existing `test` or `test-xdist-remote` jobs
- Job fires on `failure()` via `needs: [test, test-xdist-remote]` — captures logs from both matrix jobs in a single artifact bundle
- Step 1 (`actions/github-script@v7`): enumerates all failed jobs via `octokit.rest.actions.listJobsForWorkflowRun` with `per_page: 100`, filters by `conclusion === 'failure'` (with defensive self-exclusion), and downloads each log via `octokit.rest.actions.downloadJobLogsForWorkflowRun`
- Each `.log` file prepends a metadata header (job name, run URL, ISO 8601 timestamp, blank line) before the raw step output — fully self-contained for offline investigation
- Filenames sanitized: characters outside `[A-Za-z0-9._-]` → `_` (e.g., `test (ubuntu-latest, 3.14)` → `test__ubuntu-latest__3.14_.log`)
- Step 2 (`actions/upload-artifact@v4`): bundles `failed-job-logs/` directory with `hashFiles` guard and `if-no-files-found: ignore` for resilient upload
- Artifact name: `failed-job-logs-run-${{ github.run_number }}-attempt-${{ github.run_attempt }}` — includes `run_attempt` to avoid collision on UI re-runs
- Permissions scoped to `actions: read, contents: read` — least-privilege, no write tokens or secrets
- Per-job download errors logged via `core.warning()` — loop continues, partial logs collected

## Task Commits

Each task was committed atomically:

1. **Task 1: Add collect-failed-logs job to main.yml** - `180751d` (feat)

## Files Created/Modified

- `.github/workflows/main.yml` — New `collect-failed-logs` job added after line 124 (77 insertions, 0 deletions). Two steps: github-script download + upload-artifact bundle. All 10 locked decisions satisfied.

## Decisions Made

- Metadata header written directly to log file content (not `core.info`) — ensures downloadable artifact is self-contained offline without needing cross-reference to the Actions UI
- Long inline JavaScript lines broken with string concatenation and chained method calls to satisfy yamllint `line-length` rule without changing semantics
- Artifact name line uses inline `# yamllint disable-line rule:line-length` pragma — matches the project's existing convention (`on:  # yamllint disable-line rule:truthy` on line 8) for expressions that can't be broken across lines
- `node:fs` and `node:path` imported via `node:` prefix for clarity (Node.js stdlib modules)

## Deviations from Plan

None — plan executed exactly as written. All 10 locked decisions (D-01 through D-10) implemented as specified in the plan and CONTEXT.md.

## Issues Encountered

None. One trivial adjustment: long inline JavaScript lines in the github-script body were broken into shorter multi-line expressions to pass yamllint `line-length` (80-char) rule. This is a formatting-only change with zero behavioral impact — the same template literals, API calls, and error handling are preserved.

## User Setup Required

None — no external service configuration required. Both actions (`actions/github-script@v7`, `actions/upload-artifact@v4`) are GitHub-owned and resolve at runtime on the GitHub Actions runner. No local tools, API keys, or environment variables needed for the developer.

## Next Phase Readiness

- Plan 33-01 is the only plan in Phase 33 — phase complete
- Functional verification requires a throwaway PR with intentional failure against live GitHub Actions (per design spec §Verification plan)
- Ready for `/gsd-verify-work 33` to confirm runtime behavior

---
*Phase: 33-gather-failed-ci-logs-into-workflow-artifact*
*Completed: 2026-07-10*
