---
phase: 20
slug: multiple-refactorings
status: complete
nyquist_compliant: true
wave_0_complete: true
updated: 2026-06-09
created: 2026-06-08
audit_count: 3
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Audit #1 (2026-06-09): 7 test files created, 65 passing, 2 xfail.
> Audit #2 (2026-06-09): re-audited 2 escalated gaps; both confirmed as implementation blockers, moved to Manual-Only.
> Audit #3 (2026-06-09): both escalated gaps resolved by gap-closure plans 13-22; nyquist_compliant set to true.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x-9.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run python -m pytest tests/cases/unit/unit/ -x --timeout=60` |
| **Full suite command** | `uv run python -m pytest tests/cases/ -q` |
| **Type check** | `uv run python -m mypy --strict src/` |
| **Lint check** | `uv run ruff check src/ tests/` |
| **Layer rules** | `uv run python -m pytest_bdd._ruff.rules.layer_rules` |
| **File size rules** | `uv run python -m pytest_bdd._ruff.rules.file_size_rules` |
| **Init rules** | `uv run python -m pytest_bdd._ruff.rules.init_rules` |
| **Layout rules** | `uv run python -m pytest_bdd._ruff.rules.layout_rules` |
| **Estimated runtime** | ~300 seconds (full suite) |

---

## Sampling Rate

- **After every task commit:** Run `ruff check` + `mypy` (incremental, scope-dependent)
- **After every plan wave:** Run `uv run python -m pytest tests/cases/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green + mypy --strict passes
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-0A-01 | 01 | 1 | A4 (layer definition) | — | N/A | unit | `uv run python -m pytest tests/cases/unit/unit/test_layer_rules.py -v` | ✅ | ✅ green |
| 20-0A-02 | 01 | 1 | A4, D2 (ADRs) | — | N/A | doc | `test -f docs/architecture/LAYERS.md` | ✅ | ✅ green |
| 20-0B-01 | 02 | 2 | A2 (plugin audit) | — | N/A | unit | `uv run python -m pytest tests/cases/unit/unit/test_plugin_boundary.py -v` | ✅ | ✅ green |
| 20-0B-02 | 02 | 2 | A2, A4 | — | N/A | unit | `ruff check src/pytest_bdd/plugin/` | ✅ | ✅ green |
| 20-0C-01 | 03 | 3 | A1 (file splits) | — | N/A | unit | `uv run python -m pytest tests/cases/unit/unit/test_file_size_rules.py -v` | ✅ | ✅ green |
| 20-0C-02 | 03 | 3 | A1 | — | N/A | compliance | `uv run python -m pytest tests/cases/unit/unit/test_file_size_compliance.py -v` | ✅ | ✅ green |
| 20-0D-01 | 04 | 4 | A3 (Go parser) | — | N/A | unit | `pip install . && pip install .[go-parser]` | ✅ | ✅ green |
| 20-0D-02 | 04 | 4 | A3 | — | N/A | bench | benchmark ≥2× speedup | ⬜ | ⬜ manual |
| 20-0E-01 | 05 | 5 | T0 (type checker comparison) | — | N/A | doc | `test -f .planning/phases/20-multiple-refactorings/20-06-SUMMARY.md` | ✅ | ✅ green |
| 20-0F-01 | 06 | 6 | T1 (stubs) | — | N/A | type | `uv run python -m pytest tests/cases/unit/unit/test_stubs.py -v -k no_import_untyped` | ✅ | ✅ green |
| 20-0F-02 | 06 | 6 | T1 | — | N/A | unit | `uv run python -m pytest tests/cases/unit/unit/test_stubs.py -v` | ✅ | ✅ green |
| 20-0G-01 | 07 | 7 | T2 (strict flags) | — | N/A | compliance | `uv run python -m pytest tests/cases/unit/unit/test_mypy_strict.py -v` | ✅ | ✅ green |
| 20-0G-02 | 07 | 7 | T2 | — | N/A | full | Full test suite passes | ✅ | ✅ green |
| 20-0H-01 | 08 | 8 | T3 (type:ignore rule) | — | N/A | lint | `ruff check src/ tests/ scripts/` | ✅ | ✅ green |
| 20-0I-01 | 09 | 9 | D0 (object map) | — | N/A | unit | `python scripts/collect_arch_scores.py` avg ≥ 4.0 | ✅ | ✅ green |
| 20-0J-01 | 10 | 10 | D1 (API ref) | — | N/A | doc | `make docs` no warnings | ✅ | ✅ green |
| 20-0K-01 | 11 | 11 | D2 (ADRs) | — | N/A | doc | `ls docs/adr/*.md \| wc -l` == 10 | ✅ | ✅ green |
| 20-0L-01 | 12 | 11 | D3 (how-to guides) | — | N/A | doc | `ls docs/guides/*.md \| wc -l` >= 5 | ✅ | ✅ green |
| 20-15-01 | 15 | * | INIT-01 (init rules) | — | N/A | compliance | `uv run python -m pytest tests/cases/unit/unit/test_init_rules.py -v` | ✅ | ✅ green |
| 20-21-01 | 21 | * | INIT-01 (layout rules) | — | N/A | compliance | `uv run python -m pytest tests/cases/unit/unit/test_layout_rules.py -v` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/cases/unit/unit/test_layer_rules.py` — 12 tests for A4 layer enforcement rule (BLQ1301/BLQ1302)
- [x] `tests/cases/unit/unit/test_plugin_boundary.py` — 15 tests for A2 plugin audit (BLQ1002)
- [x] `tests/cases/unit/unit/test_file_size_rules.py` — 13 tests for A1 file-size rule (BLQ1201/BLQ1202)
- [x] `tests/cases/unit/unit/test_stubs.py` — 25 tests for T1 stub correctness
- [x] `tests/cases/unit/unit/test_mypy_strict.py` — 1 test for T2 mypy --strict compliance (Audit #3: PASSES)
- [x] `tests/cases/unit/unit/test_file_size_compliance.py` — 1 test for A1 file-size compliance (Audit #3: PASSES)
- [x] `tests/cases/unit/unit/test_init_rules.py` — 1 test for INIT-01 init rules compliance (Audit #3: PASSES)
- [x] `tests/cases/unit/unit/test_layout_rules.py` — 1 test for INIT-01 layout rules compliance (Audit #3: PASSES)
- [x] `stubs/` directory scaffolding — T1 prerequisite
- [x] `docs/architecture/` directory — A4, D0 output targets
- [x] `docs/adr/` directory — D2 output target (10 ADRs)
- [x] `docs/guides/` directory — D3 output target (6 guides)
- [x] `docs/api/` directory — D1 output target

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Go parser ≥2× benchmark | A3 | Requires Go toolchain + native build | Run benchmark script; verify speedup ratio |
| Sphinx autodoc renders all public symbols | D1 | ReadTheDocs preview needed | `make docs` then inspect `_build/html/api/` |
| ReadTheDocs publishes current version | D1 | External service | Verify ReadTheDocs build succeeds on push |
| Plugin extras auto-load correctly | A2 | Requires `pip install .[formatters]` integration | Install each extra; verify plugins load via `pytest --trace-config` |

## Resolved (was Manual-Only)

| Behavior | Requirement | Resolved By | Evidence |
|----------|-------------|-------------|----------|
| ~~mypy --strict exits 0 (T2)~~ | T2 | Plans 13, 16, 17, 18 | `mypy --strict src/` → "Success: no issues found in 306 source files", exit 0; test_mypy_strict.py PASSES |
| ~~No file in src/ exceeds 400 LOC (A1)~~ | A1 | Plans 19, 20, 14, 22 | `file_size_rules.py` exits 0; 0 `.py` files >400 LOC; test_file_size_compliance.py PASSES |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or manual verification path
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s (mypy --strict is ~2.8s, tests ~5s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** verified — Audit #3 (2026-06-09)

---

## Forward-Looking Notes (2026-06-09)

These are architectural considerations noted during Audit #3. They are NOT gaps — they are future improvements beyond Phase 20 scope:

1. **Move tests into src as optional package:** Consider shipping tests as `pytest_bdd[testing]` extra before __init__.py elimination work.
2. **Eliminate empty __init__.py:** Many package-marker `__init__.py` files exist solely for namespace packaging. Consider PEP 420 implicit namespace packages once Python 3.3+ is the minimum.
3. **Remove `__all__` where unnecessary:** Re-evaluate explicit `__all__` exports now that `# init:` classification comments provide equivalent metadata.

---

## Audit Trail

### Audit #1 — Initial Nyquist Assessment (2026-06-09)

#### Gaps Filled
| # | File | Tests | Type |
|---|------|-------|------|
| 1 | tests/cases/unit/unit/test_layer_rules.py | 12 | unit |
| 2 | tests/cases/unit/unit/test_plugin_boundary.py | 15 | unit |
| 3 | tests/cases/unit/unit/test_file_size_rules.py | 13 | unit |
| 4 | tests/cases/unit/unit/test_stubs.py | 25 | unit |

#### Initial Escalation
| # | Task | Requirement | Reason | Test |
|---|------|-------------|--------|------|
| 1 | 20-0G-01 | T2 — mypy --strict exits 0 | 809 mypy errors in ~91 files. Plan 08 reduced from 819 to 656 but work incomplete. | test_mypy_strict.py (xfail strict) |
| 2 | 20-0C-02 | A1 — no file >400 LOC | 7 files violate BLQ1201. | test_file_size_compliance.py (xfail strict) |

#### Audit #1 Summary
- **Total tasks:** 17
- **✅ COVERED:** 14
- **❌ ESCALATED:** 2 (20-0G-01, 20-0C-02)
- **⬜ MANUAL:** 1 (20-0D-02 Go benchmark)
- **Tests created:** 6 files, 65 passing + 2 xfail
- **nyquist_compliant:** false (blocked by 2 escalated tasks)

---

### Audit #2 — Re-audit (2026-06-09)

**Method:** Nyquist auditor re-validated both escalated gaps against current codebase.

#### Findings
| Gap | Current State | Verdict |
|-----|---------------|---------|
| 20-0G-01 (T2 mypy) | 800 errors in 104 files (regression from 656 — likely Python 3.14 compat) | **ESCALATED → MANUAL** |
| 20-0C-02 (A1 file size) | 7 files over 400 LOC; paths updated (cli.py → script/message_capability_governance/cli.py, etc.) | **ESCALATED → MANUAL** |

#### Test Improvements
| File | Change |
|------|--------|
| test_mypy_strict.py | Updated xfail reason (656→800 errors, 91→104 files), improved assertion to show mypy stdout summary |
| test_file_size_compliance.py | Updated xfail reason with corrected file paths, documented Plan 05 exception context |

#### Audit #2 Summary
| Metric | Count |
|--------|-------|
| Gaps audited | 2 |
| Resolved | 0 |
| Escalated → Manual | 2 |
| Test files improved | 2 |

Both gaps are implementation-level: require source code changes (fixing 800 mypy errors in 104 files; splitting 7 oversized files). Neither can be resolved at test level. Tests correctly detect violations. Moved to Manual-Only pending future implementation work.

- **nyquist_compliant:** false (2 implementation gaps remain)

---

### Audit #3 — Re-audit after Gap-Closure Plans 13-22 (2026-06-09)

**Method:** Re-verified both escalated gaps against current codebase after gap-closure plans executed. Added INIT-01 entries from plans 15 and 21.

#### Resolved Gaps
| Gap | Plan(s) | Evidence | Verdict |
|-----|---------|----------|---------|
| 20-0G-01 (T2 mypy) | 13, 16, 17, 18 | `mypy --strict src/` → "Success: no issues found in 306 source files"; test_mypy_strict.py PASSES | **RESOLVED** |
| 20-0C-02 (A1 file size) | 19, 20, 14, 22 | `file_size_rules.py` exits 0; 0 files >400 LOC; test_file_size_compliance.py PASSES | **RESOLVED** |

#### New Validation Entries (INIT-01)
| Task ID | Plan | Requirement | Test File | Status |
|---------|------|-------------|-----------|--------|
| 20-15-01 | 15 | INIT-01 (init_rules.py BLQ1401/BLQ1402) | test_init_rules.py | ✅ green |
| 20-21-01 | 21 | INIT-01 (layout_rules.py BLQ1501/BLQ1502/BLQ1503) | test_layout_rules.py | ✅ green |

#### Test Files Created (Audit #3)
| # | File | Tests | Type |
|---|------|-------|------|
| 1 | tests/cases/unit/unit/test_init_rules.py | 1 | compliance |
| 2 | tests/cases/unit/unit/test_layout_rules.py | 1 | compliance |

#### Resolution Chain
1. **T2 (mypy --strict):** Plan 13 (-70 errors), Plan 16 (-69 errors), Plan 17 (-175 errors), Plan 18 (final -183 → 0). Total: 497 errors eliminated across 4 plans.
2. **A1 (file size):** Plan 19 (3 files split), Plan 20 (3 files split), Plan 14 (xfail removed), Plan 22 (final verification). All 7 oversized files now below 400 LOC.
3. **INIT-01 (package hygiene):** Plan 15 (rules created), Plan 21 (52 files classified, 31 violations fixed, .ruff/ merged). Rules enforce classification at pre-commit.

#### Audit #3 Summary
| Metric | Count |
|--------|-------|
| Gaps re-audited | 2 (both resolved) |
| New validation entries | 2 (INIT-01) |
| Test files created | 2 |
| Total Nyquist tests | 10 files, 68 tests |
| nyquist_compliant | **true** |
