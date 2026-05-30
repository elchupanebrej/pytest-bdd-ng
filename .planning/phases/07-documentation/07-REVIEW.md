---
status: "completed"
files_reviewed: 13
issue_counts:
  critical: 0
  warning: 2
  info: 2
  total: 4
---

# Code Review Findings

## Critical Issues
*None found.*

## Warnings
1. **Broken Markdown Documentation Includes**
   - **File:** `docs/include.rst`
   - **Line:** 14-15
   - **Description:** The `.. include::` directive natively expects RST syntax. Including `../DEPRECATIONS.md` and `../MIGRATION.md` will result in broken rendering because Sphinx will try to parse them as RST. Furthermore, `myst_parser` or `m2r2` is missing from the `extensions` in `docs/conf.py` and the `doc-gen` dependencies in `pyproject.toml`, meaning Sphinx won't properly parse markdown.
   - **Recommendation:** Either convert the `.md` files to `.rst` format, or add `myst_parser` to dependencies and Sphinx `extensions`, and use the `.. mdinclude::` directive (or `myst` equivalent) for embedding markdown into RST.

2. **Incorrect Package Name for Allure Pytest Plugin**
   - **File:** `MIGRATION.md` (Lines 157, 166) and `DEPRECATIONS.md` (Line 8)
   - **Description:** The documentation advises users to migrate from the internal allure plugin to the external `pytest-allure` package. The official and correct PyPI package name is `allure-pytest`. Instructing users to install `pytest-allure` may lead to `pip install` failures or potentially unsafe typosquatting packages.
   - **Recommendation:** Change `pytest-allure` to `allure-pytest` in both `MIGRATION.md` and `DEPRECATIONS.md`.

## Info / Code Quality
1. **Incorrect Local Path in Sphinx Configuration**
   - **File:** `docs/conf.py`
   - **Line:** 22
   - **Description:** `sys.path.insert(0, str(Path("..").resolve()))` points to the repository root. Since the source code is under the `src/` layout (`src/pytest_bdd`), this won't help Sphinx locate the `pytest_bdd` module unless it's already installed in the environment.
   - **Recommendation:** Change it to `sys.path.insert(0, str((Path("..") / "src").resolve()))` so that autodoc can successfully import the local module without requiring it to be `pip install`ed first.

2. **Missing `myst-parser` in Dependencies**
   - **File:** `pyproject.toml`
   - **Line:** 114
   - **Description:** `docs/conf.py` configures `source_suffix = [".rst", ".md"]`, but the `doc-gen` optional dependencies list lacks `myst-parser` (or any equivalent Markdown processor for Sphinx). Sphinx requires an extension to process Markdown files out of the box.
   - **Recommendation:** Add `"myst-parser"` to the `doc-gen` dependencies and `myst_parser` to the `extensions` list in `docs/conf.py`.
