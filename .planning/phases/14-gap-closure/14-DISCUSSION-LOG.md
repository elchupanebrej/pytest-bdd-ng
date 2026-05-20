# Phase 14: Gap Closure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-05-20
**Phase:** 14-gap-closure
**Areas discussed:** Coverage Strategy, Test Type Mix, Coverage Granularity, Module Exemptions, Coverage Gap Approach, BDD Fix Strategy, BDD Triage Method, Step Def vs Feature File Fix, Regression Verification, Bug Fix Policy, E2E Organization, Coverage Metric, Leftovers (folded todos)

---

## Coverage Strategy

**User's choice:** Broad coverage augmentation -- add tests across all modules evenly
**Alternatives:** Target least-covered core modules (rejected), Plugin and formatter focused (rejected)

## Test Type Mix

**User's choice:** Mix of unit + integration tests
**Notes:** Unit tests under tests/unit/ and tests/model/; integration tests under tests/feature/ (testdir-based)
**Alternatives:** Primarily unit tests (rejected), Mostly testdir integration (rejected)

## Coverage Granularity

**User's choice:** Per-module minimum threshold of 70% line+branch
**Notes:** Exemptions for entrypoint.py, script/ modules, and _gherkin_go/ bridge
**Alternatives:** Aggregate total across codebase (rejected)

## Module Exemptions

**User's choice:** Exempt entrypoints and scripts from per-module threshold
**Notes:** These modules are adequately tested by integration/e2e tests
**Alternatives:** Strict no exemptions (rejected)

## Coverage Gap Approach

**User's choice:** Quick coverage gap scan first
**Notes:** Easy wins (error paths, edge cases) before complex gaps
**Alternatives:** Blind augmentation (rejected)

## BDD Fix Strategy

**User's choice:** Triage first, fix after -- categorize all 27 by root cause, then fix by category
**Alternatives:** Fix step definitions only (rejected), Fix feature files and step defs (rejected)

## BDD Triage Method

**User's choice:** Automated triage with error-type categories (StepNotFound, AssertionError, etc.)
**Alternatives:** Manual one-by-one review (rejected)

## Step Def vs Feature File Fix

**User's choice:** Case-by-case judgment -- intended behavior gets step implementation, outdated behavior gets feature update
**Alternatives:** Implement missing step defs only (rejected)

## Regression Verification

**User's choice:** Single full-suite verification run at end after all fixes
**Alternatives:** Full test suite after each category fix (rejected)

## Bug Fix Policy

**User's choice:** Fix production code bugs discovered during BDD triage -- do not defer
**Alternatives:** Document bugs and defer fixes (rejected), Fix only trivial bugs (rejected)

## E2E Organization

**User's choice:** Split E2E test modules per feature file as part of fixing -- apply Phase 12 D-18 rule
**Alternatives:** Fix first split later (rejected), Skip splitting (rejected)

## Coverage Metric

**User's choice:** Line + branch coverage on src/pytest_bdd/ for the 70% gate
**Alternatives:** Line coverage only (rejected)

## Leftovers (Folded Todos)

**User's choice:** Fold all 4 STATE.md pending items into Phase 14 scope:
- Migrate 6 test files to tests/unit/
- Write model module tests (run.py, scenario_run.py, feature_binding.py)
- Write steps.py testdir tests
- Extend parser tests + pragma audit
- Also: Expand feature tests for undocumented behaviors

## the agent's Discretion

- Exact module-by-module test allocation within broad augmentation
- Specific test structure and naming
- Order of triage categories after automated categorization
- File-by-file organization of E2E module split
- Which undocumented behaviors to cover with new feature files
- Per-file pragma audit decisions

## Deferred Ideas

None -- all STATE.md pending items were folded into Phase 14 scope.
