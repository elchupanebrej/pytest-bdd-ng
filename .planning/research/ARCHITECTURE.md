# Architecture Research

**Domain:** pytest BDD Plugin Library
**Researched:** 2026-05-12
**Confidence:** HIGH

## Standard Architecture

### System Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                          PUBLIC API LAYER                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ scenario │  │  given   │  │  when    │  │  then    │  │  step    │   │
│  │  ( )     │  │  ( )     │  │  ( )     │  │  ( )     │  │  ( )     │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │              │        │
│  ┌────┴──────────────┴──────────────┴──────────────┴──────────────┴───┐  │
│  │                      hooks (before/after/around)                     │  │
│  └────────────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────┤
│                          PLUGIN LAYER (17 plugins)                        │
│  ┌───────────────────┐ ┌─────────────────────┐ ┌──────────────────────┐  │
│  │ Scenario Collector │ │   Pickle Runner      │ │ Formatter Subsystem  │  │
│  │  (test discovery)  │ │  (step execution)    │ │  (cucumber_json,     │  │
│  │                    │ │                      │ │   cucumber_pretty,   │  │
│  │ ┌───┐ ┌───┐ ┌───┐ │ │ ┌───┐ ┌───┐ ┌─────┐ │ │   cucumber_junit,    │  │
│  │ │Col│ │Btc│ │Loc│ │ │ │Run│ │Tnx│ │Match│ │ │   etc - 12 plugins)  │  │
│  │ └───┘ └───┘ └───┘ │ │ └───┘ └───┘ └─────┘ │ │                      │  │
│  └───────┬───────────┘ └──────────┬──────────┘ └──────────┬───────────┘  │
│          │                        │                        │              │
│  ┌───────┴────────────────────────┴────────────────────────┴───────────┐ │
│  │                     Custom BDD Hook Interface                         │ │
│  │  pytest_bdd_is_collectible  pytest_bdd_run_scenario                  │ │
│  │  pytest_bdd_before_step     pytest_bdd_after_scenario                │ │
│  │  pytest_bdd_match_step      pytest_bdd_step_func_lookup_error        │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────────┤
│                          CORE LAYER (Models + Services)                   │
│  ┌─────────────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │
│  │    Run / ScenarioRun  │  │  StepDefinition   │  │  Parser Subsystem    │ │
│  │    (runtime state)    │  │  Manager          │  │  (Gherkin, Markdown, │ │
│  │    FeatureRuntime     │  │  (registry+match)  │  │   Go ctypes backend) │ │
│  │    Binding            │  │                    │  │                      │ │
│  └──────────┬───────────┘  └────────┬───────────┘  └──────────┬───────────┘ │
├─────────────┴───────────────────────┴───────────────────────┴──────────────┤
│                          PYTEST FRAMEWORK                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ config.stash  │  │   pluggy     │  │   fixture    │  │   marks      │   │
│  │ (session      │  │  (hook call  │  │  (dependency  │  │  (metadata)  │   │
│  │  state)       │  │   dispatch)  │  │   injection)  │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

**Key Principle:** Plugins communicate only through pytest's hook system and `config.stash` — never through direct module imports of each other's internals. This is the standard that the codebase mostly follows but needs to fully enforce.

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Entrypoint module** | Register hooks, add CLI options, bootstrap plugin class | `entrypoint.py` with `pytest_addhooks`, `pytest_addoption`, `pytest_configure` |
| **Plugin class** | Implement BDD-specific behavior via hook methods | Class registered via `config.pluginmanager.register(MyPlugin())` |
| **Hook spec class** | Declare custom BDD hooks that other plugins implement | Class with `@pytest.hookspec` methods, registered via `pytest_addhooks` |
| **Model objects** | Domain state: `Run`, `ScenarioRun`, `FeatureRuntimeBinding`, `ScenarioRun` | `@define` (attrs) classes stored in `config.stash` |
| **Step Definition Manager** | Registry + Matcher for step-to-function resolution | Singleton-ish registry with parent-chain hierarchy |
| **Parser** | Gherkin text → `GherkinDocument` + `Source` objects | ABC with Python and Go backends |
| **Formatter base** | Shared formatter lifecycle (CLI option → Node.js runtime → output) | `FormatterReporterPlugin` base class |
| **Scenario Locator** | Resolve feature file paths/URLs → parsed documents | `FileScenarioLocator`, `UrlScenarioLocator` |
| **Stash Access** | Typed read/write to `pytest.Stash` | `StashBound` base + `StashKey[T]` typed keys |

## Recommended Refactored Structure

```text
src/pytest_bdd/
├── __init__.py              # Public API: lazy imports via __getattr__
├── scenario.py              # scenario(), scenarios() decorators
├── steps.py                 # given(), when(), then(), step() + StepDefinitionManager
├── parsers.py               # StepParser hierarchy (7 parser types)
├── hook.py                  # before/after/around hook decorators
│
├── model/                   # DOMAIN OBJECTS — NO plugin imports
│   ├── run.py               # Run class (session-scoped container) ← split from scenario_run.py
│   ├── scenario_run.py      # ScenarioRun class (per-test execution) ← split from scenario_run.py
│   ├── feature_binding.py   # FeatureRuntimeBinding (per-feature data) ← split from scenario_run.py
│   ├── stash_access.py      # StashBound base + StashAccess helpers
│   ├── message_converter.py # Dict ↔ cucumber_messages conversion
│   ├── message_validation.py
│   ├── message_serialization.py
│   └── message_transport.py
│
├── collector/               # TEST DISCOVERY — depends on model + parser
│   ├── collector.py         # FeatureFileModule (pytest collector)
│   ├── batch.py             # FeatureBatchParser (async parallel parsing)
│   ├── locator_file.py      # FileScenarioLocator
│   └── locator_url.py       # UrlScenarioLocator
│
├── parser/                  # GHERKIN PARSING — no plugin deps
│   ├── base.py              # BaseParser (normalize, emit errors)
│   ├── gherkin.py           # GherkinParser (plain)
│   ├── markdown.py          # MarkdownGherkinParser
│   └── _gherkin_go/         # Go ctypes backend
│
├── plugin/                  # PLUGINS — each is self-contained
│   ├── _base/               # Shared plugin infrastructure
│   │   ├── formatter.py     # FormatterReporterPlugin base class
│   │   └── reporter.py      # ReporterPluginBase
│   │
│   ├── collection/          # scenario_test_collector (renamed for clarity)
│   │   ├── __init__.py
│   │   ├── entrypoint.py    # pytest_addhooks, pytest_addoption, pytest_configure
│   │   ├── plugin.py        # ScenarioTestCollector class (hook methods)
│   │   ├── hook.py          # ScenarioTestCollectorHookSpec
│   │   └── const.py
│   │
│   ├── execution/           # pickle_runner (renamed for clarity)
│   │   ├── __init__.py
│   │   ├── entrypoint.py    # Registration + fixtures
│   │   ├── plugin.py        # PickleRunner class (hook methods)
│   │   ├── hook.py          # PickleRunnerHookSpec
│   │   ├── transitions.py   # apply_transition() state machine
│   │   ├── access.py        # require_feature_object, etc.
│   │   └── const.py
│   │
│   ├── formatters/          # All output formatters
│   │   ├── _base.py         # Formatter base classes
│   │   ├── cucumber_json.py
│   │   ├── cucumber_junit.py
│   │   ├── cucumber_pretty.py
│   │   ├── cucumber_progress.py
│   │   ├── cucumber_snippets.py
│   │   └── ...
│   │
│   ├── gherkin_message_reporter/
│   ├── struct_bdd/
│   ├── code_generator/
│   ├── allure_logger/       # Dead? Flags: review for removal
│   └── scenario_reporter/
│
├── compatibility/           # Cross-version shims (keep as-is)
│   ├── pytest/
│   ├── pathlib.py
│   └── ...
│
└── util/                    # Shared utilities
    ├── test_group_ordering.py
    ├── data_table.py
    └── ...
```

### Structure Rationale

- **`model/` → single-file-per-class:** Splits `scenario_run.py` (1422 lines) into `run.py` (~200 lines), `scenario_run.py` (~400 lines), `feature_binding.py` (~500 lines). Each file owns one `@define` class plus its methods. **Why:** 1422-line file is the #1 maintainability problem; class-per-file matches pytest's own `_pytest/` structure.
- **`collector/` → flat package:** Pulls `collector.py`, `collector_batch.py`, `scenario_locator.py`, `feature_locator.py` into one package. **Why:** These are all about test discovery — they share the `FeatureBatchParser` stash object and tighter coupling is acceptable.
- **`parser/` → package:** Moves `parser.py` (Python) + `_gherkin_go/` (Go) under one roof. **Why:** They share the `ParserProtocol` ABC — natural co-location.
- **`plugin/` → one subpackage per plugin:** Standard pytest convention. Each plugin package has `entrypoint.py` (registration), `plugin.py` (class), `hook.py` (hook specs). **Why:** Consistent structure makes plugin authoring predictable. Current code does this for most plugins — `code_generator` is the outlier (module-level functions, no class).
- **`plugin/_base/`:** Shared infrastructure for plugins (formatter base class, reporter base). **Why:** Reduces duplication across 12 formatter plugins that share 90% of their lifecycle.

## Architectural Patterns

### Pattern 1: Plugin Class + Registration

**What:** Each pytest plugin is a class with hook methods, registered via `config.pluginmanager.register()` in `pytest_configure`. The entrypoint module handles CLI options, hook specs, and plugin bootstrap.

**When to use:** Every plugin in the system. This is the standard internally.

**Trade-offs:**
- Pro: Lifetime is explicit (registered at configure, torn down at session end). State is instance-local.
- Pro: `pluginmanager.get_plugin("name")` allows inter-plugin lookup without imports.
- Con: Slightly more boilerplate than module-level functions, but the entrypoint/plugin split is worth it.

**Example (from codebase — scenario_test_collector):**

```python
# entrypoint.py
def pytest_addhooks(pluginmanager):
    pluginmanager.add_hookspecs(ScenarioTestCollectorHookSpec)

def pytest_addoption(parser):
    group = parser.getgroup("bdd", "Scenario")
    group.addoption("--disable-feature-autoload", ...)

def pytest_configure(config):
    config.pluginmanager.register(ScenarioTestCollector())
    FeatureBatchParser().initialize_in_stash(config.stash)

# plugin.py
class ScenarioTestCollector:
    def pytest_collect_file(self, parent, file_path): ...
    def pytest_generate_tests(self, metafunc): ...
```

### Pattern 2: StashBound for Session State

**What:** Objects needing session-long persistence are stored in `pytest.Stash` (via `config.stash`) using typed `StashKey[T]` keys. The `StashBound` base class provides `initialize_in_stash()`, `from_stash()`, `find_in_stash()` classmethods.

**When to use:** Any object that outlives a single test item — `Run` (entire session), `FeatureBatchParser` (collection phase), `IdGenerator` (sequential IDs across tests).

**Trade-offs:**
- Pro: Type-safe (mypy-compatible via `StashKey[T]`).
- Pro: No globals. State is scoped to `config` lifecycle.
- Pro: Multiple plugins can access the same state object via `Run.from_stash(config.stash)`.
- Con: Must be initialized in `pytest_configure` before any hook that reads it.

**Example (from codebase):**

```python
# model/stash_access.py
class StashBound:
    STASH_KEY: ClassVar[str]

    @classmethod
    def from_stash(cls, stash: pytest.Stash) -> "StashBound": ...

    def initialize_in_stash(self, stash: pytest.Stash) -> None: ...

# model/run.py (refactored)
@define
class Run(StashBound):
    STASH_KEY = "pytest_bdd/run"
    feature_bindings: dict[str, FeatureRuntimeBinding] = Factory(dict)
    scenario_runs: list[ScenarioRun] = Factory(list)
```

### Pattern 3: Hook-Driven Inter-Plugin Communication

**What:** Plugins never import each other's internal modules. Instead, they declare custom hooks (via HookSpec classes) and call them through `config.hook.pytest_bdd_*()`. Other plugins implement those hooks in their plugin classes.

**When to use:** Any time one plugin needs behavior from another (e.g., collection plugin needs step matching from execution plugin).

**Trade-offs:**
- Pro: Plugins are truly decoupled — can be enabled/disabled independently.
- Pro: Third-party plugins can hook into BDD lifecycle without depending on internal modules.
- Pro: pytest's `tryfirst=True`/`trylast=True` gives ordering control.
- Con: Indirection makes control flow harder to trace. Debug logging should annotate hook calls.

**Example (current pattern to preserve and expand):**

```python
# Plugin A declares hook
class ScenarioTestCollectorHookSpec:
    @pytest.hookspec(firstresult=True)
    def pytest_bdd_match_step_definition_to_step(
        self, request: FixtureRequest, run: Run
    ) -> StepDefinitionManager.Definition | None:
        """Find match between step text and step definition."""

# Plugin B implements hook
class PickleRunner:
    def pytest_bdd_match_step_definition_to_step(self, request, run):
        matcher = StepDefinitionManager.Matcher(...)
        return matcher.match(...)
```

### Pattern 4: Formatter Base Class Hierarchy

**What:** All 12 formatter plugins inherit from `FormatterReporterPlugin` which handles CLI option registration, Node.js runtime lifecycle, output path resolution, and runtime asset rendering. Each formatter subclass only specifies `output_mode`, `runtime_template_name`, and a few overrides.

**When to use:** All output formatters. This is the model for consistency.

**Trade-offs:**
- Pro: Adding a new formatter is ~50 lines vs ~500 lines.
- Pro: Consistent CLI behavior (`--cucumber-pretty`, `--cucumber-json` all work identically).
- Con: Tight coupling to Node.js runtime — but that's the trade-off for Cucumber compatibility.

**Example (to expand for code_generator):**

```python
class PrettyFormatterPlugin(FormatterReporterPlugin):
    output_mode = FormatterOutputMode.stdout
    writes_to_terminal = True
    runtime_kind = FormatterRuntimeKind.module
    runtime_template_name = "pretty.cjs.j2"
```

## Data Flow

### Collection Flow (Test Discovery)

```text
pytest session start
    ↓
pytest_configure() → register ScenarioTestCollector
    ↓                  initialize FeatureBatchParser in stash
    ↓                  initialize Run in stash
    ↓
pytest_collect_file(parent, file_path)
    ↓
ScenarioTestCollector.is_enabled(config)? ──→ NO → return None
    ↓ YES
Is file_path a .feature/.gherkin/.url/.desktop/.webloc?
    ↓ YES
hook.pytest_bdd_is_collectible(config, path)  ← other plugins can reject
    ↓ YES
FeatureBatchParser.register(path)  [async batch mode]
    ↓
FeatureFileCollector.build(parent, file_path)
    ↓
scenarios() → builds pytest mark + fixture stack
    ↓
pytest_generate_tests(metafunc) → ScenarioLocatorBuilder
    ↓
FileScenarioLocator.resolve(config) → yield (GherkinDocument, Pickle, Source)
    ↓
FeatureRuntimeBinding.ensure_pickles() → compile pickles via gherkin compiler
    ↓
metafunc.parametrize("gherkin_document, pickle, feature_source", [...])
    ↓
pytest generates one test per scenario × Examples table row
```

### Execution Flow (Test Running)

```text
pytest_runtest_setup(item)
    ↓
PickleRunner checks PYTEST_BDD_MARK on item
    ↓
Run.create_scenario_run(request, gherkin_document, pickle, feature_source)
    ↓
hook.pytest_bdd_before_scenario(request, run)
    ↓  apply_transition() → RunStage.scenario_running
    ↓
hook.pytest_bdd_run_scenario(request, run)  [firstresult=True]
    ↓
  step dispatcher pops steps from deque
    ↓
  for each step:
    hook.pytest_bdd_run_step(request, run)
      ↓
    hook.pytest_bdd_match_step_definition_to_step(request, run)  [firstresult=True]
      ↓ StepDefinitionManager.Matcher (3-pass matching)
      ↓
    hook.pytest_bdd_before_step(request, run, step_func)
      ↓
    hook.pytest_bdd_before_step_call(request, run, step_func, args, definition)
      ↓
    call_fixture_func(step_func, request, **parsed_args)
      ↓ success → hook.pytest_bdd_after_step(...)
      ↓ failure → hook.pytest_bdd_step_error(..., exception=...)
      ↓
    inject target fixtures
    ↓
hook.pytest_bdd_after_scenario(request, run)  [finally block, always runs]
    ↓
pytest_runtest_teardown(item) → Run.pop_scenario_run()
```

### State Management

```text
config.stash (pytest.Stash instance)
├── Run (STASH_KEY="pytest_bdd/run")
│   ├── feature_bindings: dict[uri, FeatureRuntimeBinding]
│   │   ├── gherkin_document: GherkinDocument
│   │   ├── pickles: list[Pickle]
│   │   └── ast_node_index: dict[id, GherkinDocument node]
│   ├── scenario_runs: list[ScenarioRun]  (stack, push/pop per test)
│   │   ├── stage: RunStage (state machine)
│   │   ├── active_objects: (feature, scenario, step refs)
│   │   ├── step_run: StepRun (current step data)
│   │   └── status: RunStatus
│   └── reporting_state: ReportLifecycle
├── FeatureBatchParser (STASH_KEY="pytest_bdd/feature_batch_parser")
│   └── registered_paths: list[Path] → flushed on first get()
└── IdGenerator (STASH_KEY="pytest_bdd/id_generator")
    └── counter: int → sequential IDs for Cucumber Messages
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Small project (10-100 features) | Current architecture sufficient. Batch parser overhead negligible. |
| Medium project (100-1000 features) | Batch parser with multiprocessing provides value. Stash size manageable. |
| Large project (1000-10K features) | FeatureBinding cache may need eviction. Consider per-session Run with LRU for feature_bindings dict. |
| CI/CD distributed (xdist) | Already supported. `gherkin_message_reporter` handles remote module communication. |
| IDE integration | `config.stash` read access is thread-safe. Plugin classes are not — need stateless query API for IDE use. |

### Scaling Priorities

1. **First bottleneck:** `FeatureBatchParser` multiprocessing startup overhead on Windows (spawn is slow). Already handled via `batch_threshold` config (50 Linux, 1000 Windows).
2. **Second bottleneck:** `ScenarioRun` stack size under many parametrized scenarios. Already a list (not recursion) — safe.
3. **Third bottleneck:** `FeatureRuntimeBinding.ast_node_index` memory for large feature files. Only materialized on first resolution — lazy is fine.

## Anti-Patterns

### Anti-Pattern 1: God Object in `scenario_run.py`

**What people do:** One file holding `Run` (session container), `ScenarioRun` (per-test state), `FeatureRuntimeBinding` (per-feature data), `HookPhase`, `RunStage`, `RunStatus`, and `StepRun` — 1422 lines with all classes interleaved.

**Why it's wrong:** Any change to `ScenarioRun` requires navigating past `FeatureRuntimeBinding` internals. Test isolation is impossible (unit tests must import the whole file). Merge conflicts are guaranteed on any team.

**Do this instead:** Split into `model/run.py` (Run), `model/scenario_run.py` (ScenarioRun + RunStage + StepRun), `model/feature_binding.py` (FeatureRuntimeBinding). Each file imports only what it needs from the others.

### Anti-Pattern 2: Module-Level Functions Instead of Plugin Classes

**What people do:** The `code_generator/plugin.py` uses module-level functions (`check_existence`, `generate_code`, etc.) decorated with `@pytest.hookimpl` instead of a plugin class.

**Why it's wrong:** Inconsistent with all 16 other plugins. No instance state. Harder to test (can't instantiate with mock config). Can't benefit from `pluginmanager.get_plugin()` for inter-plugin access.

**Do this instead:** Refactor `code_generator` into a `CodeGeneratorPlugin` class following the same `entrypoint.py` → register class → hook methods pattern as all other plugins.

### Anti-Pattern 3: Broad Exception Catchers (`except Exception:`)

**What people do:** 22 instances of bare `except Exception:` across the codebase, catching everything including `KeyboardInterrupt` (on Python <3.11) and `SystemExit`.

**Why it's wrong:** Silently swallows unexpected errors. Makes debugging near-impossible. `KeyboardInterrupt` should propagate, not be caught.

**Do this instead:**
- In hook implementations: catch specific `PytestBDDError` subclasses.
- In parser code: catch `gherkin.errors.CompositeParserException` specifically.
- In step execution: catch `Exception` only in the `pytest_bdd_step_error` hook handler, log the full traceback, and re-raise after notifying observers.
- Never catch `BaseException` — let `KeyboardInterrupt` and `SystemExit` propagate.

### Anti-Pattern 4: `return None` in Non-Hook Code

**What people do:** 96 instances of functions that return `None` implicitly or explicitly, violating the AGENTS.md rule: "Outside pytest hook implementations, returning `None` is an antipattern; use explicit values or deterministic exceptions instead."

**Why it's wrong:** `None` is ambiguous — "not found" vs "error" vs "no result" vs "not applicable". Callers must check for `None` everywhere. Pytest hook system is the only place where `None` has defined semantics (means "next implementation, please").

**Do this instead:**
- Return sentinel objects: `MISSING = object()` for "not found".
- Raise specific exceptions: `StepDefinitionNotFoundError` for lookup failures.
- Return empty collections: `[]` or `{}` for "no results".
- Use `Optional[T]` only where `None` has a single unambiguous meaning.

### Anti-Pattern 5: Plugin Internal Coupling Via Direct Imports

**What people do:** `scenario_test_collector/plugin.py` imports from `pickle_runner/run_access.py` (`require_feature_object`, `require_pickle_object`, etc.).

**Why it's wrong:** Creates hard dependency between plugins. If `pickle_runner` is disabled, `scenario_test_collector` breaks at import time.

**Do this instead:** The `require_*` functions should live in `model/` (they access `Run` and `ScenarioRun` — model objects). Or the collector should call the hook `pytest_bdd_require_feature_object` and let the runner plugin implement it.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Cucumber Messages Protocol | `cucumber-messages` Python library | Type-safe message objects for interoperable reporting |
| Cucumber Expressions | `cucumber-expressions` library | Step pattern matching using Cucumber expression syntax |
| Gherkin Parser (Python) | `gherkin-official` library | Standard compliant parsing; fallback when Go backend unavailable |
| Gherkin Parser (Go) | ctypes shared library (build-time) | 10-50x faster parsing; optional, compiled via `build_go` command |
| Node.js Runtime (Formatters) | Subprocess via `@cucumber/cucumber` + `@cucumber/pretty-formatter` | Cucumber-compatible output rendering; managed by `npm_resource.py` |
| pytest-xdist (Distributed) | `pytest_xdist_getremotemodule` hook | Remote module communication for live reporting |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Plugin ↔ Plugin | Custom BDD hooks via `config.hook.pytest_bdd_*` | Never direct import. This is the critical rule. |
| Plugin ↔ Model | Direct method calls + `config.stash` | Plugins depend on models; models never depend on plugins. |
| Model ↔ Parser | Direct method calls (parser returns domain objects) | Parsers produce `GherkinDocument` — model stores them. |
| Entrypoint ↔ Plugin Class | Entrypoint registers plugin class in `pytest_configure` | Entrypoint has no other dependency on plugin class. |
| Public API ↔ Plugin Layer | Public API sets pytest marks/fixtures that plugins consume | Thin wrapper — no direct plugin imports. |
| Formatters ↔ Node.js | `RenderRuntimeAssets → Node.js subprocess → stdout/files` | Managed by `FormatterReporterPlugin` base class. |

## Plugin Lifecycle

```text
pytest startup
    │
    ├─ 1. Load entrypoint modules (pytest11 in pyproject.toml)
    │     ├─ pytest_addhooks(pluginmanager) → register HookSpec classes
    │     └─ pytest_addoption(parser) → register CLI flags
    │
    ├─ 2. pytest_configure(config)
    │     ├─ Initialize stash objects: Run, FeatureBatchParser, IdGenerator
    │     ├─ Register plugin class: config.pluginmanager.register(MyPlugin())
    │     └─ Register markers: config.addinivalue_line("markers", ...)
    │
    ├─ 3. Collection phase
    │     ├─ pytest_collect_file → discovery
    │     └─ pytest_generate_tests → parametrization
    │
    ├─ 4. Execution phase (per test)
    │     ├─ pytest_runtest_setup → scenario setup
    │     ├─ pytest_runtest_call → step execution
    │     └─ pytest_runtest_teardown → scenario teardown
    │
    ├─ 5. Reporting phase
    │     ├─ pytest_runtest_logreport → per-test reporting
    │     ├─ pytest_sessionfinish → final reports
    │     └─ pytest_terminal_summary → terminal output
    │
    └─ 6. Shutdown (config.stash garbage collected)
```

## Migration Strategy from Current Architecture

The current architecture is sound but has accumulated technical debt. Migration should be incremental:

### Phase 0: Already Done
- Plugin class pattern adopted by 16/17 plugins
- `StashBound` base class for stash access
- `FormatterReporterPlugin` base for formatters
- Hook-driven inter-plugin communication (custom hooks declared)

### Phase 1: Split `scenario_run.py`
Split the 1422-line file into three modules:
1. `model/run.py` — `Run` class (~200 lines)
2. `model/scenario_run.py` — `ScenarioRun`, `RunStage`, `StepRun` (~400 lines)
3. `model/feature_binding.py` — `FeatureRuntimeBinding` (~500 lines)

No behavior changes. Pure file split. Run full test suite after each split to verify.

### Phase 2: Fix Antipatterns
1. Replace 22 bare `except Exception:` with specific types
2. Replace 96 `return None` with sentinels/exceptions
3. Refactor `code_generator` into class-based plugin
4. Move `run_access.py` functions to `model/`

### Phase 3: Consolidation (Optional)
1. Rename `scenario_test_collector` → `collection`
2. Rename `pickle_runner` → `execution`
3. Move formatter files into `plugin/formatters/`
4. Remove dead `allure_logger` plugin or reimplement it

## Sources

- **pytest official docs (v9.x):** Writing plugins — <https://docs.pytest.org/en/stable/how-to/writing_plugins.html> (HIGH confidence — official)
- **pytest official docs:** Writing hook functions — <https://docs.pytest.org/en/stable/how-to/writing_hook_functions.html> (HIGH confidence — official)
- **pytest official docs:** `config.stash` / `StashKey[T]` — <https://docs.pytest.org/en/stable/how-to/writing_hook_functions.html#storing-data-on-items-across-hook-functions> (HIGH confidence — official)
- **pluggy documentation:** Hook specs, hookimpl markers, wrappers — <https://pluggy.readthedocs.io/en/stable/> (MEDIUM confidence — external but canonical)
- **Codebase analysis:** `.planning/codebase/ARCHITECTURE.md` mapped at commit `c59470a9` (HIGH confidence — direct codebase reading)
- **Plugin class pattern:** Observed in `scenario_test_collector`, `pickle_runner`, `gherkin_message_reporter`, `struct_bdd`, all formatters (HIGH confidence — codebase evidence)
- **Entrypoint pattern:** `entrypoint.py` + `plugin.py` + `hook.py` + `const.py` observed across 9 plugin packages (HIGH confidence — codebase evidence)

---

*Architecture research for: pytest-bdd-ng BDD plugin library*
*Researched: 2026-05-12*
