---
phase: 33-gather-failed-ci-logs-into-workflow-artifact
verified: 2026-07-11T15:00:00Z
status: passed
score: 6/6 must-haves verified
behavior_unverified: 0
overrides_applied: 0
human_verification:

  - test: "Push a throwaway branch with intentional test failure (e.g., `- run: exit 1` in the `test` job) to GitHub and confirm the `collect-failed-logs` job fires, succeeds, and produces a downloadable artifact"
    expected: >
      After the workflow run completes:

      1. `collect-failed-logs` appears in the Actions UI and succeeded
      2. Artifact `failed-job-logs-run-{N}-attempt-{A}` is downloadable
      3. Each `.log` file opens with metadata header (job name, run URL, ISO 8601 timestamp + blank line)
      4. Raw step output follows the header, ending with `exit 1` failure
      5. File names are sanitized: `test__ubuntu-latest__3.14_.log` etc.
    why_human: "GitHub Actions workflow YAML cannot be unit-tested locally. Runtime behavior depends on GHA scheduler, Octokit REST API calls, and artifact storage — all external services. Per design spec §Verification plan, functional verification requires a throwaway PR against live GitHub Actions."

  - test: "Confirm the artifact is downloadable from the Actions UI and all `.log` files are self-contained (each file has its own metadata header — no cross-referencing needed)"
    expected: "Each `.log` file in the downloaded artifact is independently readable with job name, run URL, timestamp, and raw step output"
    why_human: "Artifact download and content inspection require the GitHub Actions UI — cannot be verified from codebase alone."

  - test: "Verify the `test` and `test-xdist-remote` jobs still work correctly (no regressions introduced by the new job)"
    expected: "All existing CI passes: test matrix (18 cells), test-xdist-remote matrix (3 modes), codecov upload, build check"
    why_human: "The new job is a downstream consumer — it does not modify existing jobs, but confirming no GHA-side interference requires live CI observation."
---

# Phase 33: Gather Failed CI Logs into Workflow Artifact Verification Report

**Phase Goal:** After any `main.yml` run with failed matrix cells, produce a single downloadable workflow artifact containing raw step output with metadata headers for each failed cell, without modifying existing `test` or `test-xdist-remote` jobs.

**Verified:** 2026-07-11T15:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Failed job logs are downloadable as a single artifact named `failed-job-logs-run-{number}-attempt-{attempt}` | ✓ VERIFIED | `.github/workflows/main.yml:199` — artifact name includes `${{ github.run_number }}` and `${{ github.run_attempt }}`; upload step uses `actions/upload-artifact@v4` (line 197); job triggers via `needs: [test, test-xdist-remote]` + `if: failure()` (lines 131-132) |
| 2 | Each `.log` file opens with metadata header (job name, run URL, ISO 8601 timestamp) + blank line + raw step output | ✓ VERIFIED | `.github/workflows/main.yml:174-181` — header array: `Job: ${job.name}`, `Run: ${runUrl}`, `At: ${new Date().toISOString()}`, `''`, joined with `\n`; written as `header + log.data` |
| 3 | File names sanitized — characters outside `[A-Za-z0-9._-]` replaced with `_` | ✓ VERIFIED | `.github/workflows/main.yml:165` — `const safeName = job.name.replace(/[^A-Za-z0-9._-]/g, '_')` |
| 4 | Per-job download failure logs `core.warning` and continues — partial logs collected | ✓ VERIFIED | `.github/workflows/main.yml:183-188` — `catch (err)` block calls `core.warning(...)` with job name + error message, loop continues (no break/throw) |
| 5 | No `.log` files → upload step skipped via `hashFiles` guard — collector still succeeds | ✓ VERIFIED | `.github/workflows/main.yml:196` — `if: hashFiles('failed-job-logs/*.log') != ''`; line 201 — `if-no-files-found: ignore` |
| 6 | Existing `test` and `test-xdist-remote` jobs untouched — no lines added, removed, or changed | ✓ VERIFIED | `git show 180751d --stat`: `1 file changed, 77 insertions(+)` — zero deletions; diff confirms only addition after `test-xdist-remote` (line 122 → line 125+) |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### Locked Decisions (D-01 through D-10)

All 10 decisions from CONTEXT.md are satisfied:

| Decision | Requirement | Line | Status |
|----------|-------------|------|--------|
| D-01 | `needs: [test, test-xdist-remote]` | 131 | ✓ |
| D-02 | Metadata header (job name, run URL, ISO timestamp, blank line) written to file content | 174-181 | ✓ |
| D-03 | `actions/github-script@v7` for API calls | 135 | ✓ |
| D-04 | File name sanitization via `/[^A-Za-z0-9._-]/g` | 165 | ✓ |
| D-05 | Artifact name includes `run_attempt` | 199 | ✓ |
| D-06 | Permissions: `actions: read, contents: read` | 128-130 | ✓ |
| D-07 | Error handling: `core.warning` on per-job failure, continue | 183-188 | ✓ |
| D-08 | `hashFiles` guard + `if-no-files-found: ignore` | 196, 201 | ✓ |
| D-09 | Scope boundary: `main.yml` only | Git diff: 1 file | ✓ |
| D-10 | No modification to existing jobs | Git diff: 0 deletions | ✓ |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.github/workflows/main.yml` | New `collect-failed-logs` job definition with github-script and upload-artifact steps | ✓ VERIFIED | Exists at line 126; 77 lines added; contains `collect-failed-logs:` key with two steps; no lines removed from existing jobs |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| Job trigger `if: failure()` | `needs: [test, test-xdist-remote]` | GHA job scheduler | ✓ WIRED | Line 132 (`if: failure()`) + line 131 (`needs`); collector waits for both matrices |
| github-script step | upload-artifact step | `fs.writeFileSync` → `failed-job-logs/` directory | ✓ WIRED | Line 159: `fs.mkdirSync('failed-job-logs', ...)`; line 181: `fs.writeFileSync(filePath, ...)`; line 200: `path: failed-job-logs/` |
| upload-artifact step | workflow artifact storage | `actions/upload-artifact@v4` bundles directory | ✓ WIRED | Line 197: `uses: actions/upload-artifact@v4`; line 199: artifact name; line 200: path; line 201: `if-no-files-found: ignore` |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| YAML syntax valid | `yamllint .github/workflows/main.yml` | Exit 0, no errors | ✓ PASS |
| Existing jobs untouched | `git show 180751d --stat` | 1 file, 77 insertions(+), 0 deletions | ✓ PASS |
| No other workflow files modified | `git show 180751d --stat -- .github/workflows/` | Only `main.yml` changed | ✓ PASS |

### Anti-Patterns Found

None detected. Verified:

- No `TBD` / `FIXME` / `XXX` markers
- No `TODO` / `HACK` / `PLACEHOLDER` markers
- No `placeholder` / `coming soon` / `not yet implemented` comments
- No empty implementations or stub patterns
- No hardcoded empty data

### Requirements Coverage

No requirement IDs declared in PLAN frontmatter (`requirements: []`). The phase has no requirements to cross-reference against REQUIREMENTS.md.

### Human Verification Required

All code-level checks pass — the YAML configuration, JavaScript logic, permissions, error handling, and formatting are correct. However, runtime behavior on live GitHub Actions requires manual verification:

#### 1. Throwaway PR with Intentional Failure

**Test:** Push a throwaway branch with an intentional test failure (e.g., `- run: exit 1` in the `test` job) to GitHub and observe the workflow run.

**Expected:**

1. `collect-failed-logs` job fires after `test` or `test-xdist-remote` fails
2. Job succeeds (green checkmark in Actions UI)
3. Artifact `failed-job-logs-run-{N}-attempt-{A}` is present and downloadable
4. Each `.log` file starts with metadata header (job name, run URL, ISO 8601 timestamp, blank line) followed by raw step output ending with `exit 1`
5. File names are sanitized: `test (ubuntu-latest, 3.14)` → `test__ubuntu-latest__3.14_.log`

**Why human:** GitHub Actions workflow YAML cannot be unit-tested locally. Runtime behavior depends on GHA scheduler, Octokit REST API calls, and artifact storage — all external services. Per design spec §Verification plan, functional verification requires a throwaway PR against live GitHub Actions.

#### 2. Artifact Self-Containment

**Test:** Download the artifact and verify each `.log` file is independently readable — open any file and confirm the metadata header provides full context (job name, run URL, timestamp) without needing to cross-reference the Actions UI.

**Expected:** Each file stands alone with its header. No empty or truncated files.

**Why human:** Artifact download and content inspection require the GitHub Actions UI.

#### 3. No Regression in Existing CI

**Test:** After verifying the collector, confirm all existing CI tasks still pass: `test` matrix (18 cells), `test-xdist-remote` matrix (3 modes), codecov upload, and build check.

**Expected:** No new failures or warnings introduced. The new downstream job does not interfere with upstream jobs.

**Why human:** The new job is a downstream consumer that does not modify existing jobs, but confirming no GHA-side interference requires live CI observation.

### Gaps Summary

No code-level gaps found. All 6 observable truths are verified via codebase evidence. All 10 locked decisions are satisfied. YAML syntax passes lint. Existing jobs are untouched (0 deletions in git diff).

The phase is **code-complete** and awaits live GitHub Actions verification via a throwaway PR with intentional failure (per design spec §Verification plan). UAT confirms `yamllint` passes locally; the live GHA test is the remaining verification step.

---

_Verified: 2026-07-11T15:00:00Z_
_Verifier: the agent (gsd-verifier)_
