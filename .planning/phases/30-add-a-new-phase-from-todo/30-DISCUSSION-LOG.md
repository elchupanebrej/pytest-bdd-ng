# Phase 30: Strict Module API & Import Rules - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-02
**Phase:** 30-Strict Module API & Import Rules
**Areas discussed:** Phase scope selection

---

## Phase Scope Selection

### Q1: Single focused phase or multi-todo bundle?

| Option | Description | Selected |
|--------|-------------|----------|
| One focused phase | Pick the single highest-impact todo and give it a full phase | ✓ |
| Multi-todo bundled phase | Bundle 2-3 related todos into one broader phase | |
| One primary + one secondary | Pick one, include a secondary if within same work scope | |

**User's choice:** One focused phase (Recommended)
**Notes:** Clear accountability, easier to plan and verify.

### Q2: Which pending todo should become Phase 30?

| Option | Description | Selected |
|--------|-------------|----------|
| Ruff rule: no TestClasses | Enforce 'no TestClasses' via custom ruff rule | |
| Typing best practices | Improve typing using awesome-python-typing | |
| Remove __init__.py usage | Remove __init__.py entirely, unify ruff rules | |
| Expand feature tests | Expand feature tests for undocumented behaviors | |

**User's choice:** (Freeform) — Same as option 3 but supersedes it: `__all__` for public module interfaces. Custom pylint rule to validate this. Referenced the "Implement strict module API and import custom pylint rules" document.
**Notes:** User redirected from option 3 to the more specific deferred item from Phase 29: Strict Module API and Import Custom Pylint Rules. The todo document at `.planning/todos/pending/2026-07-01-strict-module-api-import-rules.md` was loaded and confirmed as the requirements source.

### Q3: How to handle violations — fix all at once or phased?

| Option | Description | Selected |
|--------|-------------|----------|
| Fix all at once | One coordinated sweep across ~50+ modules | ✓ |
| Phased in sub-plans | Core first, then plugins, then utilities | |
| Timeboxed sprint | Single plan with timebox, defer edge cases | |

**User's choice:** Fix all at once (Recommended)
**Notes:** Most consistent approach. No accrual of tech debt.

### Q4: Supersede or complement existing BLQ1401-BLQ1404?

| Option | Description | Selected |
|--------|-------------|----------|
| Supersede | New 12-rule checker replaces BLQ14xx entirely | ✓ |
| Complement | Keep BLQ14xx alongside new rules | |
| Merge into BLQ14xx | Extend init_rules.py to include all 12 rules | |

**User's choice:** Supersede (Recommended)
**Notes:** Cleaner — no conflicting rules, single enforcement mechanism. Remove InitRulesChecker from plugin registration.

### Q5: Rule code range?

| Option | Description | Selected |
|--------|-------------|----------|
| New BLQ15xx range | Clean separation from old BLQ14xx | ✓ |
| Reuse BLQ14xx range | Keep same namespace since superseding | |
| BLQ1501-BLQ1512 | Specific sequential suggestion | |

**User's choice:** New BLQ15xx range (Recommended) — effectively BLQ1501-BLQ1512.

---

## the agent's Discretion

The planner has discretion over:
- Exact checker class name and file location
- Implementation order among the 12 rules
- Whether to use automated scripts or manual edits for ~50+ module `__all__` additions
- Whether to combine multiple rules into one checker class or use separate classes

## Deferred Ideas

All 7 remaining pending todos were deferred:
- Improve library typing (awesome-python-typing)
- No TestClasses ruff rule
- Expand feature tests for undocumented behaviors
- Split xdist-remote tests into separate parallel GHA executor job
- Gather failed CI logs into workflow artifact
- Remove __init__.py usage (overlaps with BLQ15xx; defer until this phase completes)
- Create custom pylint rule for noqa without reason (BLQ17xx already exists; review needed)
