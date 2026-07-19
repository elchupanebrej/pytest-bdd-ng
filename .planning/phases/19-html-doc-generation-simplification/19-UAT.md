---
phase: 19-html-doc-generation-simplification
plan: 04
status: complete
created: 2026-06-04
updated: 2026-06-04
---

# Phase 19 UAT Checklist

## Scope

Manual checks that cannot be completed locally before merge for the HTML documentation generation simplification.

## Blocking Checks

| Check | Owner | Status | Evidence | Required Result |
|-------|-------|--------|----------|-----------------|
| ReadTheDocs preview | Release owner | PASS | User reported: Test 1 - passed | Preview build succeeds from `.readthedocs.yaml` without adding pandoc or the removed feature RST generator. |
| ReadTheDocs feature navigation | Release owner | PASS | User reported: yes | Feature navigation page renders and links to copied `.feature.md` pages with scenario content. |
| README/PyPI rendering | Release owner | PASS | User reported: yes | `README.md` renders badges, install block, tables, Gherkin example, and project layout without broken Markdown. |
| CHANGES rendering | Release owner | PASS | User reported: yes | `CHANGES.md` renders version headings, nested lists, links, and code formatting without damaged conversion artifacts. |
| ReadTheDocs config unchanged | Executor | PASS | `.readthedocs.yaml` still points Sphinx at `docs/conf.py`; no Plan 19-04 edits made. | No ReadTheDocs config redesign required for local verification. |

## Local Verification Completed

| Check | Owner | Status | Evidence |
|-------|-------|--------|----------|
| Sphinx HTML build | Executor | PASS | `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html` exited 0. |
| Rendered feature index | Executor | PASS | `docs/_build/html/features/features.html` exists. |
| Rendered feature scenario page | Executor | PASS | `docs/_build/html/features/01 Tutorial/01 Launch.feature.html` contains `Feature:`, `Scenario:`, `Given`, `When`, and `Then` content. |
| No generated feature RST files | Executor | PASS | `Get-ChildItem -Recurse docs/features -Filter *.rst` returned no files. |
| No active old generator command | Executor | PASS | Active path search found no `bdd_tree_to_rst` or `features-docs` references. |

## Merge Gate

All Phase 19 blocking manual checks passed.
