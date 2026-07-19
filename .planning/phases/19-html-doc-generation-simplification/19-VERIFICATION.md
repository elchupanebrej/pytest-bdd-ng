---
phase: 19-html-doc-generation-simplification
verified: 2026-06-04T18:48:54Z
status: human_needed
score: 9/9 must-haves verified
overrides_applied: 0
human_verification:
  - test: "ReadTheDocs preview build"
    expected: "Preview build succeeds from `.readthedocs.yaml` without pandoc or the removed feature RST generator."
    why_human: "Requires branch/PR preview service behavior after push."
  - test: "ReadTheDocs feature navigation"
    expected: "Feature navigation page renders and links to copied `.feature.md` pages with scenario content."
    why_human: "Requires hosted ReadTheDocs preview and link inspection."
  - test: "README/PyPI rendering"
    expected: "`README.md` renders badges, install block, tables, Gherkin example, and project layout without broken Markdown."
    why_human: "Package index rendering cannot be proven by local Sphinx output alone."
  - test: "CHANGES rendering"
    expected: "`CHANGES.md` renders version headings, nested lists, links, and code formatting without conversion artifacts."
    why_human: "Requires rendered changelog preview or equivalent human review."
---

# Phase 19: HTML doc generation simplification Verification Report

**Phase Goal:** HTML doc generation simplification: durable documentation source conversion to Markdown/Sphinx/MyST/local feature-tree extension, removal of obsolete RST generation pipeline, docs/tooling cleanup, and captured manual UAT where local verification cannot prove merge/post-push behavior.
**Verified:** 2026-06-04T18:48:54Z
**Status:** human_needed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | D-01: Full migration removes old generated RST pipeline. | VERIFIED | `src/pytest_bdd/script/bdd_tree_to_rst.py` and feature RST templates are absent; `rg "bdd_tree_to_rst\|features-docs\|pypandoc\|panflute" pyproject.toml Makefile .pre-commit-config.yaml tox.ini .github docs src tests` found no active old generator path. Historical/design-only `pandoc` mentions remain, not active commands. |
| 2 | D-02: No fallback to old generated RST pipeline remains. | VERIFIED | No `bdd_tree_to_rst` console script in `pyproject.toml`; no `features-docs` Makefile target; no pre-commit/tox/CI command path for old generator. |
| 3 | D-03: Invalid feature tree structure fails hard. | VERIFIED | `src/pytest_bdd/script/_feature_tree.py` raises `OrderingValidationError` for missing/duplicate prefixes; `docs/ext/feature_tree.py` wraps validation/copy/write failures in `sphinx.errors.ExtensionError`; contract tests pass. |
| 4 | D-04: Copied feature docs are transient and gitignored. | VERIFIED | `.gitignore` contains `docs/features/**/*.feature.md`, `docs/features/**/*.feature.gherkin`, and `docs/features/**/*.bdd.yaml`; durable committed feature source is `docs/features/features.md`. |
| 5 | D-05: Converted Markdown root prose is included in Sphinx HTML. | VERIFIED | `README.md`, `DOCUMENTATION.md`, `AUTHORS.md`, `LICENSE.md`, `CHANGES.md` exist; `docs/include.md` includes all through MyST `{include}` directives; Sphinx build succeeded. |
| 6 | D-06: Old root RST files are deleted. | VERIFIED | Legacy root/docs RST replacements are absent by path inspection: `README.rst`, `DOCUMENTATION.rst`, `AUTHORS.rst`, `LICENSE.rst`, `CHANGES.rst`, `docs/index.rst`, `docs/include.rst`, `docs/features/features.rst`. |
| 7 | D-07: Metadata and docs includes reference Markdown sources. | VERIFIED | `pyproject.toml` uses `readme = {file = "README.md", content-type = "text/markdown"}` and `license = {file = "LICENSE.md"}`; `docs/conf.py` maps `.md` to Markdown and loads `feature_tree`; `docs/include.md` references Markdown paths. |
| 8 | D-08: Verification proves local Sphinx build, rendered feature pages, no pandoc requirement, no generated feature RST files, and captures RTD preview UAT. | VERIFIED | `rtk uv run --extra doc-gen sphinx-build -b html docs docs/_build/html` exited 0; `docs/_build/html/features/features.html` exists; `01 Launch.feature.html` contains Feature/Scenario/Given/When/Then HTML; `docs/features` has no `.rst`; `19-UAT.md` captures RTD preview as blocking manual gate. |
| 9 | D-09: README.md and CHANGES.md get explicit spot-checks. | VERIFIED | `19-UAT.md` includes blocking README/PyPI and CHANGES rendering checks with owner/status/evidence fields; local Sphinx includes both files via `docs/include.md`. |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/pytest_bdd/script/_feature_tree.py` | Shared feature-tree ordering and validation logic | VERIFIED | Substantive typed module with `OrderingValidationError`, ordered source models, prefix parsing, deterministic walking, and validation errors. |
| `docs/ext/feature_tree.py` | Local Sphinx extension that prepares Markdown feature docs | VERIFIED | Defines `setup(app: Sphinx)`, registers `builder-inited`, calls `walk_feature_tree`, copies `.feature.md`, writes `features.md`, raises `ExtensionError`. SDK artifact checker missed literal `setup(app)` because annotation changes text shape. |
| `docs/index.md` | Markdown Sphinx root index | VERIFIED | Contains MyST toctree. |
| `docs/include.md` | Markdown include/navigation page | VERIFIED | Includes root Markdown prose and navigation to features/internal/tutorial. |
| `.gitignore` | Ignore rules for transient copied feature docs | VERIFIED | Contains Markdown, Gherkin, and StructBDD feature-copy ignore globs. |
| `Makefile` | Sphinx docs command and no separate feature-doc generation target | VERIFIED | `docs: env-check` runs `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html`; `features-docs` not present. SDK checker missed negative literal "No features-docs target"; manual search verified absence. |
| `.planning/phases/19-html-doc-generation-simplification/19-UAT.md` | Manual verification checklist | VERIFIED | Contains blocking RTD preview, feature navigation, README/PyPI rendering, and CHANGES rendering checks. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `docs/conf.py` | `docs/ext/feature_tree.py` | `sys.path.insert(... docs/ext)` and `extensions = [..., "feature_tree"]` | WIRED | Sphinx build loads extension and succeeds. |
| `docs/ext/feature_tree.py` | `features/` and `docs/features/` | `prepare_feature_tree` on `builder-inited` | WIRED | Extension derives project root, validates `features/`, copies into `docs/features/`, writes `features.md`. |
| `docs/features/features.md` | copied feature Markdown pages | MyST generated toctrees without suffix | WIRED | Generated entries such as `01 Tutorial/01 Launch.feature`; rendered HTML page exists. |
| `Makefile` | Sphinx docs build | `docs` target runs `sphinx-build` | WIRED | Target exists; old `features-docs` target absent. |
| `pyproject.toml` | Markdown package metadata | `README.md` and `LICENSE.md` metadata | WIRED | Metadata points at Markdown sources. |
| `.readthedocs.yaml` | Sphinx docs config | `sphinx.configuration: docs/conf.py` | WIRED | RTD config still points at current Sphinx config. Hosted preview remains human UAT. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `docs/ext/feature_tree.py` | `feature_directories` | `walk_feature_tree(features_path)` reading real `features/` tree | Yes | FLOWING |
| `docs/features/features.md` | generated toctree entries | Sphinx extension generated from `features/**/*.feature.md` | Yes | FLOWING |
| `docs/_build/html/features/01 Tutorial/01 Launch.feature.html` | rendered scenario content | copied Markdown feature page parsed by MyST/Sphinx | Yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Contract tests for feature-tree extension and packaging | `rtk uv run python -m pytest tests/cases/contract/doc/test_doc.py tests/cases/contract/generation/test_template_packaging.py -q` | `15 passed in 0.64s` | PASS |
| Ruff on phase code/tests | `rtk uv run ruff check docs/ext/feature_tree.py src/pytest_bdd/script/_feature_tree.py tests/cases/contract/doc/test_doc.py tests/cases/contract/generation/test_template_packaging.py` | `All checks passed!` | PASS |
| Sphinx HTML build | `rtk uv run --extra doc-gen sphinx-build -b html docs docs/_build/html` | Exit 0; build succeeded with 15 known docs warnings | PASS |
| Rendered feature page content | `Select-String docs/_build/html/features/01 Tutorial/01 Launch.feature.html -Pattern 'Feature:|Scenario:|Given|When|Then'` | Feature, Scenario, Given, When, Then content found | PASS |
| Generated feature RST absence | `Get-ChildItem -Recurse docs/features -Filter *.rst` | No files returned | PASS |

### Probe Execution

| Probe | Command | Result | Status |
|---|---|---|---|
| Conventional probes | `Get-ChildItem scripts -Recurse -Filter 'probe-*.sh'` | No probe files found | SKIPPED |

### Requirements Coverage

Plan frontmatter `requirements:` arrays are empty for all four Phase 19 plans, and `.planning/REQUIREMENTS.md` has no Phase 19 requirement IDs. Decision IDs D-01 through D-09 from Phase 19 context/plans were verified above.

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| None | 19-01..19-04 | No requirement IDs declared | N/A | Requirements coverage not applicable; decision must-haves verified instead. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `.planning/phases/19-html-doc-generation-simplification/19-UAT.md` | 18-21 | `TBD`, `BLOCKING - pending` | INFO | Intentional manual UAT evidence placeholders; drive `human_needed` status. |
| `README.md` | 31 | `not available` | INFO | User-facing descriptive text, not a placeholder/stub. |
| `pyproject.toml` | 373 | `TD`/TODO rule label | INFO | Ruff rule configuration label, not debt marker. |

### Human Verification Required

### 1. ReadTheDocs Preview Build

**Test:** Trigger or inspect the branch/PR ReadTheDocs preview build.
**Expected:** Preview build succeeds from `.readthedocs.yaml` without adding pandoc or the removed feature RST generator.
**Why human:** Hosted preview build behavior is external to local repo verification.

### 2. ReadTheDocs Feature Navigation

**Test:** Open the preview feature navigation page and one copied feature page.
**Expected:** Feature navigation renders and links to copied `.feature.md` pages with scenario content.
**Why human:** Requires preview URL and browser/link inspection.

### 3. README/PyPI Rendering

**Test:** Render README through PyPI/check-render or package preview.
**Expected:** Badges, install block, tables, Gherkin example, and project layout render without broken Markdown.
**Why human:** PyPI renderer behavior differs from Sphinx and needs preview evidence.

### 4. CHANGES Rendering

**Test:** Inspect rendered changelog preview.
**Expected:** Version headings, nested lists, links, and code formatting render without conversion artifacts.
**Why human:** Conversion quality requires rendered content inspection.

### Gaps Summary

No automated blocker gaps found. Phase goal is technically achieved in the codebase, but completion cannot be marked `passed` because Phase 19 intentionally carries four pending manual UAT gates for hosted ReadTheDocs and rendered README/CHANGES behavior.

---

_Verified: 2026-06-04T18:48:54Z_
_Verifier: the agent (gsd-verifier)_
