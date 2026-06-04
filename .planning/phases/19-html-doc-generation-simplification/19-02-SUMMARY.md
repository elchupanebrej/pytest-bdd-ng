---
phase: 19-html-doc-generation-simplification
plan: 02
subsystem: docs
tags: [sphinx, myst, markdown, readthedocs, pyproject]

requires:
  - phase: 19-html-doc-generation-simplification
    provides: Feature-tree Sphinx extension and shared ordering validation from Plan 19-01
provides:
  - Markdown root prose sources for README, DOCUMENTATION, AUTHORS, LICENSE, and CHANGES
  - MyST Sphinx entry pages for docs index, include aggregation, and feature navigation
  - Sphinx configuration that loads the local feature-tree extension and reads Markdown sources
  - Project metadata pointing README and LICENSE at Markdown sources
affects: [docs, readthedocs, package-metadata, feature-doc-generation]

tech-stack:
  added: [sphinxcontrib-mermaid]
  patterns:
    - Markdown root prose is the durable package/docs source
    - Sphinx feature Markdown copies are transient build artifacts ignored by git
    - docs/features/features.md is the committed navigation file populated by the feature-tree extension

key-files:
  created:
    - README.md
    - DOCUMENTATION.md
    - AUTHORS.md
    - LICENSE.md
    - CHANGES.md
    - docs/index.md
    - docs/include.md
    - docs/features/features.md
  modified:
    - docs/conf.py
    - pyproject.toml
    - .gitignore
  deleted:
    - README.rst
    - DOCUMENTATION.rst
    - AUTHORS.rst
    - LICENSE.rst
    - CHANGES.rst
    - docs/index.rst
    - docs/include.rst
    - docs/features/features.rst

key-decisions:
  - "Markdown root prose is now the project metadata and Sphinx include source."
  - "Sphinx source suffixes are explicit so `.md` files use the MyST Markdown parser."
  - "Build-time copied `.feature.md` files under docs/features are ignored; only features.md remains committed."

patterns-established:
  - "Use MyST `{include}` directives in docs/include.md for root Markdown prose."
  - "Use MyST `{toctree}` directives in docs/index.md and docs/features/features.md."
  - "Declare every configured Sphinx extension in the doc-gen extra."

requirements-completed: []

duration: 37 min
completed: 2026-06-04
---

# Phase 19 Plan 02: Markdown Documentation Source Migration Summary

**Markdown-first Sphinx entry pages with converted root prose, local feature-tree wiring, and package metadata pointed at Markdown sources**

## Performance

- **Duration:** 37 min
- **Started:** 2026-06-04T10:29:28Z
- **Completed:** 2026-06-04T11:06:15Z
- **Tasks:** 3
- **Files modified:** 17

## Accomplishments

- Converted `README`, `DOCUMENTATION`, `AUTHORS`, `LICENSE`, and `CHANGES` from RST to Markdown and deleted the old root RST sources.
- Added MyST Sphinx entry pages: `docs/index.md`, `docs/include.md`, and `docs/features/features.md`.
- Wired `docs/conf.py` to load `feature_tree`, use explicit Markdown/RST source suffix parsers, and keep `index` as the Sphinx root document.
- Updated `pyproject.toml` metadata to use `README.md` and `LICENSE.md`.
- Added `.gitignore` coverage for transient feature Markdown copies generated during Sphinx builds.

## Task Commits

1. **Task 19-02-01: Convert root prose to Markdown** - `457ed307` (`docs`)
2. **Task 19-02-02: Add Markdown Sphinx entry pages** - `2269dc07` (`docs`)
3. **Task 19-02-03: Wire Sphinx Markdown sources** - `f170d685` (`docs`)

Additional fix commits:

- `f8c7deca` (`fix`) - Declared `sphinxcontrib-mermaid` in `doc-gen`.
- `f534d306` (`fix`) - Ignored transient copied feature Markdown files and committed generated feature navigation.
- `412f2c08` (`fix`) - Repaired Markdown conversion warnings and explicit Sphinx parser mapping.

## Files Created/Modified

- `README.md` - Converted PyPI/GitHub README source with Markdown badges, links, tables, and snippets.
- `DOCUMENTATION.md` - Converted advanced usage documentation.
- `AUTHORS.md` - Converted author/contributor list with Markdown links.
- `LICENSE.md` - Converted MIT license text.
- `CHANGES.md` - Converted changelog with Markdown headings, links, and code formatting.
- `docs/index.md` - MyST root toctree entry page.
- `docs/include.md` - MyST include aggregation page for root Markdown prose and docs navigation.
- `docs/features/features.md` - MyST feature navigation with generated-tree markers and generated toctrees.
- `docs/conf.py` - Added local extension path, `feature_tree`, explicit source suffix parsers, and `root_doc`.
- `pyproject.toml` - Updated readme/license metadata and doc-gen dependency declaration.
- `.gitignore` - Ignored transient `docs/features/**/*.feature.md` build copies.

Deleted legacy RST sources:

- `README.rst`, `DOCUMENTATION.rst`, `AUTHORS.rst`, `LICENSE.rst`, `CHANGES.rst`
- `docs/index.rst`, `docs/include.rst`, `docs/features/features.rst`

## Verification

- `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html` - PASS; final build succeeded with 82 warnings.
- `docs/_build/html/index.html` spot check - PASS; rendered `include` navigation, README title, install section, and changelog link.
- `docs/_build/html/include.html` spot check - PASS; rendered README content, install snippet, changelog, `2.4.0`, and `2.4.0 legacy` headings.
- `docs/_build/html/features/features.html` spot check - PASS; rendered feature navigation from MyST toctrees.
- `docs/_build/html/features/01 Tutorial/01 Launch.feature.html` spot check - PASS; rendered copied feature page scenario content.
- Task acceptance checks - PASS for Markdown file existence, README badges/install links, CHANGES link/code-fence sanity, MyST include paths, generated-tree markers, Sphinx extension loading, Markdown source recognition, pyproject README metadata, and no active docs include paths pointing at deleted root RST files.

Remaining Sphinx warnings are not plan blockers:

- Duplicate source warnings come from old committed generated `.feature.rst` files that coexist with new transient `.feature.md` copies; deletion belongs to the next cleanup plan.
- Existing `toc.not_included` warnings for architecture/spec pages and two existing MyST cross-reference warnings in `DEPRECATIONS.md`/`MIGRATION.md` predate this plan.

## Decisions Made

- Kept root Markdown files as the single durable prose source and deleted matching root RST files in the same task.
- Used MyST `{include}` directives rather than RST include parser workarounds for root prose.
- Added `sphinxcontrib-mermaid` to `doc-gen` because `docs/conf.py` already configured `sphinxcontrib.mermaid` and local Sphinx verification could not import it without the dependency.
- Added a scoped `.gitignore` rule for transient feature Markdown copies to satisfy D-04 while keeping `docs/features/features.md` committed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Declared missing Sphinx mermaid dependency**
- **Found during:** Plan verification
- **Issue:** `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html` failed because `docs/conf.py` loaded `sphinxcontrib.mermaid`, but the `doc-gen` extra did not include `sphinxcontrib-mermaid`.
- **Fix:** Verified the package on PyPI and added `sphinxcontrib-mermaid` to `pyproject.toml` `doc-gen`.
- **Files modified:** `pyproject.toml`
- **Verification:** Sphinx build imported the extension and proceeded after the dependency was declared.
- **Committed in:** `f8c7deca`

**2. [Rule 2 - Missing Critical] Ignored transient feature Markdown copies**
- **Found during:** Plan verification
- **Issue:** Sphinx build copied `.feature.md` files under `docs/features/` and left them untracked. D-04 requires these build-time copies to be transient and gitignored.
- **Fix:** Added `docs/features/**/*.feature.md` to `.gitignore` and committed the generated navigation content in `docs/features/features.md`.
- **Files modified:** `.gitignore`, `docs/features/features.md`
- **Verification:** `git check-ignore "docs/features/01 Tutorial/01 Launch.feature.md"` passed; `git status --short` no longer listed copied feature Markdown files.
- **Committed in:** `f534d306`

**3. [Rule 1 - Bug] Repaired conversion warnings from Markdown sources**
- **Found during:** Plan verification
- **Issue:** Converted `AUTHORS.md` and `CHANGES.md` produced MyST cross-reference warnings from RST-style links, and `source_suffix` used list syntax that Sphinx 9 normalized ambiguously.
- **Fix:** Converted invalid contributor links to plain text or `mailto:` links, converted the stale README reference in `CHANGES.md` to code text, and made `source_suffix` an explicit parser map.
- **Files modified:** `AUTHORS.md`, `CHANGES.md`, `docs/conf.py`
- **Verification:** Final Sphinx build no longer reported warnings from `AUTHORS.md` or `CHANGES.md`, and Markdown sources remained rendered.
- **Committed in:** `412f2c08`

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 missing critical, 1 bug)
**Impact on plan:** All fixes were required for local verification or D-04 correctness. No architectural scope change.

## Issues Encountered

- `pandoc` conversion emitted one unresolved `pytest-bdd` reference warning from `DOCUMENTATION.rst`; the converted Markdown was manually repaired to link to the upstream pytest-bdd repository.
- First Sphinx verification failed on missing `sphinxcontrib.mermaid`; fixed as a dependency declaration deviation.
- Final Sphinx build still reports warnings from old generated `.feature.rst` files and unrelated pre-existing docs navigation gaps. The build succeeds and uses `.feature.md` pages where duplicates exist.

## Known Stubs

None. Stub-pattern hits found during scanning were existing test/source fixtures or source feature content, not stubs introduced by this plan.

## Threat Flags

None. This plan changed documentation source formats and build-time file copying/metadata only; no new network endpoints, auth paths, runtime file access paths, or schema trust boundaries were introduced.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Plan 19-03. Markdown entry pages build successfully, root prose is Markdown, and transient feature Markdown copies are ignored. The next cleanup plan should remove old generated `.feature.rst` artifacts and the obsolete RST/pandoc conversion pipeline to eliminate duplicate-source warnings.

## Self-Check: PASSED

- Files found: `README.md`, `DOCUMENTATION.md`, `AUTHORS.md`, `LICENSE.md`, `CHANGES.md`, `docs/index.md`, `docs/include.md`, `docs/features/features.md`, `docs/conf.py`, `pyproject.toml`, `.gitignore`, `.planning/phases/19-html-doc-generation-simplification/19-02-SUMMARY.md`.
- Commits found: `457ed307`, `2269dc07`, `f170d685`, `f8c7deca`, `f534d306`, `412f2c08`.

---
*Phase: 19-html-doc-generation-simplification*
*Completed: 2026-06-04*
