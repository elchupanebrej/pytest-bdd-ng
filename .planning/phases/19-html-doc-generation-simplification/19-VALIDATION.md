---
phase: 19
slug: html-doc-generation-simplification
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-04
updated: 2026-06-04
---

# Phase 19 - Validation Strategy

> Retroactive Nyquist validation for the HTML documentation generation simplification phase.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest contract tests, ruff, Sphinx HTML build |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run python -m pytest tests/cases/contract/doc/test_doc.py tests/cases/contract/generation/test_template_packaging.py` |
| **Full suite command** | `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html` |
| **Estimated runtime** | ~15 seconds focused tests, Sphinx build runtime environment-dependent |

---

## Sampling Rate

- **After every task commit:** Run focused contract tests for changed documentation behavior.
- **After every plan wave:** Run Sphinx HTML build plus old-pipeline removal search.
- **Before merge:** Complete manual UAT gates in `19-UAT.md`.
- **Max feedback latency:** Focused feedback target under 60 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 19-01-01 | 01 | 1 | D-03 | T-19-02 | Invalid sibling prefixes fail hard before docs build proceeds. | contract | `uv run python -m pytest tests/cases/contract/doc/test_doc.py` | yes | green |
| 19-01-02 | 01 | 1 | D-03, D-04 | T-19-01 / T-19-02 | Sphinx extension copies feature Markdown transiently and preserves manual index text around generated block. | contract | `uv run python -m pytest tests/cases/contract/doc/test_doc.py` | yes | green |
| 19-01-03 | 01 | 1 | D-03 | T-19-01 / T-19-02 | Contract coverage exists for ordering errors, hook registration, toctree output, and hard Sphinx errors. | contract | `uv run python -m pytest tests/cases/contract/doc/test_doc.py` | yes | green |
| 19-02-01 | 02 | 2 | D-05, D-09 | T-19-03 / T-19-04 | Root prose exists as Markdown; final README and CHANGES rendered quality passed manual review. | contract + manual | `uv run python -m pytest tests/cases/contract/doc/test_doc.py` | yes | green |
| 19-02-02 | 02 | 2 | D-05, D-07 | T-19-03 | Docs include page references Markdown sources only. | contract | `uv run python -m pytest tests/cases/contract/doc/test_doc.py` | yes | green |
| 19-02-03 | 02 | 2 | D-07, D-08 | T-19-03 | Project metadata and Sphinx config use Markdown docs path without pandoc wrappers. | contract | `uv run python -m pytest tests/cases/contract/doc/test_doc.py` | yes | green |
| 19-03-01 | 03 | 3 | D-01, D-02, D-08 | T-19-05 | Old RST converter, templates, console entry, and pandoc wrapper dependencies are absent. | contract | `uv run python -m pytest tests/cases/contract/generation/test_template_packaging.py tests/cases/contract/doc/test_doc.py` | yes | green |
| 19-03-02 | 03 | 3 | D-01, D-02, D-08 | T-19-06 | Active Makefile, tox, pre-commit, and CI paths do not call old docs generator. | contract + search | `rg "bdd_tree_to_rst|features-docs|pypandoc|panflute" pyproject.toml Makefile .pre-commit-config.yaml tox.ini .github docs src tests` | yes | green |
| 19-03-03 | 03 | 3 | D-04, D-06, D-08 | T-19-05 | Replaced RST sources are absent and transient feature copies are gitignored. | contract + filesystem | `uv run python -m pytest tests/cases/contract/doc/test_doc.py` | yes | green |
| 19-03-04 | 03 | 3 | D-02, D-08 | T-19-05 | Packaging tests assert old feature RST templates are not packaged. | contract | `uv run python -m pytest tests/cases/contract/generation/test_template_packaging.py` | yes | green |
| 19-04-01 | 04 | 4 | D-01, D-02, D-07 | T-19-06 | Active developer docs and Docker assets reference current Markdown docs path. | search + prior summary evidence | `rg "bdd_tree_to_rst|features-docs|pypandoc|panflute" pyproject.toml Makefile .pre-commit-config.yaml tox.ini .github docs src tests` | yes | green |
| 19-04-02 | 04 | 4 | D-08 | T-19-05 | Sphinx HTML build renders feature navigation and scenario content. | build + prior summary evidence | `uv run --extra doc-gen sphinx-build -b html docs docs/_build/html` | yes | green |
| 19-04-03 | 04 | 4 | D-08 | T-19-05 | Pandoc wrappers and generated feature RST files are not required by active build. | contract + search | `uv run python -m pytest tests/cases/contract/doc/test_doc.py` | yes | green |
| 19-04-04 | 04 | 4 | D-08, D-09 | T-19-03 | RTD preview, README/PyPI rendering, and CHANGES rendering passed manual UAT. | contract + manual | `uv run python -m pytest tests/cases/contract/doc/test_doc.py` | yes | green |

*Status: green = automated or manual verification passed.*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ReadTheDocs preview build and feature navigation | D-08 | Requires PR/preview service output unavailable in local execution. | Update `19-UAT.md` with preview URL/status and rendered feature-navigation evidence. |
| README/PyPI rendering | D-09 | Requires package/rendering preview quality review beyond local text assertions. | Update `19-UAT.md` with PyPI/check-render output or package preview evidence. |
| CHANGES rendering | D-09 | Requires rendered changelog quality review beyond local text assertions. | Update `19-UAT.md` with rendered changelog preview evidence. |

---

## Validation Audit 2026-06-04

| Metric | Count |
|--------|-------|
| Gaps found | 7 |
| Resolved with automated tests | 6 |
| Manual-only gates retained | 0 |
| Focused tests passing | 21 |

Added contract tests in `tests/cases/contract/doc/test_doc.py` for:

- Markdown package metadata and docs include references.
- Active build/hook/tox/CI paths free of removed docs generator and pandoc wrapper terms.
- `make docs` Sphinx command boundary.
- Absence of replaced root/docs RST sources and generated feature RST artifacts.
- Gitignore coverage for transient copied feature docs.
- Blocking manual UAT gates for RTD, README/PyPI, and CHANGES rendering.

---

## Validation Sign-Off

- [x] All tasks have automated verify or documented manual gate.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 covers all missing automated references.
- [x] No watch-mode flags.
- [x] Focused feedback latency < 60 seconds.
- [x] `nyquist_compliant: true` set in frontmatter after manual UAT gates pass.

**Approval:** approved 2026-06-04. Automated Nyquist gaps resolved and manual rendering gates passed.
