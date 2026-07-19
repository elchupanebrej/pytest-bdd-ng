# Phase 12: restructure-test-suite-into-semantic-groups - Context

**Gathered:** 2026-05-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure the test suite so `tests/cases/` communicates semantic purpose, `tests/assets/` holds passive data only, shared active test harness code moves into `src/pytest_bdd/testing/`, and Makefile targets become the only documented human API for local, full, semantic, slow, and environment-specific runs.

This phase is a test infrastructure restructure only. It must not change product behavior, SpecKit constitution artifacts, completed specs, parser behavior, or the Python/pytest support matrix.

</domain>

<decisions>
## Implementation Decisions

### Migration Slicing
- **D-01:** Use a big-bang migration for the test tree. Do not require a separate move-only commit before behavior/config edits.
- **D-02:** Planner may combine file moves, import updates, pytest config changes, Makefile changes, tox changes, and documentation edits when that keeps the migration coherent.
- **D-03:** Validation must still distinguish mechanical relocation from behavior changes in the plan and test strategy.

### Classification Edge Cases
- **D-04:** Use strict semantic classification. No mixed-purpose directories under `tests/cases/`.
- **D-05:** Ambiguous tests may be classified case-by-case by the agent based on purpose, not legacy path. Defaulting all ambiguous tests to `integration` is not locked.
- **D-06:** Canonical semantic groups are `unit`, `integration`, `contract`, `e2e`, `compat`, `perf`, and `external`.
- **D-07:** `messages`, formatter golden, docs/generation/scripts, Docker xdist, and long benchmark tests must be split according to the design doc's purpose-based mapping.

### Environment Target Policy
- **D-08:** Keep default `make test` feasible on the current machine without surprise provisioning; unavailable environment-specific tests are excluded from default selection.
- **D-09:** Explicit environment targets fail early with actionable setup errors when prerequisites are missing.
- **D-10:** `make test-all` should include feasible local, Docker, and platform bridge targets after validation; it should not fail solely because an unsupported/unavailable environment cannot run on the current host.
- **D-11:** Environment checks are read-only. Provisioning must be explicit through `env-install-*` targets.

### Helper-Code Extraction
- **D-12:** Shared active helpers move to internal `src/pytest_bdd/testing/` modules.
- **D-13:** `src/pytest_bdd/testing/` is internal project-owned test infrastructure, not documented as public user API.
- **D-14:** Local fixture code that only serves one semantic group may remain in that group's `conftest.py`.
- **D-15:** `tests/assets/` must contain passive fixtures, templates, golden files, Docker assets, and feature-document fixtures only.

### E2E Split Rule
- **D-16:** Split E2E collection per feature file where practical.
- **D-17:** Whole-directory E2E scenario loaders are forbidden after this phase.
- **D-18:** Each E2E module should bind only the feature file or files it owns so failures, selection, and ownership stay file-local.

### Makefile Contract
- **D-19:** Document only the new Makefile API. Old commands are not part of the user-facing contract.
- **D-20:** Remove old commands if they are unusable or misleading. Existing commands that naturally still work do not need documentation aliases.
- **D-21:** Tox remains the matrix engine; Make is the human entrypoint.

### the agent's Discretion
- Exact file-by-file classification for ambiguous tests, provided it follows strict purpose-based semantics.
- Exact implementation order inside the big-bang migration.
- Exact names and boundaries for internal helper modules under `src/pytest_bdd/testing/`, within the design doc's proposed module set.
- Exact validation command sequence, as long as it proves semantic group mapping, Makefile target shape, and representative old/new slice equivalence.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Design
- `docs/superpowers/specs/2026-05-18-test-suite-restructure-design.md` — Source design for target tree, semantic groups, markers, Makefile API, environment behavior, migration safety, and development guide updates.
- `.planning/ROADMAP.md` — Phase 12 entry and phase dependency on Phase 11.
- `.planning/PROJECT.md` — Core value, constraints, current test infrastructure context, and development workflow.
- `.planning/REQUIREMENTS.md` — v1 testing and documentation requirements affected by the restructure.

### Prior Decisions
- `.planning/phases/11-audit-prune/11-CONTEXT.md` — Prior phase CI matrix gate, plugin audit constraints, and large-file cleanup context.
- `.planning/phases/10-pattern-unification/10-CONTEXT.md` — Plugin pattern and StashBound consistency decisions.
- `.planning/phases/09-compatibility-streamlining/09-CONTEXT.md` — Compatibility layer and tox/CI matrix split decisions.

### Codebase Maps
- `.planning/codebase/TESTING.md` — Current test organization, pytester patterns, markers, group ordering, and e2e loader state.
- `.planning/codebase/CONVENTIONS.md` — Test naming, style, import, fixture, and helper conventions.
- `.planning/codebase/STRUCTURE.md` — Current source/test directory structure and key integration points.

### Source and Configuration
- `tests/` — Existing test suite to migrate.
- `tests/conftest.py` — Current pytest adapter for test group ordering; must remain thin.
- `src/pytest_bdd/util/test_group_ordering.py` — Shared group parsing, assignment, marker application, and xdist barrier logic.
- `pyproject.toml` — Pytest markers, `test_group_paths`, ruff/pre-commit config, package metadata.
- `tox.ini` — Matrix engine and environment definitions.
- `Makefile` — Human test entrypoint to update.
- `DEVELOPMENT.rst` — Must document new test configuration and contribution rules.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/pytest_bdd/util/test_group_ordering.py` — Existing path-based group assignment and marker application logic; extend rather than duplicating test-local grouping utilities.
- `tests/support/docker.py`, `tests/support/docker_cluster.py`, `tests/support/cucumber_formatters.py`, and related support helpers — Candidates for internal `src/pytest_bdd/testing/` modules.
- `tests/e2e/conftest.py` — Existing BDD acceptance step definitions; may need ownership-aware fixture boundaries after E2E split.
- `.coveragerc`, `tox.ini`, `pyproject.toml`, and `Makefile` — Configuration integration points for selection, coverage, and matrix behavior.

### Established Patterns
- Tests use pytest native `assert`, pytester `testdir`, `tmp_path`, and inline feature/conftest generation.
- Test grouping is path-driven through `[tool.pytest.ini_options]` with `test_group_paths`.
- Existing markers include speed/platform/environment style markers, but Phase 12 replaces old semantic paths with canonical semantic groups plus speed/environment facets.
- Shared helper code should be project-owned when active and reusable; passive data belongs under `tests/assets/`.

### Integration Points
- Moving tests changes pytest collection paths, marker resolution, coverage includes, tox commands, Makefile targets, documentation, and any hardcoded test paths in scripts.
- E2E split must update `scenarios(...)` usage so modules bind owned feature files instead of collecting the full feature directory.
- Environment targets must separate read-only validation from explicit provisioning.

</code_context>

<specifics>
## Specific Ideas

- Big-bang migration is preferred despite diff size; keep plan clear about mechanical move versus behavioral/config edits.
- Strict classification matters more than preserving legacy folder shape.
- `make test-all` means "all feasible for this machine after validation," not "fail because every possible platform is absent."
- `src/pytest_bdd/testing/` is internal. Do not market it as supported user API.
- Whole-directory E2E collection is explicitly disallowed after the restructure.
- Old Makefile commands may be removed if unusable; do not preserve compatibility through documented aliases.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 12-restructure-test-suite-into-semantic-groups*
*Context gathered: 2026-05-18*
