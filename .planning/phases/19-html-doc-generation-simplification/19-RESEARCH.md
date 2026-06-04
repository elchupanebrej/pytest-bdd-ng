# Phase 19 Research: HTML doc generation simplification

## RESEARCH COMPLETE

### Summary

Phase 19 should replace the current two-step `features/` -> generated RST -> Sphinx pipeline with a single Sphinx build that uses MyST to render copied `.feature.md` sources. The existing `bdd_tree_to_rst` script contains two reusable concerns: ordering-prefix validation and generated-block replacement. The migration should keep those behaviors, but move ordering validation into a small Python utility and let a local Sphinx extension own build-time feature copying plus MyST toctree generation.

### Current Pipeline

- `Makefile` exposes `features-docs`, which runs `uv run bdd_tree_to_rst $(FEATURES_ROOT) $(FEATURE_DOCS_OUTPUT)`.
- `pyproject.toml` exposes the `bdd_tree_to_rst` console script, packages three RST Jinja2 templates, and keeps `pandoc`, `panflute`, and `pypandoc` in `doc-gen`.
- `src/pytest_bdd/script/bdd_tree_to_rst.py` walks feature sources, validates numeric ordering prefixes, converts Markdown to RST through `pypandoc`, and writes committed generated RST under `docs/features/`.
- `docs/index.rst` and `docs/include.rst` are RST entry pages that include root RST prose.
- `tests/cases/contract/doc/test_doc.py` and `tests/cases/contract/generation/test_template_packaging.py` assert current RST generation behavior and template packaging.

### Target Approach

1. Extract ordering-prefix parsing and validation into `src/pytest_bdd/script/_feature_tree.py`.
2. Add `docs/ext/feature_tree.py` as a local Sphinx extension using `builder-inited`.
3. During Sphinx build, validate `features/`, copy `.feature.md` files into matching transient paths under `docs/features/`, and update the generated block in `docs/features/features.md`.
4. Convert root RST prose to Markdown and switch Sphinx navigation to `docs/index.md` and `docs/include.md`.
5. Delete obsolete generated RST artifacts, templates, script, entry point, Makefile target, pre-commit/tox references, and pandoc-related dependencies.
6. Verify with local Sphinx build, rendered feature-page checks, dependency checks, and explicit manual ReadTheDocs/PyPI spot-check instructions.

### Implementation Notes

- MyST can parse `.feature.md` files when copied under the Sphinx source tree. Toctree entries should omit suffixes, for example `01 Tutorial/01 Launch.feature`.
- The generated `docs/features/features.md` file should preserve manual text outside marker comments such as `% BEGIN AUTO-GENERATED FEATURES TREE` and `% END AUTO-GENERATED FEATURES TREE`.
- Sphinx extension errors should raise `sphinx.errors.ExtensionError` or another hard Sphinx failure, not warnings.
- `.gitignore` should ignore copied feature files under `docs/features/` while keeping `docs/features/features.md` committed.
- Tests should avoid requiring pandoc. Unit/contract tests can create temporary feature trees and Sphinx app inputs to validate ordering and generated Markdown.

### Risks

- Markdown conversion of `CHANGES.rst` can damage RST reference links and code-block formatting. The plan includes explicit manual spot-checks for `CHANGES.md` and `README.md`.
- Deleting `docs/features/**/*.rst` can break stale references in tests, specs, or internal docs. The cleanup plan includes repository-wide search and targeted test updates.
- ReadTheDocs behavior depends on the same Sphinx config path. The plan keeps `.readthedocs.yaml` unchanged unless local build exposes a blocker.

### Verification Targets

- `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html`
- Rendered HTML exists for `docs/_build/html/features/features.html` and at least one copied feature page.
- Generated feature RST files are absent from `docs/features/`.
- `doc-gen` no longer includes `pandoc`, `panflute`, or `pypandoc`.
- `bdd_tree_to_rst` script and entry point are absent.
- ReadTheDocs preview and PyPI README/changelog rendering are manually spot-checked before merge.
