---
phase: 20-multiple-refactorings
plan: 27
subsystem: testing
tags: [docker, compose, cleanup, path-fix]

# Dependency graph
requires:
  - phase: 20-26
    provides: pytest_bdd_testing package at src/pytest_bdd_testing/
provides:
  - Clean repo with no tests/ directory
  - Docker compose with correct 5-level context depth
  - All Dockerfiles using pytest_bdd_testing paths
  - Makefile without tests/ references
affects: [20-28-eliminate-all-and-empty-init, 20-29-update-init-rules]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - src/pytest_bdd_testing/assets/docker/remote_xdist/docker-compose.yml
    - src/pytest_bdd_testing/assets/docker/remote_xdist/controller.Dockerfile
    - src/pytest_bdd_testing/assets/docker/remote_xdist/worker.Dockerfile
    - src/pytest_bdd_testing/cases/external/e2e/test_xdist_remote_message_aggregation.py
    - src/pytest_bdd_testing/cases/unit/test_test_suite_classification.py
    - src/pytest_bdd_testing/docker_cluster.py
    - Makefile

key-decisions:
  - "Removed COPY tests/* lines from Dockerfiles — tests/ directory deleted per R3"
  - "Updated pip install to include testing extra in Dockerfiles"

patterns-established: []

requirements-completed: [R3, R4]

# Metrics
duration: 10min
completed: 2026-06-10
---

# Phase 20 Plan 27: Docker/CI Path Fixes Summary

**Removed duplicate tests/ directory at repo root (372 files), fixed all Docker compose/Dockerfile paths for new pytest_bdd_testing location, and cleaned up Makefile references**

## Performance

- **Duration:** 10 min
- **Started:** 2026-06-10
- **Completed:** 2026-06-10
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Fixed docker-compose.yml path references from pytest_bdd/testing to pytest_bdd_testing
- Updated controller.Dockerfile: removed COPY tests/* lines, added COPY src/pytest_bdd_testing paths, updated pip install to include testing extra
- Updated worker.Dockerfile: same pattern as controller
- Fixed FIXTURE_DIR in test_xdist_remote_message_aggregation.py: parents[5] with src/pytest_bdd_testing path
- Fixed tests.assets references to pytest_bdd_testing.assets in test file
- Fixed docker_cluster.py entrypoint path reference
- Updated Makefile: removed tests/ from ruff-check, typing_rules, and format targets
- Deleted entire tests/ directory (372 files, 39645 lines)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix Docker files for new package layout** — `175f7438` (feat)
2. **Task 2: Delete tests/ directory and final verification** — `bfaadb63` (feat)

## Files Created/Modified

- `src/pytest_bdd_testing/assets/docker/remote_xdist/docker-compose.yml` — Fixed path references
- `src/pytest_bdd_testing/assets/docker/remote_xdist/controller.Dockerfile` — Removed tests/ COPY, updated paths
- `src/pytest_bdd_testing/assets/docker/remote_xdist/worker.Dockerfile` — Same as controller
- `src/pytest_bdd_testing/cases/external/e2e/test_xdist_remote_message_aggregation.py` — Fixed FIXTURE_DIR and module refs
- `src/pytest_bdd_testing/cases/unit/test_test_suite_classification.py` — Updated test assertions for new paths
- `src/pytest_bdd_testing/docker_cluster.py` — Fixed entrypoint path
- `Makefile` — Removed tests/ from ruff-check, typing_rules, format targets
- `tests/` — Deleted entire directory (372 files)

## Decisions Made

- Removed COPY tests/* lines from Dockerfiles — tests/ directory deleted per R3 requirement
- Updated pip install to include testing extra in Dockerfiles — ensures pytest_bdd_testing is available in containers
- Fixed FIXTURE_DIR path computation: parents[5] instead of parents[6] — pytest_bdd_testing is one level shallower than pytest_bdd/testing was

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- tests/ directory deleted — R3 requirement satisfied
- Docker compose functional at new location — R4 requirement satisfied
- Plan 20-28 (Eliminate __all__ and empty __init__.py) can proceed
- Plan 20-29 (Update init_rules.py) can proceed

---

*Phase: 20-multiple-refactorings*
*Completed: 2026-06-10*
