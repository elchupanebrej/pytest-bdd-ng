---
created: "2026-06-09T17:19:30.112Z"
title: "Rethink __init__.py: remove empty files, eliminate __all__, consider namespace packages"
area: tooling
files:
  - src/pytest_bdd/**/__init__.py
  - tests/**/__init__.py
  - .planning/phases/20-multiple-refactorings/20-21-PLAN.md
  - pyproject.toml
---

## Problem

Phase 20 Plan 21 added classification comments (`# init: public-api / allow / package-marker`) to all 52 `__init__.py` files, but the current approach has several issues:

1. **Empty `__init__.py` in tests directory**: Many test `__init__.py` files contain only the classification comment with no actual code. These serve no purpose other than marking the directory as a package — but modern Python alternatives exist.

2. **`__all__` in `__init__.py` is undesirable**: The user doesn't want `__all__` definitions inside `__init__.py`. Instead, packages should expose their public API through direct imports. The `__all__` pattern adds maintenance burden without clear benefit for this project.

3. **Backward compatibility not needed**: The init-01 work was done under the assumption that backward-compatible re-exports are needed. The user explicitly states: "We don't want to have backward compatibility for now."

4. **Namespace packages (PEP 420) not investigated**: Python 3.3+ supports implicit namespace packages — directories without `__init__.py` are automatically treated as namespace packages. This could simplify the package structure significantly, especially for:
   - `src/pytest_bdd/plugin/` — each plugin directory could be a namespace package
   - `src/pytest_bdd/testing/` — test utilities
   - `tests/` — test directories
   - The `stubs/` directory

## Solution

1. Remove all empty `__init__.py` files (those with only classification comments or `# init: package-marker`).
2. Remove `__all__` definitions from `__init__.py` files that only serve as re-export lists.
3. Research and evaluate namespace packages (PEP 420) for the project:
   - Which directories can safely use implicit namespace packages?
   - Which directories MUST keep `__init__.py` (e.g., those with non-import logic like `src/pytest_bdd/_ruff/rules/`)?
   - What's the impact on pytest plugin discovery? (pytest uses entry points, not `__init__.py`)
   - What's the impact on `pyproject.toml` package discovery?
4. Update `init_rules.py` (BLQ13xx) to enforce the new convention.
5. Update `pyproject.toml` ruff rules configuration accordingly.
