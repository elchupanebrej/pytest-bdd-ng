# Phase 10: Pattern Unification - Research

## Context Analysis
The goal of this phase is to ensure consistency across the 17 plugin modules. From `10-CONTEXT.md`, most of the plugin structural requirements (e.g., `class + entrypoint + hook.py + plugin.py`, `attrs` usage, `StashBound` base class) are already being followed. The primary implementation steps will involve cleaning up two empty plugin directories, validating compliance programmatically, and writing a script to serve as an automated CI lint gate.

## Actionable Requirements
1. **Remove Empty Plugin Directories**
   - Target directories: `src/pytest_bdd/plugin/cucumber_formatter_support/` and `src/pytest_bdd/plugin/scenario_runner/`.
   - Verification: Confirm neither directory contains source files and they have no pyproject.toml entry point registration.

2. **Lint Gate Implementation (Plugin Validation Script)**
   - To validate these rules consistently, a new custom quality gate script should be created. Following the pattern set by `quality_gates.py`, we can create `src/pytest_bdd/_ruff/rules/plugin_patterns.py`.
   - **Validation 1: Structure**
     Ensure every directory inside `src/pytest_bdd/plugin/` (excluding `__init__.py` or `__pycache__`) contains `entrypoint.py`, `hook.py`, and `plugin.py`.
   - **Validation 2: Cross-Plugin Imports**
     Parse the AST of each file within a plugin directory. If an import resolves to `pytest_bdd.plugin.<other_plugin>`, flag it as a cross-plugin violation. Intra-plugin imports (e.g., `from pytest_bdd.plugin.gherkin_message_reporter.utils import ...`) are allowed.
   - **Validation 3: StashBound Coverage**
     Ensure that any access to `pytest.config.stash` occurs ONLY via `StashBound` logic. For example, if the script detects `.stash[` or `.stash.get(` in any plugin, it flags an error unless it's within `model/stash_access.py` or `types/exception.py` (which formatting errors).

3. **`pyproject.toml` integration**
   - Register the new custom lint script in a GitHub Actions CI step or as a new `[tool.quality_gates]` entry to ensure pattern enforcement. Wait, there is already `[tool.quality_gates]` which points to `pytest_bdd._ruff.rules.quality_gates`. We can either add to it, or make a combined runner.

## Technical Feasibility & Risks
- **AST Parsing for cross-imports**: Python's `ast` module handles import checking efficiently.
- **No Decopatch replacement**: Explicitly deferred to Phase 11.
- **Zero Impact on Runtime**: This phase purely cleans up dead folders and adds test/lint infrastructure. The only potential disruption is if a cross-plugin import was missed in the manual contextual scan, but `10-CONTEXT.md` explicitly noted none were found.

## Conclusion
The requirements are well-defined. The main deliverable of this phase will be the `plugin_patterns.py` validation script, and minor cleanup tasks for dead folders. I'm ready to proceed to planning.
