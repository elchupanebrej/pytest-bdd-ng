# Phase 05: Unit Test Fortification - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-14
**Phase:** 05-unit-test-fortification
**Areas discussed:** Coverage prioritization & ordering, Test organization & methodology, Coverage enforcement, Pragma: no cover & dead code, Test retrofitting & reorganization

---

## Coverage Prioritization & Ordering

| Option | Description | Selected |
|--------|-------------|----------|
| Model modules first | Start with run.py/scenario_run.py/feature_binding.py (hard 85% gate) | |
| Highest user-impact first | Start with steps.py (630 lines, high support burden) | ✓ |
| Interleave by difficulty | Tackle low-hanging gaps across all modules | |

**User's choice:** Highest user-impact first
**Notes:** steps.py → model modules → parsers.py last. Parser tests via public API only (respect freeze).

| Option | Description | Selected |
|--------|-------------|----------|
| Edge cases in step matching | Priority on hardest-to-debug failures | |
| Coverage density | Systematically fill every branch to hit 80% | ✓ |
| Error path coverage first | Focus on failure paths | |

**User's choice:** Coverage density — fill every gap
**Notes:** Pragmatic approach. Run `pytest --cov=pytest_bdd.<module> --cov-report=term-missing` per-module.

---

## Test Organization & Methodology

| Option | Description | Selected |
|--------|-------------|----------|
| Follow existing pattern | Co-locate tests by type, use markers | ✓ |
| New dedicated tests/unit/ | All unit tests in one place | |

**User's choice:** Follow existing pattern + pytest markers for classification

| Option | Description | Selected |
|--------|-------------|----------|
| Prefer direct unit tests | Import, call, assert. Fast. | |
| Prefer testdir throughout | Closer to real usage, slower | |
| Hybrid | testdir for steps.py, direct for model | ✓ |

**User's choice:** Hybrid approach
**Notes:** steps.py needs pytest runtime context; model modules are pure data classes.

| Option | Description | Selected |
|--------|-------------|----------|
| @pytest.mark.unit | Simple, clear, no collision | ✓ |
| @pytest.mark.unittest | Slightly more explicit | |
| No new marker | Use existing grouping | |

**User's choice:** @pytest.mark.unit registered in pyproject.toml

| Option | Description | Selected |
|--------|-------------|----------|
| tests/unit/test_parsers.py | New dedicated file | |
| tests/args/ — extend existing | Add to existing parser-specific tests | ✓ |

**User's choice:** Extend tests/args/

---

## Coverage Enforcement

| Option | Description | Selected |
|--------|-------------|----------|
| Hard gate in CI | Coverage fail blocks merge | ✓ |
| Advisory only | Report, don't block | |

**User's choice:** Hard gate — 100% test pass rate. No per-module coverage thresholds in CI.
**Notes:** 85%/80% are planning targets, not CI gates.

| Option | Description | Selected |
|--------|-------------|----------|
| No global fail_under | Coverage purely informational | |
| Low global fail_under (70%) | Coarse safety net | ✓ |

**User's choice:** Add `fail_under = 70` to .coveragerc

---

## Pragma: no cover & Dead Code

| Option | Description | Selected |
|--------|-------------|----------|
| Audit and justify or remove | Review each, keep with justification or remove | ✓ |
| Leave them — not in scope | None in target modules, skip | |
| Audit + add policy | Review + add ongoing rule | |

**User's choice:** Audit all 9 instances, justify or remove each.

| Option | Description | Selected |
|--------|-------------|----------|
| Add policy to CONTEXT.md | Require justification comment for new pragmas | ✓ |
| No — audit is enough | One-time cleanup sufficient | |

**User's choice:** Policy: `# pragma: no cover — reason: <justification>` required.

---

## Test Retrofitting & Reorganization

| Option | Description | Selected |
|--------|-------------|----------|
| Include in Phase 5 scope | Retofit ALL existing unit tests | ✓ |
| Only files we touch | Less churn, mixed taxonomy | |
| Defer to Phase 10 | Pattern unification phase | |

**User's choice:** Full retrofit in Phase 5 scope — all unit tests get @pytest.mark.unit.

| Option | Description | Selected |
|--------|-------------|----------|
| Keep current directories | Just add markers | |
| Reorganize by source module | Move all to tests/unit/ by src module | ✓ |

**User's choice:** Reorganize tests/unit/ by source module tree. Move ALL existing unit tests.

| Option | Description | Selected |
|--------|-------------|----------|
| New tests only | Place new tests in new structure | |
| Move ALL unit tests | Full migration of existing tests | ✓ |

**User's choice:** Full migration — all existing unit tests moved to tests/unit/ by module.

| Option | Description | Selected |
|--------|-------------|----------|
| Only unit tests | Integration/E2E stay | ✓ |
| Full reorganization | Reorganize everything | |

**User's choice:** Only unit tests — integration/E2E tests stay in current locations.

---

## the agent's Discretion

- Specific assertion strategies per test (vanilla assert vs hamcrest for allure)
- Coverage gap triage priority within each module
- Mock setup details (follow existing unittest.mock patterns)
- Test file granularity (per class vs per module)

## Deferred Ideas

None — discussion stayed within phase scope.
