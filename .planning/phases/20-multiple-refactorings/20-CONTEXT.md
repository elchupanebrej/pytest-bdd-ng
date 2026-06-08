# Phase 20: multiple-refactorings - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Elevate pytest-bdd-ng from 4-star to 5-star quality across three dimensions: type safety (mypy `--strict` compliance with zero errors across the entire repository), architecture (no file exceeds 400 LOC, plugins audited and modularized with core/extra split, Go parser extracted as optional extra, explicit layered architecture with enforcement rule), and documentation (complete public API object map with architectural scores, auto-generated API reference via Sphinx autodoc, 10 ADRs, 5 how-to guides).

This phase owns mypy `--strict` enforcement, stub creation for untyped packages, custom ruff rules for type:ignore/file-size/layer-violations, file decomposition of 5 oversized files, plugin audit and core/extra categorization, Go parser extraction to optional dependency, architectural layer definition and enforcement, object map generation (wave 1: public API), Sphinx autodoc API reference, 10 ADR files, and 5 user-facing how-to guides.

Out of scope: adding pyright/ty/pytype to CI (T0 is research only), refactoring plugin behavior, replacing the build system, replacing decopatch, modifying parsers.py logic (frozen during splits), Go v39 bump if it breaks the cgo bridge, new feature behavior while documenting responsibilities, new plugin development, or new BDD feature support.

</domain>

<spec_lock>
## Requirements (locked via SPEC.md)

**13 requirements are locked across 3 areas.** See `20-SPEC.md` for full requirements, boundaries, and acceptance criteria.

Downstream agents MUST read `20-SPEC.md` before planning or implementing. Requirements are not duplicated here.

**In scope (from SPEC.md):**
- T0-T3: Type checker comparison, stub creation/installation, all mypy `--strict` flags enabled, custom ruff rule for `# type: ignore`
- A1-A5: Ruff rule for file decomposition + split 5 named files, plugin modularity audit + fix violations + core/extra split, Go parser extraction to optional extra, architectural layer definition + enforcement rule, and unified Pylint checker plugin
- D0-D4: Full object map with scores, full responsibility docstrings for every `src/pytest_bdd/` Python entity, auto-generated API reference via Sphinx autodoc, 10 ADR files, 5 how-to guides
- Entire repository typing enforcement (src/ + tests/ + scripts/)
- Mypy `--strict` with zero errors across all code

**Out of scope (from SPEC.md):**
- Changing type checker infrastructure beyond mypy (T0 is research only — adding pyright/ty/pytype to CI is a recommendation, not implementation)
- Refactoring plugin behavior or adding new plugin features (A2 is structural cleanup and categorization only)
- Replacing the build system (A3 keeps setuptools; no migration to maturin/poetry/hatch)
- Replacing decopatch (already deferred per D-01 from Phase 11)
- `parsers.py` behavior modification (A1 may split the file for organization but must not change parsing logic)
- Go v39 bump if it breaks the cgo bridge (A3 skips v39 if incompatible)
- New feature development or behavior changes while adding responsibility documentation; D4 is documentation/tooling/gating only
- New plugin development or new BDD feature support

</spec_lock>

<decisions>
## Implementation Decisions

### Task Ordering and Wave Planning
- **D-01:** Architecture (A1-A4) executes first, followed by Typing (T0-T3), then Documentation (D0-D3). Architecture is the structural foundation; typing errors cascade from structural changes; documentation reflects final state.
- **D-02:** Within Architecture, A4 (layer definition) executes before A2 (plugin audit) and A1 (file splits). Layer boundaries tell A1 where split sub-modules belong and A2 which plugins violate layer direction.
- **D-03:** Within Typing, T0 (type checker comparison) gates T1-T3. The comparison report may reveal findings that affect stub strategy or flag prioritization.
- **D-04:** ADRs (D2) are written during architecture work as design documents, before implementation. Each architecture task (stubs strategy, layer model, plugin split, Go extraction) gets its ADR as a design gate.
- **D-05:** D0 (object map wave 1) and D1 (API reference) execute after architecture and typing are stable. D3 (how-to guides) can run in parallel with D0/D1 since guides are user-facing and don't depend on internal object scoring.

### Stub Packaging Strategy (T1)
- **D-06:** Local `.pyi` stubs ship in the distributed wheel so downstream users can run mypy on code that imports pytest-bdd without installing types-* packages.
- **D-07:** Stubs live at `stubs/` at the repository root (not under `src/pytest_bdd/_stubs/`). This is the standard typeshed-like layout. `mypy_path = stubs` in `pyproject.toml` picks them up.
- **D-08:** Stubs are organized as package directories with `__init__.pyi` (e.g., `stubs/pluggy/__init__.pyi`). This allows adding sub-module stubs later and matches typeshed convention.

### Custom Ruff Rule Organization
- **D-09:** Three separate rule files under `src/pytest_bdd/_ruff/` matching the existing pattern (`plugin_patterns.py`, `quality_gates.py`): `typing_rules.py` (T3: type:ignore enforcement), `file_size_rules.py` (A1: file-size detection), `layer_rules.py` (A4: layer violation).
- **D-10:** The file-size rule (A1) performs AST analysis to count distinct responsibility clusters (classes/functions without shared imports/data) and outputs split proposals, not just a >400 LOC flag.
- **D-11:** Layer boundaries (A4) are defined in a configuration file (TOML), not hardcoded in the rule source. The rule reads the config at runtime, allowing layer updates without rule code changes.

### Plugin Core/Extra Split Criteria (A2)
- **D-12:** Core plugins (always loaded, no opt-out): `scenario_test_collector` (collection), `pickle_runner` (execution), `gherkin_message_reporter` (live reporting bridge). These form the runtime-critical path — without them, pytest-bdd does nothing.
- **D-13:** Extra plugins are grouped thematically in `pyproject.toml` `[project.optional-dependencies]`: `formatters` (all 10 formatter plugins), `struct-bdd` (struct_bdd + deps), `allure` (allure_logger + allure-python-commons), `code-gen` (code_generator).
- **D-14:** Extra plugins auto-load when their optional-dependency extra is installed (via pytest11 entry points). Users do not need to pass `-p` explicitly; installing the extra is sufficient.

### the agent's Discretion
- Exact plan breakdown into numbered sub-plans (which tasks share a plan, wave grouping)
- Exact stub file content and which packages get types-* vs local stubs
- Exact ruff rule implementation details (prefix codes, visitor patterns, test approach)
- Exact TOML config schema for layer boundaries
- Exact `pyproject.toml` extras dependency lists and entry point registration
- ADR template and exact ADR numbering
- How-to guide content and example code beyond what SPEC.md specifies
- Object map scoring script implementation and output format
- Sphinx autodoc page structure and directive placement
- Go parser build system changes within the setuptools constraint

### Responsibility Documentation Expansion (D4)
- **D-15:** Add a new documentation wave after the existing Pylint/static-analysis work. The wave owns full responsibility documentation for every Python entity under `src/pytest_bdd/`.
- **D-16:** Existing docstrings are source-of-truth prose and must be preserved. Contracts are appended when absent; missing docstrings get a short normal summary plus the architecture contract.
- **D-17:** Responsibility contracts must document direct owned responsibility, reason for existence, delegates, cohesion, separation from actual peers when possible, main consumers derived from source evidence, and score values. Low scores are valid when evidence supports them.
- **D-18:** Tooling is part of the requirement: an idempotent injector/checker with `--check`, `--write`, and `--stub`; expanded object-map scoring; responsibility-zone analysis; Pylint validation; and Sphinx documentation links.
- **D-19:** The stub workflow intentionally inserts `<...>` placeholders for incomplete contracts and those placeholders must fail validation until filled.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Definition
- `.planning/phases/20-multiple-refactorings/20-SPEC.md` — **Locked requirements — MUST read before planning.** 13 requirements across Typing (T0-T3), Architecture (A1-A5), Documentation (D0-D4). Boundaries, constraints, and acceptance criteria checkboxes.
- `.planning/phases/20-multiple-refactorings/20-32-PLAN.md` — D4 full responsibility documentation wave covering docstring contracts, injector/check tooling, object map expansion, gap analysis, Pylint gate, and docs links.
- `.planning/ROADMAP.md` — Phase 20 entry and dependency on Phase 19.

### Project-Level
- `.planning/PROJECT.md` — Project constraints: `attrs` over `dataclass`, `StashBound` pattern, no comments unless asked, compatibility matrix.
- `.planning/REQUIREMENTS.md` — Requirement traceability and deferred testing concerns.
- `.planning/STATE.md` — Current state: 19 phases complete, TEST-01/TEST-02 deferred to next milestone.

### Prior Phase Decisions
- `.planning/phases/17-adapt-github-ci-to-use-make-and-validate-with-act/17-CONTEXT.md` — Makefile as project command boundary; CI setup stays visible in workflows.
- `.planning/phases/18-split-xdist-remote-tests-into-separate-parallel-gha-executor/18-CONTEXT.md` — Preserve Makefile boundary; avoid unrelated CI redesign.
- `.planning/phases/19-html-doc-generation-simplification/19-CONTEXT.md` — Generated artifacts handling; MyST/Sphinx integration patterns; `docs/conf.py` as Sphinx config center.

### Codebase Maps
- `.planning/codebase/ARCHITECTURE.md` — Plugin-oriented architecture, layers (Plugin/Model/Collector/Parser/StepDefinition/PublicAPI/Compatibility/Utility), stash-based state management, step matching flow, plugin entry point registration.
- `.planning/codebase/CONVENTIONS.md` — Code style: `ruff format` 120-char lines, `attrs` for data classes, `from __future__ import annotations` in all source files, naming patterns, import organization, error handling patterns.
- `.planning/codebase/STACK.md` — Tooling: mypy with `check_untyped_defs`, ruff rule sets, tox matrix, pytest entry points, Go build-time deps, JavaScript formatter bridge.

### Source and Configuration
- `pyproject.toml` — `[tool.mypy]` overrides (21 `ignore_missing_imports` entries to eliminate), `[project.entry-points.pytest11]` (18 plugins to categorize), `[tool.ruff]` rules, `[tool.setuptools]` package data.
- `src/pytest_bdd/_ruff/` — Existing custom ruff rule directory (`plugin_patterns.py` BLQ1001-BLQ1003, `quality_gates.py` BLQ901-BLQ902). Three new rule files go here.
- `src/pytest_bdd/plugin/` — 18 plugin directories/packages to audit and categorize.
- `src/pytest_bdd/_gherkin_go/` — Go parser (4 files, 279 LOC) to extract to optional extra.
- `docs/conf.py` — Sphinx configuration; enable autodoc pages.
- `Makefile` — Project command boundary; add `type-check` target if needed.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/pytest_bdd/_ruff/plugin_patterns.py` — Existing custom ruff rule pattern (BLQ prefix, visitor-based AST analysis, multiple rules per file). Blueprint for three new rule files.
- `src/pytest_bdd/_ruff/quality_gates.py` — Second existing rule file confirming the separate-files-by-concern pattern.
- `docs/conf.py` — Sphinx config already uses `myst_parser` and `sphinx.ext.autodoc`. Only needs autodoc directive pages, not new extension setup.
- `pyproject.toml` `[project.entry-points.pytest11]` — Existing 18-plugin registration. Core/extra split reorganizes this section.
- `_gherkin_go/` + `pyproject.toml` `[tool.setuptools.cmdclass] build_go` — Complete Go parser build chain ready to move to optional extra.

### Established Patterns
- Custom ruff rules follow `_ruff/<concern>.py` with BLQ prefix codes, visitor classes, and per-file test fixtures.
- Makefile is the project command boundary; CI delegates to Makefile targets (Phase 17).
- `attrs` used for all data classes; `StashBound` for config stash access; `from __future__ import annotations` in every source file.
- Plugin structure follows `entrypoint.py` + `plugin.py` + hook implementations; cross-plugin imports forbidden (BLQ1002 enforces).
- Generated docs under `docs/` are transient build artifacts; source-of-truth stays in `features/` or `src/`.

### Integration Points
- `pyproject.toml`: Add 3 new ruff rules to `[tool.ruff.lint].select`; remove `ignore_missing_imports` entries; add `[project.optional-dependencies]` for plugin groups; add `stubs/` to package data; add `mypy_path = stubs`.
- `src/pytest_bdd/_ruff/`: Add `typing_rules.py`, `file_size_rules.py`, `layer_rules.py`.
- `src/pytest_bdd/plugin/`: Restructure 18 plugins into core (3) + extra (15 in 4 thematic groups).
- `_gherkin_go/`: Move to optional extra; keep Python fallback + `importlib` dynamic import in main package.
- `docs/`: Add `docs/api/` with autodoc pages, `docs/adr/` with 10 ADRs, `docs/guides/` with 5 how-to guides, `docs/architecture/LAYERS.md` and `docs/architecture/OBJECT_MAP.md`.
- `stubs/`: New directory at repo root with package subdirectories containing `__init__.pyi` files.
- Split targets (A1): `parsers.py` → `parsers/` package, `scenario_locator.py` → package, `message_stream_validation.py` → package, `testing/cucumber_formatters.py` → package, `util/tests_group_ordering.py` → package. Each gets `facade.py` for backward compatibility.

</code_context>

<specifics>
## Specific Ideas

- Architecture executes first because structural changes cascade typing errors and documentation should reflect final state.
- A4 (layer definition) comes before A2 (audit) and A1 (splits) because layer boundaries determine where split sub-modules belong and which plugin dependencies are violations.
- ADRs serve as design documents during architecture work, not as retrospective documentation after the fact.
- T0 research gates T1-T3 because the type checker comparison may surface findings that affect stub strategy.
- File-size ruff rule should go beyond simple LOC counting — AST analysis identifies responsibility clusters for split proposals.
- Layer boundaries should be config-driven (TOML) so the enforcement rule stays decoupled from layer model evolution.
- Plugin auto-loading from extras preserves current user experience; no `-p` flag required for extra plugins when the extra is installed.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

### Reviewed Todos (not folded)
- **Integrate BDD/ATDD tests into development workflow and UAT phase** — weak match (score 0.2); broad process change outside typing/architecture/docs refactoring scope.
- **Vulture must be run not via pytest but as pre-commit hook** — weak match (score 0.2); completed Phase 16 scope.
- **Fix Makefile SHELL for cross-platform (Win/Mac/Linux)** — weak match (score 0.2); completed Phase 15 scope.

</deferred>

---

*Phase: 20-multiple-refactorings*
*Context gathered: 2026-06-08*
