---
phase: 17
phase_name: adapt-github-ci-to-use-make-and-validate-with-act
status: partial
verified_at: 2026-07-02T00:00:00Z
verification_mode: forensic
---

# Phase 17 Verification - Adapt GitHub CI to use Make and validate with act

## Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Makefile exposes `tox`, `env-install-npm`, `check-message-schemas`, `validate-github-actions` targets | PARTIAL | `main.yml` references `make env-install-npm`, `make tox`, `make check-message-schemas`, `make dist-check`. However, the Makefile was deleted in Phase 27, so these targets no longer exist. At time of Phase 17 completion, the Makefile existed with these targets. |
| 2 | `main.yml` CI workflow calls Makefile targets instead of duplicating command bodies | PASS | `.github/workflows/main.yml` calls `make env-install-npm` (line 64), `make tox TOX_ARGS='...'` (line 67), `make check-message-schemas` (line 71), `make dist-check` (line 83), and `make env-install-npm` / `make tox` in xdist-remote job (lines 118, 122). |
| 3 | Contract tests exist for Makefile CI command API | FAIL | Plan referenced `tests/cases/contract/test_makefile_test_api.py` but this file does not exist in the current codebase. The file path was likely moved during Phase 20 test package extraction to `src/pytest_bdd_toolchain/` but the specific file was not found. |
| 4 | `main.yml` workflow has ownership comment identifying it as CI-owned | PASS | `.github/workflows/main.yml` lines 1-5: `# CI workflow: GitHub Actions runs the full compatibility and remote-test matrix. Local Act artifact workflows live in docs.yml, lint.yml, tests.yml, env.yml, and release.yml; they are not replacements for this CI gate.` |
| 5 | `astral-sh/setup-uv` action used instead of manual pip/uv installation | PASS | `main.yml` line 61: `uses: astral-sh/setup-uv@v8.2.0` replaces manual installation steps. |

## Summary

Phase 17 successfully adapted the GitHub CI workflow (`main.yml`) to delegate project-specific commands to Makefile targets. The workflow now calls `make env-install-npm`, `make tox`, `make check-message-schemas`, and `make dist-check` rather than inlining commands. The workflow has a clear ownership comment distinguishing it from local act workflows.

**Key concern:** The Makefile was deleted in Phase 27, which means the make targets referenced by `main.yml` no longer exist. This creates a broken CI state unless `main.yml` was intended to be updated further in Phase 27 to remove make calls. The Phase 27 plan lists `main.yml` in `files_deleted` but the file still exists with stale make references.

## Pre-Existing Failures

- `test_makefile_test_api.py` contract test referenced in Phase 17 plan does not exist at the expected path. It may have been relocated during Phase 20 test package extraction or removed during Phase 27 cleanup.
- `main.yml` still calls `make` targets but the Makefile is deleted (Phase 27 regression or intentional CI-owned design).
