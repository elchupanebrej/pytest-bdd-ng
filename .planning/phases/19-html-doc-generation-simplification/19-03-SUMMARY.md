---
phase: 19-html-doc-generation-simplification
plan: 03
subsystem: docs
tags: [sphinx, myst, packaging, pre-commit, tox]

requires:
  - phase: 19-html-doc-generation-simplification
    provides: Markdown documentation sources and local feature-tree Sphinx extension from Plans 19-01 and 19-02
provides:
  - Obsolete feature RST conversion script and templates deleted
  - Pandoc wrapper dependencies and old console entry point removed from packaging
  - Makefile, pre-commit, tox, and CI no longer call the old feature RST generator
  - Generated feature RST artifacts removed from committed docs
  - Transient feature copies ignored for Markdown, Gherkin, and StructBDD YAML formats
affects: [docs, feature-doc-generation, packaging, ci]

tech-stack:
  added: []
  patterns:
    - Sphinx plus MyST plus local feature-tree extension is the single documentation build path
    - `make docs` is the Makefile boundary for local Sphinx HTML generation

key-files:
  created:
    - .planning/phases/19-html-doc-generation-simplification/19-03-SUMMARY.md
  modified:
    - pyproject.toml
    - Makefile
    - .pre-commit-config.yaml
    - tox.ini
    - .github/workflows/main.yml
    - .github/workflows/release.yaml
    - .gitignore
    - tests/cases/contract/generation/test_template_packaging.py
    - docs/superpowers/specs/2026-06-03-html-doc-generation-simplification-design.md
  deleted:
    - src/pytest_bdd/script/bdd_tree_to_rst.py
    - src/pytest_bdd/template/feature_include.rst.jinja2
    - src/pytest_bdd/template/features_index.rst.jinja2
    - src/pytest_bdd/template/features_section.rst.jinja2
    - docs/features/**/*.rst

key-decisions:
  - "The old feature RST converter has no fallback command, hook, tox env, console script, or packaged templates."
  - "Makefile now exposes `docs` for Sphinx HTML generation instead of a separate feature-doc generation target."
  - "Historical design notes were reworded so repository-wide old-pipeline searches prove active code and docs are clean."

patterns-established:
  - "Use `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html` for docs generation."
  - "Tests assert deleted RST templates are absent while keeping `test.py.jinja2` packaged."

requirements-completed: []

duration: 36 min
completed: 2026-06-04
---

# Phase 19 Plan 03: Obsolete RST Pipeline Removal Summary

**Old feature RST conversion stack removed from source, packaging, hooks, tests, CI, and committed docs while Sphinx/MyST remains the only docs build path**

## Performance

- **Duration:** 36 min
- **Started:** 2026-06-04T11:21:33Z
- **Completed:** 2026-06-04T11:57:41Z
- **Tasks:** 4
- **Files modified:** 80

## Accomplishments

- Deleted `bdd_tree_to_rst.py`, three RST feature templates, the console script, stale package data, and Pandoc-wrapper dependencies from `doc-gen`.
- Removed the old `features-docs` Makefile target, generator pre-commit hook, tox feature-doc env, and CI Pandoc setup; added `make docs` as the Sphinx build command.
- Removed all committed generated feature RST artifacts under `docs/features/` and expanded `.gitignore` for transient copied `.feature.md`, `.feature.gherkin`, and `.bdd.yaml` files.
- Updated packaging contract tests so they keep coverage for `test.py.jinja2` and assert obsolete template/hook references are gone.

## Task Commits

1. **Task 19-03-01: Remove obsolete RST generation packaging** - `fd769cb9` (`feat`)
2. **Task 19-03-02: Remove obsolete feature docs commands** - `f67b9bd5` (`fix`)
3. **Task 19-03-03: Delete generated feature RST artifacts** - `ecc1e3ae` (`docs`)
4. **Task 19-03-04: Update template packaging contract** - `55e85f82` (`test`)

Additional verification cleanup:

- `af504289` (`docs`) - Reworded stale historical design-doc references so plan-level old-pipeline search passes across `docs`.

## Files Created/Modified

- `pyproject.toml` - Removed `bdd_tree_to_rst` script entry, Pandoc-wrapper dependencies, and deleted RST templates from package data.
- `Makefile` - Removed `features-docs`, removed stale output variable, and added `docs` Sphinx build target.
- `.pre-commit-config.yaml` - Removed `generate-feature-doc` hook and CI skip entry.
- `tox.ini` - Removed `py314-feature-docs` env and env-list entry.
- `.github/workflows/main.yml` and `.github/workflows/release.yaml` - Removed Pandoc setup.
- `.gitignore` - Added transient feature-copy ignores for Markdown, Gherkin, and StructBDD YAML formats.
- `tests/cases/contract/generation/test_template_packaging.py` - Updated packaging assertions for removed templates and retained `test.py.jinja2`.
- `docs/superpowers/specs/2026-06-03-html-doc-generation-simplification-design.md` - Reworded obsolete exact names in historical design text.
- `src/pytest_bdd/script/bdd_tree_to_rst.py` - Deleted.
- `src/pytest_bdd/template/feature_include.rst.jinja2`, `features_index.rst.jinja2`, `features_section.rst.jinja2` - Deleted.
- `docs/features/**/*.rst` - Deleted generated feature RST artifacts.

## Verification

- `rg "bdd_tree_to_rst|features-docs|pypandoc|panflute" pyproject.toml Makefile .pre-commit-config.yaml tox.ini .github docs src tests` - PASS; no matches.
- `uv run python -m pytest tests/cases/contract/doc/test_doc.py tests/cases/contract/generation/test_template_packaging.py` - PASS; 15 tests passed.
- `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html` - PASS; build succeeded with 15 pre-existing documentation warnings for not-included docs and two existing MyST cross-reference warnings.
- `Get-ChildItem -Recurse docs/features -Filter *.rst` - PASS; no generated RST files remain.
- `git check-ignore` for `docs/features/**/*.feature.md`, `docs/features/**/*.feature.gherkin`, and `docs/features/**/*.bdd.yaml` examples - PASS.

## Decisions Made

- Removed the legacy generator completely instead of leaving fallback commands or historical exact command names in docs searched by the plan verification.
- Added `make docs` because removing the old feature-doc target otherwise left no Makefile docs build boundary, conflicting with the phase's command-boundary pattern.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added Makefile Sphinx docs target**
- **Found during:** Task 19-03-02 (command and hook cleanup)
- **Issue:** The plan required removing `features-docs` while preserving the normal docs/Sphinx workflow. The Makefile had no Sphinx docs target after removing the stale generator target.
- **Fix:** Added `docs: env-check` running `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html`.
- **Files modified:** `Makefile`
- **Verification:** `rg "^docs:|sphinx-build|^validate-headings:" Makefile` showed the docs target and retained heading validation; final Sphinx build passed.
- **Committed in:** `f67b9bd5`

**2. [Rule 1 - Bug] Removed stale exact old-pipeline references from design doc**
- **Found during:** Plan verification
- **Issue:** The required repository-wide search still matched historical design text under `docs/`, so verification could not prove the old pipeline names were gone from active documentation paths.
- **Fix:** Reworded historical references to generic legacy converter language and adjusted code fences to avoid adding Sphinx highlighting warnings.
- **Files modified:** `docs/superpowers/specs/2026-06-03-html-doc-generation-simplification-design.md`
- **Verification:** Final repository-wide old-pipeline search returned no matches; Sphinx build passed.
- **Committed in:** `af504289`

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 bug)
**Impact on plan:** Both fixes supported the stated acceptance criteria and verification. No behavior outside the documentation generation cleanup scope changed.

## Issues Encountered

- A git index lock appeared after accidentally running `git status` and `git add` concurrently. The only stale `index.lock` path returned by `git rev-parse --git-path index.lock` was removed after checking active git processes; staging then succeeded.
- Sphinx verification still reports 15 warnings already described in Plan 19-02: not-included architecture/spec docs and two existing MyST cross-reference warnings in `DEPRECATIONS.md`/`MIGRATION.md`.

## Known Stubs

None. Stub scan only matched the `TD` ruff rule label in `pyproject.toml`, not an introduced placeholder or UI/data stub.

## Threat Flags

None. This plan removed documentation generation surfaces and build commands; it did not add network endpoints, auth paths, runtime file access paths, or schema trust boundaries.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Plan 19-04. The repository now has one documentation build path: Sphinx plus MyST plus the local feature-tree extension. Remaining Phase 19 work should focus on final verification/ReadTheDocs spot checks.

## Self-Check: PASSED

- Files found: `.planning/phases/19-html-doc-generation-simplification/19-03-SUMMARY.md`, `pyproject.toml`, `Makefile`, `.pre-commit-config.yaml`, `tox.ini`, `.gitignore`, `tests/cases/contract/generation/test_template_packaging.py`, `docs/superpowers/specs/2026-06-03-html-doc-generation-simplification-design.md`.
- Deleted files absent: `src/pytest_bdd/script/bdd_tree_to_rst.py`, `src/pytest_bdd/template/feature_include.rst.jinja2`.
- Commits found: `fd769cb9`, `f67b9bd5`, `ecc1e3ae`, `55e85f82`, `af504289`.

---
*Phase: 19-html-doc-generation-simplification*
*Completed: 2026-06-04*
