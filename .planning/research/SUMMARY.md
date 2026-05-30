# Project Research Summary

**Project:** pytest-bdd-ng (BDD testing library — pytest plugin)
**Domain:** Python BDD testing / Cucumber ecosystem
**Researched:** 2026-05-12
**Confidence:** HIGH

## Executive Summary

pytest-bdd-ng is a mature, feature-rich BDD testing plugin for pytest in a **brownfield stabilization phase**. It already holds competitive parity with or exceeds every Python BDD tool (behave, radish) and matches Cucumber.js/Reqnroll on protocol compliance. The core differentiators — pytest fixture dependency injection, Cucumber Messages protocol, Go parser backend, Struct BDD, and Markdown Gherkin — are all functioning. This is not a greenfield "build" but a **hardening** initiative.

The recommended approach is **stabilize before refactoring**. Four critical code-quality gates must pass before any structural changes: remove the dead Allure plugin (STAB-01), eliminate 96 `return None` instances in non-hook code (STAB-02), replace 22 bare `except Exception:` handlers (STAB-03), and add deprecation warnings for legacy CLI flags (STAB-04). Only after these gates should the 1422-line `scenario_run.py` be split (REF-01) — the highest-risk refactoring due to implicit state coupling between `Run`, `ScenarioRun`, and `FeatureRuntimeBinding` classes.

The top risk is **silent pass bugs**: scenarios with zero matched step definitions passing green because `return None` propagates without an error signal. This is the primary motivator for the STAB-02 phase and must be verified with collection-time validation. Secondary risks include step matching priority regressions during refactoring, state machine desync after module splits, and broad exception handlers masking dependency-upgrade failures. All are addressable with contract/characterization tests before touching production code.

## Key Findings

### Recommended Stack

The stack is fundamentally sound but critically behind on version pins. Three immediate bumps are required: **pytest >=8.0.0** (dropping unsupported 7.x), **gherkin-official >=39.1.0** (current pin `>=33` is 6 major versions behind and out of protocol sync), and **cucumber-messages <33** (add upper bound to prevent silent breaking changes). The Go parser backend must be bumped from v28 to v39 to match the Python parser's output format — protocol misalignment between backends would cause subtle, hard-to-debug failures.

Dead weight to remove: `pathlib2` (Python 2 backport — project requires 3.10+), `docopt-ng` (legacy CLI parser — replace with argparse/click). Audit items: `decopatch` (unverifiable health, JS-rendered PyPI page) — if only used for simple decorator patterns, replace with `functools.wraps` + manual factories.

**Core technologies:**
- **pytest >=8.0.0, <10**: Plugin host with `config.stash` for type-safe cross-plugin state. 7.x lacks stash improvements and modern hook ordering.
- **gherkin-official >=39.1.0, <40**: Primary Gherkin parser (Python), must align with cucumber-messages 32.x protocol. Go backend must match at `go/v39`.
- **cucumber-messages >=32.3.1, <33**: Canonical Cucumber protocol — all formatters and live reporter depend on it. Pin upper bound to prevent silent breaking changes at v33.
- **cucumber-expressions**: Preferred step parser for Cucumber interoperability. One of 7 supported parser types.
- **attrs (latest)**: Data classes with `@attrs.define`. Project standard over stdlib `dataclass`.
- **ruff >=0.15.0**: Linting + formatting. Pre-commit config should use `rev: v0.15.12`.

### Expected Features

All table-stakes features exist and work: Gherkin parsing (plain + Markdown), 7 step parser types, scenario outlines, data tables, docstrings, Background steps, tags → pytest markers, fixture dependency injection, scenario-level hooks, Cucumber JSON/JUnit reporters, pretty terminal output, xdist parallel execution, and code generation. Nothing is missing at the foundational level.

The stabilization milestone focuses on **quality, not new features**. The P1 scope covers: eliminating `return None` in non-hook code (STAB-02), replacing bare `except Exception:` (STAB-03), splitting `scenario_run.py` (REF-01), and creating a migration guide (DOC-03). P2 adds the Allure plugin decision (STAB-01), code generator class-based refactor (REF-02), and documentation improvements (DOC-01/02). P3 (post-stabilization) defers async step definitions, retry mechanism, better error messages, and working example directories.

**Anti-features document** what NOT to build: built-in web dashboard (scope creep — use existing Messages bridge), custom Gherkin dialects (breaks interoperability), scenario-to-scenario dependencies (violates BDD principles), global mutable context objects (undermines pytest fixture isolation), and automatic retry of all failures (masks flaky tests).

### Architecture Approach

The system follows a 4-layer architecture: **Public API** (decorators: `@given`, `@when`, `@then`, `scenarios()`) → **Plugin Layer** (17 plugins registered via `pytest11` entry points, each following class + StashBound pattern) → **Core Layer** (domain models `Run`/`ScenarioRun`/`FeatureRuntimeBinding`, `StepDefinitionManager`, parser subsystem) → **pytest Framework** (`config.stash`, `pluggy` hooks, fixture injection).

The canonical architectural patterns are well-established: (1) **Plugin class + registration** — each plugin is a class with hook methods registered in `pytest_configure`, (2) **StashBound for session state** — typed `StashKey[T]` keys with `initialize_in_stash()`, `from_stash()`, `find_in_stash()` classmethods, (3) **Hook-driven inter-plugin communication** — plugins never directly import each other, they call `config.hook.pytest_bdd_*()`, (4) **Formatter base class hierarchy** — 12 formatter plugins share `FormatterReporterPlugin` base class.

The #1 architectural problem is the 1422-line `scenario_run.py` god module combining `Run`, `ScenarioRun`, `FeatureRuntimeBinding`, state machine transitions, hook lifecycle callbacks, stash access, and Cucumber Messages serialization. The recommended refactoring splits it into `model/run.py`, `model/scenario_run.py`, and `model/feature_binding.py` — but ONLY after characterization tests capture all state transitions.

**Major components:**
1. **Scenario Collector** (test discovery) — `FeatureBatchParser` async parallel parsing, `FileScenarioLocator`/`UrlScenarioLocator`, pytest collection integration
2. **Pickle Runner** (step execution) — state machine (`RunStage` transitions), hook dispatch, step matching via `StepDefinitionManager.Matcher` (3-pass matching)
3. **Formatters Subsystem** (12 output plugins) — Cucumber JSON, JUnit, Pretty, Progress, Snippets, live reporting bridge — all extend `FormatterReporterPlugin`
4. **Parser Subsystem** — ABC with Python (`gherkin-official`) and Go (ctypes) backends, plain + Markdown Gherkin support

### Critical Pitfalls

1. **Silent execution when no steps match** — Scenarios passing green with zero matched step definitions. Root cause: `return None` in the step-matching path propagates without error. Prevention: collection-time step binding validation; never let `StepMatchResult(matched=False)` propagate silently. Phase: STAB-02.

2. **Step matching priority regression during refactoring** — Splitting `steps.py` or reordering step registry changes which definition matches first. Killed pytest-bdd 6.0.0 (#542). Prevention: explicit priority order (not import-order-dependent), contract tests verifying "specific beats generic," full integration suite after any step registry changes. Phase: REF-02, REF-03.

3. **Module split breaks implicit state coupling** — Splitting 1422-line `scenario_run.py` into `run.py`/`scenario_run.py`/`feature_binding.py` can desync the state machine if implicit stash-based coupling isn't made explicit. Prevention: characterization tests for all `RunStage` transitions BEFORE splitting; move enums to dedicated `enums.py` first; test with xdist (`-n 2`). Phase: REF-01.

4. **Dead plugin code deceives users** — Allure logger plugin registered in `pyproject.toml` but `entrypoint.py` has all implementation commented out behind `# TODO: refactor`. Users installing `[allure]` extra get zero functionality with no error. Prevention: remove non-functional plugins from entry points immediately; a missing plugin is better than a dead one. Phase: STAB-01.

5. **Broad exception handlers mask dependency-upgrade failures** — 22 bare `except Exception:` clauses, including `collector.py:107` which swallows ALL parse failures during collection. Prevention: classify each instance (acceptable/logged/must-be-specific); add `logger.warning(exc_info=True)` for transport/hook failures; catch specific `ParserError`/`OSError`/`UnicodeDecodeError` for collection. Phase: STAB-03.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Stabilization Foundations
**Rationale:** Low-risk, independent cleanups that must happen before any refactoring. Dead plugin removal prevents user confusion; deprecation warnings signal intent before structural changes.
**Delivers:** Dead Allure plugin removed from entry points (or reimplemented), `DeprecationWarning` for `--cucumberjson`, `DEPRECATIONS.md` created.
**Addresses:** STAB-01 (Allure fate), STAB-04 (deprecation path)
**Avoids:** Pitfall 4 (dead plugin), Pitfall 8 (missing deprecation)
**Research flag:** Standard patterns — skip research-phase. Dead code removal and deprecation warnings are well-understood.

### Phase 2: Code Quality Gates
**Rationale:** MUST complete before ANY refactoring. The `return None` antipattern and bare `except` handlers would be copied into split modules, entrenching the problems. These gates ensure refactoring improves — rather than multiplies — technical debt.
**Delivers:** 96 `return None` instances reduced by 50%+ in non-hook code. 22 bare `except Exception:` reduced by 60%+, remaining instances have `exc_info=True` logging. Step matching path raises explicit errors for zero-match scenarios. No new `return None` or bare `except` added.
**Addresses:** STAB-02 (return None elimination), STAB-03 (exception cleanup)
**Avoids:** Pitfall 1 (silent pass), Pitfall 5 (broad exception mask), Pitfall 6 (return None propagation)
**Research flag:** Standard patterns — skip research-phase. Code quality patterns are well-documented.

### Phase 3: Core Architecture Split
**Rationale:** Highest-risk, highest-reward refactoring. The 1422-line `scenario_run.py` is the #1 maintainability blocker. Must be done AFTER code quality gates and BEFORE other refactorings (so the new module structure can serve as a template). Requires characterization tests capturing all state transitions first.
**Delivers:** `model/run.py` (Run), `model/scenario_run.py` (ScenarioRun + RunStage + StepRun), `model/feature_binding.py` (FeatureRuntimeBinding). Enums extracted. Zero behavior changes. Full test suite passing including xdist.
**Addresses:** REF-01 (scenario_run.py split)
**Avoids:** Pitfall 3 (state machine desync), Pitfall 2 (step matching regression if step logic moves)
**Research flag:** NEEDS RESEARCH — characterization tests for all RunStage transitions, implicit stash coupling mapping, enumeration of state machine edge cases. Use `/gsd-research-phase` for "model extraction characterization" before splitting.

### Phase 4: Plugin Consistency
**Rationale:** After the core model split proves safe, extend the class-based plugin pattern to the one outlier (code_generator) and consolidate the formatter directory structure. Reduces cognitive load for contributors.
**Delivers:** `CodeGeneratorPlugin` class following canonical pattern. `plugin/formatters/` directory with all 12 formatters. `run_access.py` functions moved to `model/`. `DEVELOPMENT.rst` documents canonical plugin pattern.
**Addresses:** REF-02 (code generator refactor), REF-03 (other large files), SIM-01 (unify patterns)
**Avoids:** Pitfall 9 (inconsistent plugin patterns)
**Research flag:** Standard patterns — skip research-phase. Plugin class pattern is well-documented internally.

### Phase 5: Documentation
**Rationale:** Independent of code changes. Migration guide is the highest-value user-facing deliverable (pytest-bdd → pytest-bdd-ng). Can run in parallel with Phase 3-4.
**Delivers:** Public API docstrings (DOC-01), updated DEVELOPMENT.rst with canonical patterns (DOC-02), migration guide for users (DOC-03).
**Addresses:** DOC-01, DOC-02, DOC-03
**Avoids:** Pitfall 8 (missing migration path damages user trust)
**Research flag:** Standard patterns — skip research-phase. Documentation is standard practice.

### Phase 6: Test Coverage Fortification
**Rationale:** After code stabilizes, add test coverage for the most dangerous gaps: parser edge cases, state transitions, step matching contracts. No behavior changes — only tests. Python 3.10 EOL is Oct 2026; plan to drop 3.10 support after stabilization.
**Delivers:** Unit tests for `scenario_run`, `steps`, `parsers`. Gherkin keyword edge case tests. Step priority contract tests. `# pragma: no cover` audit — 37 instances, fix genuinely uncovered production code. Run CI matrix: Python 3.10-3.14 × pytest 8.x-9.x.
**Addresses:** TEST-01 (unit coverage), TEST-03 (edge cases)
**Avoids:** Pitfall 7 (parser edge case regression — tests without behavior changes)
**Research flag:** NEEDS RESEARCH — Gherkin spec edge case catalog, Cucumber Messages compliance test patterns. Use `/gsd-research-phase` for "BDD parser edge case testing" before writing tests.

### Phase Ordering Rationale

- **Stabilization BEFORE refactoring** — Pitfall 6 is explicit: refactoring modules with active `return None` patterns entrenches the antipattern. Code quality gates (Phase 2) are a hard prerequisite for any structural changes (Phase 3+).
- **Dead plugin removal first** — Phase 1 removes confusion before users encounter it. Independent of all other phases.
- **Core architecture split before plugin refactoring** — The split `model/` structure sets the template for other refactorings. Doing it first (after gates) maximizes stabilization time.
- **Documentation runs in parallel** — No code dependencies. Can be done concurrently with Phase 3-4.
- **Tests last (after code shape stabilizes)** — Adding tests to modules that are being split creates merge conflicts. Test after the structure is settled.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (REF-01):** Characterization tests for RunStage state transitions, implicit stash coupling mapping, state machine edge cases. Needs codebase instrumentation research.
- **Phase 6 (TEST-03):** Gherkin spec edge case catalog (escaped pipes, table escaping, docstrings, Unicode, comments in tables). Needs Cucumber Messages compliance test pattern research.

Phases with standard patterns (skip research-phase):
- **Phase 1 (STAB-01, STAB-04):** Dead code removal, deprecation warnings — standard Python practices.
- **Phase 2 (STAB-02, STAB-03):** Return None elimination, exception cleanup — well-documented code quality patterns.
- **Phase 4 (REF-02, REF-03, SIM):** Plugin class pattern — internally documented, 16/17 plugins already follow it.
- **Phase 5 (DOC-01, DOC-02, DOC-03):** Standard documentation practices.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions verified via PyPI live (May 2026), Context7 docs for pytest and Cucumber protocol, direct codebase inspection of pyproject.toml. Exception: `decopatch` — LOW confidence (unverifiable PyPI page). |
| Features | HIGH | Feature matrix built from Context7 docs (behave, Cucumber.js, Reqnroll), PyPI metadata, codebase source inspection, upstream pytest-bdd issue tracker. Competitor analysis is comprehensive. |
| Architecture | HIGH | Direct codebase reading at commit `c59470a9`, pytest official docs (v9.x), pluggy documentation, codebase ARCHITECTURE.md. Plugin patterns verified across all 17 plugins. |
| Pitfalls | MEDIUM | Derived from issue trackers (observation, not post-mortem), codebase CONCERNS.md analysis, and ecosystem patterns. Some findings from WebSearch only for behave issues. Parser edge cases cataloged from upstream bugs — not exhaustive. |
| Overall | **HIGH** | Stack, features, and architecture have high source quality. Pitfalls are medium because they derive from issue observation rather than post-mortem analysis — root causes are inferred, not confirmed by original developers. |

### Gaps to Address

- **`decopatch` health:** PyPI page requires JS — could not verify maintenance status. Manual audit needed during Phase 4 (plugin consistency). If unmaintained, replace with `functools.wraps` + manual decorator factories.
- **`parse_type` Python 3.12-3.14 compatibility:** Classifier metadata only lists through 3.11, but v0.6.6 is from Aug 2025. Verify with test matrix during Phase 6 (test coverage).
- **Parser edge case coverage:** `ParserBuildValueError` at `parsers.py:678` is marked `# pragma: no cover` — no test exercises the case where ALL four parsers fail. Add during Phase 6.
- **`# pragma: no cover` audit:** 37 instances across codebase. Some may mask genuinely untested production code. Systematic audit during Phase 6.
- **Go parser v39 compatibility:** Bump from v28 to v39 has not been tested. Import path change (`go/v28` → `go/v39`) plus protocol alignment with gherkin-official v39. Test during stack upgrade in Phase 2-3 infrastructure changes.
- **npm detection edge cases:** `npm_resource.py` `get_npm_root()` can still raise `CalledProcessError` if npm is not on PATH. Only `check_npm` and `check_npm_package` are guarded. Fix during Phase 1 or 2.

## Sources

### Primary (HIGH confidence)
- `/cucumber/messages` (Context7) — Protocol version 32.3.1, message lifecycle, type definitions
- `/cucumber/gherkin` (Context7) — Go parser v39 import paths, Python parser API
- `/cucumber/cucumber-js` (Context7) — Competitor feature matrix (async, retry, parallel, snippets)
- `/reqnroll/reqnroll` (Context7) — Competitor feature matrix (DI container, LivingDoc, IDE integration)
- `/websites/pytest_en_stable` (Context7) — Plugin architecture, StashKey pattern, hook specifications
- `/python-attrs/attrs` (Context7) — Modern `@attrs.define` API, dataclass comparison
- PyPI (live) — Version checks: gherkin-official 39.1.0, cucumber-messages 32.3.1, cucumber-tag-expressions 9.1.0, pytest 9.0.3, pluggy 1.6.0, parse 1.22.0, parse_type 0.6.6, makefun 1.16.0, ruff 0.15.12
- `pyproject.toml` (project file) — Current dependency pins, entry points, tool configuration
- `AGENTS.md` (project constitution) — Go parser versions, attrs requirement, StashBound pattern, `return None` antipattern rule
- `.planning/codebase/ARCHITECTURE.md` (at commit `c59470a9`) — Codebase structure analysis
- `.planning/codebase/CONCERNS.md` — Technical debt inventory

### Secondary (MEDIUM confidence)
- pytest-bdd upstream issue tracker (GitHub) — Bug patterns: step matching regression (#542), silent pass (#403), parser edge cases (#741, #655, #333), fixture lifecycle (#689)
- behave/behave issue tracker (GitHub) — Ecosystem patterns: ResourceWarning (#1313), Python version breakage (#1270), formatter coupling (#1231)
- behave documentation (behave.readthedocs.io) — Competitor feature comparison, philosophy
- pluggy documentation (pluggy.readthedocs.io) — Hook specs, hookimpl markers, wrappers

### Tertiary (LOW confidence)
- `decopatch` PyPI page — JS-rendered, could not verify health. Needs manual audit.
- radish GitHub README — No Context7 coverage, v0.18.4 release only
- Some behave issue tracker observations — Inferred root causes, not confirmed post-mortems

---

*Research completed: 2026-05-12*
*Ready for roadmap: yes*
