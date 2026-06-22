---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Milestone v1.0 audit passed
stopped_at: Phase 26 context gathered
last_updated: "2026-06-22T10:52:53.490Z"
last_activity: 2026-06-13 -- remaining gaps closed; docs/api/generated moved to docs/_build
progress:
  total_phases: 22
  completed_phases: 21
  total_plans: 107
  completed_plans: 107
  percent: 95
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-12)

**Core value:** Reliable, frictionless BDD testing in pytest
**Current focus:** Phase 26 - Test CLI scripts in a separate Cucumber Development flow

## Current Position

Phase: 20 (multiple-refactorings) — EXECUTING
Plan: 1 of 32
Status: Milestone v1.0 audit passed
Last activity: 2026-06-13 -- remaining gaps closed; docs/api/generated moved to docs/_build

Progress: [█████████░] 99%

## Performance Metrics

Updated after each plan completion.

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 04 | P02 | 41 min | 4 | 5 |
| 04 | P03 | 32 min | 3 | 7 |
| 04 | P04 | 8h 33m | 3 | 72 |
| 04 | P05 | 19 min | 4 | 5 |
| 04 | P06 | 2h 8m | 4 | 9 |
| 12 | P01 | 38 min | 3 | 4 |
| 12 | P04 | 47 min | 3 | 62 |
| 13 | P13-03 | 22 min | 6 | 1 |
| 14 | P01 | 35min | 2 | 2 |
| 14-gap-closure | P04 | 18min | 3 | 6 |
| 16 | P01 | 45min | 4 | 5 |
| 17 | P01 | 10min | 2 | 2 |
| 17 | P02 | 10min | 3 | 3 |
| 18 | P01 | 10 min | 4 | 2 |
| 19 | P01 | 45 min | 3 | 4 |
| 19 | P02 | 37 min | 3 | 17 |
| 19 | P03 | 36 min | 4 | 80 |
| 19 | P04 | 75 min | 4 | 6 |
| Phase 20 P01 | 45 min | 3 tasks | 13 files |

## Quick Tasks Completed

| Slug | Date | Status | Summary |
|------|------|--------|---------|
| 260611-allure3-docker | 2026-06-11 | complete ✓ | Replace Allure 2 with Allure 3 Docker image |

## Accumulated Context

### Decisions

Recent decisions affecting current work:

- Roadmap creation: Two-iteration structure - Iteration 1 vertical slices, Iteration 2 horizontal pass.
- Code quality gates from Phase 2 remain prerequisite for structural refactoring.
- Parsers frozen during stabilization - tests only, no modifications to parsers.py.
- Phase 12 Plan 04 establishes Makefile as the human test API over semantic selectors.
- [Phase 19]: Feature-tree ordering validation now lives outside the pypandoc/RST conversion script.
- [Phase 19]: Sphinx feature-tree extension raises ExtensionError for validation, copy, and write failures.
- [Phase 19]: Feature documentation contract tests no longer depend on pypandoc or generated .feature.rst output.
- [Phase 19]: Markdown root prose is now the project metadata and Sphinx include source.
- [Phase 19]: Sphinx source suffixes are explicit so `.md` files use the MyST Markdown parser.
- [Phase 19]: Build-time copied `.feature.md` files under docs/features are ignored; only features.md remains committed.
- [Phase 19]: The old feature RST converter has no fallback command, hook, tox env, console script, or packaged templates.
- [Phase 19]: Makefile now exposes make docs for Sphinx HTML generation instead of a separate feature-doc generation target.
- [Phase 19]: Historical design notes were reworded so repository-wide old-pipeline searches prove active code and docs are clean.
- [Phase 19]: Active contributor documentation now names make docs instead of the removed feature RST generator.
- [Phase 19]: Remote xdist Docker assets copy README.md, matching current package metadata.
- [Phase 19]: ReadTheDocs preview, README rendering, and CHANGES rendering remain explicit blocking UAT gates before merge.
- [Phase 20-26]: Removed `testing` extra from pyproject.toml — pytest_bdd_testing is local-only, not on PyPI. R1 satisfied by separate package structure, not dependency declaration.

### Roadmap Evolution

- Phase 12 added: Restructure test suite into semantic groups.
- Phase 13 inserted between Phase 12 and Phase 14: Unify cucumber-json plugins INI/CLI options.
- Phase 16 completed: Vulture moved from pytest wrapper to native pre-commit hook and native whitelist.
- Phase 17 added: Adapt GitHub CI to use make and validate with act.
- Phase 18 added: Split xdist-remote tests into separate parallel GHA executor job.
- Phase 19 added: HTML doc generation simplification.
- Phase 20 added: multiple refactorings
- Phase 20a added: docs/architecture/allure.md
- Phase 26 added: Test CLI scripts in a separate Cucumber Development flow
- Phase 26 ingested: development-script BDD requirements, roadmap detail, and phase planning artifacts from `specs/026-dev-scripts-bdd/`

### Pending Todos

- [ ] Improve library typing using best practices from awesome-python-typing.
- [ ] Integrate BDD/ATDD tests into development workflow and UAT phase.
- [ ] No TestClasses are allowed in tests - enforce via ruff rule.
- [ ] Expand feature tests for undocumented behaviors.
- [ ] Split xdist-remote tests into separate parallel GHA executor job.
- [ ] Gather failed CI logs into workflow artifact.
- [ ] Remove __init__.py usage and unify ruff rules project layout.
- [ ] Create custom pylint rule for noqa without reason.

### Blockers/Concerns

- Docker-backed remote ssh xdist tests require Docker Desktop; local non-Docker suite and xdist smoke passed in 04-06.
- Phase 3 full-suite and xdist verification are blocked by local pytester/xdist environment failures recorded in 03-03-SUMMARY.md.
- Phase 6 Gherkin spec edge case catalog needs research before test writing.
- Decopatch health unverified - audit needed during Phase 10.
- Go parser v39 compatibility untested - bump during dependency upgrades in Phase 9-10.

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| TEST-01 | Unit test coverage target | Resolved: coverage report passes at 86% | 2026-06-13 |
| TEST-02 | BDD feature test failures | Resolved: E2E slice 203 passed, 10 skipped | 2026-06-13 |

## Quick Tasks Completed

| Date | ID | Slug | Status | Description |
|------|----|------|--------|-------------|
| 2026-05-21 | 260521-bye | fix-make-test-all-command-all-way-down-f | complete | Fix make test-all command all the way down |
| 2026-05-24 | 260524-qv5 | add-phase-15-failfast-make-tox-target-gu | complete | Add Phase 15 failfast make tox target |
| 2026-05-31 | 260531-1mz | fix-all-pre-commit-errors-and-commit | complete | Fix all pre-commit errors and commit |
| 2026-05-31 | 260531-mypy | re-enable-mypy-pre-commit | complete | Re-enable MyPy pre-commit hook |
| 2026-06-01 | 260601-rn | rename-branch-to-display-changes | complete | Rename current branch to display changes |
| 2026-06-02 | 260602-lhn | seems-file-locator-doesn-t-preserve-file | complete | Fix file locator preserving file paths |
| 2026-06-02 | 260602-ruq | fix-all-failing-tests-in-pr-141-jobs-loc | complete | Fix all failing tests in PR 141 jobs locally |
| 2026-06-13 | 260613-ag | handoff-and-commit | complete | Create hand-off document and commit all changes |
| 2026-06-15 | 260615-kzf | run-pylint-architecture-injector-on-src- | complete | Run pylint architecture injector on src/pytest_bdd_testing excluding cases |
| 2026-06-20 | 260620-o6j | rewrite-all-assert-statements-in-src-pyt | complete | Rewrite all assert statements in src/pytest_bdd_testing/step to use pyhamcrest matchers |

## Session Continuity

Last session: 2026-06-20T21:21:15.530Z
Stopped at: Phase 26 context gathered
Resume file: .planning/phases/26-test-cli-scripts-in-a-separate-cucumber-development-flow/26-CONTEXT.md
