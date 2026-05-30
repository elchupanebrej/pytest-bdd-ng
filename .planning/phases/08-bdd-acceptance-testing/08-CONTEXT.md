# Phase 08: BDD Acceptance Testing - Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Expand `features/` directory with `.feature.md` files covering previously undocumented behaviors and edge cases. Full audit of existing 47 feature files for consistency and quality. Split step definitions by topic area.

**Requirement:** TEST-02 — "Expand BDD feature tests in `features/` for undocumented behaviors and edge cases"

**Scope:** Comprehensive coverage gap audit across all source modules. Split into 3 sub-phases:
- **8a Core:** Go parser, tag expressions, heading validation, mimetype detection, struct_bdd expansion
- **8b Formatters:** JUnit reporter, progress indicators, snippets, summary, usage statistics
- **8c Plugins:** Code generator, scenario reporter, compatibility layer behaviors

**Exclusions:**
- Parsers (`parsers.py`) are FROZEN — tests only, no modifications
- New plugin development — not in scope
- Performance optimization — not a phase goal

</domain>

<decisions>
## Coverage Gap Strategy

- **D-01:** Comprehensive coverage — all identified gaps covered, not just high-risk areas
- **D-02:** Agent proposes gap list first, user approves before writing feature files
- **D-03:** Gap identification focuses on known risky areas (Go parser, StructBDD, new formatters) plus agent analysis of remaining modules

## Sub-Phase Structure

- **D-04:** Phase split into 3 sub-phases: 8a (core), 8b (formatters), 8c (plugins)
- **D-05:** 8a covers: `_gherkin_go/` (4 files), `tag_expression.py`, `heading_validation.py`, `mimetype.py`, `struct_bdd` plugin expansion
- **D-06:** 8b covers: `cucumber_junit`, `cucumber_progress`, `cucumber_progress_bar`, `cucumber_snippets`, `cucumber_summary`, `cucumber_usage`, `cucumber_usage_json`
- **D-07:** 8c covers: `code_generator`, `scenario_reporter`, `compatibility/` layer behaviors, `collector_batch.py` edge cases

## Step Definition Organization

- **D-08:** Split step definitions by topic area — one file per gap area
- **D-09:** New step definition files live in `tests/e2e/` with naming pattern `steps_{topic}.py`
- **D-10:** Existing `tests/e2e/conftest.py` (470 lines) preserved — new files are additive, not replacements

## Existing Feature Refactoring

- **D-11:** Full audit of all 47 existing `.feature.md` files
- **D-12:** Review for: clarity, consistency, duplicate scenarios, standardized patterns
- **D-13:** Refactoring includes cleanup while adding new features — not add-only

## Execution Boundary

- **D-14:** Add + refactor — new feature files plus fix any existing failures found during audit
- **D-15:** All BDD tests must pass via `python -m pytest tests/e2e/` with zero failures

## the agent's Discretion

- Number of scenarios per new feature file
- Specific step text choices for new scenarios
- Exact file naming convention for step definition modules (within `steps_{topic}.py` pattern)
- Order of sub-phase execution within the overall phase plan

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/ROADMAP.md` — Phase 8 goal: "Executable BDD feature tests cover previously undocumented behaviors"
- `.planning/REQUIREMENTS.md` — TEST-02: "Expand BDD feature tests in `features/` for undocumented behaviors and edge cases"
- `.planning/STATE.md` — Current workflow state, blockers (Go parser v39 compatibility untested)
- `.planning/codebase/TESTING.md` — Test organization, patterns, fixtures, assertion approaches
- `.planning/codebase/STRUCTURE.md` — Project structure for module path references
- `.planning/phases/06-integration-testing/06-CONTEXT.md` — Integration test patterns, lifecycle coverage
- `.planning/phases/07-documentation/07-CONTEXT.md` — Documentation conventions, public API surface

## Source Code — Core Modules

- `src/pytest_bdd/_gherkin_go/__init__.py` — Go parser entry point
- `src/pytest_bdd/_gherkin_go/_bridge.py` — Go/Python bridge
- `src/pytest_bdd/_gherkin_go/_build.py` — Go shared library build logic
- `src/pytest_bdd/_gherkin_go/_types.py` — Go parser type definitions
- `src/pytest_bdd/tag_expression.py` — Tag expression parsing and evaluation
- `src/pytest_bdd/model/heading_validation.py` — Feature heading validation models
- `src/pytest_bdd/mimetype.py` — Mimetype and suffix enums
- `src/pytest_bdd/feature_locator.py` — Feature path/URL resolution
- `src/pytest_bdd/scenario_locator.py` — File and URL scenario locators
- `src/pytest_bdd/collector_batch.py` — Batch parsing with cache

## Source Code — Plugins

- `src/pytest_bdd/plugin/cucumber_junit/` — JUnit XML reporter
- `src/pytest_bdd/plugin/cucumber_progress/` — Progress formatter
- `src/pytest_bdd/plugin/cucumber_progress_bar/` — Progress bar formatter
- `src/pytest_bdd/plugin/cucumber_snippets/` — Step snippet generation
- `src/pytest_bdd/plugin/cucumber_summary/` — Summary formatter
- `src/pytest_bdd/plugin/cucumber_usage/` — Usage statistics
- `src/pytest_bdd/plugin/cucumber_usage_json/` — Usage JSON reporter
- `src/pytest_bdd/plugin/code_generator/` — Code generation from features
- `src/pytest_bdd/plugin/scenario_reporter/` — Scenario reporter
- `src/pytest_bdd/plugin/struct_bdd/` — StructBDD (YAML/JSON/HOCON/TOML) support

## Source Code — Compatibility

- `src/pytest_bdd/compatibility/` — 12 modules for Python version compatibility

## Existing Test References

- `tests/e2e/conftest.py` — 470 lines of BDD step definitions
- `tests/e2e/test_e2e.py` — E2E entry point: `scenarios(".", ...)`
- `tests/e2e/test_cucumber_formatters.py` — Formatter output tests
- `tests/e2e/test_xdist_message_aggregation.py` — xdist message tests
- `tests/unit/test_gherkin_go_parse.py` — Go parser unit tests
- `tests/unit/test_gherkin_go_fallback.py` — Go fallback tests
- `tests/unit/test_gherkin_go_bridge.py` — Go bridge tests
- `tests/feature/test_gherkin_go_collection.py` — Go collection integration tests
- `tests/struct_bdd/` — StructBDD tests

## Existing Feature Files (47 total)

- `features/01 Tutorial/` — 1 file
- `features/02 Feature/` — 8 files + 8 Load sub-files
- `features/03 Scenario/` — 8 files + 3 Outline sub-files
- `features/04 Step/` — 4 files
- `features/05 Step definition/` — 5 files + 5 Parameter sub-files
- `features/06 StructBDD/` — 1 file
- `features/07 Report/` — 8 files

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `tests/e2e/conftest.py` — Rich step definition library: file writing, pytest execution, output assertions, NDJSON parsing, Docker/xdist support
- `tests/support/pytest_results.py` — Pytest result output helpers
- `tests/support/cucumber_formatters.py` — Fake node installation, formatter output validation
- `tests/support/docker.py` — Docker daemon requirement checks
- `tests/messages/message_stream_assertions.py` — NDJSON message parsing and assertion helpers

### Established Patterns

- `.feature.md` format — Markdown Gherkin feature files
- E2E tests use `scenarios(".", filter_=...)` to load from `features/` directory
- Step definitions use `@given`, `@when`, `@then`, `@step` decorators with regex and `parsers.parse`
- Test output assertions: `result.assert_outcomes()`, `fnmatch_lines()`, returncode checks
- NDJSON report validation via `cucumber_messages` models
- testdir pattern for integration tests in `tests/feature/`

### Integration Points

- New feature files → `features/NN Topic/` directory structure
- New step definitions → `tests/e2e/steps_{topic}.py`
- E2E entry point → `tests/e2e/test_e2e.py` auto-discovers via `scenarios(".")`
- Generated docs → `docs/features/` auto-generated from `.feature.md` files
- Go parser → requires Go 1.21+ at build time, ctypes at runtime

</code_context>

<specifics>
## Specific Ideas

- Go parser feature files should cover: collection with Go available, fallback to Python when Go unavailable, bridge error handling
- Tag expression features should cover: complex boolean expressions (and/or/not), pytest mark matching across versions
- Heading validation features should cover: empty feature/scenario titles, policy enforcement, script validation
- Mimetype features should cover: file extension detection, hook overrides, StructBDD mimetype routing
- StructBDD expansion should cover: HOCON, JSON, TOML parsing edge cases, deserialization errors
- JUnit reporter features should cover: XML output format, test suite nesting, error/failure elements
- Progress formatter features should cover: output during test run, quiet mode, verbose mode
- Snippet generation features should cover: undefined step suggestions, template format
- Summary formatter features should cover: run summary statistics, duration reporting
- Usage statistics features should cover: step definition usage counts, unused step detection
- Code generator features should cover: step definition scaffolding from feature files, template customization
- Scenario reporter features should cover: scenario-level output, attachment handling
- Compatibility layer features should cover: Python 3.10-3.14 matrix behaviors, pytest version differences

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-BDD Acceptance Testing*
*Context gathered: 2026-05-16*
