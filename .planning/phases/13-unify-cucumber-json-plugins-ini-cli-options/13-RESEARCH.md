# Phase 13: Research — Unify cucumber-json plugins INI/CLI options

**Researched:** 2026-05-20

---

## Summary

Phase 13 adds a third pytest11 plugin (`cucumber_json_dispatcher`) that reads both the
INI `cucumber_json_path` option and the CLI `--cucumber-json` flag. When triggered, it
delegates to one of the two existing backends — without modifying them. The biggest
constraint discovered is the **BLQ1002 cross-plugin import ban**: the dispatcher **must
not import** from `pytest_bdd.plugin.cucumber_json` or
`pytest_bdd.plugin.cucumber_json_formatter`. All constants (option names, flag strings)
must be duplicated in the dispatcher's own `const.py`.

---

## Existing Plugin Analysis

### cucumber_json (INI-based)

**Files:** `__init__.py`, `const.py`, `entrypoint.py`, `hook.py`, `model.py`, `plugin.py`

#### entrypoint.py (55 lines)

```python
def pytest_addoption(parser: Parser) -> None:
    parser.getgroup("bdd", "Cucumber JSON")
    parser.addini(
        str(CucumberJson.Ini.PATH_OPTION),   # "cucumber_json_path"
        default="", type="string",
        help="create cucumber json style report file at given path.",
    )

def pytest_configure(config) -> None:
    cucumber_json_path = config.getini(str(CucumberJson.Ini.PATH_OPTION))
    if cucumber_json_path and not hasattr(config, "workerinput"):   # xdist guard
        config._bddcucumberjson = CucumberJsonPlugin(cucumber_json_path)
        config.pluginmanager.register(config._bddcucumberjson)

def pytest_unconfigure(config) -> None:
    plugin = getattr(config, "_bddcucumberjson", None)
    if plugin is not None:
        del config._bddcucumberjson
        config.pluginmanager.unregister(plugin)
```

**Key observations:**
- INI option name: `"cucumber_json_path"` (from `CucumberJson.Ini.PATH_OPTION`)
- Plugin stored on `config._bddcucumberjson` (private attr on config)
- xdist guard: `not hasattr(config, "workerinput")` — checked INSIDE `pytest_configure`, not in `pytest_addoption`
- `pluginmanager.register(plugin)` with no name — registered anonymously

#### const.py (18 lines)

```python
class CucumberJson:
    class Ini(StrEnum):
        PATH_OPTION = "cucumber_json_path"    # INI key read via config.getini()
    class Cli(StrEnum):
        PATH_OPTION = "cucumber_json_path"    # ⚠️ SAME VALUE as Ini — historical artifact
```

> **CRITICAL:** `CucumberJson.Cli.PATH_OPTION` equals `"cucumber_json_path"` — same string
> as the INI option. The CLI option for the **formatter backend** is actually `--cucumber-json`
> with dest `cucumber_js_json_path` (different name, different plugin).
> The dispatcher must NOT import this const — duplicate in own module.

#### plugin.py (147 lines)

- `LogBDDCucumberJSON` — core hook implementor: `pytest_runtest_logreport`, `pytest_sessionstart`, `pytest_sessionfinish`, `pytest_terminal_summary`
- `CucumberJsonPlugin(LogBDDCucumberJSON)` — thin subclass (empty body, just a named type alias)
- Writes Python-legacy JSON format at session finish

### cucumber_json_formatter (CLI-based)

**Files:** `__init__.py`, `entrypoint.py`, `hook.py`, `plugin.py`

#### entrypoint.py (6 lines)

```python
from .plugin import JsonFormatterPlugin
json_plugin = JsonFormatterPlugin()
```

Pattern: module-level singleton. pytest11 entry point references `entrypoint:json_plugin` (the object).

#### plugin.py (54 lines)

```python
class JsonFormatterPlugin(FormatterReporterPlugin):
    output_mode = FormatterOutputMode.path

    def __init__(self) -> None:
        super().__init__(
            option_attr="cucumber_js_json_path",   # config.option.cucumber_js_json_path
            cli_flag="--cucumber-json",
            formatter="json",
            package_name="@cucumber/cucumber",
            module_name="pytest_bdd.plugin.cucumber_json_formatter.entrypoint",
            help_text="render the cucumber json formatter to the given path.",
            discovery_order=3,
        )
```

- CLI flag: `--cucumber-json`
- Config option attr: `cucumber_js_json_path` (NOT `cucumber_json_path`)
- Works via `FormatterReporterPlugin.pytest_addoption` hook (inherited, auto-registers `--cucumber-json`)
- `FormatterReporterPlugin` is `@frozen` (attrs) — cannot be modified at runtime

**How it activates:** The `json_plugin` singleton is loaded as a pytest11 plugin automatically.
Its inherited `pytest_addoption` registers `--cucumber-json`. Its inherited `pytest_configure`
is NOT directly called — instead the parent `GherkinMessageReporter` queries all formatter
plugins via hooks. The `json_plugin` is ALWAYS registered as a pytest plugin (module-level
singleton at import time).

> **IMPLICATION:** The dispatcher cannot "activate" `JsonFormatterPlugin` — it's already
> always registered. The dispatcher's job is to **bridge the INI value into the CLI option
> attr** (`config.option.cucumber_js_json_path`) before `GherkinMessageReporter.pytest_configure`
> reads it.

### Entry Points (pyproject.toml)

Lines 91–108, alphabetically sorted block:

```toml
[project.entry-points.pytest11]
"pytest-bdd-code-generator" = "pytest_bdd.plugin.code_generator.entrypoint"
"pytest-bdd-cucumber-formatter-json" = "pytest_bdd.plugin.cucumber_json_formatter.entrypoint:json_plugin"
"pytest-bdd-cucumber-formatter-junit" = "pytest_bdd.plugin.cucumber_junit.entrypoint:junit_plugin"
...
"pytest-bdd-cucumber-json" = "pytest_bdd.plugin.cucumber_json.entrypoint"
...
```

**Two patterns observed:**
1. Module-level object: `"module.path:object_name"` — used by formatter plugins
2. Module-level hooks: `"module.path"` — used by `cucumber_json` and `code_generator` (module exports `pytest_addoption`/`pytest_configure` at top level)

**New entry point to add:**
```toml
"pytest-bdd-cucumber-json-dispatcher" = "pytest_bdd.plugin.cucumber_json_dispatcher.entrypoint"
```
(module-level hook pattern, not object pattern — dispatcher has no singleton)

> **Alphabetical placement:** Should go between `"pytest-bdd-cucumber-json"` (line 102)
> and `"pytest-bdd-gherkin-message-reporter"` (line 103).

---

## Dispatcher Implementation Blueprint

### pluginmanager API

Correct method is `config.pluginmanager.getplugin(name)` (not `get_plugin`) — confirmed
from `gherkin_message_reporter/entrypoint.py:121`.

**Registration check pattern:**
```python
existing = config.pluginmanager.getplugin("pytest-bdd-cucumber-json")
# Returns None if not registered, else the plugin object
```

However, **this check is NOT needed** for the INI backend: `cucumber_json` is always
registered (module-level hooks, no guard), but it **self-guards** in its own
`pytest_configure` — only activates `CucumberJsonPlugin` if INI option is set.

For `cucumber_json_formatter`: already registered as `json_plugin` module-level singleton
and self-activates only when `--cucumber-json` is passed.

**The dispatcher's job is NOT to register backends, but to BRIDGE config values:**
- INI-only: dispatcher reads `config.getini("cucumber_json_path")` → does nothing (the
  INI backend already reads it itself)
- CLI-only: dispatcher reads `config.option.cucumber_js_json_path` → does nothing (the
  formatter backend reads it itself)
- Both set: dispatcher must clear `config.getini` or suppress INI backend activation

> **REVISED UNDERSTANDING:** Re-reading D-03 in CONTEXT.md: "if that plugin is already
> registered, it skips activation." This implies the dispatcher DOES register the backends
> itself in some scenarios. But given the `cucumber_json_formatter` is a frozen singleton
> always registered, the pattern must be different.

**The actual dispatcher pattern:**
- Check if CLI flag value is set (`config.option.cucumber_js_json_path is not None`)
- If CLI set AND INI also set: dispatcher needs to prevent the INI backend from activating
  by clearing/zeroing the INI value OR by unregistering it
- But we CANNOT modify existing plugins (D-05)

**CLARIFICATION on D-03 and D-06:** The dispatcher must suppress the INI backend when
CLI wins. Since INI backend's `pytest_configure` reads `config.getini(...)` and acts on
non-empty value, the dispatcher can:
- Option A: Override INI at runtime: set INI config option to empty string before INI
  plugin reads it (dispatcher runs first with `tryfirst=True`)
- Option B: Check if both are set and register a replacement for the INI plugin that
  no-ops

The cleanest approach compatible with D-05 (no modifications) is **Option A**:
`@pytest.hookimpl(tryfirst=True)` on dispatcher's `pytest_configure` → reads INI and CLI,
if both set, zeros the INI value so the INI backend's own `pytest_configure` finds nothing.

### pytest_configure flow

```python
# Dispatcher's entrypoint.py

INI_OPTION = "cucumber_json_path"       # Duplicated from cucumber_json/const.py
CLI_OPTION_ATTR = "cucumber_js_json_path"  # Duplicated from cucumber_json_formatter/plugin.py

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config) -> None:
    if hasattr(config, "workerinput"):  # xdist worker guard
        return
    ini_value = config.getini(INI_OPTION)   # "" if not set
    cli_value = getattr(config.option, CLI_OPTION_ATTR, None)  # None if not set

    if ini_value and cli_value is not None:
        # CLI wins (D-06): suppress INI backend by zeroing INI value
        # config.option is a namespace — we can't override getini() easily
        # Must use config.override_ini() or inject workaround
        pass
```

> **CRITICAL RISK:** `config.getini()` reads from the ini file — cannot easily be
> overridden at runtime without private API. Alternatives:
> - `config._inicache[INI_OPTION] = ""` — private but used widely
> - Store dispatcher state and have a mechanism to skip INI activation
> - Register an unregister hook for the INI backend
>
> Since we cannot modify existing plugins (D-05), and the INI backend has no guard
> checking dispatcher state, the dispatcher may need to **unregister** the INI backend's
> PLUGIN OBJECT (not the entrypoint module hooks) after it was activated, then re-activate
> the CLI backend — but this is complex.
>
> **Simpler path:** The dispatcher does NOT suppress the INI backend. Instead it is a
> purely additive plugin that reads INI value, and when CLI wins, it **also** ensures the
> CLI backend gets the right value. If both produce output, that's acceptable for phase 13
> scope (or dispatcher explicitly zeros `config._inicache`).

### xdist guard

Exact pattern from `cucumber_json/entrypoint.py:43`:
```python
if cucumber_json_path and not hasattr(config, "workerinput"):
```

Dispatcher copies this pattern:
```python
if hasattr(config, "workerinput"):
    return   # suppress all dispatcher logic on xdist worker nodes
```

**Placement:** First check in `pytest_configure`, BEFORE any config reading.

---

## Test Coverage Analysis

### Existing tests

| File | Location | Test group | Coverage |
|------|----------|------------|----------|
| `test_cucumber_json.py` | `tests/cases/e2e/feature/` | `e2e` | INI path: step trace, status parity with canonical messages |
| `test_cucumber_formatter_cli_contract.py` | `tests/cases/contract/contract/` | `contract` | CLI formatter catalog, contract checks, lifecycle |
| `test_cucumber_formatters.py` | `tests/cases/e2e/e2e/` | `e2e` | CLI `--cucumber-json` flag writes output, live stream |
| `test_plugin_patterns_contract.py` | `tests/cases/contract/contract/` | `contract` | Required files, cross-plugin import ban, no dataclass |

**Scenarios covered for existing plugins:**
- INI only: `test_step_trace`, `test_cucumber_json_step_status_parity_with_canonical_messages`
- CLI only: `test_file_formatter_flags_write_output[--cucumber-json]`
- CLI multiple formatters combined: `test_multiple_cucumber_formatters_run_in_one_session`
- No config: (implicitly — other test files use neither)

**NOT covered by existing tests:**
- Both INI + CLI set simultaneously
- Dispatcher plugin existence and registration
- CLI wins over INI silent suppression
- xdist worker guard for dispatcher

### Required new tests

New test file: `tests/cases/integration/cucumber_json/test_cucumber_json_dispatcher.py`
(group: `integration`, per test_group_paths mapping `tests/cases/integration/** = integration`)

| Test | What it verifies |
|------|-----------------|
| `test_dispatcher_ini_only_activates_ini_backend` | INI set → INI backend writes Python-format JSON, CLI backend silent |
| `test_dispatcher_cli_only_activates_cli_backend` | `--cucumber-json=path` set → formatter backend writes, INI backend silent |
| `test_dispatcher_cli_wins_over_ini` | Both set → only CLI backend produces output (D-06) |
| `test_dispatcher_no_config_both_silent` | Neither INI nor CLI → no JSON output, no error |
| `test_dispatcher_xdist_worker_guard` | On xdist worker node (`workerinput` present) → dispatcher no-ops |
| `test_dispatcher_entry_point_registered` | `pytest-bdd-cucumber-json-dispatcher` in pytest11 entry points |
| `test_dispatcher_no_warning_on_cli_override_ini` | CLI wins silently — no warnings emitted (D-07) |

**Test pattern:** Use `testdir` (pytester) fixture. For INI, write `pytest.ini` with
`cucumber_json_path = ...`. For CLI, pass `--cucumber-json=path` arg. For xdist, pass
`workerinput`-bearing config or use `pytester.runpytest_subprocess` with `-n1`.

---

## Canonical Plugin Structure

From `plugin_patterns.py` rule `BLQ1001`, **REQUIRED files** per plugin dir:
```
REQUIRED_FILES = {"entrypoint.py", "hook.py", "plugin.py"}
```

Plus: `__init__.py` (conventional, not checked by BLQ1001 but present in all plugins).

**Dispatcher package structure:**
```
src/pytest_bdd/plugin/cucumber_json_dispatcher/
    __init__.py       # docstring only
    const.py          # dispatcher-local copy of INI/CLI string constants
    entrypoint.py     # pytest_addoption + pytest_configure (tryfirst) + pytest_unconfigure
    hook.py           # placeholder docstring (canonical requirement)
    plugin.py         # CucumberJsonDispatcherPlugin class if needed (or empty/placeholder)
```

**Cross-plugin import ban (BLQ1002):** Dispatcher MUST NOT import from:
- `pytest_bdd.plugin.cucumber_json.*`
- `pytest_bdd.plugin.cucumber_json_formatter.*`

All string constants (`"cucumber_json_path"`, `"cucumber_js_json_path"`, `"--cucumber-json"`)
must be defined locally in `cucumber_json_dispatcher/const.py`.

**No `dataclass` allowed** (BLQ pattern contract) — use `attrs` if data classes needed.

---

## Validation Architecture

### Unit tests (fast, no subprocess)

Location: `tests/cases/unit/`

| Test | What |
|------|------|
| dispatcher const values correct | Assert `DISPATCHER_INI_OPTION == "cucumber_json_path"` etc. |
| dispatcher plugin structure | All required files exist (`entrypoint.py`, `hook.py`, `plugin.py`) |
| plugin_patterns checker passes | Run `check_plugin_patterns()` programmatically — no new violations |

### Integration tests (pytester, subprocess-light)

Location: `tests/cases/integration/cucumber_json/`

Use `testdir` (pytester) fixture — runs pytest in-process subprocess-light.

```python
def test_dispatcher_ini_only(testdir):
    ini = testdir.tmpdir.join("pytest.ini")
    output = testdir.tmpdir.join("result.json")
    ini.write(f"[pytest]\ncucumber_json_path = {output}\n")
    # ... add minimal BDD test ...
    result = testdir.runpytest("-s")
    assert output.check()   # file was written
    data = json.load(output.open())
    assert isinstance(data, list)
```

### Contract tests

Location: `tests/cases/contract/contract/`

Add to `test_cucumber_formatter_cli_contract.py` or new file:
```python
def test_dispatcher_entry_point_in_pyproject():
    pyproject_path = Path(__file__).resolve().parents[4] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    pytest11 = pyproject["project"]["entry-points"]["pytest11"]
    assert "pytest-bdd-cucumber-json-dispatcher" in pytest11

def test_dispatcher_no_cross_plugin_imports():
    from pytest_bdd._ruff.rules.plugin_patterns import check_cross_plugin_imports
    plugin_root = Path("src/pytest_bdd/plugin")
    violations = check_cross_plugin_imports(plugin_root)
    assert violations == []
```

---

## Key Risks and Gotchas

### 1. Cross-plugin import ban (BLQ1002) — HIGHEST RISK

The plugin_patterns checker (`check_cross_plugin_imports`) will fail CI if dispatcher
imports from `cucumber_json` or `cucumber_json_formatter`. All string constants must be
locally duplicated. If the constants ever change in the originals, the dispatcher copy
will silently drift — document this in dispatcher's docstring.

### 2. config.getini() cannot be overridden easily at runtime

When CLI wins over INI (D-06), the dispatcher needs to prevent the INI backend from
activating. Options:
- **`config._inicache[key] = ""`** — writes to private dict, effective but internal API
- **Run dispatcher with `@pytest.hookimpl(tryfirst=True)`** before INI backend's
  `pytest_configure` reads the ini value, then zero the `_inicache`
- **Alternative**: Accept that when both are set, BOTH backends may activate (different
  output files) — but D-06 says CLI wins, implying INI backend should be silent

**Recommend: Use `config._inicache[INI_OPTION] = ""`** — this is the only way to
override `getini()` at runtime without modifying the INI backend.

### 3. `config.option` may not exist in all hook call sites

`pytest_configure` is called during early setup before all options are fully parsed.
`config.option` may raise `AttributeError` for CLI options if called from wrong hook.
Use `getattr(config, "option", None)` and then `getattr(config.option, CLI_OPTION_ATTR, None)`.

### 4. cucumber_json_formatter is always registered (module-level singleton)

`json_plugin = JsonFormatterPlugin()` at module level means `cucumber_json_formatter` is
ALWAYS active as a pytest plugin. Dispatcher cannot "activate" it — it already is.
The CLI option `--cucumber-json` drives it. If dispatcher bridges INI → CLI attr, it
effectively activates the formatter backend via config injection.

### 5. pytest_addoption not needed in dispatcher

The dispatcher does NOT register any new CLI options or INI options. It only reads
EXISTING options registered by the two backends. Dispatcher's `pytest_addoption` can be
omitted or be a no-op.

### 6. Plugin pattern checker will scan new dispatcher package

The `check_required_files` rule requires `entrypoint.py`, `hook.py`, `plugin.py` — the
`plugin.py` is required even if dispatcher logic lives entirely in `entrypoint.py`.
Create `plugin.py` with a `CucumberJsonDispatcherPlugin` placeholder class, or
with actual dispatcher logic if a class wrapper is used.

### 7. No `pytest_unconfigure` needed for INI-suppression approach

If dispatcher zeros `_inicache` in `pytest_configure`, no cleanup is needed in
`pytest_unconfigure` — the `_inicache` modification only affects the current session.

### 8. StrEnum compatibility

Use `from pytest_bdd.compatibility.enum import StrEnum` (as done in `cucumber_json/const.py`)
for the dispatcher's const module — not `enum.StrEnum` directly (Python 3.10 compat).

---

## RESEARCH COMPLETE
