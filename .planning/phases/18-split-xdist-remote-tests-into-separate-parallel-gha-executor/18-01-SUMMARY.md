---
phase: 18-split-xdist-remote-tests-into-separate-parallel-gha-executor
plan: 01
subsystem: ci
tags: [github-actions, tox, docker, xdist-remote, make]

requires:
  - phase: 17-adapt-github-ci-to-use-make-and-validate-with-act
    provides: GitHub Actions uses Makefile command boundaries
provides:
  - Dedicated parallel GitHub Actions job for xdist-remote tox environments
  - Makefile tox argument forwarding through TOX_ARGS
  - Docker setup and diagnostic checks before xdist-remote tox execution
affects: [github-actions, tox, ci, xdist-remote]

tech-stack:
  added: []
  patterns:
    - GitHub Actions tox invocations go through make tox with TOX_ARGS
    - Docker-backed xdist-remote environments run in a dedicated matrix job

key-files:
  created: []
  modified:
    - Makefile
    - .github/workflows/main.yml

key-decisions:
  - "Preserve the Phase 17 Makefile boundary by forwarding tox options with TOX_ARGS."
  - "Run xdist-remote environments in a separate two-OS by three-mode matrix with fail-fast disabled."

patterns-established:
  - "Use TOX_ARGS for workflow-specific tox filtering without changing tox.ini."
  - "Validate Docker availability before starting Docker-backed tox work."

requirements-completed: []

duration: 10 min
completed: 2026-06-02
---

# Phase 18 Plan 01: Split xdist-remote GitHub Actions job Summary

**GitHub Actions xdist-remote tox environments split into a dedicated Docker-verified parallel matrix job**

## Performance

- **Duration:** 10 min
- **Started:** 2026-06-02T21:45:32Z
- **Completed:** 2026-06-02T21:55:31Z
- **Tasks:** 4
- **Files modified:** 2

## Accomplishments

- Added `TOX_ARGS ?=` and forwarded it through the Makefile `tox` target.
- Updated the main `test` GitHub Actions job to skip `xdist-remote-.*` tox environments.
- Added `test-xdist-remote` as a parallel GitHub Actions job with six matrix cells, Docker setup, Docker diagnostics, npm dependency install, and targeted tox execution.

## Task Commits

Planned CI changes were committed together because the four tasks modify one workflow boundary and one workflow file.

1. **Tasks 18-01-01 through 18-01-04: Split xdist-remote CI job** - `512e030a` (`ci(18-01): split xdist remote workflow job`)

## Files Created/Modified

- `Makefile` - Adds `TOX_ARGS ?=` and forwards `$(TOX_ARGS)` in the `tox` target.
- `.github/workflows/main.yml` - Skips xdist-remote envs in the main test job and adds the dedicated `test-xdist-remote` matrix job.

## Decisions Made

- Preserved the Makefile command boundary by using `make tox TOX_ARGS=...` instead of invoking tox directly in GitHub Actions.
- Used a shell-computed `target_env` to keep workflow lines yamllint-compliant while still selecting the exact xdist-remote tox environment.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope change.

## Issues Encountered

- Initial commit attempt failed yamllint because the generated tox environment command exceeded 80 columns. The workflow command was split into shell variable construction and revalidated.
- `make validate-github-actions` fails under PowerShell because the Makefile requires Git Bash on Windows. Re-ran the same target through Git Bash and it passed.

## Verification

- `uvx --with ruamel.yaml python -c "from ruamel.yaml import YAML; YAML(typ='safe').load(open('.github/workflows/main.yml', encoding='utf-8'))"` - PASS
- `uvx --with tox-uv tox -l` filtered for `xdist-remote` - PASS, exactly 6 environments:
  - `py314-pytestlatest-xdist-remote-socket-lin`
  - `py314-pytestlatest-xdist-remote-socket-win`
  - `py314-pytestlatest-xdist-remote-via-lin`
  - `py314-pytestlatest-xdist-remote-via-win`
  - `py314-pytestlatest-xdist-remote-ssh-lin`
  - `py314-pytestlatest-xdist-remote-ssh-win`
- `make -n tox` through Git Bash - PASS, default command remains `uvx --with tox-uv tox`
- `make validate-github-actions` through Git Bash - PASS, `act --validate` completed
- Matrix structure check - PASS, `test-xdist-remote` has no `needs`, `fail-fast: false`, two OS values, three mode values, and six cells

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 18 implementation is ready for phase verification and post-push GitHub Actions UI confirmation that six `test-xdist-remote` cells run in parallel with the main `test` job and no xdist-remote tox env runs twice.

## Self-Check: PASSED

- Key files exist on disk.
- Plan commit exists: `512e030a`.
- Acceptance criteria and plan verification checks passed.

---
*Phase: 18-split-xdist-remote-tests-into-separate-parallel-gha-executor*
*Completed: 2026-06-02*
