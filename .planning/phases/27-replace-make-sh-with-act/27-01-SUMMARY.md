# Phase 27: Replace Make&sh with Act — Summary

**Plan:** 27-01-PLAN.md
**Completed:** 2026-06-22
**Status:** All tasks complete

## What Was Built

Replaced the 445-line GNU Makefile with GitHub Actions workflows (run locally via `act`) and Python scripts. Eliminated
Make and shell script dependencies from the development workflow.

## Deliverables

### GitHub Actions Workflows (5 files)

- `.github/workflows/lint.yml` — ruff check, format, custom rules
- `.github/workflows/env.yml` — workflow_dispatch with selectable action (check/install/docker/browser)
- `.github/workflows/tests.yml` — 8 test jobs sharing UV_SYNC_EXTRAS env var
- `.github/workflows/docs.yml` — sphinx-build + feature heading validation
- `.github/workflows/release.yml` — build + dist check (manual trigger)

### Python Scripts (2 files)

- `scripts/run_messages_coverage_audit.py` — Python port of bash audit script using subprocess.run
- `scripts/docs_build.py` — Python wrapper for sphinx-build supporting 9 targets

### Documentation (4 files)

- `DEVELOPMENT.rst` — all Make references replaced with act/Python equivalents
- `CONTRIBUTING.md` — quality check commands updated
- `docs/TESTING.md` — test commands updated
- `docs/adr/011-make-to-act-migration.md` — ADR documenting the decision

### Deleted Files (5 files)

- `Makefile` (445 lines)
- `docs/Makefile` (153 lines)
- `scripts/run_messages_coverage_audit.sh` (106 lines)
- `.github/workflows/main.yml` (old testing workflow)
- `.github/workflows/release.yaml` (old release workflow)

## Key Design Decisions

1. **act for local CI parity** — Workflows run identically on GitHub Actions and locally
2. **workflow_dispatch inputs** — Single workflow with selectable action replaces multiple Make targets
3. **Shared UV_SYNC_EXTRAS** — Avoids dependency repetition across 8 test jobs
4. **Python for non-CI tasks** — Maintainable, testable replacements for shell scripts

## Verification

All deliverables verified:

- Makefile deleted
- 5 workflows exist
- 2 Python scripts exist
- ADR exists
- Documentation updated

## Gap Closure

Validation gaps from `27-VALIDATION.md` were closed on 2026-06-22:

- Replaced obsolete Makefile contract coverage with act workflow and Python script contract tests.
- Kept workflow structure checks in contract tests instead of BDD/e2e executable docs.
- Superseded prior BDD workflow coverage after the 2026-06-23 context ingest. `act --list`, `act -n`, fake `uv`,
  fake `sphinx`, and exit-code-only checks are not final acceptance evidence for Phase 27.
- Reopened `07 Messages Coverage Audit.feature.md`, `08 Docs Build Script.feature.md`, and `09 Act Workflow Structure.feature.md`
  for real-Act artifact-producing BDD scenarios.
- Replaced long inline `python -c` feature commands with either doc string Python snippets or behavioral command steps.
- Updated stale documentation and contract references to the deleted shell script and old workflow names.
- Updated `messages-baseline-drift.yml` to call `python scripts/run_messages_coverage_audit.py`; this is a deviation
  from the original "leave untouched" note, required because the shell wrapper was deleted.

Focused BDD verification from 2026-06-23 is superseded:

- `PATH="$HOME/.local/bin:$PATH" uv run python -m py_compile src/pytest_bdd_testing/step/harness.py src/pytest_bdd_testing/case/e2e/feature/test_18_development.py`
- `PATH="$HOME/.local/bin:$PATH" uv run python -m pytest src/pytest_bdd_testing/case/e2e/feature/test_18_development.py -k 'Messages or Docs' -q`
  — superseded because it used fake external dependencies.
- `PATH="$HOME/.local/bin:$PATH" uv run python -m pytest src/pytest_bdd_testing/case/e2e/feature/test_18_development.py -k 'Act' -q`
  — superseded because it asserted dry-run success without required artifacts.

## Artifact-BDD Reopen

New requirements from context ingest:

- BDD/e2e must run real Act jobs, not fake tools.
- Act jobs must produce durable artifacts visible in the host workspace.
- BDD assertions must inspect artifact existence, non-empty content, parseability, and relevant semantic fields.
- Producer output may be handed to consumer jobs through stable workspace paths or workflow dependencies.
- The artifact acquisition matrix for `07`, `08`, and `09` must be agreed before implementation.

## Dialogue Capture 2026-06-23

Later review clarified two Phase 27 interpretation points:

- Development BDD prose should read like PRD/acceptance rationale. It should explain the capability, why it exists, and
  the framework pain it covers. It should not repeat "This feature/scenario..." boilerplate, and it should not present
  Act itself as the target under test.
- The statement "all scripts in `scripts/` are covered by BDD/ATDD" is false. BDD currently covers the `arch.py` facade
  partially and the messages audit script indirectly through workflow artifacts. `docs_build.py` has contract tests but
  no exact feature/workflow invocation evidence. Most helper scripts have no direct BDD/ATDD evidence.

Phase 27 scope is therefore refined: the required proof is not "every helper script by filename"; it is that every new
or retained Make/shell replacement command surface is covered through a real workflow/facade target with artifact or
content assertions. Helper scripts must be either clearly private behind a covered surface or promoted to covered
development targets.

Additional current-phase requirement:

- `features/18 Development/09 Act Workflow Structure.feature.md` was split into separate features:
  `09 Lint`, `10 Environment`, `11 Tests`, and `12 Release`.
- Each split feature deepens coverage for its workflow target with meaningful artifact/content assertions beyond job
  identity and success status.
- The split features document development capabilities and artifact contracts; the local workflow runner remains the
  execution tool, not the feature target.

## Impact

- Git Bash no longer required on Windows for development
- Local `act` runs provide CI parity
- Shell script maintenance burden eliminated
- `make` is no longer a project dependency
