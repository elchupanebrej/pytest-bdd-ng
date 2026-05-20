# Phase 13: Unify cucumber-json plugins INI/CLI options - Context

**Gathered:** 2026-05-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a new dispatcher plugin that reads both INI (`cucumber_json_path`) and CLI (`--cucumber-json`) options and delegates to the appropriate existing backend plugin. The two existing plugins (`cucumber_json` and `cucumber_json_formatter`) remain unchanged and fully active as independent backends.

</domain>

<decisions>
## Implementation Decisions

### Consolidation Strategy
- **D-01:** Dispatcher pattern — a new plugin (`cucumber_json_dispatcher`) reads both INI and CLI config and delegates to the correct backend. Neither existing plugin is modified or removed.
- **D-02:** Dispatcher is a **third pytest11 entry point** added alongside the existing two (`pytest-bdd-cucumber-json` and `pytest-bdd-cucumber-formatter-json`). Both existing entry points remain active.
- **D-03:** Duplicate registration guard lives in the **dispatcher** — before activating a backend, the dispatcher checks `pluginmanager` to see if that plugin is already registered. If so, it skips activation.

### Entry Point Structure
- **D-04:** New package at `src/pytest_bdd/plugin/cucumber_json_dispatcher/` following canonical plugin structure (`__init__.py`, `entrypoint.py`, `hook.py`, `plugin.py`).
- **D-05:** Phase 13 scope is **strictly additive** — no deprecations, no removals, no modifications to existing plugins.

### Config Precedence
- **D-06:** **CLI wins** — when both `--cucumber-json` (CLI) and `cucumber_json_path` (INI) are set simultaneously, the dispatcher activates `cucumber_json_formatter` (Node.js backend) and ignores the INI option.
- **D-07:** Override is **silent** — no warning emitted when CLI overrides INI.

### Output Format
- **D-08:** No format convergence — the two backends intentionally produce different JSON:
  - INI path → `cucumber_json` Python writer (legacy pytest-bdd format)
  - CLI path → `cucumber_json_formatter` Node.js `@cucumber/cucumber` format
- **D-09:** Document the difference in the dispatcher's docstring/comments so users choose the right path knowingly.

### xdist Worker Behavior
- **D-10:** Dispatcher applies `workerinput` guard in `pytest_configure` — suppresses delegation on xdist worker nodes (same pattern as `cucumber_json` entrypoint).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Plugin Implementations
- `src/pytest_bdd/plugin/cucumber_json/entrypoint.py` — INI-based plugin: registers `cucumber_json_path` INI option, activates `CucumberJsonPlugin` with `workerinput` xdist guard
- `src/pytest_bdd/plugin/cucumber_json/const.py` — `CucumberJson.Ini` and `CucumberJson.Cli` StrEnum constants (both currently have identical value `cucumber_json_path`)
- `src/pytest_bdd/plugin/cucumber_json/plugin.py` — `CucumberJsonPlugin` / `LogBDDCucumberJSON`: Python JSON writer implementation
- `src/pytest_bdd/plugin/cucumber_json_formatter/entrypoint.py` — CLI-based plugin: thin module-level `json_plugin = JsonFormatterPlugin()` pattern
- `src/pytest_bdd/plugin/cucumber_json_formatter/plugin.py` — `JsonFormatterPlugin`: extends `FormatterReporterPlugin`, uses `--cucumber-json` CLI flag, delegates to Node.js formatter bridge

### Plugin Entry Point Registry
- `pyproject.toml` lines 93, 102 — current `[project.entry-points."pytest11"]` registrations for both plugins

### Canonical Plugin Pattern
- `src/pytest_bdd/plugin/cucumber_json/hook.py` — placeholder hook.py structure (canonical pattern requirement)
- Any other plugin under `src/pytest_bdd/plugin/` — reference for canonical `class + entrypoint + hook.py` structure

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CucumberJson.Ini.PATH_OPTION` / `CucumberJson.Cli.PATH_OPTION` in `const.py` — string constants for config option names; dispatcher should import these rather than hardcoding strings
- `FormatterReporterPlugin.build_required_path_addoption_kwargs()` — used by `cucumber_json_formatter`; dispatcher can call this indirectly via the existing plugin
- `workerinput` guard pattern in `cucumber_json/entrypoint.py:43` — copy this exact pattern in dispatcher's `pytest_configure`

### Established Patterns
- Canonical plugin structure: `__init__.py` + `entrypoint.py` + `hook.py` + `plugin.py` — new dispatcher package must follow this
- `pluginmanager.register()` / `pluginmanager.get_plugin()` — use `get_plugin()` or `get_plugins()` to check if a backend is already registered before the dispatcher activates it
- `attrs` over `dataclass` — if dispatcher needs any data classes

### Integration Points
- `pyproject.toml` `[project.entry-points."pytest11"]` — add `pytest-bdd-cucumber-json-dispatcher` entry pointing to `pytest_bdd.plugin.cucumber_json_dispatcher.entrypoint`
- `pytest_configure` hook — dispatcher's primary integration point; reads both INI and CLI, applies precedence logic, delegates to backend

</code_context>

<specifics>
## Specific Ideas

- Dispatcher docstring should explicitly state: "INI path activates the Python-written JSON reporter (legacy format). CLI path activates the Node.js @cucumber/cucumber JSON formatter (Cucumber-spec format). These produce different JSON structures by design."

</specifics>

<deferred>
## Deferred Ideas

- Deprecation of existing individual entry points — out of scope for Phase 13; may be addressed in a future cleanup phase
- Format convergence between Python writer and Node.js formatter — out of scope; formats intentionally differ

</deferred>

---

*Phase: 13-unify-cucumber-json-plugins-ini-cli-options*
*Context gathered: 2026-05-20*
