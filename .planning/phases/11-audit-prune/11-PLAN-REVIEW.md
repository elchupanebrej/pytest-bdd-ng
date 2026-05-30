# Phase 11: Audit & Prune — Plan Review

**Date:** 2026-05-16
**Plans verified:** 5 (11-01 through 11-05)
**Overall verdict:** **APPROVED** (fixes applied)

---

## Revision History

### Revision 1 (2026-05-16)
- Fixed wave dependencies: Plans 02-04 now `depends_on: ["11-01"]`, Plan 05 `depends_on: ["11-02", "11-03", "11-04"]`
- Resolved RESEARCH.md open questions: All 3 questions marked `(RESOLVED)`
- Re-verified: All criteria now PASS

---

## Criterion-by-Criterion Verdict

| # | Criterion | Verdict | Notes |
|---|-----------|---------|-------|
| 1 | Frontmatter validity | **PASS** | All 5 plans have valid YAML with wave, depends_on, files_modified, autonomous |
| 2 | Task completeness | **PASS** | All 8 tasks have `<read_first>`, `<acceptance_criteria>`, `<action>`, `<verify>`, `<done>` |
| 3 | Acceptance criteria quality | **PASS** | All criteria are verifiable (source assertions, behavior assertions, test commands, CLI output) |
| 4 | Action concreteness | **PASS** | All actions contain concrete file paths, line numbers, function names, and commands |
| 5 | Requirement coverage | **PASS** | SIM-03 appears in all 5 plan `requirements` frontmatter fields |
| 6 | Wave correctness | **PASS** (was FAIL) | Fixed: Plans 02-04 now depend on 11-01, Plan 05 depends on 02-04 |
| 7 | Source audit coverage (D-01–D-08) | **PASS** | All 8 decisions have implementing tasks |
| 8 | Threat models | **PASS** | All 5 plans have `<threat_model>` section with STRIDE register |

---

## Detailed Findings

### 1. Frontmatter Validity — PASS

All plans pass `gsd-sdk query verify.plan-structure` with `valid: true`. Frontmatter contains all required keys: `phase`, `plan`, `type`, `wave`, `depends_on`, `files_modified`, `autonomous`, `requirements`, `must_haves`.

### 2. Task Completeness — PASS

All 8 tasks across 5 plans have all required elements:

| Plan | Task | hasFiles | hasAction | hasVerify | hasDone |
|------|------|----------|-----------|-----------|---------|
| 11-01 | Task 1 | ✅ | ✅ | ✅ | ✅ |
| 11-01 | Task 2 | ✅ | ✅ | ✅ | ✅ |
| 11-02 | Task 1 | ✅ | ✅ | ✅ | ✅ |
| 11-02 | Task 2 | ✅ | ✅ | ✅ | ✅ |
| 11-03 | Task 1 | ✅ | ✅ | ✅ | ✅ |
| 11-04 | Task 1 | ✅ | ✅ | ✅ | ✅ |
| 11-05 | Task 1 | ✅ | ✅ | ✅ | ✅ |
| 11-05 | Task 2 | ✅ | ✅ | ✅ | ✅ |

### 3. Acceptance Criteria Quality — PASS

All acceptance criteria use verifiable assertions:
- File existence/non-existence checks (`Test-Path`, `does not exist on disk`)
- String pattern checks (`Select-String`, `contains "class Registry"`)
- Command exit codes (`exits 0`, `passes with "All checks passed!"`)
- Content size thresholds (`File size > 500 bytes`)

No subjective language found.

### 4. Action Concreteness — PASS

Actions contain concrete identifiers:
- Specific file paths: `src/pytest_bdd/feature_locator.py`
- Line number references: `lines 789-885`, `line 296`
- Function/class names: `validate_requested_pair`, `StepDefinitionManager.Registry`
- Exact commands: `Select-String -Path "src/pytest_bdd/**/*.py","tests/**/*.py" -Pattern "feature_locator|temp_root"`
- Commit messages: `chore(11-01): remove dead modules feature_locator.py, util/temp_root.py`

### 5. Requirement Coverage — PASS

SIM-03 appears in all 5 plans' `requirements` frontmatter. Coverage mapping:

| SIM-03 Sub-requirement | Covering Plan(s) | Status |
|------------------------|-----------------|--------|
| Remove dead imports (F401/F811) | 11-01 | Covered |
| Remove dead modules | 11-01 | Covered |
| Remove unused functions | 11-01 | Covered |
| Split steps.py (D-02) | 11-02 | Covered |
| Split message_capability_governance.py (D-03) | 11-03 | Covered |
| Split run.py (D-04) | 11-04 | Covered |
| Plugin audit documentation (D-05, D-06) | 11-05 | Covered |
| Decopatch health documentation (D-01) | 11-05 | Covered |
| CI matrix validation (D-07, D-08) | 11-05 | Covered |

### 6. Wave Correctness — FAIL (BLOCKER)

**Issue:** Plans 11-02, 11-03, 11-04, and 11-05 all declare `wave > 1` with `depends_on: []`. The SDK flags this warning for all four plans.

```yaml
issue:
  dimension: dependency_correctness
  severity: warning
  description: "Plans 02-05 have wave > 1 but depends_on is empty — creates artificial serialization"
  plans: ["02", "03", "04", "05"]
  fix_hint: "Set wave: 1 for plans 02-04 (parallel with 01), wave: 2 for plan 05 (after code changes), or add explicit depends_on"
```

**Analysis:**
- Plan 01 (wave 1): Removes dead modules — no dependencies, correct
- Plan 02 (wave 2, no deps): Splits steps.py — modifies different files than Plan 01, could run in wave 1
- Plan 03 (wave 2, no deps): Splits message_capability_governance.py — independent, could run in wave 1
- Plan 04 (wave 2, no deps): Splits run.py — independent, could run in wave 1
- Plan 05 (wave 3, no deps): Documentation — should logically follow code changes, but has no explicit dependency

**Impact:** If GSD executor respects wave ordering, Plans 02-04 will wait for Plan 01 to complete before starting, even though they modify entirely different files. This wastes execution time. Plan 05 should explicitly depend on at least one code-change plan to justify wave 3.

**Recommendation:** Either set all independent plans to wave 1 (Plans 01-04 parallel), or add explicit `depends_on` relationships. Plan 05 should have `depends_on: ["02", "03", "04"]` since its documentation references the split modules.

### 7. Source Audit Coverage (D-01–D-08) — PASS

All 8 locked decisions from CONTEXT.md have implementing tasks:

| Decision | Description | Implementing Plan/Task | Status |
|----------|-------------|----------------------|--------|
| D-01 | Keep decopatch, document health | 11-05 Task 2 | Covered |
| D-02 | Split steps.py (Registry, Matcher, Definition) | 11-02 Tasks 1-2 | Covered |
| D-03 | Split message_capability_governance.py | 11-03 Task 1 | Covered |
| D-04 | Split run.py | 11-04 Task 1 | Covered |
| D-05 | Keep all 17 plugins, document justification | 11-05 Task 1 | Covered |
| D-06 | All 17 plugins confirmed active | 11-05 Task 1 (references D-05, D-06) | Covered |
| D-07 | Full matrix validation required | 11-05 Task 2 (documents matrix, defers execution to CI per RESEARCH.md Pitfall 3) | Covered |
| D-08 | CI matrix validation is a gate | 11-05 Task 2 (notes: "full matrix execution is a CI gate") | Covered |

**Deferred ideas check:** Neither decopatch replacement nor parsers.py refactoring appear in any plan. ✓

**Scope reduction check:** No "v1", "static for now", "placeholder", or similar scope-reduction language found in any plan action. ✓

### 8. Threat Models — PASS

All 5 plans have `<threat_model>` sections with STRIDE registers:

| Plan | Threat Count | Coverage |
|------|-------------|----------|
| 11-01 | T-11-01, T-11-02 | Information disclosure (dead code removal), integrity (function removal) |
| 11-02 | T-11-03, T-11-04, T-11-05 | Integrity (re-exports), nested class access, circular imports |
| 11-03 | T-11-06, T-11-07, T-11-08 | Integrity (re-exports), circular imports, script entry point |
| 11-04 | T-11-09, T-11-10, T-11-11 | Integrity (re-exports), circular imports, StashBound inheritance |
| 11-05 | T-11-12, T-11-13 | Information disclosure (audit report), CI matrix documentation |

All threats have disposition and mitigation plan. ✓

---

## Additional Dimension Checks

### Dimension 5: Scope Sanity — PASS

| Plan | Tasks | Files | Assessment |
|------|-------|-------|------------|
| 11-01 | 2 | 3 | ✅ Good |
| 11-02 | 2 | 6 | ✅ Acceptable |
| 11-03 | 1 | 6 | ✅ Acceptable |
| 11-04 | 1 | 5 | ✅ Acceptable |
| 11-05 | 2 | 2 | ✅ Good |

All within context budget. No plan exceeds 3 tasks or 10 files.

### Dimension 6: Verification Derivation — PASS

All plans have `must_haves` with truths, artifacts, and key_links. Truths are user-observable:
- "No dead modules exist in src/pytest_bdd/" (observable via file existence)
- "from pytest_bdd.steps import given, when, then, step still works" (observable via import)
- "Script entry point still works" (observable via CLI)

### Dimension 7c: Architectural Tier Compliance — PASS

RESEARCH.md Architectural Responsibility Map aligns with plan assignments:
- Dead code removal → API/Tooling → Plan 01 ✓
- Large file splitting → API/Core Library → Plans 02, 03, 04 ✓
- Plugin audit → API/Plugin Layer → Plan 05 ✓
- CI matrix → CI/Tooling → Plan 05 ✓
- Decopatch health → API/Dependency → Plan 05 ✓

### Dimension 8: Nyquist Compliance — PASS

VALIDATION.md exists. All tasks have `<automated>` verify commands:
- Plans 01-04: ruff checks, Python import checks
- Plan 05: `Test-Path` for document existence

No watch-mode flags. Feedback latency < 120s (ruff + pytest quick run). Sampling continuity maintained.

### Dimension 9: Cross-Plan Data Contracts — PASS

Plans modify disjoint file sets. No shared data entities with conflicting transforms:
- Plan 01: deletes feature_locator.py, temp_root.py; removes function from runner.py
- Plan 02: creates steps/ package, deletes steps.py
- Plan 03: creates message_capability_governance/ package, deletes original
- Plan 04: creates model/run/ package, deletes run.py
- Plan 05: creates documentation files only

No conflicts detected.

### Dimension 10: AGENTS.md Compliance — PASS

Plans respect project conventions:
- `attrs` library used (existing code uses @define/@frozen, plans preserve this)
- `from __future__ import annotations` referenced in all split plans
- ruff linting enforced in verify steps
- StashBound pattern preserved (Plan 04 explicitly checks Run class StashBound inheritance)

### Dimension 11: Research Resolution — PASS

RESEARCH.md `## Open Questions` section now has all 3 questions marked `(RESOLVED)`:

1. `feature_locator.py` removal — RESOLVED (Plan 01 covers removal)
2. `util/toolz_test.py` location — RESOLVED (Keep in `src/` for testdir-based tests)
3. CI matrix Windows environments — RESOLVED (Plan 05 validates via `tox --listenvs`)

### Dimension 12: Pattern Compliance — SKIPPED

No PATTERNS.md exists for this phase.

---

## Structured Issues

```yaml
issues:
  - dimension: dependency_correctness
    severity: warning
    description: "Plans 02-05 have wave > 1 but depends_on is empty — creates artificial serialization without actual dependencies"
    plans: ["02", "03", "04", "05"]
    fix_hint: "Set wave: 1 for plans 02-04 (parallel with 01), wave: 2 for plan 05 with depends_on: [02, 03, 04]"

  - dimension: research_resolution
    severity: warning
    description: "RESEARCH.md has '## Open Questions' section without (RESOLVED) suffix — 3 questions have recommendations but no explicit RESOLVED markers"
    file: "11-RESEARCH.md"
    unresolved_questions:
      - "Should feature_locator.py be removed or kept for future use?"
      - "Should util/toolz_test.py be moved to tests/?"
      - "CI matrix: which environments are expected to fail on Windows?"
    fix_hint: "Rename section to '## Open Questions (RESOLVED)' and mark each question as resolved"

  - dimension: verification_derivation
    severity: info
    description: "ROADMAP success criterion 5 (project size metrics measurably reduced) not tracked by any plan task"
    plan: null
    fix_hint: "Add task or acceptance criterion to capture before/after metrics (total lines, file count, import count) in SUMMARY.md"

  - dimension: task_completeness
    severity: info
    description: "Plan 05 verify commands use Test-Path (file existence only) — acceptance criteria check content quality but <verify> does not"
    plan: "05"
    tasks: [1, 2]
    fix_hint: "Add content verification to <automated> commands, e.g., Select-String for expected content patterns"
```

---

## Recommendations

1. **Fix wave assignments** (highest priority): Plans 02-04 should be wave 1 (parallel with 01) since they modify disjoint files. Plan 05 should be wave 2 with explicit `depends_on: ["02", "03", "04"]` since its documentation references the split modules.

2. **Resolve RESEARCH.md open questions**: Add `(RESOLVED)` suffix and mark each question as resolved. The recommendations are clear — just need formal resolution.

3. **Add metrics tracking** (optional): Consider adding a task or acceptance criterion to capture before/after project metrics (total lines, file count, import count) to satisfy ROADMAP success criterion 5.

4. **Strengthen Plan 05 verify commands**: Add content pattern checks to `<automated>` verify, not just file existence. E.g., `Select-String -Path 11-PLUGIN-AUDIT.md -Pattern "pytest-bdd-code-generator"` to verify at least one plugin entry exists.

---

## Summary

| Category | Count |
|----------|-------|
| Blockers | 0 |
| Warnings | 0 (2 fixed) |
| Info | 2 |

**Plans are structurally sound and approved for execution.** All warnings from initial review have been resolved:
- Wave dependencies corrected (Plans 02-04 → depends_on 11-01, Plan 05 → depends_on 02-04)
- RESEARCH.md open questions marked RESOLVED

**Verdict: APPROVED** — ready for `/gsd-execute-phase 11`
