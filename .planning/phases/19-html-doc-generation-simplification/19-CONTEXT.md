# Phase 19: html-doc-generation-simplification - Context

**Gathered:** 2026-06-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Simplify HTML documentation generation by replacing the current `features/` Markdown to generated RST to Sphinx HTML pipeline with a single Sphinx build path that reads Markdown feature files through MyST. This phase owns removal of the `bdd_tree_to_rst` script and entry point, deletion of committed generated feature RST artifacts, migration of root project prose from RST to Markdown, addition of the local Sphinx feature-tree extension, dependency cleanup for `doc-gen`, and verification that ReadTheDocs can still build equivalent HTML output.

This phase does not own runtime Cucumber HTML report behavior, formatter bridge changes, CI matrix redesign, documentation content rewrites beyond format conversion, or new user-facing documentation sections.

</domain>

<decisions>
## Implementation Decisions

### Migration Boundary
- **D-01:** Execute the spec-complete migration in one phase. Remove `bdd_tree_to_rst`, committed generated feature RST docs, pandoc/pypandoc/panflute dependencies, RST feature templates, the `features-docs` Makefile target, and any CI/pre-commit calls to that target as part of this phase.
- **D-02:** Do not keep the old generated RST pipeline as a fallback. Once the new Sphinx/MyST path lands, the old conversion stack is deleted.

### Feature Tree Build Behavior
- **D-03:** The new Sphinx feature-tree extension must fail hard on invalid feature tree structure, duplicate or missing ordering prefixes, copy errors, missing files, or MyST/Sphinx rendering issues. Warnings that allow incomplete feature docs are not acceptable.
- **D-04:** Feature files copied into `docs/features/` during Sphinx build are transient build artifacts and must be gitignored. Durable committed docs under `docs/features/` should be limited to index/navigation files such as `features.md`.

### Root RST to Markdown Conversion
- **D-05:** Convert root `.rst` prose files to `.md` once during this migration, then include the converted Markdown files in Sphinx HTML generation.
- **D-06:** Delete the old root `.rst` files in the same phase after conversion. Markdown becomes the single source for `README`, `DOCUMENTATION`, `AUTHORS`, `LICENSE`, and `CHANGES`.
- **D-07:** Update project metadata and docs includes to reference Markdown sources, including the `pyproject.toml` README declaration and `docs/include.md`.

### Verification
- **D-08:** Verification must include local Sphinx build, content checks for rendered feature pages, proof that pandoc is not required/invoked, proof that generated feature RST files are gone, and manual ReadTheDocs preview spot-check before merge.
- **D-09:** `CHANGES.md` and `README.md` need explicit spot-checks because conversion quality affects changelog rendering and PyPI README rendering.

### the agent's Discretion
- Exact shape of `docs/ext/feature_tree.py`, provided it preserves ordering-prefix validation and fails hard on invalid input.
- Exact split of shared ordering-prefix utilities, provided planner keeps validation testable without depending on deleted `bdd_tree_to_rst`.
- Exact MyST directive syntax in `docs/index.md`, `docs/include.md`, and `docs/features/features.md`, provided Sphinx builds cleanly and navigation matches existing feature docs.
- Exact automated conversion command for one-time RST to Markdown migration, provided converted files are manually reviewed before commit.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Definition and Design
- `.planning/ROADMAP.md` - Phase 19 entry and dependency on Phase 18.
- `.planning/PROJECT.md` - Project constraints, docs/generated-artifact expectations, and core value.
- `.planning/REQUIREMENTS.md` - Requirement traceability and deferred testing context.
- `docs/superpowers/specs/2026-06-03-html-doc-generation-simplification-design.md` - Approved baseline design for the Sphinx/MyST feature-tree migration. Decisions in this context refine and lock discussion choices.

### Prior Phase Decisions
- `.planning/phases/17-adapt-github-ci-to-use-make-and-validate-with-act/17-CONTEXT.md` - Makefile as project command boundary and visible CI setup ownership.
- `.planning/phases/18-split-xdist-remote-tests-into-separate-parallel-gha-executor/18-CONTEXT.md` - Preserve Makefile boundary and avoid unrelated CI redesign.

### Codebase Maps
- `.planning/codebase/CONVENTIONS.md` - Python style, docs conventions, generated docs handling, and lint expectations.
- `.planning/codebase/STRUCTURE.md` - Documentation, feature files, script, template, and Sphinx directory layout.

### Source and Configuration
- `src/pytest_bdd/script/bdd_tree_to_rst.py` - Existing feature Markdown to generated RST pipeline to delete after extracting reusable ordering logic.
- `src/pytest_bdd/template/feature_include.rst.jinja2` - RST feature include template to delete.
- `src/pytest_bdd/template/features_index.rst.jinja2` - RST feature index template to delete.
- `src/pytest_bdd/template/features_section.rst.jinja2` - RST feature section template to delete.
- `src/pytest_bdd/template/test.py.jinja2` - Code-generator template that is unrelated and must be kept.
- `docs/conf.py` - Sphinx configuration; add MyST/local feature-tree extension and remove old conversion assumptions.
- `docs/index.rst` - Legacy Sphinx index to replace with Markdown.
- `docs/include.rst` - Legacy include page to replace with Markdown.
- `docs/features/features.rst` - Generated feature docs index to replace with `docs/features/features.md`.
- `docs/features/` - Current committed generated feature RST tree; generated RST files should be deleted.
- `features/` - Source-of-truth executable feature Markdown tree.
- `pyproject.toml` - Remove `bdd_tree_to_rst` entry point, update `doc-gen` dependencies, update README metadata, and remove deleted templates from package data.
- `Makefile` - Remove `features-docs` target and any stale feature-doc generation command.
- `.pre-commit-config.yaml` - Remove/update `generate-feature-doc` hook that calls `bdd_tree_to_rst`.
- `.gitignore` - Ignore Sphinx build-time feature file copies under `docs/features/`.
- `.readthedocs.yaml` - Expected to remain unchanged unless planning finds a hard blocker.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/pytest_bdd/script/bdd_tree_to_rst.py`: source for existing ordering-prefix validation behavior; extract only needed validation logic into a smaller shared utility before deleting the script.
- `features/`: source-of-truth feature Markdown tree that Sphinx should read through copied transient files.
- `docs/conf.py`: existing Sphinx config already uses `myst_parser` and ReadTheDocs-compatible settings.
- `Makefile`: current `features-docs` target calls `uv run bdd_tree_to_rst $(FEATURES_ROOT) $(FEATURE_DOCS_OUTPUT)`.

### Established Patterns
- Generated docs under `docs/features/` are derived from `features/` and should not become hand-edited source.
- Makefile remains the project command boundary for developer-facing build/test/docs commands.
- CI/readthedocs setup should stay visible; project-specific command internals belong in project files.
- Public source files need typed, ruff-compatible Python and should avoid broad rewrites outside the phase boundary.

### Integration Points
- Add `docs/ext/feature_tree.py` and wire it through `docs/conf.py`.
- Add shared ordering logic in `src/pytest_bdd/script/_feature_tree.py` if planner needs production-tested validation outside the Sphinx extension.
- Replace `docs/index.rst` and `docs/include.rst` with Markdown equivalents that include root Markdown files.
- Replace `docs/features/features.rst` with `docs/features/features.md` that preserves durable intro/suffix text and generated toctree block.
- Remove `bdd_tree_to_rst` entry point and deleted RST templates from `pyproject.toml`.
- Remove pre-commit/Makefile hooks that generate committed feature RST artifacts.

</code_context>

<specifics>
## Specific Ideas

- Build output should keep the same conceptual URL/navigation shape for ReadTheDocs feature pages.
- The feature-tree extension should preserve the ordering-prefix rules from `bdd_tree_to_rst`: numeric prefixes are required, duplicates at the same level are hard errors, and missing prefixes on siblings are hard errors.
- Sphinx build should copy `.feature.md` files into `docs/features/` at build time rather than committing mirrored copies.
- `README.md` and `CHANGES.md` require manual review after conversion because PyPI/readme rendering and changelog links/code blocks are high-risk.
- Verification should include `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html`, rendered feature-page content checks, no pandoc dependency/import requirement, no generated feature RST files, and ReadTheDocs preview spot-check.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

### Reviewed Todos (not folded)
- **Integrate BDD/ATDD tests into development workflow and UAT phase** - weak todo match only through generic planning terms; out of scope for HTML doc generation simplification.
- **Vulture must be run not via pytest but as pre-commit hook** - weak match and already handled by earlier scope; unrelated to docs pipeline migration.
- **Fix Makefile SHELL for cross-platform (Win/Mac/Linux)** - weak match through generic Makefile wording; unrelated except that Phase 19 still respects Makefile command-boundary patterns.

</deferred>

---

*Phase: 19-html-doc-generation-simplification*
*Context gathered: 2026-06-04*
