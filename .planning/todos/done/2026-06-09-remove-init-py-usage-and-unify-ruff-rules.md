---
created: 2026-06-09 13:22
title: Remove __init__.py usage and unify ruff rules project layout
area: tooling
files:
  - pyproject.toml
  - src/pytest_bdd/**/__init__.py
  - scripts/
---

## Problem

The project overuses `__init__.py` as a pattern for making directories into packages, even when not necessary. These files often contain re-exports or trivial imports that add indirection without value. They should be treated as a bad pattern via a custom ruff rule.

Additionally, ruff rules are scattered across `pyproject.toml` sections without a clear organizational structure. The scripts entrypoint behavior (ruff/format/lint tooling) could also benefit from unification.

## Solution

1. Audit and remove unnecessary `__init__.py` files throughout `src/pytest_bdd/` — keep only those that serve a clear purpose (e.g., public API re-exports, plugin registration).
2. Write a custom ruff rule (or configure existing rules) that flags `__init__.py` as a bad pattern, requiring explicit justification to keep.
3. Reorganize ruff rules in `pyproject.toml` into a logical, documented layout.
4. Unify scripts/entrypoint behavior for ruff commands (lint, format, check) to have consistent invocation patterns.
