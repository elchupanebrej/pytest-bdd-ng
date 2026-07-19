# Phase 10: Pattern Unification - Patterns

## Analyzed Artifacts
- `10-CONTEXT.md`
- `10-RESEARCH.md`

## File Patterns
### 1. Custom Lint Rules (`src/pytest_bdd/_ruff/rules/plugin_patterns.py`)
- **Role**: Validates consistency of plugin structure and restricts cross-plugin imports.
- **Data Flow**: Standalone CI script that uses `ast` to parse files across the `plugin/` directory.
- **Closest Analog**: `src/pytest_bdd/_ruff/rules/quality_gates.py`.

### 2. Pyproject.toml Registration
- **Role**: Integrates the new script into the build and lint processes.
- **Closest Analog**: `[tool.quality_gates]` section in `pyproject.toml`.

### 3. Removed Files
- `src/pytest_bdd/plugin/cucumber_formatter_support/` (Directory removed)
- `src/pytest_bdd/plugin/scenario_runner/` (Directory removed)
