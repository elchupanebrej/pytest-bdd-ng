# HTML Doc Generation Simplification

## Problem

The current documentation pipeline converts feature files (`.feature.md`, Markdown/GFM Gherkin) to
HTML in two stages:

1. **Pre-build step** (legacy feature-doc make target → legacy RST converter): Walks `features/`, calls
   Pandoc through Python wrappers to convert each `.feature.md` → `.feature.rst`,
   and writes Jinja2-rendered RST toctree index files into `docs/features/`. These RST artifacts are
   committed to the repository.

2. **Sphinx build**: Reads the committed RST artifacts and renders HTML via ReadTheDocs.

### Pain Points

- **System binary dependency**: `pandoc` must be installed on every dev machine and CI node.
- **Heavy dep group**: `doc-gen` pulls in Pandoc conversion wrappers plus `sphinx>=7`, `myst-parser`.
- **RST is a leaky abstraction**: Feature files are Markdown, but the intermediate representation is RST. Developers must reason about two markup languages.
- **Committed generated artifacts**: `docs/features/**/*.rst` are generated files that live in git, causing noisy diffs whenever the feature tree changes.
- **Two-step workflow**: Forgetting the legacy feature-doc make target before `sphinx-build` produces stale docs.
- **~570-line script**: the legacy RST converter is complex for what is essentially a tree-walk + format conversion.
- **Root files in RST**: `README.rst`, `DOCUMENTATION.rst`, `AUTHORS.rst`, `LICENSE.rst`, `CHANGES.rst` require the `.. include::` workaround with `:parser: myst_parser.sphinx_` for the `.md` siblings.

## Goal

Reduce the doc pipeline to a **single Sphinx build step** that reads `.feature.md` files natively
via MyST-Parser, with no `pandoc`, no intermediate RST conversion, and no committed generated artifacts
from the feature tree. Retain ReadTheDocs with zero configuration change.

---

## Architecture

```text
features/**/*.feature.md   ← source of truth (unchanged)
        │
        ▼
docs/ext/feature_tree.py   ← new local Sphinx extension (~80 lines)
  Runs on `builder-inited` hook:
    - Walks features/ with ordering-prefix validation
    - Copies .feature.md files into docs/features/ (transient, gitignored)
    - Writes docs/features/features.md (MyST toctree index, committed)
        │
        ▼
Sphinx + myst-parser
  - MyST reads .feature.md files directly (no RST wrapper, no pandoc)
  - docs/index.md replaces docs/index.rst
  - docs/include.md replaces docs/include.rst
  - Root prose: README.md, DOCUMENTATION.md, CHANGES.md, AUTHORS.md, LICENSE.md
        │
        ▼
HTML (ReadTheDocs, alabaster theme, same URL)
```

---

## Proposed Changes

### Feature Tree Extension

**New file**: `docs/ext/feature_tree.py`

A Sphinx extension that hooks into `builder-inited`. It:

1. Walks `features/` using the same ordering-prefix logic from the legacy RST converter
   (numeric prefix `NN`, `NN-`, or `NN_` on files and directories, duplicate/missing prefix validation).
2. **Copies** each `.feature.md` file to a mirrored path under `docs/features/`
   (e.g., `features/01 Tutorial/01 Launch.feature.md` → `docs/features/01 Tutorial/01 Launch.feature.md`).
   Copies are **not committed** — they are listed in `.gitignore`.
3. Writes `docs/features/features.md` — a MyST Markdown file with `{toctree}` directives
   mirroring the current `features.rst` structure. This file **is committed** (it holds the
   manually-written introduction block, same as today).

The copy-at-build-time sub-approach is chosen over path cross-references because:
- It requires no `conf.py` `exclude_patterns` hacks to admit files from outside `docs/`.
- Sphinx source discovery works without reconfiguration.
- The pattern mirrors the current behaviour (files appear under `docs/features/`) but without the RST conversion step.

**Ordering prefix rules** (preserved from the legacy RST converter):
- Every file and directory directly under a feature directory must have a numeric prefix (`NN`, `NN-`, or `NN_`).
- Duplicate prefixes at the same level are a hard error.
- Missing prefixes on siblings are a hard error.
- The extension exits sphinx with a clear error message on validation failure.

**Template output** (`docs/features/features.md` generated section):

````markdown
% BEGIN AUTO-GENERATED FEATURES TREE

## Tutorial

```{toctree}
:maxdepth: 2

01 Tutorial/01 Launch.feature
```

% END AUTO-GENERATED FEATURES TREE
````

The extension preserves intro text before the generated block and suffix text after it (same
idempotence contract as the legacy RST converter).

---

### Jinja2 RST Templates (Deleted)

The following template files are removed (they only served the legacy RST converter):

- `src/pytest_bdd/template/feature_include.rst.jinja2`
- `src/pytest_bdd/template/features_index.rst.jinja2`
- `src/pytest_bdd/template/features_section.rst.jinja2`

The `test.py.jinja2` template (used by the code generator plugin, unrelated to docs) is **kept**.

---

### Legacy RST converter (Deleted)

The legacy RST converter script is deleted.

The entry point in `pyproject.toml` is removed:
```toml
# REMOVE:
legacy_converter = "legacy.module:main"
```

The ordering-prefix validation logic (the `OrderedSource`, `OrderingValidationError`, prefix parsing
functions) is **extracted** into a small shared utility module
`src/pytest_bdd/script/_feature_tree.py` so the Sphinx extension can import it without depending
on the full legacy RST conversion stack. This keeps the validation logic in one place and testable.

---

### Root Prose Files (RST → Markdown)

The following root files are converted from RST to Markdown (one-time automated conversion
via `pandoc` locally, with manual review):

| Old | New |
|-----|-----|
| `README.rst` | `README.md` |
| `DOCUMENTATION.rst` | `DOCUMENTATION.md` |
| `AUTHORS.rst` | `AUTHORS.md` |
| `LICENSE.rst` | `LICENSE.md` |
| `CHANGES.rst` | `CHANGES.md` |

`DEPRECATIONS.md` and `MIGRATION.md` are already Markdown — no change needed.

**`pyproject.toml` README entry** updated:
```toml
# Before:
readme = {file = "README.rst", content-type = "text/x-rst"}
# After:
readme = {file = "README.md", content-type = "text/markdown"}
```

> **Note**: The RST → MD conversion of `CHANGES.rst` requires careful review because it contains
> RST hyperlink references (`.. _label: url` style) and code-block directives. The automated
> conversion will be verified manually before committing.

---

### Sphinx Configuration (`docs/conf.py`)

```python
# Add local extension path
sys.path.insert(0, str(Path(__file__).parent / "ext"))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinxcontrib.mermaid",
    "myst_parser",
    "feature_tree",  # ← new local extension
]

# MyST settings — colon_fence is enabled by default in MyST-Parser >=2.0
# Enable explicitly if using MyST <2.0 or if directives are not recognised:
# myst_enable_extensions = ["colon_fence"]

source_suffix = [".rst", ".md"]  # keep .rst for any remaining legacy files
```

The Pandoc-wrapper imports and `ensure_pandoc_installed()` calls are removed from `conf.py` (currently
not present but referenced via the legacy converter import chain).

---

### Sphinx Index and Include Files

**`docs/index.md`** (replaces `docs/index.rst`):
````markdown
# Welcome to Pytest-BDD-NextGeneration's documentation!

```{toctree}
include
```
````

**`docs/include.md`** (replaces `docs/include.rst`):

````markdown
```{include} ../README.md
```

```{toctree}
:maxdepth: 2

features/features
internal/index
tutorial/index
```

```{include} ../DOCUMENTATION.md
```
```{include} ../AUTHORS.md
```
```{include} ../LICENSE.md
```
```{include} ../CHANGES.md
```
```{include} ../DEPRECATIONS.md
```
```{include} ../MIGRATION.md
```
````

---

### Dependencies (`pyproject.toml`)

```toml
# Before:
doc-gen = [
  'pandoc',
  'legacy-pandoc-wrapper-a',
  'legacy-pandoc-wrapper-b',
  'sphinx>=7.0',
  'myst-parser'
]

# After:
doc-gen = [
  'sphinx>=7.0',
  'myst-parser',
  'sphinxcontrib-mermaid'
]
```

`sphinxcontrib-mermaid` is added explicitly (it was previously a transitive dep via the Sphinx
chain but should be declared).

---

### `.gitignore`

Add entries to ignore the copied feature files:
```text
# Sphinx build-time feature file copies
docs/features/**/*.feature.md
docs/features/**/*.feature.gherkin
docs/features/**/*.bdd.yaml
```

The `docs/features/features.md` index file and any subdirectory `index.md` files remain committed.

---

### `Makefile`

The legacy feature-doc target is removed (the step no longer exists as a separate action).
The legacy feature-doc make step is also removed from any CI/CD workflows that call it.

The `doc-gen` UV extra in `UV_SYNC_EXTRAS` can drop Pandoc conversion wrapper references.

---

### `setuptools.package-data` (Deleted Templates)

Remove the deleted templates from `pyproject.toml`:
```text
# REMOVE from pytest_bdd.template:
"feature_include.rst.jinja2",
"features_index.rst.jinja2",
"features_section.rst.jinja2",
```

Keep `test.py.jinja2`.

---

### ReadTheDocs (`.readthedocs.yaml`)

**No changes.** The file already points to `sphinx: configuration: docs/conf.py` and installs
the project via `python: install: - path: .`. The `doc-gen` extra will be picked up automatically.

---

## Files Summary

| Action | File |
|--------|------|
| NEW | `docs/ext/feature_tree.py` |
| NEW | `src/pytest_bdd/script/_feature_tree.py` (shared ordering logic) |
| NEW | `docs/features/features.md` (replaces `features.rst`) |
| NEW | `docs/index.md` (replaces `index.rst`) |
| NEW | `docs/include.md` (replaces `include.rst`) |
| CONVERT | `README.rst` → `README.md` |
| CONVERT | `DOCUMENTATION.rst` → `DOCUMENTATION.md` |
| CONVERT | `AUTHORS.rst` → `AUTHORS.md` |
| CONVERT | `LICENSE.rst` → `LICENSE.md` |
| CONVERT | `CHANGES.rst` → `CHANGES.md` |
| MODIFY | `docs/conf.py` |
| MODIFY | `pyproject.toml` |
| MODIFY | `Makefile` |
| MODIFY | `.gitignore` |
| DELETE | legacy RST converter script |
| DELETE | `src/pytest_bdd/template/feature_include.rst.jinja2` |
| DELETE | `src/pytest_bdd/template/features_index.rst.jinja2` |
| DELETE | `src/pytest_bdd/template/features_section.rst.jinja2` |
| DELETE | `docs/index.rst` |
| DELETE | `docs/include.rst` |
| DELETE | `docs/features/**/*.rst` (all generated feature RST files) |
| DELETE | `docs/features/features.rst` |

---

## Verification Plan

### Automated

1. `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html` — exits 0, no warnings about missing files or unknown directives.
2. `docs/_build/html/features/features.html` exists and contains section headings matching the `features/` directory tree.
3. Feature Markdown content (Gherkin steps, tables) is rendered as HTML — not shown as raw code blocks.
4. `grep -r "pandoc" docs/_build/` — returns nothing (pandoc not invoked).
5. Importing a Pandoc Python wrapper is not a requirement for the doc build.
6. `docs/features/` contains no `.rst` files after build.

### Manual

1. Review ReadTheDocs preview build — all pages present, navigation matches previous structure.
2. Spot-check `CHANGES.md` rendering — headings, code blocks, and links render correctly.
3. Spot-check `README.md` on PyPI preview — badge links, code blocks, installation instructions intact.
4. Verify legacy feature-doc make target removal does not break CI (search `.github/workflows/` for references).
