---
status: in-progress
quick_id: 260705-vmm
date: 2026-07-05
---

# Quick Task 260705-vmm: Move package src/pytest_bdd/_pylint to toolchain

## Goal

Move the custom Pylint plugin package out of the runtime `pytest_bdd` package and into the development `pytest_bdd_toolchain` package.

## Tasks

1. Move `src/pytest_bdd/_pylint` to `src/pytest_bdd_toolchain/_pylint`.
2. Update active plugin references from `pytest_bdd._pylint` and `src/pytest_bdd/_pylint` to the new toolchain path.
3. Verify the new plugin path imports, Pylint can load it, and the custom checker unit tests still pass.
