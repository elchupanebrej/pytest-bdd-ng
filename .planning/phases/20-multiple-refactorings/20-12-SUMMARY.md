---
phase: 20-multiple-refactorings
plan: 12
subsystem: documentation
tags: [how-to-guides, migration, sphinx, myST]

requires:
  - phase: 20-multiple-refactorings
    plan: 11
    provides: Architectural layer definitions and enforcement rules documented
provides:
  - 5 user-facing how-to guides in docs/guides/
  - Sphinx toctree integration via docs/index.md
affects: [user-documentation, onboarding]

tech-stack:
  added: []
  patterns:
    - "problem → solution → example → mistakes format for how-to guides"
    - "Sphinx MyST Markdown toctree with glob and maxdepth"

key-files:
  created:
    - docs/guides/01-custom-gherkin-parser.md
    - docs/guides/02-structured-bdd-yaml-json.md
    - docs/guides/03-parallel-execution-xdist.md
    - docs/guides/04-custom-formatter-plugin.md
    - docs/guides/05-migration-from-v1.md
    - docs/guides/index.md
  modified:
    - docs/index.md

key-decisions:
  - "All example code in guides is verified against the actual API (sourced from codebase)"
  - "Migration guide covers 6 breaking change areas: fixture injection, hooks, CLI flags, config, parser behavior, plugin loading"
  - "Custom formatter guide follows ADR-003 three-file pattern (entrypoint.py + hook.py + plugin.py)"

requirements-completed: [D3]

duration: 22min
completed: 2026-06-09
---

# Phase 20 Plan 12: How-To Guides Summary

**5 how-to guides covering custom parser, structured BDD, parallel xdist, custom formatter, and v1 migration — with Sphinx toctree integration**

## Performance

- **Duration:** 22 min
- **Started:** 2026-06-08T23:55:00Z
- **Completed:** 2026-06-09T00:17:00Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- 5 user-facing how-to guides at `docs/guides/` following problem→solution→example→mistakes format
- Migration guide with 6 breaking-change categories and before/after code comparison
- Custom formatter guide demonstrating the ADR-003 three-file plugin pattern
- Sphinx toctree integration via `docs/index.md` with `guides/index` entry

## Task Commits

Each task was committed atomically:

1. **Task 1: Guides 01-02 (Custom Parser, Structured BDD)** — `94c62c05` (feat(20-09))
2. **Task 2: Guides 03-04 (Parallel xdist, Custom Formatter)** — `8adf7ccc` (docs(20-12))
3. **Task 3: Guide 05 (v1 Migration), index, toctree** — `59381b11` (feat(20-10))

**Plan metadata:** this commit

_Note: Due to parallel agent execution on the same branch, Task 1 and Task 3 commits were interleaved with other agent commits (20-09, 20-10) that picked up the working-tree files._

## Files Created/Modified
- `docs/guides/index.md` — Toctree linking all 5 guides with section descriptions
- `docs/guides/01-custom-gherkin-parser.md` — Custom StepParser subclass guide (7061 chars)
- `docs/guides/02-structured-bdd-yaml-json.md` — YAML/JSON/TOML/HOCON BDD guide (7843 chars)
- `docs/guides/03-parallel-execution-xdist.md` — pytest-xdist parallel execution guide (6016 chars)
- `docs/guides/04-custom-formatter-plugin.md` — Formatter plugin creation guide (9227 chars)
- `docs/guides/05-migration-from-v1.md` — pytest-bdd v1 to pytest-bdd-ng migration guide (10251 chars)
- `docs/index.md` — Added `guides/index` to toctree

## Decisions Made
None — followed plan as specified.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
- Pre-commit hook stash conflict during Task 3 commit; resolved by restoring modified file and re-committing.
- Parallel agent interleaving caused Task 1 and Task 3 commits to appear under different agent commit messages (20-09, 20-10) on the shared refactoring branch. All file content is intact and verified.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- D3 (how-to guides) complete — all 5 guides written and toctree integrated.
- Ready for phase 20 verification and milestone completion.

---
*Phase: 20-multiple-refactorings*
*Completed: 2026-06-09*
