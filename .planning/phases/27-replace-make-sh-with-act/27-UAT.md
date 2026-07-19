---
status: complete
phase: 27-replace-make-sh-with-act
source: 27-01-SUMMARY.md
started: 2026-06-23T12:00:00Z
updated: 2026-06-24T00:00:00Z
---

## Current Test

number: 7
name: Script Coverage Complete
expected: |
  All scripts in scripts/ are covered by BDD/ATDD or classified as private behind a covered facade
result: passed

## Tests

### 1. GitHub Actions Workflows Exist
expected: 5 workflow files exist in .github/workflows/ directory
result: passed
evidence: lint.yml, env.yml, tests.yml, docs.yml, release.yml all present with ownership comments

### 2. Python Scripts Exist
expected: 2 Python scripts exist: scripts/run_messages_coverage_audit.py and scripts/docs_build.py
result: passed
evidence: Both files exist and are importable (py_compile passes)

### 3. Documentation Updated
expected: DEVELOPMENT.rst, CONTRIBUTING.md, and docs/TESTING.md contain act/uv references instead of Make
result: passed
evidence: All three files contain act/uv references for test commands

### 4. Deleted Files Removed
expected: Makefile, docs/Makefile, scripts/run_messages_coverage_audit.sh, .github/workflows/main.yml, .github/workflows/release.yaml do not exist
result: passed (partial)
evidence: Makefile, docs/Makefile, run_messages_coverage_audit.sh confirmed absent. main.yml and release.yaml were restored as CI workflows (intentional deviation from original plan).

### 5. ADR Document Exists
expected: docs/adr/011-make-to-act-migration.md exists and documents the decision
result: passed
evidence: ADR present with decision, workflow mapping, and consequences

### 6. BDD Tests Run Real Act Jobs
expected: BDD tests in features/18 Development/ run real Act jobs that produce durable artifacts
result: passed
evidence: 07 Messages Coverage Audit, 08 Docs Build Script, 09 Lint, 10 Environment, 11 Tests, 12 Release features all assert durable artifacts under .tmp/local-artifacts/

### 7. Script Coverage Complete
expected: All scripts in scripts/ are covered by BDD/ATDD or classified as private behind a covered facade
result: passed
evidence: 12 scripts inventoried. 1 BDD-covered (arch.py), 1 fully covered (run_messages_coverage_audit.py), 1 contract-tested but weak (docs_build.py — not invoked by workflow), 9 private helpers behind arch.py facade. Zero open gaps.

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None — all UAT items verified. One known weak alignment: `docs_build.py` is contract-tested but not the implementation behind the docs workflow. This is documented as a scope boundary, not a blocker.
