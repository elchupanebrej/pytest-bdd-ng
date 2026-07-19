---
phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl
plan: 1
subsystem: testing
tags: [pytest, mcp-pdb, debug-mcp, pytest-cache, config-stash]
requires:
  - phase: 20-codegen-step-binding-and-tolerant-steps
    provides: Recent pytest plugin option and integration test conventions
provides:
  - Debug MCP pytest plugin package shell
  - Optional `debug-mcp` dependency extra for `mcp-pdb>=0.6.0,<0.7`
  - CLI and ini option surface for debug MCP enablement and endpoint settings
  - Config.stash-backed session state and discovery JSON writer
  - Integration tests for inert defaults, option registration, port behavior, warnings, and stash state
affects: [debug-mcp, pytest-plugin, phase-20]
tech-stack:
  added: [mcp-pdb]
  patterns: [StashBound state, atomic discovery JSON, pytest option/ini mirror]
key-files:
  created:
    - src/pytest_bdd/plugin/debug_mcp/__init__.py
    - src/pytest_bdd/plugin/debug_mcp/discovery.py
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py
    - src/pytest_bdd/plugin/debug_mcp/hook.py
    - src/pytest_bdd/plugin/debug_mcp/options.py
    - src/pytest_bdd/plugin/debug_mcp/state.py
    - tests/cases/integration/debug_mcp/test_options_and_discovery.py
  modified:
    - pyproject.toml
key-decisions:
  - "Discovery file path is `.pytest_cache/mcp-pdb/session.json`, not pytest cache's nested data namespace."
  - "Invalid debug MCP config raises pytest UsageError instead of surfacing as an internal pytest error."
patterns-established:
  - "Debug MCP state is attrs-based and bound to config.stash through StashBound."
  - "Debug MCP endpoint discovery is serialized through a narrow SessionDiscovery model and atomic replace."
requirements-completed: [P21-MCP-01, P21-MCP-03, P21-MCP-04]
duration: 80min
completed: 2026-06-05
---

# Phase 21 Plan 01 Summary

**Pytest-only debug MCP shell with mirrored config, stash session state, and session discovery JSON**

## Performance

- **Duration:** 80 min
- **Started:** 2026-06-05T05:48:00Z
- **Completed:** 2026-06-05T07:10:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added `pytest-bdd-debug-mcp` pytest11 plugin entry point and `debug-mcp` optional dependency extra.
- Implemented `--mcp-pdb-on-fail` plus mirrored ini-backed timeout, lease, artifact, host, and port settings.
- Added `DebugMcpState` in `config.stash` plus `.pytest_cache/mcp-pdb/session.json` discovery with `mcp_pdb` and sidecar endpoints.
- Covered disabled default, missing legacy alias, fixed and auto ports, public-host warning, invalid config, and stash state.

## Task Commits

1. **Task 1: Add plugin package, optional extra, and option/config parsing** - `f0c70eec` (feat)
2. **Task 2: Implement stash state, endpoint allocation, and session discovery** - `f0c70eec` (feat)

## Files Created/Modified

- `pyproject.toml` - Added `pytest-bdd-debug-mcp` entry point and `debug-mcp` optional extra.
- `src/pytest_bdd/plugin/debug_mcp/options.py` - Resolves CLI/ini options with defaults and validation.
- `src/pytest_bdd/plugin/debug_mcp/state.py` - Defines attrs state and endpoint models using `StashBound`.
- `src/pytest_bdd/plugin/debug_mcp/discovery.py` - Allocates local ports and writes atomic discovery JSON.
- `src/pytest_bdd/plugin/debug_mcp/entrypoint.py` - Registers pytest options and initializes enabled sessions.
- `src/pytest_bdd/plugin/debug_mcp/hook.py` - Adds explicit hook surface placeholder.
- `tests/cases/integration/debug_mcp/test_options_and_discovery.py` - Contract tests for options and discovery.

## Decisions Made

- Used terminal output for public-host trusted-environment warnings to avoid warning-filter failures under repository `filterwarnings = error`.
- Wrote discovery directly under `.pytest_cache/mcp-pdb/` because pytest `config.cache.mkdir()` nests plugin data under `.pytest_cache/d/`.
- Converted invalid option values into `pytest.UsageError` so bad user config fails as a pytest usage problem.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- RTK command wrapper hung in this PowerShell environment, so verification commands were run directly with `uv run`.
- Initial commit attempt exposed TOML formatting and local mypy environment setup requirements; reran formatter/pre-commit and verified mypy through `uv run --extra testtypes mypy`.

## Verification

- `uv run python -m pytest tests/cases/integration/debug_mcp/test_options_and_discovery.py -q` - 7 passed.
- `uv run ruff check src/pytest_bdd/plugin/debug_mcp tests/cases/integration/debug_mcp/test_options_and_discovery.py` - passed.
- `uv run --extra testtypes mypy src/pytest_bdd/plugin/debug_mcp` - passed.
- Pre-commit during `git commit` - passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 21-02 can build the failure queue and hold lifecycle on top of `DebugMcpOptions`, `DebugMcpState`, endpoint discovery, and enabled-session initialization.

---
*Phase: 21-pdb-mcp-integration-for-agentic-debugging-and-producing-expl*
*Completed: 2026-06-05*
