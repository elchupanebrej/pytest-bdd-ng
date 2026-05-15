# Phase 07: Documentation - Context

**Gathered:** 2026-05-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Documentation phase for pytest-bdd-ng stabilization. Three requirements:

1. **DOC-01:** All public API functions in `src/pytest_bdd/__init__.py` have comprehensive docstrings with parameter and return descriptions
2. **DOC-02:** `DEVELOPMENT.rst` updated with current conventions — comprehensive rewrite
3. **DOC-03:** Migration guide for users coming from pytest-bdd (original) — focused on top breaking changes

Plus: `DEPRECATIONS.md` listing deprecated features with replacement paths and timeline.

Parsers (`parsers.py`) are FROZEN — no modifications, tests only, no documentation changes needed.

## Exclusions

- New feature documentation beyond public API — Phase 8 (BDD Acceptance Testing)
- Internal architecture docs — already exist in `docs/internal/`
- Generated feature docs in `docs/features/` — auto-generated, not manual
</domain>

<decisions>
## Docstring Approach

- **D-01:** Comprehensive docstrings — full examples, edge cases, cross-references to related functions
- **D-02:** Google-style format — `Args:`, `Returns:`, `Raises:`, `Example:` sections
- **D-03:** Scope covers all `__all__` exports: `scenario`, `scenarios`, `given`, `when`, `then`, `step`, `FeaturePathType`, `PytestBDDStepDefinitionWarning`
- **D-04:** Docstrings are the source of truth for API reference — Sphinx autodoc generates from them

## DEVELOPMENT.rst

- **D-05:** Comprehensive rewrite, not minimal update
- **D-06:** Must include: architecture overview, plugin development lifecycle, testing strategy (unit/feature/e2e/messages), BDD workflow, CI matrix, StashBound pattern, attrs usage, plugin class standard
- **D-07:** Current file (uv setup + test running) is insufficient — replace with full developer guide

## Migration Guide

- **D-08:** Focused guide — top 10 breaking changes with before/after code examples
- **D-09:** Primary audience: existing pytest-bdd users migrating to pytest-bdd-ng
- **D-10:** Format: quick-reference style, not exhaustive API diff
- **D-11:** Cover: fixture injection differences, hook name changes, configuration changes, CLI flag differences, step definition pattern changes

## Documentation Format

- **D-12:** Sphinx autodoc for API reference (generated from docstrings)
- **D-13:** Manual RST for guides (DEVELOPMENT.rst, migration guide, DEPRECATIONS.md)
- **D-14:** Existing `docs/` structure preserved — new docs added alongside generated feature docs

## Deferred Ideas

- Full API diff from original pytest-bdd — too comprehensive for this phase; focused guide is sufficient
- Markdown docs at repo root — RST + Sphinx is the established pattern; Markdown would duplicate effort
- Tutorial expansion — Phase 8 (BDD Acceptance Testing) will cover undocumented behaviors
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/ROADMAP.md` — Phase 7 goal: "Public API docstrings, developer guide, migration guide"
- `.planning/REQUIREMENTS.md` — DOC-01, DOC-02, DOC-03 requirements
- `.planning/PROJECT.md` — Core value, constraints (ruff, attrs, StashBound, no comments unless asked)
- `src/pytest_bdd/__init__.py` — Public API surface (`__all__` exports)
- `src/pytest_bdd/scenario.py` — `scenario()`, `scenarios()`, `FeaturePathType` implementations
- `src/pytest_bdd/steps.py` — `given`, `when`, `then`, `step` implementations
- `src/pytest_bdd/types/warning.py` — `PytestBDDStepDefinitionWarning`
- `DEVELOPMENT.rst` — Existing development guide (to be replaced)
- `docs/` — Existing documentation structure
- `docs/internal/` — Internal architecture docs (reference for DEVELOPMENT.rst content)
</canonical_refs>

<code_context>
## Reusable Assets and Patterns

**Existing documentation infrastructure:**
- `docs/index.rst` — Root documentation index
- `docs/include.rst` — Shared RST includes
- `docs/features/` — Auto-generated feature docs (from `features/*.feature.md`)
- `docs/internal/` — Internal architecture docs (cucumber formatter, execution context, etc.)
- `docs/tutorial/index.rst` — Tutorial entry point

**Public API surface (small — 8 exports):**
- `scenario()` — Single scenario decorator/loader
- `scenarios()` — Bulk scenario loader
- `given()` / `when()` / `then()` / `step()` — Step definition decorators (lazy-loaded via `__getattr__`)
- `FeaturePathType` — Type alias for feature path handling
- `PytestBDDStepDefinitionWarning` — Warning class for ambiguous step definitions

**Codebase patterns to document:**
- `StashBound` base class for pytest config stash access (model layer)
- `attrs` library for data classes (not stdlib dataclass)
- Plugin class-based pattern (`class + entrypoint + hook.py`)
- testdir pattern for integration tests
- BDD acceptance tests in `features/` as `.feature.md` files
</code_context>

<specifics>
## Specific Ideas

- Sphinx autodoc setup needs `conf.py`, `extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']` for Google-style
- Migration guide should reference actual pytest-bdd (original) API — check their docs/source for comparison
- DEPRECATIONS.md should list: legacy `--cucumberjson` flag (removed in Phase 1), dead Allure plugin (removed in Phase 1), any other deprecated features
- DEVELOPMENT.rst should include the GSD planning workflow since this project uses ATDD/BDD
</specifics>

---

*Phase: 07-Documentation*
*Context gathered: 2026-05-15*
