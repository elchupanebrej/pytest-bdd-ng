# Phase 20 — Gap Closure: Test Package & __init__.py Refactoring

**Gathered:** 2026-06-09
**Status:** Ready for planning
**Source:** User requirements (R1-R10) — gap closure for Wave 3 inadequacies

<domain>
## Phase Boundary

This gap-closure addresses deficiencies in Phase 20 Wave 3 (plans 20-23, 20-24, 20-25):

1. Tests were placed at `src/pytest_bdd/testing/` (nested inside main package) — must be independent `src/pytest_bdd_testing/` package at `./src` level
2. `tests/` directory retained as safety copy — must be fully removed
3. Docker compose and Dockerfiles still reference old paths — must be reworked
4. `[testing]` extra was empty `[]` — must reference `pytest_bdd_testing`
5. `__init__.py` cleanup was incomplete — empty files, `__all__`, and namespace packages need systematic elimination per user directives

Out of scope: new plugin development, parser modifications, type checker changes.
</domain>

<decisions>
## Implementation Decisions (LOCKED — from user R1-R10)

### R1: Separate test package at ./src level
Tests must live in `src/pytest_bdd_testing/` — a completely separate package, NOT nested inside `pytest_bdd`. Parallel to `src/pytest_bdd/` in the source tree.

### R2: Optional dependency must reference the package
`[project.optional-dependencies]` testing extra MUST be:
```toml
testing = ["pytest_bdd_testing"]
```
NOT empty `[]`. `pip install pytest-bdd[testing]` installs both packages.

### R3: Remove old tests/ directory entirely
No deferral. Actually delete `tests/` after migration. All `__init__.py`, `__pycache__`, stale Docker compose, scripts — gone.

### R4: Docker compose reworked for new layout
All Docker paths resolve from repo root. docker-compose.yml context, Dockerfile COPY paths, controller/worker entrypoint imports — all must use new `src/pytest_bdd_testing/` paths.

### R5: Eliminate empty __init__.py
Files with only classification comments deleted. PEP 420 implicit namespace packages (Python 3.3+).

### R6: Eliminate __all__ from __init__.py
No `__all__` lists. Packages expose API via direct imports from canonical modules.

### R7: No backward compatibility
Remove re-exports added during INIT-01 (Plan 21). No transitional facade.py patterns for testing package. Clean break.

### R8: Research PEP 420 namespace packages
Before deleting `__init__.py`: which directories can use implicit namespace packages? Which MUST keep `__init__.py` (e.g., `_ruff/rules/`)? Impact on package discovery and pytest plugin loading?

### R9: Update init_rules.py for new convention
BLQ1401: No `__all__` in `__init__.py`. BLQ1402: No empty `__init__.py`. BLQ1403: `__init__.py` only for actual code.

### R10: Dependency order
First: R1-R4 (test package extraction — prerequisite). Then: R5-R9 (__init__.py elimination + namespace packages).

### the agent's Discretion
- Exact directory structure of `src/pytest_bdd_testing/` (sub-packages, conftest placement)
- Whether to use `pytest_bdd_testing` or alternative package name
- How to handle the `stubs/` directory (already namespace-package-like)
- Whether mypy `no_implicit_reexport` exceptions for the remaining 10 `__all__` files are acceptable or need rework
</decisions>

<canonical_refs>
## Canonical References

- `.planning/phases/20-multiple-refactorings/20-REVIEW.md` — Code review findings (5 blockers, 5 warnings from Wave 3)
- `.planning/phases/20-multiple-refactorings/20-REVIEW-FIX.md` — Fixes applied (10 findings resolved)
- `.planning/phases/20-multiple-refactorings/20-SPEC.md` — Original Phase 20 specification
- `.planning/phases/20-multiple-refactorings/20-RESEARCH.md` — Phase 20 technical research
- `src/pytest_bdd/_ruff/rules/init_rules.py` — Current BLQ14xx rules
- `pyproject.toml` — Current package config, optional-dependencies, testpaths
- `docs/migration/phase-renumbering.md` — Phase numbering reference
</canonical_refs>

<specifics>
## Specific Ideas

- `pytest_bdd_testing` package at `src/pytest_bdd_testing/`
- Package name follows `pytest_bdd` convention (underscore separator)
- Docker compose: `src/pytest_bdd_testing/assets/docker/remote_xdist/docker-compose.yml`
- testpaths: `["src/pytest_bdd_testing/cases"]`
- No `__all__` anywhere; any remaining `__all__` in `pytest_bdd/__init__.py` must have explicit justification
</specifics>

<deferred>
## Deferred Ideas

- Full PEP 420 migration of `stubs/` directory — already compatible
- Removing `__init__.py` from `_ruff/rules/` directory — needs code execution, not just namespace
- Addressing 32 pre-existing layer_rules violations — separate concern
</deferred>

---
*Phase: 20-multiple-refactorings*
*Context gathered: 2026-06-09 via user requirements gap closure*
