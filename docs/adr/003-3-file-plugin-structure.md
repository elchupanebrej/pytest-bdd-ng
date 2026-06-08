# ADR-003: Three-file plugin structure (`entrypoint.py` + `hook.py` + `plugin.py`)

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** pytest-bdd-ng core team

## Context

pytest-bdd-ng has 17+ plugins registered via `pytest11` entry points. These
plugins handle collection, execution, reporting, formatting, struct-BDD,
code generation, and Allure integration.

Early plugins used varying file structures: some had everything in `plugin.py`,
others split across `__init__.py` and `plugin.py`, and a few had ad-hoc
organization. During Phase 10, the plugin structure was unified to a consistent
three-file pattern enforced by BLQ1001 in `plugin_patterns.py`.

## Decision

Every plugin directory under `src/pytest_bdd/plugin/` must contain exactly
three files:

| File | Purpose |
|------|---------|
| `entrypoint.py` | pytest hook registration (`pytest11` entry point). Contains `pytest_configure()`, `pytest_addoption()`, and other standard pytest hooks. References `plugin.py` for the main plugin class. |
| `hook.py` | pytest-bdd-specific hooks. Declares and documents hook specifications that other plugins or test code can implement. |
| `plugin.py` | Plugin implementation class. Contains the core plugin logic, step implementations, and state management. |

This structure separates concerns:
- **pytest integration** (`entrypoint.py`) — what pytest sees at registration time
- **BDD hook API** (`hook.py`) — what other plugins and test code implement
- **Implementation** (`plugin.py`) — the plugin's business logic

Enforcement is automated via `plugin_patterns.py` rule BLQ1001, which checks
that each plugin directory contains all three required files.

## Consequences

### Positive
- Predictable structure: contributors know exactly where to find pytest hooks,
  BDD hook specs, and plugin logic
- Discoverable: automated checks (BLQ1001) catch missing files immediately
- Separation of concerns: pytest integration changes don't affect hook API
- Consistent across 17+ plugins: no plugin-specific conventions to learn

### Negative
- Overhead for single-hook plugins: a plugin that only has one hook spec must
  still create three files
- Three-file minimum creates small boilerplate files (often <10 lines)
  that exist solely to satisfy the convention

### Neutral
- The convention is enforced but not technically required by pytest
- Plugin directories could be flattened if pytest-bdd moved away from
  directory-per-plugin organization, but the current structure is stable
