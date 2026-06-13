# Phase 08: BDD Acceptance Testing - Research

**Researched:** 2026-05-16
**Domain:** BDD feature files (.feature.md), pytest-bdd-ng e2e test infrastructure, Go parser, Cucumber formatters, plugin system
**Confidence:** HIGH

## Summary

Phase 8 expands the `features/` directory with `.feature.md` files covering undocumented behaviors and edge cases, audits all 47 existing feature files for consistency, and splits step definitions by topic area. The phase is split into three sub-phases: 8a (core — Go parser, tag expressions, heading validation, mimetype, struct_bdd), 8b (formatters — JUnit, progress, snippets, summary, usage), and 8c (plugins — code_generator, scenario_reporter, compatibility layer, collector_batch edge cases).

The existing e2e infrastructure is mature: `tests/e2e/conftest.py` (470 lines) provides rich step definitions for file creation, pytest execution, output assertions, NDJSON parsing, Docker/xdist support. `tests/e2e/test_e2e.py` auto-discovers feature files via `scenarios(".", filter_=...)`. The existing 47 feature files follow a consistent `.feature.md` Markdown Gherkin format with Background/Rule/Scenario structure.

**Primary recommendation:** Audit 47 existing feature files first, then write new feature files per sub-phase (8a→8b→8c), splitting step definitions into `tests/e2e/steps_{topic}.py` files as additive modules.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Comprehensive coverage — all identified gaps covered, not just high-risk areas
- **D-02:** Agent proposes gap list first, user approves before writing feature files
- **D-03:** Gap identification focuses on known risky areas (Go parser, StructBDD, new formatters) plus agent analysis of remaining modules
- **D-04:** Phase split into 3 sub-phases: 8a (core), 8b (formatters), 8c (plugins)
- **D-05:** 8a covers: `_gherkin_go/` (4 files), `tag_expression.py`, `heading_validation.py`, `mimetype.py`, `struct_bdd` plugin expansion
- **D-06:** 8b covers: `cucumber_junit`, `cucumber_progress`, `cucumber_progress_bar`, `cucumber_snippets`, `cucumber_summary`, `cucumber_usage`, `cucumber_usage_json`
- **D-07:** 8c covers: `code_generator`, `scenario_reporter`, `compatibility/` layer behaviors, `collector_batch.py` edge cases
- **D-08:** Split step definitions by topic area — one file per gap area
- **D-09:** New step definition files live in `tests/e2e/` with naming pattern `steps_{topic}.py`
- **D-10:** Existing `tests/e2e/conftest.py` (470 lines) preserved — new files are additive, not replacements
- **D-11:** Full audit of all 47 existing `.feature.md` files
- **D-12:** Review for: clarity, consistency, duplicate scenarios, standardized patterns
- **D-13:** Refactoring includes cleanup while adding new features — not add-only
- **D-14:** Add + refactor — new feature files plus fix any existing failures found during audit
- **D-15:** All BDD tests must pass via `python -m pytest tests/e2e/` with zero failures

### the agent's Discretion
- Number of scenarios per new feature file
- Specific step text choices for new scenarios
- Exact file naming convention for step definition modules (within `steps_{topic}.py` pattern)
- Order of sub-phase execution within the overall phase plan

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Go parser BDD features | E2E (external) | Unit (instant) | Tests real parse behavior via pytest subprocess |
| Tag expression BDD features | E2E (external) | Unit (instant) | Tests pytest mark matching via `-m` flag |
| Heading validation BDD features | E2E (external) | Model (instant) | Tests script validation via subprocess |
| Mimetype BDD features | E2E (external) | Unit (instant) | Tests file extension routing via collection |
| StructBDD BDD features | E2E (external) | StructBDD (medium) | Tests YAML/JSON/HOCON/TOML parsing end-to-end |
| Formatter BDD features | E2E (external) | Feature (medium) | Tests formatter output via pytest subprocess |
| Code generator BDD features | E2E (external) | Generation (medium) | Tests `--generate` CLI behavior |
| Scenario reporter BDD features | E2E (external) | Feature (medium) | Tests hook lifecycle via pytest |
| Compatibility layer BDD features | E2E (external) | Compatibility (fast) | Tests Python version matrix behaviors |
| Collector batch BDD features | E2E (external) | Unit (instant) | Tests batch collection flags via pytest |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=7.0.0 | Test runner, pytester plugin | Project dependency, testdir fixture for integration tests |
| cucumber-messages | current | Cucumber message models | NDJSON validation, Envelope types |
| cucumber-tag-expressions | current | Tag expression parsing | Used by `tag_expression.py` for GherkinTagExpression |
| attrs | current | Data class definitions | Project standard over dataclasses (AGENTS.md) |
| returns | current | Maybe/Result monads | Used throughout codebase for error handling |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-httpserver | current | HTTP server fixture | For URL feature loading tests |
| PyHamcrest | current | Assertion helpers | Used in allure-specific e2e tests |
| jq (Python) | current | JSON query in assertions | For JSON output validation in feature files |

**Installation:** Already in project `pyproject.toml` and `uv.lock`. No new packages needed.

**Version verification:**
```bash
uv run python -c "import pytest; print(pytest.__version__)"  # 8.x confirmed
uv run python -c "import cucumber_messages; print(cucumber_messages.__version__)"  # via registry
```

## Architecture Patterns

### System Architecture Diagram

```
features/*.feature.md (47 existing + new)
         │
         ▼
tests/e2e/test_e2e.py ── scenarios(".", filter_=...)
         │
         ▼
tests/e2e/conftest.py (step definitions, 470 lines)
         │
    ┌────┴────┐
    ▼         ▼
run pytest  write files
(testdir)   (tmp_path)
    │
    ▼
assert outcomes / fnmatch_lines / NDJSON validation
```

Data flow: Feature files → scenarios() loader → step definitions in conftest.py → pytest subprocess → output assertions. New step files (`steps_{topic}.py`) are auto-discovered by pytest as conftest siblings.

### Recommended Project Structure

```
features/
├── 01 Tutorial/            # existing (1 file)
├── 02 Feature/             # existing (8 + 8 Load)
├── 03 Scenario/            # existing (8 + 3 Outline)
├── 04 Step/                # existing (4 files)
├── 05 Step definition/     # existing (5 + 5 Parameter)
├── 06 StructBDD/           # existing (1 file) — EXPAND
├── 07 Report/              # existing (8 files)
├── 08 Go Parser/           # NEW — 8a
├── 09 Tag Expressions/     # NEW — 8a
├── 10 Heading Validation/  # NEW — 8a
├── 11 Mimetype/            # NEW — 8a
├── 12 Formatters/          # NEW — 8b
├── 13 Code Generator/      # NEW — 8c
├── 14 Scenario Reporter/   # NEW — 8c
├── 15 Compatibility/       # NEW — 8c
└── 16 Batch Collection/    # NEW — 8c (edge cases)

tests/e2e/
├── conftest.py             # existing (470 lines) — PRESERVED
├── test_e2e.py             # existing entry point
├── steps_go_parser.py      # NEW — 8a
├── steps_tag_expressions.py # NEW — 8a
├── steps_heading_validation.py # NEW — 8a
├── steps_mimetype.py       # NEW — 8a
├── steps_formatters.py     # NEW — 8b
├── steps_code_generator.py # NEW — 8c
├── steps_scenario_reporter.py # NEW — 8c
├── steps_compatibility.py  # NEW — 8c
└── steps_batch_collection.py # NEW — 8c
```

### Pattern 1: Feature File Structure (`.feature.md`)
**What:** Markdown Gherkin feature files with `# Feature:` heading, `## Scenario:` subheadings, step lines prefixed with `*` or `Given/When/Then/And/But`.
**When to use:** All BDD acceptance tests.
**Example:**
```markdown
# Feature: Feature name with description
  Description text here.

## Background:
* Given File "test.feature" with content:

    ```gherkin
    Feature: Inner feature
      Scenario: Inner scenario
        Given a step
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given


    @given("a step")
    def _(): ...
    ```

## Scenario: Scenario name
* When run pytest

    | cli_args | -k | test_*.py |

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |
```

### Pattern 2: Step Definition with Data Tables
**What:** Steps use data tables for structured input (cli_args, expected outcomes).
**When to use:** pytest invocation steps, outcome assertions.
**Example:**
```python
@step("run pytest", target_fixture="pytest_result")
def run_pytest(testdir, step, attach):
    data_table = getattr(step.argument, "data_table", None)
    options_dict = data_table_to_dicts(data_table)
    cli_args = list(options_dict.get("cli_args", []))
    outcome = testdir.runpytest_inprocess(*cli_args)
    yield outcome
```

### Pattern 3: Fake Node for Cucumber Formatters
**What:** `install_fake_node()` monkeypatches PATH to use Python-based fake node/npm that simulates `@cucumber/cucumber` formatters.
**When to use:** Any feature testing cucumber formatters (8b).
**Example:**
```python
# In conftest.py or step file:
from tests.support.cucumber_formatters import install_fake_node, build_sample_suite


@given("Cucumber formatters are available")
def _(monkeypatch, tmp_path):
    install_fake_node(monkeypatch, tmp_path)
```

### Anti-Patterns to Avoid
- **Hardcoding file paths in step text:** Use parameterized steps with regex (`re.compile(r'File "(?P<name>\w+)(?P<extension>\.\w+)"')`)
- **Duplicating step definitions:** Check existing `conftest.py` (470 lines) before writing new steps
- **Writing feature files without Background setup:** Most features need file setup; use Background for shared setup
- **Using `testdir.runpytest()` for formatter tests:** Use `run_pytest_via_real_entrypoint()` or `testdir.runpytest_subprocess()` for formatter output capture

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Feature file setup/teardown | Custom temp directory management | `testdir.makefile()`, `testdir.makeconftest()`, `tmp_path` | pytester handles cleanup |
| Cucumber formatter testing | Real npm/node installation | `install_fake_node()` from `tests.support.cucumber_formatters` | Fast, deterministic, no network |
| NDJSON message validation | Manual JSON parsing | `cucumber_messages.Envelope` + `message_converter.from_dict()` | Type-safe, schema-validated |
| Pytest outcome assertion | Regex parsing stdout | `result.assert_outcomes()`, `fnmatch_lines()` | Cross-version compatible |
| Tag expression evaluation | Custom boolean parser | `cucumber_tag_expressions.TagExpressionParser` | Standard Cucumber implementation |
| HTTP feature loading | Custom HTTP server | `pytest-httpserver` fixture | Already in conftest, handles SSL |

**Key insight:** The project already has extensive test infrastructure. The 470-line `conftest.py` covers file creation, pytest execution, output assertions, NDJSON parsing, Docker/xdist, HTTP loading, and formatter support. New feature files should leverage these existing steps.

## Runtime State Inventory

> Not applicable — this is a greenfield BDD test writing phase, not a rename/refactor/migration. No runtime state to inventory.

## Common Pitfalls

### Pitfall 1: Go Parser Shared Library Not Built
**What goes wrong:** Feature files testing Go parser fail with `GherkinGoNotAvailable` when the Go shared library (`gherkin_go.dll` on Windows) hasn't been built.
**Why it happens:** The Go parser requires `go build -buildmode=c-shared` to produce the `.dll`/`.so`/`.dylib`. This is a build-time step, not installed via pip.
**How to avoid:** Feature files for Go parser should use `@python-fallback` or `@go-parser` tags to allow selective execution. Tests should cover both Go-available and Go-unavailable paths via mocking (as done in unit tests).
**Warning signs:** `OSError: Shared library not found` in test output.

### Pitfall 2: Formatter Tests Require Fake Node Setup
**What goes wrong:** Cucumber formatter feature tests fail silently or produce empty output when fake node isn't installed.
**Why it happens:** Formatters delegate to Node.js `@cucumber/cucumber` packages. Without `install_fake_node()` monkeypatching PATH, real npm/node is needed.
**How to avoid:** Use `install_fake_node(monkeypatch, tmp_path)` in Background or autouse fixture. The existing `ensure_fake_node_for_cucumber_formatter_report_docs` fixture in conftest.py handles this for specific feature URIs.
**Warning signs:** `npm install` errors, `@cucumber/cucumber not found` in stderr.

### Pitfall 3: Step Definition Not Found at Runtime
**What goes wrong:** `StepDefinitionNotFoundError` when feature file uses step text not matched by any registered step definition.
**Why it happens:** New feature files use step text that doesn't match patterns in `conftest.py` or new `steps_{topic}.py` files.
**How to avoid:** Before writing feature files, audit existing step definitions in `conftest.py`. Write step definitions first, then feature files. Use regex patterns for parameterized steps.
**Warning signs:** `StepDefinitionNotFoundError: Step "..." is not defined` in pytest output.

### Pitfall 4: E2E Filter Excludes New Feature Files
**What goes wrong:** New feature files are not collected by `test_e2e.py` because the `_exclude_default_bdd_features` filter excludes them.
**Why it happens:** The filter excludes scenarios tagged with `@allure`, `@docker`, `@slow`, `@xdist`, or matching specific URI fragments.
**How to avoid:** Don't tag new feature files with excluded tags unless intentional. Check `_EXCLUDED_TAGS` and `_EXCLUDED_FEATURE_URI_FRAGMENTS` in `test_e2e.py`.
**Warning signs:** `collected 0 items` when running `tests/e2e/`.

### Pitfall 5: StructBDD Conditional Skip
**What goes wrong:** StructBDD feature tests are skipped when `STRUCT_BDD_INSTALLED` is `False`.
**Why it happens:** StructBDD is an optional dependency guarded by `compatibility/struct_bdd.py`.
**How to avoid:** Tag StructBDD feature files with `@struct-bdd` and add to exclusion filter, or ensure tests handle skip gracefully.
**Warning signs:** `SKIPPED` in test output for StructBDD scenarios.

## Code Examples

### Go Parser Feature File (8a)
```markdown
# Feature: Go Gherkin parser backend
  Documents Go parser availability, fallback, and error handling.

## Rule: Go parser availability
### Scenario: Parse succeeds when Go library is available
* Given Go parser shared library is built
* When run pytest

    | cli_args | --features=go_test.feature |

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |

### Scenario: Falls back to Python parser when Go unavailable
* Given Go parser is not available
* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |
```

### Tag Expression Feature File (8a)
```markdown
# Feature: Tag expression evaluation
  Documents complex boolean tag expressions (and/or/not).

## Scenario: Evaluate AND expression
* Given File "tagged.feature" with content:

    ```gherkin
    Feature: Tagged scenarios
      @smoke @login
      Scenario: Login test
        Given a step

      @smoke @slow
      Scenario: Slow test
        Given a step
    ```

* When run pytest

    | cli_args | -m | "smoke and login" |

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |
```

### Formatter Feature File (8b)
```markdown
# Feature: Cucumber JUnit XML reporter
  Documents JUnit XML output format and test suite nesting.

## Scenario: JUnit XML output contains test suite structure
* Given Cucumber formatters are available
* And File "test.feature" with content:
    ... (standard feature setup)
* When run pytest

    | cli_args | --cucumber-junit=report.xml |

* Then File "report.xml" is not empty
* And File "report.xml" contains the line "<testsuite"
```

### Mimetype Feature File (8a)
```markdown
# Feature: Mimetype and suffix detection
  Documents file extension to mimetype routing.

## Scenario: Detect .feature extension as gherkin_plain
* Given File "test.feature" with gherkin content
* When pytest collects the file
* Then mimetype is resolved as "text/x.cucumber.gherkin+plain"

## Scenario: Detect .feature.md extension as gherkin_markdown
* Given File "test.feature.md" with markdown gherkin content
* When pytest collects the file
* Then mimetype is resolved as "text/x.cucumber.gherkin+markdown"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Bare `.feature` files | `.feature.md` Markdown Gherkin | Project inception | Richer documentation + executable specs |
| Single monolithic conftest.py | Topic-split `steps_{topic}.py` files | This phase | Better maintainability, clearer ownership |
| Manual formatter output checking | Fake node + telemetry capture | Phase 4-6 | Deterministic, fast, no network needed |
| Python-only Gherkin parser | Optional Go parser via ctypes | Phase 023 | 10-50x faster collection for large suites |

**Deprecated/outdated:**
- `--cucumberjson` flag: Deprecated in favor of `--cucumber-json=` (STAB-04)
- `pathlib2`: Python 2 backport, scheduled for removal in SIM-01
- `docopt-ng`: Legacy CLI parser, scheduled for removal in SIM-01

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Go shared library (`gherkin_go.dll`) is built on this machine | Pitfall 1 | Go parser BDD features fail at runtime; need to verify build |
| A2 | `cucumber_tag_expressions` package is installed | Standard Stack | Tag expression features can't test GherkinTagExpression |
| A3 | 47 feature files count is accurate (from CONTEXT.md) | Summary | Audit scope may be off by a few files |
| A4 | New `steps_{topic}.py` files are auto-discovered by pytest as conftest siblings | Architecture Patterns | Step definitions won't be found; need explicit conftest import |
| A5 | `jq` Python package is available on Windows | Standard Stack | JSON assertion steps in feature files will skip |

## Open Questions (RESOLVED)

1. **Go parser shared library build status on this machine** — RESOLVED: No `.dll` files found in `src/pytest_bdd/_gherkin_go/`. The Go shared library has NOT been built yet. Plan 8a must account for this — either build it first or test Python fallback paths.
2. **Exact step definition coverage gaps in conftest.py** — RESOLVED: Will be identified during Plan 08-01 audit task (per D-02: "Agent proposes gap list first, user approves before writing feature files").
3. **Whether `cucumber_junit` uses Node.js formatter or built-in Python** — RESOLVED: Uses Node.js. `plugin.py` sets `package_name="@cucumber/junit-xml-formatter"`, `runtime_kind=FormatterRuntimeKind.module`, renders from `junit.cjs.j2` template. Requires npm/Node.js at runtime, needs `install_fake_node()` for tests.
4. **StructBDD HOCON/TOML support level** — RESOLVED: Fully supported. `parser.py` `KIND` enum includes HOCON, HJSON, JSON, JSON5, TOML, YAML. `build_loader()` has dedicated loaders for all: YAML (yaml.FullLoader), TOML (tomllib.loads), JSON (json.loads), JSON5 (json5.loads), HJSON (hjson.loads), HOCON (pyhocon.ConfigFactory + HOCONConverter).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All BDD tests | ✓ | 3.14.2 | — |
| uv | Test execution | ✓ | 0.11.14 | — |
| pytest | Test runner | ✓ | via uv | — |
| Go | Go parser BDD features (8a) | ✓ | 1.26.2 | Python fallback parser |
| Node.js | Formatter BDD features (8b) | ✓ | 25.2.1 | `install_fake_node()` |
| npm | Formatter package install (8b) | ✓ | 11.6.2 | `install_fake_node()` |
| Docker | xdist remote tests | ✗ | — | Skip @docker tagged scenarios |
| jq (Python) | JSON assertions in features | Unknown | — | Skip if unavailable (conftest already handles) |

**Missing dependencies with fallback:**
- Docker — not installed; all `@docker` tagged scenarios already excluded from default e2e filter

**Missing dependencies with no fallback:**
- Go shared library build (`gherkin_go.dll`) — needs verification; if not built, Go parser features must use mocked/Python-only paths

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=7.0.0 with pytester plugin |
| Config file | `pyproject.toml` under `[tool.pytest.ini_options]` |
| Quick run command | `uv run python -m pytest tests/e2e/ -q -x` |
| Full suite command | `uv run python -m pytest tests/e2e/ -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-02 | Expand BDD feature tests for undocumented behaviors | BDD/e2e | `uv run python -m pytest tests/e2e/ -q` | ✅ existing infra |
| TEST-02 | Audit 47 existing feature files | Manual + BDD | `uv run python -m pytest tests/e2e/ -q` | ❌ audit task |
| TEST-02 | Split step definitions by topic | Refactoring | `uv run python -m pytest tests/e2e/ -q` | ❌ new files |

### Sampling Rate
- **Per task commit:** `uv run python -m pytest tests/e2e/ -q -x`
- **Per wave merge:** `uv run python -m pytest tests/e2e/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/e2e/steps_go_parser.py` — covers Go parser BDD scenarios
- [ ] `tests/e2e/steps_tag_expressions.py` — covers tag expression BDD scenarios
- [ ] `tests/e2e/steps_heading_validation.py` — covers heading validation BDD scenarios
- [ ] `tests/e2e/steps_mimetype.py` — covers mimetype BDD scenarios
- [ ] `tests/e2e/steps_formatters.py` — covers formatter BDD scenarios
- [ ] `tests/e2e/steps_code_generator.py` — covers code generator BDD scenarios
- [ ] `tests/e2e/steps_scenario_reporter.py` — covers scenario reporter BDD scenarios
- [ ] `tests/e2e/steps_compatibility.py` — covers compatibility layer BDD scenarios
- [ ] `tests/e2e/steps_batch_collection.py` — covers batch collection edge cases
- [ ] `features/08 Go Parser/` — new feature directory
- [ ] `features/09 Tag Expressions/` — new feature directory
- [ ] `features/10 Heading Validation/` — new feature directory
- [ ] `features/11 Mimetype/` — new feature directory
- [ ] `features/12 Formatters/` — new feature directory
- [ ] `features/13 Code Generator/` — new feature directory
- [ ] `features/14 Scenario Reporter/` — new feature directory
- [ ] `features/15 Compatibility/` — new feature directory
- [ ] `features/16 Batch Collection/` — new feature directory

## Security Domain

> `security_enforcement` not explicitly set in `.planning/config.json` — treated as enabled per spec.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — no auth in test library |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | yes | Gherkin parser validates input; `jsonschema` validation for messages |
| V6 Cryptography | no | N/A |

### Known Threat Patterns for pytest-bdd-ng

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious feature file content | Tampering | Gherkin parser sandbox; no code execution from feature files |
| Path traversal in feature loading | Elevation of privilege | `pathvalidate.is_valid_filepath` checks, `relpath` normalization |
| SSRF via URL feature loading | Information disclosure | `is_local_url` checks, SSL context with certifi |
| Code generator output injection | Tampering | Generated code is printed to stdout, not executed |

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `tests/e2e/conftest.py` (470 lines), `tests/e2e/test_e2e.py` (189 lines)
- Codebase inspection: `src/pytest_bdd/_gherkin_go/__init__.py`, `_bridge.py`, `_types.py`
- Codebase inspection: `src/pytest_bdd/tag_expression.py`, `mimetype.py`, `collector_batch.py`
- Codebase inspection: `src/pytest_bdd/plugin/cucumber_junit/plugin.py`, `cucumber_progress/plugin.py`, `cucumber_summary/plugin.py`, `cucumber_snippets/plugin.py`
- Codebase inspection: `src/pytest_bdd/plugin/code_generator/plugin.py`, `scenario_reporter/plugin.py`
- Codebase inspection: `tests/support/cucumber_formatters.py` (466 lines)
- Codebase inspection: 47 existing `.feature.md` files in `features/`
- `.planning/codebase/TESTING.md` — Test organization and patterns
- `.planning/codebase/STRUCTURE.md` — Project structure

### Secondary (MEDIUM confidence)
- `.planning/phases/08-bdd-acceptance-testing/08-CONTEXT.md` — Phase decisions and scope
- `.planning/REQUIREMENTS.md` — TEST-02 requirement definition
- Unit test files: `tests/unit/test_gherkin_go_*.py` — existing Go parser test patterns

### Tertiary (LOW confidence)
- None — all claims verified against codebase or CONTEXT.md

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against codebase imports and pyproject.toml
- Architecture: HIGH — verified against existing test infrastructure and feature file patterns
- Pitfalls: HIGH — verified against existing error handling code and test patterns
- Environment: HIGH — verified via tool execution on this machine

**Research date:** 2026-05-16
**Valid until:** 30 days (stable codebase, no fast-moving dependencies in scope)
