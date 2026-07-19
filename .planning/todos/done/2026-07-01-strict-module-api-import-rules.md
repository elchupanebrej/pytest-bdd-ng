---
created: 2026-07-01
title: Implement strict module API and import custom pylint rules
area: tooling
files:
  - src/pytest_bdd/_pylint/checkers/
  - src/pytest_bdd/_pylint/__init__.py
  - pyproject.toml
---

## Problem

The project is moving away from package facades and implicit public API surfaces. Current checks cover some
`__init__.py` hygiene, but they do not fully enforce a repository-wide contract for module exports and local import
discipline. Without explicit rules, modules can accidentally expose undocumented names, bypass local module boundaries,
or import sibling implementation details that are not part of the source module's declared API.

## Scope

Apply the rules across the whole repository except:

1. `case` and `cases` paths used for executable scenarios, fixtures, and test cases.
2. Script-like files and packages, including script/tool/CLI entrypoint areas for the initial strict rollout.

The rollout is strict from the start: no temporary legacy allowlist for existing violations.

## Solution

Implement custom Pylint rules when there is no existing Pylint or Ruff rule with equivalent behavior:

1. Every non-`__init__.py` module must define a top-level `__all__`.
2. `__all__` must be a static list or tuple of unique string names.
3. Every name in `__all__` must exist in the defining module.
4. Every `__init__.py` must define exactly `__all__ = []`.
5. `__init__.py` must not re-export names from submodules.
6. Star imports are forbidden.
7. Parent-relative imports using `..` are forbidden.
8. Sibling modules must be imported with explicit one-dot relative imports.
9. Prefer `from . import module` over `from .module import name` for sibling imports.
10. Imported names from local modules must exist in the source module's `__all__`.
11. Attribute access through imported local modules must target names present in the source module's `__all__`.
12. If a module is in the same hierarchy path, enforce the sibling/local import form instead of absolute package import.

## Acceptance Criteria

1. The custom checker is registered in the existing Pylint plugin entrypoint.
2. Rule messages have stable symbolic names and clear remediation text.
3. Unit tests cover passing and failing examples for each rule.
4. `pre-commit run --all-files` fails on violations and passes after fixes.
5. The implementation documents why any overlap with built-in Pylint/Ruff rules is not sufficient.
