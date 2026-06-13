---
title: Add `__tracebackhide__ = True` module-level to all src/pytest_bdd/ modules
date: 2026-06-16
priority: high
---

## Task

Add `__tracebackhide__ = True` at module level in every Python file under `src/pytest_bdd/` to hide internal library tracebacks from pytest output, showing only user code traces when steps fail.

## Context

- This is a pytest plugin; hiding internal frames improves user experience.
- Official pytest recommendation is function-local, but module-level is acceptable for library code (not test functions).
- `--full-trace` flag will still reveal all frames for debugging.
- Decision: hide all internal frames (not just specific ones) for simplicity.

## Acceptance Criteria

- [ ] All `.py` files under `src/pytest_bdd/` have `__tracebackhide__ = True` at module level (after imports, before code).
- [ ] No test functions within the library are affected (test files are in `tests/`, not `src/`).
- [ ] Existing tests pass (no regression).
- [ ] Consider whether `__init__.py` files should be included (technical decision during implementation).

## Notes

- Research shows tradeoffs: module-level hiding masks bugs in assertion helpers, but user wants all internal frames hidden.
- Future improvement: conditional hiding for specific exception types (see seed).
