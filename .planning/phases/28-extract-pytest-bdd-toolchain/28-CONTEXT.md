# Phase 28: Extract pytest_bdd_toolchain - Context

**Gathered:** 2026-06-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Extract `pytest_bdd_testing` into `pytest_bdd_toolchain`: rename the package, move all 11 development scripts into
`src/pytest_bdd_toolchain/tool/` as `pbt-*` entrypoints, update active references, and preserve zero-regression behavior.
This is a clean break with no backward compatibility package or wrapper layer.

`ROADMAP.md` has been updated during discussion so Phase 28 is this rename/extraction phase. The obsolete Phase 28
"implement all 24 feature specs" scope was deleted and must not guide planning.

</domain>

<spec_lock>
## Requirements (locked via SPEC.md)

**6 requirements are locked.** See `28-SPEC.md` for full requirements, boundaries, and acceptance criteria.

Downstream agents MUST read `28-SPEC.md` before planning or implementing. Requirements are not duplicated here.

**In scope (from SPEC.md):**
- Package rename (`pytest_bdd_testing` -> `pytest_bdd_toolchain`)
- Script migration to `src/pytest_bdd_toolchain/tool/`
- `pbt-*` entrypoint registration in `pyproject.toml`
- Documentation updates (README, CHANGELOG, DEVELOPMENT.rst, all active references)
- Test suite validation

**Out of scope (from SPEC.md):**
- CI/CD workflow redesign; only update package references where needed
- Backward compatibility layer, deprecation warnings, or wrapper packages
- New feature development
- Performance optimization

</spec_lock>

<decisions>
## Implementation Decisions

### Phase Identity And Roadmap Alignment
- **D-01:** Phase 28 is the `pytest_bdd_toolchain` rename/extraction phase. `28-SPEC.md` and this context are the
  authoritative planning inputs.
- **D-02:** The old ROADMAP scope to implement all 24 feature specs was deleted, not deferred or moved to backlog.
- **D-03:** `ROADMAP.md` has already been updated to match `28-SPEC.md`; downstream planning must not recreate the
  24-plan feature-spec breakdown.
- **D-04:** The Phase 28 planning directory has already been renamed from
  `.planning/phases/28-feature-specs-implementation/` to
  `.planning/phases/28-extract-pytest-bdd-toolchain/`.

### Migration Granularity
- **D-05:** Implement the rename as one atomic change rather than multiple GSD plans or staged checkpoint tasks.
- **D-06:** Despite being atomic, the implementation is not done until the full `28-SPEC.md` validation passes.
- **D-07:** Commit shape is planner discretion; intermediate local commits are allowed only if the final delivered phase
  is coherent and not left half-renamed.
- **D-08:** If validation exposes blockers, fix forward within the same plan instead of reverting at first failure.

### Reference Cleanup And Validation
- **D-09:** Old-name references must be removed from active code, config, docs, features, root docs, current roadmap,
  current context, and current spec surfaces.
- **D-10:** Historical `.planning/phases/*` summaries and audit records may keep old-name references when they document
  past states.
- **D-11:** Replace invalid test acceptance targets with
  `uv run python -m pytest src/pytest_bdd_toolchain/case -q --tb=short --no-header`.
- **D-12:** Validate old-name cleanup with scoped `rg` commands over active surfaces. Do not use broad repository-wide
  greps that fail on historical planning records.

### Tool Package And Lint Policy
- **D-13:** Moved scripts should not inherit broad `scripts/*` ignores as a directory-level policy.
- **D-14:** The planner should attempt to remove tool-module ignores and fix lint issues as part of the rename, but this
  is best effort rather than a hard blocker if cleanup becomes too large.
- **D-15:** If strict lint cleanup is too large, use narrow local `# noqa` comments with reasons. Do not add a
  directory-level `src/pytest_bdd_toolchain/tool/**` ignore fallback.
- **D-16:** Each `pbt-* --help` command should have a proper CLI help path that exits 0 and shows meaningful usage/help
  without running the tool's main side effects.

### Package Configuration
- **D-17:** Remove the package discovery exclusion for `pytest_bdd_toolchain` so the package is distributable.
- **D-18:** Remove the broad mypy exclusion for `pytest_bdd_toolchain`; keep only targeted exclusions needed for test
  code such as `case/`.
- **D-19:** Update `testpaths`, all configured `test_group_paths`, architecture config roots, quality gate commands, and
  script entrypoints to the new package path.

### the agent's Discretion
- The planner may choose the exact mechanics for the atomic rename, including whether to use a temporary migration
  script or direct edits, as long as the final state satisfies this context and `28-SPEC.md`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Definition
- `.planning/ROADMAP.md` — Updated Phase 28 goal, success criteria, and 0/1 plan count.
- `.planning/phases/28-extract-pytest-bdd-toolchain/28-SPEC.md` — Locked requirements, boundaries, and acceptance
  criteria.
- `.planning/phases/28-extract-pytest-bdd-toolchain/28-CONTEXT.md` — This decision context.

### Rename Source Documents
- `docs/superpowers/specs/2026-06-24-rename-pytest-bdd-testing-to-toolchain.md` — Original rename design spec.
- `docs/superpowers/plans/2026-06-24-rename-pytest-bdd-testing-to-toolchain.md` — Detailed rename task list and
  expected entrypoint names.

### Current Package And Scripts
- `src/pytest_bdd_testing/` — Current package to rename.
- `src/pytest_bdd_testing/case/` — Current test suite path; target is `src/pytest_bdd_toolchain/case/`.
- `scripts/` — Development scripts to move into `src/pytest_bdd_toolchain/tool/`.

### Configuration And Quality Gates
- `pyproject.toml` — Package discovery, entrypoints, architecture config, mypy, pytest paths, test group paths, quality
  gate command, and ruff per-file ignores.
- `.pre-commit-config.yaml` — Pre-commit path references that must follow the rename.
- `.github/workflows/` — Workflow references that may need package-path updates only; workflow redesign is out of scope.
- `src/pytest_bdd/_pylint/checkers/` — Checker messages and path rules containing old package references.

### Documentation And Active Surfaces
- `DEVELOPMENT.rst` — Canonical development guide.
- `CONTRIBUTING.md` — Contributor commands and quality guidance.
- `README.rst` and `CHANGES.rst` — Root documentation surfaces.
- `features/` — Executable BDD documentation.
- `docs/` — Sphinx documentation.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pathlib.Path` and `re` are sufficient for mechanical path/reference discovery if the planner uses a temporary
  migration script.
- Existing scripts under `scripts/` provide the content to move into `src/pytest_bdd_toolchain/tool/`.
- Existing test grouping config in `pyproject.toml` already defines the target group structure to preserve.

### Established Patterns
- The project uses `src/` package layout and `pyproject.toml` for console scripts, setuptools discovery, pytest config,
  ruff config, mypy config, and architecture tooling.
- Test group ordering is configuration-driven through `test_group_paths`; group names are config values, not constants.
- Repository rules forbid broad/global lint disabling without explicit approval. For this phase, directory-level
  `src/pytest_bdd_toolchain/tool/**` ignore fallback is not approved.

### Integration Points
- `pyproject.toml [project.scripts]` is the integration point for all `pbt-*` commands.
- `src/pytest_bdd_testing/case/e2e/conftest.py` and related E2E loaders import development step modules and must move
  with the package rename.
- Pylint checker strings, custom quality rules, and architecture config paths must move with the package name.

</code_context>

<specifics>
## Specific Ideas

### Required Entrypoints

```toml
[project.scripts]
pbt-arch = "pytest_bdd_toolchain.tool.arch:main"
pbt-collect-arch-scores = "pytest_bdd_toolchain.tool.collect_arch_scores:main"
pbt-collect-test-scores = "pytest_bdd_toolchain.tool.collect_test_scores:main"
pbt-fill-arch-scores = "pytest_bdd_toolchain.tool.fill_arch_scores:main"
pbt-fill-test-docstrings = "pytest_bdd_toolchain.tool.fill_test_docstrings:main"
pbt-fix-incomplete-scores = "pytest_bdd_toolchain.tool.fix_incomplete_scores:main"
pbt-fix-long-lines = "pytest_bdd_toolchain.tool.fix_long_lines:main"
pbt-inject-responsibility-docstrings = "pytest_bdd_toolchain.tool.inject_responsibility_docstrings:main"
pbt-inject-test-docstrings = "pytest_bdd_toolchain.tool.inject_test_docstrings:main"
pbt-run-messages-coverage-audit = "pytest_bdd_toolchain.tool.run_messages_coverage_audit:main"
pbt-analyze-responsibility-zones = "pytest_bdd_toolchain.tool.analyze_responsibility_zones:main"
```

### Validation Commands

- `python -c "import pytest_bdd_toolchain"`
- `python -c "import pytest_bdd_testing"` must fail with `ImportError`
- `uv run python -m pytest src/pytest_bdd_toolchain/case -q --tb=short --no-header`
- All 11 `pbt-* --help` commands exit 0 and show meaningful help
- `tox -e py310,py311,py312,py313,py314`
- Scoped `rg` checks over active surfaces prove old-name references were removed without failing on historical
  `.planning/phases/*` audit records

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 28-Extract pytest_bdd_toolchain*
*Context gathered: 2026-06-25*
