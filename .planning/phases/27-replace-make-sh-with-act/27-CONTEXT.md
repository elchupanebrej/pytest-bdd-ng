# Phase 27: Replace Make&sh with Act - Context

**Gathered:** 2026-06-22
**Status:** Implementation complete

<domain>
## Phase Boundary

Replace the 445-line GNU Makefile with GitHub Actions workflows (run locally via `act`) and Python scripts. Eliminate Make and shell script dependencies from the development workflow.

</domain>

<decisions>
## Implementation Decisions

### Workflow Architecture
- **D-01:** Five separate GitHub Actions workflows: `lint.yml`, `env.yml`, `tests.yml`, `docs.yml`, `release.yml`
- **D-02:** `tests.yml` contains 8 jobs (native, unit, integration, contract, e2e, compat, perf, slow) sharing a `UV_SYNC_EXTRAS` env var
- **D-03:** `env.yml` uses `workflow_dispatch` inputs with selectable action (check/install/install-docker/install-browser) instead of separate Make targets
- **D-04:** `lint.yml` and `tests.yml` trigger on push/PR to main + workflow_dispatch; `release.yml` is manual-only

### Shell Script Replacement
- **D-05:** `scripts/run_messages_coverage_audit.sh` → `scripts/run_messages_coverage_audit.py` (Python port using subprocess.run)
- **D-06:** `docs/Makefile` → `scripts/docs_build.py` (Python wrapper for sphinx-build supporting 9 targets, default=html)

### File Deletions
- **D-07:** `Makefile` (445 lines) deleted entirely — no thin wrapper retained
- **D-08:** `docs/Makefile` (153 lines) deleted
- **D-09:** `scripts/run_messages_coverage_audit.sh` (106 lines) deleted
- **D-10:** `.github/workflows/main.yml` (old testing workflow) deleted, replaced by `tests.yml`
- **D-11:** `.github/workflows/release.yaml` (old release workflow) deleted, replaced by `release.yml`

### Documentation Updates
- **D-12:** `DEVELOPMENT.rst` — all Make references replaced with act/Python equivalents; "Makefile Test API" renamed to "Test Commands"
- **D-13:** `CONTRIBUTING.md` — quality check commands updated to use act/uv
- **D-14:** `docs/TESTING.md` — test commands updated to use act/uv
- **D-15:** Historical `make` references preserved only in notes documenting what was replaced

### Pre-existing Workflows Preserved
- **D-16:** `.github/workflows/messages-baseline-drift.yml` left untouched (scheduled drift check, unrelated to Make migration)

### Architectural Decision Record
- **D-17:** `docs/adr/011-make-to-act-migration.md` created documenting the full decision, workflow mapping, and consequences

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture
- `docs/adr/011-make-to-act-migration.md` — Full ADR for Make→act+Python decision, workflow mapping, consequences

### Workflows
- `.github/workflows/lint.yml` — Linting (ruff check, ruff format, custom rules)
- `.github/workflows/env.yml` — Environment provisioning (check/install/docker/browser)
- `.github/workflows/tests.yml` — Test matrix (8 jobs: native, unit, integration, contract, e2e, compat, perf, slow)
- `.github/workflows/docs.yml` — Sphinx docs build + feature heading validation
- `.github/workflows/release.yml` — Build + dist check (manual trigger)

### Python Scripts
- `scripts/run_messages_coverage_audit.py` — Python port of bash audit script
- `scripts/docs_build.py` — Python Sphinx builder (9 targets)

### Updated Documentation
- `DEVELOPMENT.rst` — Canonical development guide with act-based commands
- `CONTRIBUTING.md` — Contributor quality check commands
- `docs/TESTING.md` — Test running guide

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `act` CLI — GitHub Actions local runner (https://nektosact.com/)
- `uv` — Package manager used throughout all workflows
- `astral-sh/setup-uv@v4` — GitHub Action for uv with caching

### Established Patterns
- All workflows use `actions/checkout@v4` + `astral-sh/setup-uv@v4` with `enable-cache: true`
- Test workflows share `UV_SYNC_EXTRAS` env var to avoid dependency repetition
- Python scripts use `subprocess.run` for command invocation with `pathlib.Path` for path handling

### Integration Points
- Workflows integrate with existing `uv` dependency management
- Python scripts invoke existing pytest infrastructure (`pytest_bdd.plugin.gherkin_message_reporter.entrypoint`)
- `act` runs workflows in Docker containers matching GitHub Actions runners

</code_context>

<specifics>
## Specific Ideas

No specific requirements — implementation follows standard GitHub Actions and Python patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 27-Replace Make&sh with Act*
*Context gathered: 2026-06-22*
