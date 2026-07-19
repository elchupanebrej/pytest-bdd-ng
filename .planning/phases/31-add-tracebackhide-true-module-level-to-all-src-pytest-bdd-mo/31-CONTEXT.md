# Phase 31: Add __tracebackhide__ = True module-level to all src/pytest_bdd/ modules - Context

**Gathered:** 2026-07-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Add `__tracebackhide__ = True` at the module level in every non-empty Python file under `src/pytest_bdd/` to hide library-internal implementation details from pytest tracebacks when user tests fail. Empty `__init__.py` files that only contain `__all__ = []` are excluded. Redundant function-level `__tracebackhide__` variables will be removed.

</domain>

<decisions>
## Implementation Decisions

### Module Scope
- **D-01:** Include all Python files and non-empty `__init__.py` files under `src/pytest_bdd/`, excluding empty `__init__.py` files that only contain `__all__ = []` and no code.
- **D-02:** Clean up existing redundant function-level `__tracebackhide__ = True` definitions (e.g. in `src/pytest_bdd/compatibility/pytest.py` and `src/pytest_bdd/plugin/pickle_runner/plugin/runner_plugin.py`) where module-level declarations are added.
- **D-03:** Do not add any explicit `__tracebackhide__ = False` overrides inside user-code invocation paths for now; let standard module-level hiding apply uniformly.

### Declaration Placement
- **D-04:** Declare `__tracebackhide__ = True` at the module level, below all imports, and before any classes, functions, or other constants.
- **D-05:** Apply standard spacing: one blank line after imports, and two blank lines before any functions or classes.

### Verification Strategy
- **D-06:** Write an integration test using the `testdir` fixture that runs a failing step and asserts that no `pytest_bdd` internal frames appear in the stdout traceback, but they DO appear when `--full-trace` is passed.
- **D-07:** Run the full test suite first, identify any traceback-checking tests that fail, and adjust them to either expect hidden frames or run with `--full-trace`.

### Automation Script
- **D-08:** Use a robust Python script using regex/string operations to locate insertion points and insert the declaration after imports, followed by ruff formatting to clean up spacing.
- **D-09:** Store the automation script in the local scratch directory under the active phase (not committed to the repository).

### the agent's Discretion
- The planner/executor decides the exact implementation details of the regex-based Python script.
- The planner decides the exact location and name of the integration test file.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements & Decisions
- `.planning/todos/add-tracebackhide-module-level.md` — Original task and context for module-level `__tracebackhide__`.
- `.planning/notes/tracebackhide-decision.md` — Decision record on traceback hiding and tradeoffs.

### Project Conventions & Structure
- `.planning/PROJECT.md` — Project context and constraints.
- `.planning/codebase/CONVENTIONS.md` — Established coding conventions.
- `.planning/codebase/STRUCTURE.md` — Source structure and file locations.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets & Existing Patterns
- There are already function-level `__tracebackhide__ = True` definitions in:
  - `src/pytest_bdd/compatibility/pytest.py` (inside the `fail` function)
  - `src/pytest_bdd/plugin/pickle_runner/plugin/runner_plugin.py` (various step/scenario invocation functions)
- Spacing must comply with Ruff rules (single blank line after imports, double blank lines before classes/functions).

### Integration Points
- All non-empty `.py` files under `src/pytest_bdd`.

</code_context>

<specifics>
## Specific Ideas

- No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 31-add-tracebackhide-true-module-level-to-all-src-pytest-bdd-mo*
*Context gathered: 2026-07-08*
