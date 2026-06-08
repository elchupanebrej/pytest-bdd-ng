# Phase 11: Audit & Prune — Specification

**Created:** 2026-06-08
**Ambiguity score:** 0.071 (gate: ≤ 0.20)
**Requirements:** 8 locked

## Goal

Achieve zero dead code, zero unused imports, and zero stale modules in `src/pytest_bdd/`; split 3 large files (>700 LOC) into focused sub-modules; validate the full CI matrix passes across all Python 3.10-3.14 × pytest 7.x-latest combinations.

## Background

Phase 11 is the final quality sweep in the v1.0 stabilization milestone. Prior phases established code quality gates (Phase 2), refactored core runtime (Phase 3), unified plugin patterns (Phase 10), and streamlined compatibility (Phase 9). This phase audits remaining dead code, splits the last 3 oversized source files, documents plugin justifications, and validates the complete CI matrix as the final gate.

Current state (from codebase research):
- ruff F401/F811/ERA001 already passes clean — lint gate satisfied
- vulture found 12 high-confidence (80%+) dead code findings and 270 at 60% confidence
- 3 modules confirmed dead: `feature_locator.py` (292L, zero imports), `runner.py:validate_requested_pair` (unused function), `util/temp_root.py` (zero imports)
- 3 files exceed 700 LOC: `steps.py` (971L), `message_capability_governance.py` (853L), `run.py` (783L)
- 17 plugins are active with entry points in `pyproject.toml` — none are dead
- decopatch (1.4.10, 2022 release) to be kept as-is per D-01
- `parsers.py` is FROZEN (tests only — no modifications)

## Requirements

1. **Dead import removal**: All dead imports eliminated from `src/pytest_bdd/`.
   - Current: ruff F401/F811 already passes clean across the codebase
   - Target: Zero dead imports — ruff `--select F401,F811` passes clean on `src/pytest_bdd/`
   - Acceptance: `uv run python -m ruff check src/pytest_bdd/ --select F401,F811` exits with code 0 and reports "All checks passed!"

2. **Dead module removal**: Confirmed dead modules removed from the source tree.
   - Current: `feature_locator.py` (292L, zero imports), `runner.py:validate_requested_pair` (unused function), `util/temp_root.py` (zero imports) exist in the codebase
   - Target: All 3 confirmed dead modules removed; no `ModuleNotFoundError` or `ImportError` in tests
   - Acceptance: Full test suite passes after removal; `grep -r "feature_locator\|temp_root\|validate_requested_pair" src/ tests/` returns zero results (except deprecation-documentation references)

3. **Vulture 80%+ findings audited**: Each of the 12 high-confidence vulture findings manually reviewed and resolved.
   - Current: 12 vulture findings at 80%+ confidence reported by `vulture src/pytest_bdd/ --min-confidence 80`
   - Target: Zero findings at 80%+ confidence after audit — each finding either: (a) code removed because genuinely dead, or (b) code retained with documented justification. Pytest hook methods `pytest_*` must be verified against `pyproject.toml` entry points before any removal.
   - Acceptance: `uv run python -m vulture src/pytest_bdd/ --min-confidence 80` exits with zero findings; all retained findings have justification in phase audit report

4. **Commented-out code removal**: No commented-out code blocks remain except deprecation-path documentation.
   - Current: ruff ERA001 passes clean (already enforced via pre-commit)
   - Target: Continue clean pass; no new commented-out code added during file splits
   - Acceptance: `uv run python -m ruff check src/pytest_bdd/ --select ERA001` exits with code 0

5. **Large file splits**: Three oversized files split into sub-module packages with backward-compatible direct imports.
   - Current: `steps.py` (971L), `message_capability_governance.py` (853L), `run.py` (783L) — all above 700 LOC
   - Target: Each file converted to a package with sub-modules. Exact sub-module boundaries determined during implementation. New sub-module paths are the primary import path — old `from pytest_bdd.X import Y` paths may be removed. No file in `src/pytest_bdd/` exceeds 500 LOC after splits.
   - Acceptance: No file in `src/` exceeds 500 LOC; full test suite passes; dedicated import test verifies all public API paths resolve; ruff F401 passes clean on new `__init__.py` files

6. **Plugin audit report**: All 17 active plugins documented with usage justification.
   - Current: No per-plugin documentation exists beyond `pyproject.toml` entry points and source code
   - Target: Per-plugin audit files at `docs/audit/plugins/<plugin_name>.md` for each of the 17 plugins, covering: entry point, purpose, test coverage status, and justification for retention
   - Acceptance: 17 files exist at `docs/audit/plugins/*.md`; each file contains entry point declaration, purpose, test coverage, and justification

7. **Decopatch health documentation**: Full health metrics documented for the decopatch dependency.
   - Current: decopatch 1.4.10 in use; health status not formally documented
   - Target: Full metrics table document created covering: version, last release date, repository stars, open PRs, commit activity, maintainer responsiveness assessment
   - Acceptance: Decopatch health metrics published in `docs/audit/decopatch-health.md` or appended to plugin audit report

8. **CI matrix validation**: Full tox matrix passes all environments.
   - Current: tox.ini defines ~30 environments (Python 3.10-3.14 × pytest 7.x-latest × platforms); matrix infrastructure exists
   - Target: All ~30 tox environments pass unconditionally. Core subset validated at intermediate implementation steps; full matrix via `act` at phase end. No tolerance for infrastructure flakiness — any failure blocks the phase until resolved.
   - Acceptance: `uv run tox` exit code 0 (all environments green); `act` workflow run green on full matrix; no environment skipped or marked as "known failure"

## Boundaries

**In scope:**
- Dead code removal: confirmed dead modules (`feature_locator.py`, `validate_requested_pair`, `temp_root.py`)
- Vulture audit: manual review and resolution of all 12 high-confidence (80%+) findings
- Commented-out code: verified clean via ruff ERA001
- Large file splits: `steps.py`, `message_capability_governance.py`, `run.py` → sub-module packages
- Plugin audit: per-plugin documentation for all 17 active plugins
- Decopatch health: full metrics table documenting dependency status
- CI matrix: full tox matrix validation across all environments
- Project size metrics: baseline and final measurements of LOC, file count, import count, largest file size, average file size, cyclomatic complexity

**Out of scope:**
- decopatch replacement — deferred to future phase (keep as-is per D-01)
- New plugin development — stabilization phase only
- `parsers.py` modifications — FROZEN (tests only)
- Python version support matrix changes — keep 3.10-3.14
- `script/` module audit — only `src/pytest_bdd/` package is audited
- Vulture 60% confidence findings — only 80%+ findings in scope (60% findings are predominantly false positives)
- `script/` module evaluation beyond the 3 confirmed dead modules — `sync_messages_contract_schemas.py` and `validate_feature_headings.py` are test infrastructure, out of scope

## Constraints

- Must maintain Python 3.10-3.14 and pytest >=7.0.0 compatibility
- Large file splits must not break existing test suite — all tests must pass before/after
- Dedicated import test must verify all public API paths resolve after splits
- Pytest hook methods (`pytest_*`) must never be auto-removed on vulture signal alone — must cross-reference `pyproject.toml` entry points
- CI matrix must pass ALL environments unconditionally — no tolerance for infrastructure flakiness
- Phase gate: full matrix green via `act` before phase completion
- All 17 plugins confirmed active and retained — none removed based on assumed low usage
- ruff F401/F811/ERA001 must remain clean throughout
- `parsers.py` is FROZEN — no modifications permitted

## Acceptance Criteria

- [ ] `uv run python -m ruff check src/pytest_bdd/ --select F401,F811,ERA001` exits with code 0
- [ ] `uv run python -m vulture src/pytest_bdd/ --min-confidence 80` exits with zero findings
- [ ] 3 confirmed dead modules removed: `feature_locator.py`, `validate_requested_pair`, `temp_root.py`
- [ ] Full test suite passes after dead module removal
- [ ] `steps.py` (971L) split into sub-module package — no file exceeds 500 LOC
- [ ] `message_capability_governance.py` (853L) split into sub-module package — no file exceeds 500 LOC
- [ ] `run.py` (783L) split into sub-module package — no file exceeds 500 LOC
- [ ] No file in `src/` exceeds 500 LOC after splits
- [ ] Dedicated import test verifies all public API paths resolve
- [ ] Full test suite passes after each file split
- [ ] 17 per-plugin audit files exist at `docs/audit/plugins/*.md`
- [ ] Decopatch health metrics documented
- [ ] Full tox matrix green: `uv run tox` exit code 0
- [ ] `act` workflow run green on full matrix
- [ ] Project size metrics captured: baseline (before) and final (after) — all 6 metrics reduced or stable

## Ambiguity Report

| Dimension          | Score | Min  | Status | Notes                              |
|--------------------|-------|------|--------|------------------------------------|
| Goal Clarity       | 0.98  | 0.75 | ✓      | All 6 scope items from CONTEXT.md confirmed |
| Boundary Clarity   | 0.98  | 0.70 | ✓      | Explicit in-scope/out-of-scope lists locked |
| Constraint Clarity | 0.95  | 0.65 | ✓      | CI unconditional pass, parser frozen, plugin retention confirmed |
| Acceptance Criteria| 0.97  | 0.70 | ✓      | 16 pass/fail checkboxes defined |
| **Ambiguity**      | 0.071 | ≤0.20| ✓      | All dimensions above minimums |

## Interview Log

| Round | Perspective     | Question summary              | Decision locked                         |
|-------|-----------------|------------------------------|-----------------------------------------|
| 1     | Researcher      | Vulture 80%+ findings disposition | Manual audit each finding individually |
| 1     | Researcher      | File split boundary precision | Exact sub-module boundaries determined during implementation |
| 1     | Researcher      | CI matrix gate scope | Core subset at intermediate steps; full `act` run at phase end |
| 2     | Simplifier      | Plugin justification format | Consolidated audit report with per-plugin files |
| 2     | Simplifier      | Minimum viable outcome | All 6 scope items from CONTEXT.md — nothing cut |
| 2     | Simplifier      | Decopatch health depth | Full metrics table (version, last release, stars, open PRs, commit activity) |
| 3     | Boundary Keeper | Adjacent exclusions | Only CONTEXT.md exclusions — nothing else |
| 3     | Boundary Keeper | Split import compatibility | New sub-module paths are primary; old paths may be removed |
| 3     | Boundary Keeper | CI failure tolerance | All environments must pass unconditionally — no tolerance for flakiness |
| 4     | Failure Analyst | Vulture hook false-positive risk | Planner must verify each 80%+ finding against `pyproject.toml` entry points |
| 4     | Failure Analyst | Split re-export chain verification | Explicit import test for all public API paths |
| 4     | Failure Analyst | CI flakiness contingency | Phase blocked until clean run — no tolerance for flakiness |
| 5     | Seed Closer     | Plugin audit file format | Per-plugin files at `docs/audit/plugins/<plugin_name>.md` |
| 5     | Seed Closer     | Project size metrics scope | All 6 metrics: LOC, file count, import count, largest file, avg file size, cyclomatic complexity |
| 5     | Seed Closer     | `script/` module audit scope | Only audit `src/pytest_bdd/` package — `script/` modules excluded |

---

*Phase: 11-audit-prune*
*Spec created: 2026-06-08*
*Next step: /gsd-discuss-phase 11 — implementation decisions (module boundaries, CI config, audit methodology)*
