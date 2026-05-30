# Feature Research

**Domain:** BDD testing library (pytest plugin)
**Researched:** 2026-05-12
**Confidence:** HIGH

## Executive Summary

The BDD testing ecosystem in Python is mature and stable, dominated by behave (standalone runner) and pytest-bdd (pytest plugin). The pytest-bdd-ng fork inherits a rich feature set from upstream pytest-bdd while adding Cucumber Messages protocol compliance, Go parser backend, Struct BDD, and live reporting. The plugin operates in a brownfield stabilization phase — the focus is on hardening existing features, not adding new ones.

Competitor analysis across behave, Cucumber.js, Reqnroll (SpecFlow), radish, and Cucumber-JVM reveals that pytest-bdd-ng already has parity with or exceeds most Python BDD tools. Key gaps compared to the broader ecosystem are: async step definitions, built-in retry mechanism, and better documentation/examples. The pytest fixture dependency injection model remains the library's strongest differentiator.

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or users migrate to behave.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Gherkin `.feature` file parsing | Foundational; every BDD tool does this | LOW (exists) | ✅ Both plain and Markdown (.feature.md) supported via `MarkdownGherkinParser` |
| Step definition decorators (`@given`/`@when`/`@then`) | Core BDD pattern; users expect decorator API | LOW (exists) | ✅ With `target_fixture`, converters, stacklevel, aliases |
| Step parameter matching | Steps need to accept dynamic values from feature files | LOW (exists) | ✅ 7 parsers: string, re, parse, cfparse, cucumber_expression, cucumber_expression_re, cucumber_expression_parameter_type |
| Scenario auto-discovery (`scenarios()`) | Users shouldn't manually bind every scenario | LOW (exists) | ✅ Batch-parallel feature collection with `aiofiles` |
| Scenario outlines with Examples | Parameterized testing is fundamental to BDD | LOW (exists) | ✅ Multiple example tables, tagged examples, parameter substitution in docstrings/datatables |
| Data tables (`datatable`) | Tabular test data is common in Gherkin scenarios | LOW (exists) | ✅ Passed as list-of-lists to step function |
| Docstrings (`docstring`) | Multi-line string arguments are a Gherkin standard | LOW (exists) | ✅ Indentation-stripped, passed as string |
| Background steps | Common setup across scenarios in a feature | LOW (exists) | ✅ Only Given steps allowed in Background |
| Tags for selective execution | CI/CD filtering of tests by category | LOW (exists) | ✅ Mapped to pytest markers; custom tag handling via `pytest_bdd_apply_tag` hook |
| Fixture dependency injection | pytest users expect seamless fixture integration | LOW (exists) | ✅ Core differentiator — steps receive pytest fixtures as function arguments |
| Scenario-level hooks | Reporting tools need lifecycle events | LOW (exists) | ✅ `pytest_bdd_before_scenario`, `pytest_bdd_after_scenario`, `pytest_bdd_before_step`, `pytest_bdd_before_step_call`, `pytest_bdd_after_step`, `pytest_bdd_step_error`, `pytest_bdd_step_func_lookup_error` |
| Cucumber JSON reporter | CI integration (Jenkins, GitLab, etc.) | LOW (exists) | ✅ Cucumber Messages-compliant JSON output |
| Pretty terminal output | Developers read test output in terminals | LOW (exists) | ✅ `--gherkin-terminal-reporter` with -v/-vv |
| Feature file path configuration | Teams have different directory layouts | LOW (exists) | ✅ `bdd_features_base_dir` in pytest.ini; per-scenario override |
| Step definition reuse across test files | Shared step libraries via conftest.py | LOW (exists) | ✅ Steps in parent conftest.py auto-discovered |
| Code generation from feature files | Onboarding new users | MEDIUM (exists, needs refactor) | ✅ `pytest-bdd generate` CLI + `--generate-missing` pytest flag. REF-02 pending: class-based refactor |
| Python 3.10-3.14 support | Modern Python ecosystem expectation | LOW (exists) | ✅ With PyPy support |
| pytest-xdist parallel execution | CI performance at scale | MEDIUM (exists) | ✅ With execnet + filelock for cross-worker coordination |

### Differentiators (Competitive Advantage)

Features that set pytest-bdd-ng apart from behave, radish, and other BDD tools. These exist or are planned.

| Feature | Value Proposition | Complexity | Status |
|---------|-------------------|------------|--------|
| **pytest fixture dependency injection** | Steps declare dependencies as function args — pytest resolves them. No global context object. No manual state management. Fixtures are evaluated once and cached. This is the reason to choose pytest-bdd over behave. | LOW (exists) | ✅ Core differentiator. Behave uses a shared `context` object; pytest-bdd uses pytest's fixture system which is cleaner, typesafer, and integrates with fixture-scoped setup/teardown. |
| **Go parser backend** | 10-50x faster Gherkin parsing via ctypes shared library. Only BDD tool in Python with native-compiled parser option. | LOW (exists) | ✅ `gherkin-official` Python fallback unchanged. Go 1.21+ required at build time only. |
| **Cucumber Messages protocol** | Full compliance with the official Cucumber interop protocol. Enables live reporting to any Cucumber-compatible dashboard. | LOW (exists) | ✅ Gherkin message reporter with xdist-aware transport. Only Python BDD tool with full Messages compliance. |
| **Struct BDD (YAML/JSON/TOML/HOCON)** | Write BDD scenarios in structured data formats instead of Gherkin. Appeals to teams that prefer machine-readable specs. | LOW (exists) | ✅ No other Python BDD tool offers this. |
| **7 step parsers** | More parsing options than any other Python BDD tool. Choose between simplicity (string), power (re), readability (parse), or Cucumber compatibility (cucumber_expression). | LOW (exists) | ✅ Behave has 3 (parse, cfparse, re). Radish has 2. |
| **Test group ordering** | CI pipelines can order test execution groups (e.g., smoke → integration → e2e) and apply xdist barriers between groups. | LOW (exists) | ✅ Unique to pytest-bdd-ng. |
| **Live reporting bridge** | Real-time Cucumber Messages streaming from pytest workers to a central formatter process. Enables live dashboards during test runs. | LOW (exists) | ✅ gherkin_message_reporter plugin with Node.js bridge. |
| **Markdown Gherkin (`.feature.md`)** | Feature files render beautifully on GitHub/GitLab. Combines documentation and executable specs in one file. | LOW (exists) | ✅ `MarkdownGherkinParser`. Requested in upstream #780. |
| **URL-based feature files** | Load feature files from HTTP URLs for distributed test scenarios. | LOW (exists) | ✅ `UrlScenarioLocator` with async fetching via aiohttp. |

### Should-Have Improvements (Stabilization Phase)

These are not new features but quality improvements to existing features that users need. These align with the stabilization milestone.

| Feature | Why Needed | Complexity | Phase Mapping |
|---------|-----------|------------|---------------|
| **Async step definitions** | Users running async code (HTTP clients, database queries) need `async def` steps without boilerplate. Requested since 2017 (#223). Cucumber.js, Reqnroll, and radish all support this. | MEDIUM | STAB milestone: requires hook changes in pickle_runner. Core to modern Python testing. |
| **Better error messages for step matching failures** | When steps don't match, users get cryptic errors. #608: parser fails silently when two When statements share a prefix. | MEDIUM | STAB-02 related: eliminate bare `except Exception:` in step matching path. |
| **Duplicate scenario detection** | Users accidentally create duplicate scenarios across feature files with no warning (#191). | LOW | Could be a validation check during collection. |
| **Built-in retry for flaky steps** | Cucumber.js has `--retry N --retry-tag-filter @flaky`. pytest has `pytest-rerunfailures` but it doesn't integrate with BDD context. | MEDIUM | Post-stabilization. Requires careful design to avoid masking real failures. |
| **Working examples in repo** | Users struggle with initial setup (#644). A copy-paste example directory lowers the adoption barrier significantly. | LOW | DOC-02/DOC-03: part of documentation improvements. |
| **Summary test report** | Users want a high-level overview of features/scenarios passed/failed (#359). | LOW | Could leverage existing Cucumber JSON formatter. |
| **Disable argument-as-fixture behavior** | When step arguments shadow pytest fixture names, users get confusing errors (#330). Need an opt-out mechanism. | MEDIUM | Requires careful design to preserve backward compatibility. |

### Future Differentiators (Post-Stabilization)

Features that could make pytest-bdd-ng the definitive Python BDD tool. Not for this milestone.

| Feature | Value Proposition | Complexity | Priority |
|---------|-------------------|------------|----------|
| **Step definition snippet generation** | When a step has no definition, generate a code snippet (like Cucumber.js). Dramatically improves onboarding. | MEDIUM | P2 - Requires extending `pytest_bdd_step_func_lookup_error` hook output |
| **Dry-run mode** | Validate all steps are defined without executing them. Cucumber.js `--dry-run`. CI guardrail. | LOW | P2 - Collection-time validation |
| **Tag expressions (Cucumber-style)** | `@smoke and not @wip` syntax instead of pytest marker expressions. Better Cucumber compatibility. | MEDIUM | P3 - Can be layered on existing tag→marker mapping |
| **Scenario-level parallelism** | Beyond xdist (file-level), allow individual scenarios within a feature to run in parallel. Like Cucumber.js `--parallel N` at scenario granularity. | HIGH | P3 - Requires significant architectural changes |
| **Attachments API** | Allow steps to attach screenshots, logs, or data to test reports. Cucumber.js `this.attach()`. | MEDIUM | P3 - Messages protocol already supports attachments |
| **Living documentation generator** | Generate static HTML docs from feature files showing which scenarios pass/fail. Like Reqnroll's living doc or Cucumber's reports. | MEDIUM | P3 |
| **Step auto-completion / IDE integration** | VS Code / PyCharm plugin for navigation between feature files and step definitions. Like Reqnroll's Visual Studio integration. | HIGH | P3 - Large scope, depends on LSP work |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems. Documented to prevent scope creep.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Built-in web UI / dashboard** | "I want to see test results in a browser" | Massive scope creep. Maintenance burden. Competes with dedicated tools (Allure, ReportPortal, Cucumber Reports). The live reporting bridge already enables external dashboards. | Use Cucumber Reports service or Allure via the existing Messages protocol bridge. |
| **Custom Gherkin dialect extensions** | "I want to add new keywords like 'Verify' or 'Check'" | Breaks interoperability with Cucumber ecosystem. Feature files can't be shared with non-pytest teams. Gherkin is a standard — extending it fragments the ecosystem. | Use tags (`@verify`) or comments. Use `And`/`But`/`*` for flexibility within standard Gherkin. |
| **Scenario-to-scenario dependency** | "I want Scenario B to depend on data from Scenario A" | Violates fundamental BDD principle: scenarios must be independent. Creates flaky, order-dependent test suites. Makes parallel execution impossible. | Use Background for shared setup. Use pytest fixtures that are recreated per scenario. Extract shared logic into helper functions called by both scenarios. |
| **Global mutable context object** | "I want to store data in a shared world object like Cucumber.js" | Undermines pytest's fixture isolation. Creates hidden dependencies between steps. Makes debugging harder because state mutations are implicit. The whole point of pytest-bdd's DI model is to avoid this. | Use pytest fixtures. Pass state through fixture return values. Use `target_fixture` in Given/When/Then steps to inject values into the fixture graph. |
| **Automatic retry of all failed scenarios** | "Just retry failures automatically" | Masks flaky tests. Flaky tests are bugs — retrying hides them. Leads to CI pipelines that "sometimes pass." | Use `@flaky` tag + explicit retry opt-in (future feature). Fix the root cause of flakiness. |
| **Imperative step definitions in Gherkin** | Users coming from Selenium/procedural testing write UI-click-level steps | Produces brittle, unreadable feature files that aren't BDD — they're just procedural test scripts in Gherkin syntax. Defeats the purpose of BDD as a collaboration tool. | Document declarative vs imperative patterns. The cucumber-best-practices skill has strong guidance here. |
| **Feature-level Examples (deprecated in upstream)** | Used to share example data across scenarios | Already removed from Gherkin spec. Pytest-bdd 5.x deprecated this. Violates scenario independence. | Copy example data to individual scenario Example tables. |

## Feature Dependencies

```text
Scenario auto-discovery (scenarios())
    └──requires──> Gherkin parser (plain + Markdown)
                       └──requires──> Go parser backend (optional, performance only)

Step definitions (@given/@when/@then)
    └──requires──> Step matching (parsers)
    └──enhances──> Fixture dependency injection

Scenario execution (pickle_runner)
    └──requires──> Step definitions
    └──requires──> Scenario hooks (before/after)
    └──enhances──> Cucumber Messages (live reporting)
                        └──requires──> pytest-xdist coordination

Code generation
    └──requires──> Gherkin parser
    └──independent──> (no runtime dependency on execution)

Cucumber JSON/JUnit reporters
    └──requires──> Scenario hooks (collect execution data)
    └──requires──> Scenario execution

Async step definitions (future)
    └──requires──> Step dispatch refactoring in pickle_runner
    └──requires──> Hook signature changes for async support

Retry mechanism (future)
    └──requires──> Scenario execution lifecycle
    └──conflicts──> Automatic retry of all scenarios (see anti-features)
```

### Dependency Notes

- **Code generation is independent of execution**: Can be refactored (REF-02) without affecting test execution. Low risk.
- **Async steps require pickle_runner changes**: The current step dispatch/call chain is synchronous. Adding async support requires careful hook signature evolution to avoid breaking existing plugins.
- **Retry requires design work**: Needs explicit opt-in (tags), careful state reset between retries, and integration with xdist. Not for stabilization milestone.
- **Allure plugin is dead weight**: It's in the tree but non-functional. STAB-01 must decide: remove or reimplement. If removed, Allure users use the Cucumber JSON output path instead.

## MVP Definition (Stabilization Context)

This is a brownfield project. "MVP" here means: what must work flawlessly after stabilization.

### Must Work (P1 — Stabilization)

- [x] Gherkin parsing (both plain and Markdown) — never regress
- [x] Step definition matching — deterministic, all 7 parsers working
- [x] Scenario execution — hooks fire in correct order, errors propagate correctly
- [ ] **STAB-02**: Eliminate 96 `return None` in non-hook code — silent failures mask bugs
- [ ] **STAB-03**: Replace 22 bare `except Exception:` — swallowed errors break determinism
- [ ] **REF-01**: Split `scenario_run.py` (1422 lines) — maintainability blocker
- [x] Cucumber Messages compliance — existing, must not regress
- [x] pytest-xdist support — existing, must not regress
- [ ] **DOC-03**: Migration guide for pytest-bdd → pytest-bdd-ng users

### Should Work (P2 — Quality)

- [ ] **STAB-01**: Decide fate of dead Allure plugin (remove or reimplement)
- [ ] **REF-02**: Code generator plugin class-based refactor
- [ ] **REF-03**: Reduce other 400+ line files
- [ ] **TEST-01**: Unit test coverage for scenario_run, steps, parsers
- [ ] **DOC-01**: Public API docstrings
- [ ] **DOC-02**: Update DEVELOPMENT.rst

### Nice to Have (P3 — Post-Stabilization)

- [ ] Async step definitions
- [ ] Better step matching error messages
- [ ] Duplicate scenario detection
- [ ] Working example directory in repo
- [ ] Retry mechanism (explicit opt-in via tags)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Deterministic step matching (STAB-02, STAB-03) | HIGH | MEDIUM | P1 |
| scenario_run.py split (REF-01) | MEDIUM | HIGH | P1 |
| Migration guide (DOC-03) | HIGH | LOW | P1 |
| Async step definitions | HIGH | MEDIUM | P3 |
| Better error messages | HIGH | MEDIUM | P3 |
| Duplicate scenario detection | MEDIUM | LOW | P3 |
| Retry mechanism | MEDIUM | HIGH | P3 |
| Working examples | MEDIUM | LOW | P3 |
| Allure plugin decision (STAB-01) | LOW | LOW | P2 |
| Code generator refactor (REF-02) | LOW | MEDIUM | P2 |

**Priority key:**
- P1: Must have for stabilization completion
- P2: Should have, do during stabilization
- P3: Post-stabilization roadmap

## Competitor Feature Analysis

| Capability | behave | pytest-bdd (upstream) | pytest-bdd-ng | radish | Cucumber.js | Reqnroll |
|------------|--------|----------------------|---------------|--------|-------------|----------|
| Gherkin parsing | ✅ | ✅ | ✅ (plain+MD+Go) | ✅ | ✅ | ✅ |
| Step decorators | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (attributes) |
| Step parsers | 3 (parse, cfparse, re) | 7 | 7 | 2 | 2 (expr+re) | 2 (expr+re) |
| Fixture/DI system | context object | pytest fixtures | pytest fixtures | context object | World object | DI container |
| Background | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Scenario Outlines | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Data tables | ✅ (context.table) | ✅ (datatable arg) | ✅ (datatable arg) | ✅ | ✅ | ✅ (DataTable) |
| Docstrings | ✅ (context.text) | ✅ (docstring arg) | ✅ (docstring arg) | ✅ | ✅ | ✅ |
| Tags | ✅ | ✅ (→ markers) | ✅ (→ markers) | ✅ | ✅ (expressions) | ✅ |
| Cucumber JSON | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cucumber Messages | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| Parallel execution | ❌ (external) | ❌ (via xdist) | ✅ (xdist + barriers) | ❌ | ✅ (--parallel) | ✅ (NUnit) |
| Retry mechanism | ❌ | ❌ | ❌ | ❌ | ✅ (--retry) | ✅ |
| Async steps | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| IDE integration | ❌ | ❌ | ❌ | ❌ | ✅ (VS Code) | ✅ (VS) |
| Living docs | ❌ | ❌ | ❌ | ❌ | ✅ (reports) | ✅ (LivingDoc) |
| Struct BDD | ❌ | ❌ | ✅ (YAML/JSON/TOML/HOCON) | ❌ | ❌ | ❌ |
| Markdown Gherkin | ❌ | ❌ (requested #780) | ✅ (.feature.md) | ❌ | ✅ | ❌ |
| Live reporting | ❌ | ❌ | ✅ (Messages bridge) | ❌ | ✅ | ✅ (VS) |
| Preconditions/Constants | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Step generation | ❌ | ✅ | ✅ (needs refactor) | ❌ | ✅ (snippets) | ✅ (VS) |

## Sources

- **pytest-bdd (upstream)**: PyPI page (v8.1.0, Dec 2024), GitHub issues (#223, #191, #214, #310, #330, #359, #430, #608, #644, #780), README.rst — HIGH confidence
- **pytest-bdd-ng**: Source code inspection (`src/pytest_bdd/`), plugin directory listing, grep for hooks and features — HIGH confidence
- **behave**: Official docs (behave.readthedocs.io), v1.4.0.dev0 docs, comparison page, Context7 API — HIGH confidence
- **Cucumber.js**: Official docs via Context7 (`/cucumber/cucumber-js`), v11.x API reference — HIGH confidence
- **Reqnroll**: Official docs via Context7 (`/reqnroll/reqnroll`), quickstart, hooks, IDE integration docs — HIGH confidence
- **radish**: GitHub README, v0.18.4 release (Feb 2026) — MEDIUM confidence (no Context7 coverage)
- **Cucumber best practices**: Internal skill documentation — HIGH confidence
- **pytest-bdd-ng AGENTS.md / PROJECT.md**: Project requirements and constraints — HIGH confidence

---

*Feature research for: pytest-bdd-ng (pytest BDD plugin)*
*Researched: 2026-05-12*
