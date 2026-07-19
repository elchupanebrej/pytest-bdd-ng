# Phase 08: BDD Acceptance Testing - Discussion Log

**Date:** 2026-05-16
**Mode:** discuss-phase (default interactive)

## Gray Areas Presented

1. Coverage gap audit approach
2. Step definition organization
3. Execution boundary (add vs add+fix vs add+refactor)
4. Coverage gap audit methodology
5. Phase plan scoping
6. Step definition file split strategy
7. Existing feature refactoring thoroughness

## Discussion Summary

### Coverage Gap Audit

**Question:** Which areas to discuss for coverage gaps?
**Options:**
- Manual review of source modules vs existing features
- Focus on known risky areas (Go parser, StructBDD, new formatters)
- Let the agent analyze and propose

**Selection:** Focus on known risky areas + let the agent analyze and propose

**Question:** How should we proceed with coverage gap audit?
**Options:**
- Agent proposes gap list first, you approve
- Agent writes features directly
- I'll list the obvious gaps now

**Selection:** Agent proposes gap list first, you approve

**Gap list presented:** 15+ gap areas across Go parser, tag expressions, heading validation, mimetype, struct_bdd, 6 cucumber formatters, code generator, scenario reporter, compatibility layer, collector_batch.

**Selection:** All of the above (comprehensive coverage)

### Step Definition Organization

**Question:** How should new step definitions be organized?
**Options:**
- Extend conftest.py (add to existing 470-line file)
- Split by topic (create modular step definition files)
- You decide

**Selection:** Split by topic — Create modular step definition files

**Question:** How should step definition files be split?
**Options:**
- Split by topic area — one file per gap area
- Split by sub-phase — 8a, 8b, 8c files

**Selection:** Split by topic area — one file per gap area

### Execution Boundary

**Question:** What's the execution boundary?
**Options:**
- Add only — New feature files, all must pass
- Add + fix — New features plus fix any existing failures
- Add + refactor — Clean up existing features while adding new ones

**Selection:** Add + refactor — Clean up existing features while adding new ones

### Phase Plan Scoping

**Question:** This is 15+ new feature files plus refactoring. How should we scope the phase plan?
**Options:**
- All in one phase — one large PLAN.md with waves
- Split into sub-phases — 8a core, 8b formatters, 8c plugins

**Selection:** Split into sub-phases — 8a core, 8b formatters, 8c plugins

### Existing Feature Refactoring

**Question:** For existing feature refactoring — how thorough?
**Options:**
- Full audit — Review all 47 existing feature files
- Light touch — Fix inconsistencies only when encountered

**Selection:** Full audit — Review all 47 existing feature files

## Decisions Captured

| ID | Category | Decision |
|----|----------|----------|
| D-01 | Coverage | Comprehensive coverage — all identified gaps |
| D-02 | Coverage | Agent proposes gap list first, user approves |
| D-03 | Coverage | Focus on known risky areas + agent analysis |
| D-04 | Structure | Split into 3 sub-phases: 8a, 8b, 8c |
| D-05 | 8a Scope | Go parser, tag expressions, heading validation, mimetype, struct_bdd |
| D-06 | 8b Scope | JUnit, progress, progress_bar, snippets, summary, usage, usage_json |
| D-07 | 8c Scope | Code generator, scenario reporter, compatibility layer, collector_batch |
| D-08 | Step defs | Split by topic area — one file per gap area |
| D-09 | Step defs | New files in `tests/e2e/` with `steps_{topic}.py` pattern |
| D-10 | Step defs | Existing conftest.py preserved — additive, not replacement |
| D-11 | Refactor | Full audit of all 47 existing `.feature.md` files |
| D-12 | Refactor | Review for clarity, consistency, duplicates, standardized patterns |
| D-13 | Refactor | Refactoring includes cleanup while adding new features |
| D-14 | Execution | Add + refactor — new features plus fix existing failures |
| D-15 | Execution | All BDD tests must pass via `python -m pytest tests/e2e/` |

## Deferred Ideas

None — discussion stayed within phase scope.
