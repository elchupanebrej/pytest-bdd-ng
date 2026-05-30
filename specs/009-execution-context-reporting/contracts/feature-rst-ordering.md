# Contract: Feature-Driven RST Ordering

## Scope

Defines how `src/pytest_bdd/script/bdd_tree_to_rst.py` converts feature trees into end-user
RST navigation and per-feature include pages under `docs/features/`.

## Inputs

- Feature source root containing `.gherkin`, `.feature`, `.gherkin.md`, `.feature.md`, and `.bdd.yaml` files
- Output documentation root containing `features.rst` and generated per-feature `.rst` pages
- Template assets:
  - `src/pytest_bdd/template/features_section.rst.jinja2`
  - `src/pytest_bdd/template/feature_include.rst.jinja2`

## Ordering Rules

1. General-to-specialized ordering:
- Relative directory depth is the primary ordering signal.
- Shallower sections MUST be emitted before deeper sections.
- Parent topic sections MUST appear before any child topic sections.

2. Deterministic tie-breaks:
- Within the same depth, sections MUST be ordered by normalized relative path.
- Within a section, entries MUST be ordered by normalized relative path.
- Filesystem iteration order MUST NOT be relied on as a user-facing ordering contract.

3. Rendering behavior:
- `docs/features/features.rst` preserves manual intro/suffix content outside the auto-generated block.
- Only the region between `.. BEGIN AUTO-GENERATED FEATURES TREE` and `.. END AUTO-GENERATED FEATURES TREE` is regenerated.
- Plain Gherkin and StructBDD files render as include pages; Markdown-backed feature files render converted RST pages.

## Prohibited Behavior

- Emitting specialized child branches before their broader parent topics
- Non-deterministic ordering caused by raw glob or directory iteration order
- Rewriting manual prose outside the auto-generated markers
- Injecting runtime implementation notes into the generated user-facing feature index

## Validation Requirements

- `tests/contract/test_jinja2_doc_generation_contract.py` validates the feature-driven documentation contract surface.
- `tests/generation/test_template_packaging.py` validates packaged templates used by the generator.
- `tests/doc/test_doc.py` validates deterministic rendered output, intro preservation, marker-based regeneration, and stale-doc failure behavior.
