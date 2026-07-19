# Phase 20: Multiple Refactorings — Specification

**Created:** 2026-06-08
**Ambiguity score:** 0.104 (gate: ≤ 0.20)
**Requirements:** 13 locked (typing, architecture, and documentation tasks)

## Goal

Elevate the project from 4-star to 5-star quality across three dimensions simultaneously: type safety (mypy `--strict` compliance with zero errors across entire repository), architecture (no file exceeds 400 LOC, plugins audited and modularized, Go parser extracted as optional extra, explicit layered architecture), and documentation (complete object map with architectural scores, responsibility contracts for every Python entity, auto-generated API reference, 10 ADRs, 5 how-to guides).

## Background

Phase 20 is a comprehensive quality upgrade for pytest-bdd-ng. The project has completed 19 stabilization phases establishing code quality gates (Phase 2), core refactoring (Phase 3), plugin unification (Phase 10), compatibility streamlining (Phase 9), and documentation pipeline (Phase 19). The codebase is structurally sound but lacks production-grade typing, has 9 Python files exceeding 400 LOC, and has no formal API reference or architecture decision records.

**Current state (from codebase scouting):**

**Typing:**
- mypy configured with `check_untyped_defs`, `warn_return_any`, `show_error_codes` — but 9 critical `--strict` flags missing
- 21 packages in `ignore_missing_imports` (attrs, cucumber_messages, gherkin, pytest, pluggy, decopatch, parse, etc.)
- 33 `# type: ignore` comments exist (all with error codes — no bare ignores detected)
- Zero `.pyi` stub files in the project
- CI skips mypy pre-commit hook (`ci: skip: [mypy]`)
- ruff `ANN` (flake8-annotations) enforced; `PYI` (flake8-pyi) enabled but no .pyi files exist

**Architecture:**
- 9 Python files exceed 400 LOC: parsers.py (606), lifecycle_runtime.py (551), run/lifecycle.py (544), pickle_runner/plugin.py (542), struct_bdd/model.py (498), message_capability_governance/cli.py (454), message_stream_validation.py (453), scenario_locator.py (447), tests_group_ordering.py (439)
- 18 plugins under `src/pytest_bdd/plugin/` — zero cross-plugin imports (BLQ1002 passing)
- But core layers (model/, steps/, parser/) have compile-time dependencies on plugin implementations (pickle_runner, struct_bdd, gherkin_message_reporter)
- Go parser at `_gherkin_go/` (4 files, 279 LOC) — only one production consumer (collector_batch.py), env-var-gated fallback
- docs/architecture/LAYERS.md does not exist
- Custom ruff rules enforce plugin patterns (BLQ1001-BLQ1003) and quality gates (BLQ901-BLQ902)

**Documentation:**
- Sphinx configured with `sphinx.ext.autodoc` but no API reference pages exist
- Zero ADR files (`docs/adr/` does not exist)
- No `docs/guides/` or `docs/howto/` directories
- `docs/architecture/OBJECT_MAP.md` does not exist
- Core public API (__init__.py exports, scenario.py, steps/decorators.py) well-documented; internal modules have ~1,865 D100-D107 docstring violations
- `make docs` works via Sphinx + ReadTheDocs; no pdoc or sphinx-autodoc2

## Requirements

### Area 1: Typing (T0-T3)

1. **T0: Type checker comparison**: Research and compare production-grade type checkers beyond mypy.
   - Current: Only mypy used; pyright, ty, pytype not evaluated
   - Target: Install and run pyright (Microsoft), ty (Astral/ruff team), pytype (Google) on `src/`. Compare findings with mypy: what each catches, what mypy misses, speed, message quality, pre-commit integration. Produce report with comparison table and CI recommendation (add / don't add each checker as additional gate).
   - Acceptance: Comparison report exists with table showing findings overlap and unique detections per checker; explicit recommendation for each checker's inclusion in CI

2. **T1: Eliminate ignored packages**: Resolve all 21 `ignore_missing_imports` entries without opening upstream issues.
   - Current: 21 packages in `[[tool.mypy.overrides]]` with `ignore_missing_imports = true`
   - Target: For each package: (a) check typeshed / `types-<pkg>` on PyPI and install if available; (b) if no public stubs exist, create local `.pyi` stubs at `src/pytest_bdd/_stubs/<pkg>/` and wire via `mypy_path`; (c) remove the `ignore_missing_imports` entry. `mypy --strict src/` must pass with 0 errors and 0 remaining `ignore_missing_imports` for external packages.
   - Acceptance: Zero `ignore_missing_imports = true` entries remain; `mypy --strict src/` exits 0 for all external packages

3. **T2: Enable strict mypy flags**: Activate all mypy `--strict` flags incrementally.
   - Current: Only `check_untyped_defs`, `warn_return_any`, `show_error_codes` enabled
   - Target: Enable one flag at a time in `pyproject.toml`: `disallow_untyped_defs`, `disallow_incomplete_defs`, `check_untyped_defs`, `warn_redundant_casts`, `warn_unused_ignores`, `warn_return_any`, `disallow_any_generics`, `no_implicit_optional`, `strict_equality`, `warn_no_return`, `local_partial_types`. On each step: fix all new errors (no exemptions — fix all regardless of count), commit, run full test matrix (Python 3.10-3.14, pytest 7-9). After all flags: `mypy --strict src/` exits 0.
   - Acceptance: All `--strict` flags enabled; `mypy --strict src/` exits 0; full CI matrix green at each step

4. **T3: Custom ruff rule for type: ignore**: Enforce disciplined `# type: ignore` usage.
   - Current: 33 `# type: ignore` comments exist, all with error codes — no bare ignores. No enforcement rule exists.
   - Target: Create a custom ruff plugin rule that: (a) requires a comment explaining the ignore reason (e.g., `# type: ignore[attr-defined] — upstream missing stubs`); (b) bans bare `# type: ignore` without error code; (c) syncs error codes with mypy `--show-error-codes`. Add to pre-commit. Apply to entire repository (src/ + tests/ + scripts/).
   - Acceptance: `ruff check` fails on bare `# type: ignore`; all existing ignores have both error code and explanation comment; rule runs in pre-commit

### Area 2: Architecture (A1-A4)

5. **A1: Custom ruff rule for file decomposition**: Detect oversized files and propose splits.
   - Current: 9 Python files exceed 400 LOC; no automated detection or split planning
   - Target: Create ruff plugin rule that: (a) flags files > 400 LOC; (b) analyzes AST for >3 unrelated responsibilities (classes/functions without shared imports/data); (c) proposes a split plan into sub-modules. Apply to: parsers.py (606), scenario_locator.py (447), message_stream_validation.py (453), testing/cucumber_formatters.py (418), util/tests_group_ordering.py (439). Each converted to a package with `facade.py` for backward compatibility. Target: no file in `src/` exceeds 400 LOC.
   - Acceptance: Custom rule runs in CI; no file in `src/` exceeds 400 LOC; all tests pass; public API unchanged via facade re-exports

6. **A2: Plugin modularity audit and cleanup**: Audit all 18 plugins, fix violations, split into core/extra.
   - Current: 18 plugins, zero cross-plugin imports (BLQ1002 passing), but core-to-plugin coupling exists (model/ imports pickle_runner, steps/ imports pickle_runner, parser/ imports struct_bdd)
   - Target: Verify and fix: (1) each plugin has clear Single Responsibility; (2) zero cross-plugin imports maintained; (3) plugins correctly separated by lifecycle: collection → parsing → runtime → reporting; (4) pytest hooks called in correct order. Split plugins into `core` (mandatory, always loaded) and `extra` (optional, loaded via `pytest -p` or extras in pyproject.toml). Output audit report with violations and resolutions.
   - Acceptance: Audit report: 0 SRP violations, 0 cross-plugin imports, clear lifecycle layers; `pyproject.toml` has `[project.optional-dependencies]` with core and extra plugin groups; full test suite passes

7. **A3: Extract Go parser to optional extra**: Make `pip install pytest-bdd` not require Go.
   - Current: Go parser at `src/pytest_bdd/_gherkin_go/` (4 files, 279 LOC), used by collector_batch.py, built via setuptools `BuildGoCommand`
   - Target: Create `go-parser` extra in `pyproject.toml`. Move `_gherkin_go/` + build logic (Go 1.21+, cgo, setuptools) into optional dependency. Keep Python fallback + `importlib` dynamic import in main package. CI: build wheel with Go parser as separate artifact. V39 bump optional — skip if it breaks the cgo bridge. Benchmark must show parsing speedup ≥2× with Go parser.
   - Acceptance: `pip install pytest-bdd` does NOT require Go; `pip install pytest-bdd[go-parser]` works; benchmark ≥2× speedup; CI produces separate Go-parser wheel artifact

8. **A4: Explicit architectural layers**: Define and enforce layer boundaries.
   - Current: No formal layer documentation; BLQ1002 enforces plugin isolation but core layers freely import plugins
   - Target: Define and document layers (bottom-up): foundation (stash, messages, util) → parsing (gherkin, markdown, feature batch) → model (Run, ScenarioRun, binding) → runtime (pickle_runner, step execution) → collection (scenario_test_collector) → reporting (formatters, reporters) → plugins (entrypoints). For each layer: module list, dependency direction (only upward), forbidden horizontal/downward dependencies. Write custom ruff rule that flags downward or horizontal imports between layers.
   - Acceptance: `docs/architecture/LAYERS.md` with layer table; custom rule in CI catches violations; 0 violations in codebase after fixes

9. **A5: Port custom static rules into unified Pylint checker plugin**: Migrate standalone AST checks into Pylint.
   - Current: 9 custom linter rules exist as standalone scripts under `src/pytest_bdd/_ruff/rules/` run via `uv run` in pre-commit and Makefile.
   - Target: Migrate all 9 custom linter rules (BLQ9xx, BLQ10xx, BLQ11xx, BLQ13xx, BLQ14xx, BLQ15xx, BLQ16xx) into a unified Pylint plugin package under `src/pytest_bdd/_pylint/`. Register plugin in Pylint configuration (`[tool.pylint.main]` in `pyproject.toml`). Integrate pylint check hook in `.pre-commit-config.yaml` and `Makefile`.
   - Acceptance: Pylint plugin registered and runs successfully in pre-commit and Makefile; custom rule violations are detected natively by Pylint; all custom linter tests ported to test the Pylint custom checkers; all checks pass.

### Area 3: Documentation (D0-D4)

9. **D0: Codebase object map with architectural scores**: Complete hierarchy of every object with quality scores.
   - Current: No object-level architecture documentation; `docs/architecture/` has component-level Mermaid diagrams only
   - Target: Build hierarchy: packages → modules → classes/functions → methods. For each object, generate documentation (in docstring or adjacent .md) with 0-5 score per criterion: (0) reason for existence, (1) SRP + Information Expert, (2) why not inline, (3) why not split further, (4) what problems it solves at its level, (5) Law of Demeter — what dependencies it hides, (6) why located in this module/package. Score tag inline (e.g., `#arch-eval:score=4`). Script `scripts/collect_arch_scores.py` produces summary with average ≥ 4.0. Batched delivery: wave 1 covers public API surface; phase succeeds when wave 1 complete; full coverage continues in subsequent waves.
   - Acceptance: Object map in `docs/architecture/OBJECT_MAP.md` or docstrings; `python scripts/collect_arch_scores.py` outputs summary with average ≥ 4.0; public API objects have scores

10. **D1: Auto-generated API reference**: Generate API docs from type hints.
    - Current: `sphinx.ext.autodoc` configured but no API reference pages; no autodoc directives in any `.rst`/`.md` file
    - Target: Set up `docs/api/` with autodoc pages for all public modules. Support attrs + generics. CI check: all public classes/functions have docstring with Args/Returns/Raises. 100% of public symbols documented.
    - Acceptance: `make docs` builds without warnings; 100% public symbols have docstring with Args/Returns/Raises; ReadTheDocs publishes current version

11. **D2: Architecture Decision Records**: Document 10 key decisions.
    - Current: No ADR files exist; `specs/` directory (23 specs) partially fills this role but isn't rendered in docs
    - Target: Create 10 ADR files at `docs/adr/NNN-short-title.md` using template (context, decision, consequences): (1) attrs vs dataclass, (2) StashBound pattern, (3) 3-file plugin structure, (4) Cucumber Messages as bus, (5) Go cgo parser, (6) test group ordering, (7) no return None policy, (8) pytest.config.stash runtime state, (9) feature batch parsing, (10) pickle runner isolation. Link from DEVELOPMENT.rst and README.
    - Acceptance: 10 ADR files at `docs/adr/`; linked from DEVELOPMENT.rst and README; new contributor finds rationale for any decision in <2 minutes

12. **D3: Tutorial and how-to guides**: Expand user-facing documentation.
    - Current: One tutorial (`docs/tutorial/`), no `docs/guides/` directory; `DOCUMENTATION.md` serves as catch-all
    - Target: Analyze `features/` and frequent issues. Write 5 new guides in `docs/guides/`: (1) Custom Gherkin parser, (2) Structured BDD (YAML/JSON), (3) Parallel execution with xdist, (4) Custom formatter plugin, (5) Migration from pytest-bdd v1. Each guide: problem statement → step-by-step solution → complete example → common mistakes.
    - Acceptance: 5 guide files at `docs/guides/`; metric: "time to first successful custom plugin" for new users under 30 minutes

13. **D4: Responsibility documentation for every Python entity**: Add architecture responsibility contracts to every module, class, function, method, async function, and async method under `src/pytest_bdd/`.
    - Current: D0 wave 1 documents public API object scores, but most internal entities do not expose their owned responsibility, reason for existence, delegation boundary, cohesion, separation from peers, consumers, or evidence-based score data in-source.
    - Target: Create/update `scripts/inject_responsibility_docstrings.py` to preserve existing docstrings and append missing contracts, create missing docstrings with normal summaries plus contracts, support `--check`, `--write`, and `--stub`, and emit `.planning/tmp/responsibility-docstrings-report.json`. `--stub` inserts `<...>` placeholders that fail validation until filled. Update `scripts/collect_arch_scores.py` to walk all `src/pytest_bdd/`, parse score tags, and regenerate `docs/architecture/OBJECT_MAP.md` with hierarchy, responsibility line, consumers, average/per-criterion scores, missing sections, summary, package averages, bottom 30, and risk zones. Add `scripts/analyze_responsibility_zones.py` to produce `docs/architecture/RESPONSIBILITY_GAPS.md` and `.planning/tmp/responsibility-gaps.json`. Add a Pylint rule for missing, placeholder, empty, and invalid responsibility contracts. Link the generated architecture/API artifacts from `docs/architecture/index.md`, `docs/api/index.md`, and `DEVELOPMENT.rst`.
    - Acceptance: Injector `--check` passes with zero missing contracts/placeholders; object map and gaps regenerate deterministically; Pylint responsibility gate passes and rejects fixtures with missing contracts/placeholders/invalid score values; Sphinx HTML build succeeds.

## Boundaries

**In scope:**
- T0-T3: Type checker comparison, stub creation/installation, all mypy `--strict` flags enabled, custom ruff rule for `# type: ignore`
- A1-A5: Ruff rule for file decomposition + split 5 named files, plugin modularity audit + fix violations + core/extra split, Go parser extraction to optional extra, architectural layer definition + enforcement rule, and unified Pylint checker plugin
- D0-D4: Full object map with scores, responsibility docstrings for every `src/pytest_bdd/` Python entity, auto-generated API reference via Sphinx autodoc, 10 ADR files, 5 how-to guides
- Entire repository typing enforcement (src/ + tests/ + scripts/)
- Mypy `--strict` with zero errors across all code

**Out of scope:**
- Changing type checker infrastructure beyond mypy (T0 is research only — adding pyright/ty/pytype to CI is a recommendation, not implementation)
- Refactoring plugin behavior or adding new plugin features (A2 is structural cleanup and categorization only)
- Replacing the build system (A3 keeps setuptools; no migration to maturin/poetry/hatch)
- Replacing decopatch (already deferred per D-01 from Phase 11)
- `parsers.py` behavior modification (A1 may split the file for organization but must not change parsing logic)
- Go v39 bump if it breaks the cgo bridge (A3 skips v39 if incompatible)
- New feature development or behavior changes while adding responsibility documentation; D4 is documentation/tooling/gating only
- New plugin development or new BDD feature support

## Constraints

- Python 3.10-3.14 compatibility must be maintained throughout
- pytest 7.x-9.x compatibility must be maintained
- Full test suite must pass at every step; CI matrix green after each mypy flag and each file split
- Mypy `--strict` enforcement: no exemptions — fix all errors regardless of count
- `parsers.py` logic is FROZEN during splits — file organization only, no behavior changes
- Go v39 bump is optional — skip if it breaks the cgo/ctypes bridge (current v28 is acceptable if v39 is incompatible)
- All custom ruff rules must run via pre-commit and in CI
- Public API backward compatibility required for all file splits (facade.py re-export pattern)
- D4 responsibility contracts must preserve runtime behavior; source edits are limited to docstrings/import-free tooling needs
- D4 main consumers must be derived from imports, calls, tests, and plugins rather than guessed
- D4 score values must reflect evidence; low scores are allowed and should feed responsibility gap reporting

## Acceptance Criteria

### Typing gates:
- [ ] T0: Comparison report exists with table covering pyright, ty, pytype vs mypy (findings, speed, integration)
- [ ] T1: Zero `ignore_missing_imports = true` entries remain; `mypy --strict src/` exits 0 for external packages
- [ ] T2: All `--strict` flags enabled in pyproject.toml; `mypy --strict src/` exits 0; CI matrix green
- [ ] T3: Custom ruff rule flags bare `# type: ignore`; all existing ignores have code + explanation; pre-commit enforces

### Architecture gates:
- [ ] A1: Custom ruff rule detects files >400 LOC with split proposals; no file in `src/` exceeds 400 LOC
- [ ] A2: Plugin audit report shows 0 SRP violations, 0 cross-plugin imports; pyproject.toml has core + extra groups
- [ ] A3: `pip install pytest-bdd` does NOT require Go; `pip install pytest-bdd[go-parser]` works; benchmark ≥2× speedup
- [ ] A4: `docs/architecture/LAYERS.md` exists; custom rule catches layer violations; 0 violations in codebase
- [ ] A5: Custom Pylint plugin package implements all 9 rules; plugin runs successfully in pre-commit and Makefile; unit tests pass

### Documentation gates:
- [ ] D0: Object map at `docs/architecture/OBJECT_MAP.md` or in docstrings; `scripts/collect_arch_scores.py` shows avg ≥ 4.0 for wave 1 (public API)
- [ ] D1: `make docs` builds without warnings; 100% public symbols have Args/Returns/Raises docstrings; ReadTheDocs publishes
- [ ] D2: 10 ADR files at `docs/adr/`; linked from DEVELOPMENT.rst and README
- [ ] D3: 5 guide files at `docs/guides/`; each has problem → solution → example → mistakes format
- [ ] D4: Every Python entity under `src/pytest_bdd/` has a filled responsibility contract; injector, object map, gap analyzer, Pylint gate, and Sphinx build all pass

### Cross-cutting gates:
- [ ] Full test suite passes at every intermediate step
- [ ] ruff check passes on entire repository (including new custom rules)
- [ ] All changes committed atomically per task
- [ ] CI matrix (Python 3.10-3.14 × pytest 7-9) green at phase completion

## Ambiguity Report

| Dimension          | Score | Min  | Status | Notes                              |
|--------------------|-------|------|--------|------------------------------------|
| Goal Clarity       | 0.95  | 0.75 | ✓      | 12 tasks across 3 sub-areas, all critical |
| Boundary Clarity   | 0.92  | 0.70 | ✓      | Explicit in-scope/out-of-scope for each area |
| Constraint Clarity | 0.82  | 0.65 | ✓      | No exemptions policy, Go v39 optional, parsers frozen |
| Acceptance Criteria| 0.85  | 0.70 | ✓      | 18 pass/fail checkboxes across 3 areas + cross-cutting |
| **Ambiguity**      | 0.104 | ≤0.20| ✓      | All dimensions above minimums |

## Interview Log

| Round | Perspective     | Question summary              | Decision locked                         |
|-------|-----------------|------------------------------|-----------------------------------------|
| 1     | Researcher      | Phase structure (one phase vs split) | 3 sub-areas within one phase |
| 1     | Researcher      | Priority ordering of 3 areas | All 3 equally critical — phase fails if any incomplete |
| 1     | Researcher      | Eliminate 21 mypy ignores vs fix 33 type:ignore | Eliminate all by search or creating stubs |
| 2     | Simplifier      | Mypy strict flags minimum scope | All `--strict` flags enabled with 0 errors — full compliance |
| 2     | Simplifier      | File decomposition minimum scope | Rule + split all 9 files, full backward compatibility |
| 2     | Simplifier      | Object map minimum scope | Full object map with scores for all objects |
| 5     | Documentation   | Responsibility documentation wave | Full responsibility contracts for every Python entity under `src/pytest_bdd/` |
| 3     | Boundary Keeper | Plugin audit depth | Audit + fix ALL violations found — full cleanup |
| 3     | Boundary Keeper | Go parser extraction adjacent changes | Allow v39 bump if needed; skip if breaks bridge |
| 3     | Boundary Keeper | Type:ignore rule scope | Entire repository (src/ + tests/ + scripts/) |
| 4     | Failure Analyst | Mypy strict errors exemption policy | No exemptions — fix all errors regardless of count |
| 4     | Failure Analyst | Go v39 compatibility risk | V39 optional — skip if breaks cgo bridge |
| 4     | Failure Analyst | Object map feasibility at 5000+ objects | Batched delivery — wave 1 (public API) gates phase |

---

*Phase: 20-multiple-refactorings*
*Spec created: 2026-06-08*
*Next step: /gsd-discuss-phase 20 — implementation decisions (task ordering, wave planning, tool selection)*
