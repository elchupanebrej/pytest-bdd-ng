# Phase 28: Extract pytest_bdd_toolchain — Specification

**Created:** 2026-06-24
**Ambiguity score:** 0.1875 (gate: ≤ 0.20)
**Requirements:** 6 locked

## Goal

Extract `pytest_bdd_testing` into `pytest_bdd_toolchain` — a standalone package with all 11 development scripts as `pbt-*` entrypoints, updated documentation, and zero regressions.

## Background

`pytest_bdd_testing` exists at `src/pytest_bdd_testing/` with 11 scripts in `scripts/`. The package is excluded from setuptools package discovery and mypy. Phase 20 decisions (20-26, 20-27) established `pytest_bdd_testing` as the independent test package name. This phase renames it to `pytest_bdd_toolchain` and moves scripts into the package as `pbt-*` entrypoints. The design spec `docs/superpowers/specs/2026-06-24-rename-pytest-bdd-testing-to-toolchain.md` proposes the full rename with script migration.

## Requirements

1. **Package rename**: Rename `pytest_bdd_testing` package to `pytest_bdd_toolchain`.
   - Current: Package exists at `src/pytest_bdd_testing/`
   - Target: Package exists at `src/pytest_bdd_toolchain/` with updated imports
   - Acceptance: `python -c "import pytest_bdd_toolchain"` succeeds; `python -c "import pytest_bdd_testing"` fails

2. **Script migration**: Move all 11 scripts to `src/pytest_bdd_toolchain/tool/` as `pbt-*` entrypoints.
   - Current: 11 scripts in `scripts/` directory
   - Target: 11 scripts in `src/pytest_bdd_toolchain/tool/` with `pbt-*` entrypoints in `pyproject.toml`
   - Acceptance: Running `pbt-arch --help` (and all 10 other `pbt-*` commands) shows usage information

3. **Documentation updates**: Update all documentation (README, CHANGELOG, DEVELOPMENT.rst, all references).
   - Current: Documentation references `pytest_bdd_testing`
   - Target: All documentation references `pytest_bdd_toolchain`
   - Acceptance: scoped `rg` checks over active code/config/docs and current planning surfaces return zero old-name matches; historical phase summaries may keep audit references

4. **Python compatibility**: Maintain Python 3.10-3.14 compatibility.
   - Current: Package supports Python 3.10-3.14
   - Target: Renamed package supports Python 3.10-3.14
   - Acceptance: `tox -e py310,py311,py312,py313,py314` passes

5. **Test suite passes**: Full test suite passes with zero failures.
   - Current: Test suite passes for `pytest_bdd_testing`
   - Target: Test suite passes for `pytest_bdd_toolchain`
   - Acceptance: `uv run python -m pytest src/pytest_bdd_toolchain/case -q --tb=short --no-header` passes with zero failures

6. **Script entrypoints work**: All scripts work as `pbt-*` entrypoints after moving.
   - Current: Scripts run via `python scripts/xxx.py`
   - Target: Scripts run via `pbt-xxx` command
   - Acceptance: All 11 `pbt-*` commands execute without import errors

## Boundaries

**In scope:**
- Package rename (`pytest_bdd_testing` → `pytest_bdd_toolchain`)
- Script migration to `src/pytest_bdd_toolchain/tool/`
- `pbt-*` entrypoint registration in `pyproject.toml`
- Documentation updates (README, CHANGELOG, DEVELOPMENT.rst, all references)
- Test suite validation

**Out of scope:**
- CI/CD workflow changes — GitHub Actions workflows remain as-is, only update package references
- Backward compatibility layer — no deprecation warnings or wrapper packages (clean break)
- New feature development — only restructuring existing code
- Performance optimization — not a performance milestone

## Constraints

- Must support Python 3.10-3.14 and pytest >=7.0.0
- Breaking changes require major version bump
- Package rename should not break existing workflows beyond the package name change
- Scripts must maintain identical functionality after moving

## Acceptance Criteria

- [ ] `python -c "import pytest_bdd_toolchain"` succeeds
- [ ] `python -c "import pytest_bdd_testing"` fails with ImportError
- [ ] All 11 `pbt-*` commands execute without import errors
- [ ] Scoped `rg` checks over active code/config/docs and current planning surfaces return zero old-name matches
- [ ] `uv run python -m pytest src/pytest_bdd_toolchain/case -q --tb=short --no-header` passes with zero failures
- [ ] `tox -e py310,py311,py312,py313,py314` passes

## Edge Coverage

**Coverage:** 15/15 applicable edges resolved · 0 unresolved

| Category | Requirement | Status | Resolution / Reason |
|----------|-------------|--------|---------------------|
| idempotency | R1 | ⛔ dismissed | Package rename is a one-time operation, not idempotent |
| concurrency | R1 | ⛔ dismissed | Package rename is a one-time operation, not concurrent |
| adjacency | R2 | ⛔ dismissed | File moves are straightforward, no adjacency issues |
| empty | R2 | ⛔ dismissed | Moving files handles empty cases via OS operations |
| ordering | R2 | ⛔ dismissed | File moves preserve ordering by filesystem |
| idempotency | R2 | ⛔ dismissed | File moves are one-time operations |
| concurrency | R2 | ⛔ dismissed | File moves are sequential operations |
| empty | R3 | ⛔ dismissed | Documentation updates are text replacements, not empty-case sensitive |
| encoding | R3 | ⛔ dismissed | Documentation updates are simple text replacements, not encoding-sensitive |
| boundary | R4 | ⛔ dismissed | Version compatibility is about API support, not numeric boundaries |
| precision | R4 | ⛔ dismissed | Version compatibility is about API support, not precision/overflow |
| idempotency | R5 | ⛔ dismissed | Test suite runs once, not repeatedly |
| concurrency | R5 | ⛔ dismissed | Test suite execution is sequential (xdist parallelism is internal) |
| idempotency | R6 | ⛔ dismissed | Script execution is single-use, not repeated |
| concurrency | R6 | ⛔ dismissed | Script execution is sequential, not concurrent |

## Prohibitions (must-NOT)

**Coverage:** 0/0 applicable prohibitions resolved · 0 unresolved

No genuine prohibitions found. All 6 requirements are pure utility operations with no user-facing surface that would trigger values/safety/ethics constraints.

## Ambiguity Report

| Dimension          | Score | Min  | Status | Notes                              |
|--------------------|-------|------|--------|------------------------------------|
| Goal Clarity       | 0.85  | 0.75 | ✓      | Specific rename + migration goal   |
| Boundary Clarity   | 0.80  | 0.70 | ✓      | Explicit in/out scope              |
| Constraint Clarity | 0.75  | 0.65 | ✓      | Python 3.10-3.14 required          |
| Acceptance Criteria| 0.80  | 0.70 | ✓      | 7 pass/fail criteria               |
| **Ambiguity**      | 0.1875| ≤0.20| ✓      |                                    |

Status: ✓ = met minimum, ⚠ = below minimum (planner treats as assumption)

## Interview Log

| Round | Perspective    | Question summary         | Decision locked                    |
|-------|----------------|-------------------------|------------------------------------|
| 1     | Researcher     | Phase goal clarification| Phase renamed to "Extract pytest_bdd_toolchain" |
| 1     | Researcher     | Scope clarification      | Priority subset, not all 24 specs  |
| 2     | Simplifier     | Primary deliverable      | Package + docs (no CI/CD)          |
| 2     | Simplifier     | Backward compatibility   | Clean break (no compatibility layer)|
| 3     | Boundary Keeper| Out of scope             | No CI/CD changes, no compat layer  |
| 3     | Boundary Keeper| Done criteria            | Package renamed + docs updated     |
| 4     | Failure Analyst| Failure modes            | Broken imports, missing entrypoints, test failures |
| 4     | Failure Analyst| Rejection criteria       | Test failures, missing docs, broken scripts |
| 5     | Seed Closer    | Constraints              | Python 3.10-3.14 support           |
| 5     | Seed Closer    | Acceptance criteria      | All criteria must be met           |

---

*Phase: 28-extract-pytest-bdd-toolchain*
*Spec created: 2026-06-24*
*Next step: /gsd-discuss-phase 28 — implementation decisions (how to build what's specified above)*
