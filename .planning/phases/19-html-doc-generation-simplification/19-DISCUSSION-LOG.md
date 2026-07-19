# Phase 19: html-doc-generation-simplification - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-04
**Phase:** 19-html-doc-generation-simplification
**Areas discussed:** Todo folding, migration boundary, feature-tree build behavior, generated files policy, root RST-to-MD conversion, verification/readthedocs expectations

---

## Todo Folding

| Option | Description | Selected |
|--------|-------------|----------|
| Ignore weak | All matches score 0.2 and look unrelated to HTML doc simplification. | x |
| Fold all | Adds BDD workflow, vulture, and Makefile-shell todos despite weak match. | |
| Pick specific todos | User selects from BDD/ATDD workflow, vulture hook, and Makefile shell todos. | |

**User's choice:** Ignore weak matches.
**Notes:** The todo matches were reviewed but not folded because they were generic low-confidence matches outside the phase boundary.

---

## Migration Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Spec-complete removal | Remove `bdd_tree_to_rst`, generated RST docs, pandoc/pypandoc/panflute, and `features-docs` target in one phase. | x |
| Staged migration | Keep old script/target temporarily as fallback while new Sphinx path lands. | |
| Minimal first pass | Add MyST/Sphinx path but leave cleanup for later. | |

**User's choice:** Spec-complete removal.
**Notes:** User selected the one-phase cleanup path.

---

## Feature-Tree Build Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Fail hard | Invalid/missing feature tree, duplicate prefixes, copy errors, or MyST issues stop `sphinx-build`. | x |
| Warn and continue | Docs build succeeds but feature pages may be incomplete. | |
| Keep old generated RST as fallback | Build can fall back during migration only. | |

**User's choice:** Fail hard.
**Notes:** Incomplete feature docs are not acceptable.

---

## Generated Files Policy

| Option | Description | Selected |
|--------|-------------|----------|
| Gitignored transient copies only | Copied feature files are never committed; committed docs/features keeps only durable index files. | x |
| Commit copied Markdown files | Easier inspection, but generated noise stays. | |
| No copy step | Configure Sphinx to read `features/` outside docs tree. | |

**User's choice:** Gitignored transient copies only.
**Notes:** Keeps source of truth in `features/` and avoids generated-doc churn.

---

## Root RST-to-MD Conversion

| Option | Description | Selected |
|--------|-------------|----------|
| Convert all in phase, manually review risky files | `CHANGES.md` and README/PyPI rendering are explicit verification gates. | |
| Convert only docs index/include now | Leave root `.rst` files for later. | |
| Keep root `.rst` files | Use MyST includes mixed with legacy RST. | |
| Convert root RST files once during migration | Converted Markdown files are included in HTML generation. | x |

**User's choice:** Convert root RST files into Markdown one time during migration. Include converted Markdown files in HTML generation.
**Notes:** Follow-up choice: delete the old root `.rst` files in the same phase so Markdown becomes the source.

---

## Old Root RST Cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Delete old `.rst` files | Markdown becomes single source; update `pyproject.toml` readme and docs includes. | x |
| Keep old `.rst` files temporarily | Avoid broad deletion now, but creates duplicate roots. | |

**User's choice:** Delete old `.rst` files.
**Notes:** This locks README/DOCUMENTATION/AUTHORS/LICENSE/CHANGES Markdown as source after migration.

---

## Verification and ReadTheDocs

| Option | Description | Selected |
|--------|-------------|----------|
| Local Sphinx + content checks + RTD preview | `sphinx-build` clean, feature pages render, no `pandoc`, no `docs/features/*.rst`, plus manual ReadTheDocs preview spot-check. | x |
| Local only | No ReadTheDocs preview gate. | |
| RTD preview required before merge | Merge blocked until preview inspected. | |

**User's choice:** Local Sphinx + content checks + RTD preview.
**Notes:** README/PyPI and CHANGES rendering are explicit manual spot-check risks.

---

## the agent's Discretion

- Exact feature-tree extension implementation shape.
- Exact shared utility extraction boundary for ordering-prefix validation.
- Exact MyST toctree/include syntax.
- Exact one-time conversion command, provided converted output is reviewed.

## Deferred Ideas

- Integrate BDD/ATDD tests into development workflow and UAT phase - not folded.
- Vulture must be run not via pytest but as pre-commit hook - not folded.
- Fix Makefile SHELL for cross-platform (Win/Mac/Linux) - not folded.
