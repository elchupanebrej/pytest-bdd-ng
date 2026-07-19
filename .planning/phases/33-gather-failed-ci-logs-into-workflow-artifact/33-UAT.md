---
status: complete
phase: 33-gather-failed-ci-logs-into-workflow-artifact
source: 33-01-SUMMARY.md
started: 2026-07-10T13:00:00Z
updated: 2026-07-11T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Collect-Failed-Logs Job Bundles Crash Logs from Failed CI Runs
expected: (1) Local: `yamllint .github/workflows/main.yml` passes with zero errors (verified: PASS). (2) Live: Push a throwaway branch with an intentional test failure to GitHub. The `collect-failed-logs` job fires after `test` or `test-xdist-remote` fails, downloads raw step logs for each failed matrix cell, prepends metadata headers (job name, run URL, ISO 8601 timestamp), and uploads a single artifact named `failed-job-logs-run-{N}-attempt-{M}` containing `failed-job-logs/*.log` files. The artifact is downloadable from the Actions UI and each .log file is self-contained with its metadata header.
result: pass

## Summary

total: 1
passed: 1
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
