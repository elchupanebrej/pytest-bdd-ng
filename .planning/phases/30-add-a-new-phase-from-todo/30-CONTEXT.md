# Phase 30: Strict Module API & Import Rules - Context

**Gathered:** 2026-07-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement 12 custom Pylint rules (BLQ1501-BLQ1512) that enforce strict module export discipline and import boundaries across the `src/pytest_bdd/` source tree. Every non-`__init__.py` module must declare a public API via `__all__`, sibling imports must use explicit relative paths, and `__init__.py` must define `__all__ = []` with no re-exports.

This phase supersedes the existing BLQ1401-BLQ1404 InitRulesChecker — the new checker replaces it entirely.

Scope covers all source modules under `src/pytest_bdd/` except `case`/`cases` paths and script/tool/CLI entrypoint areas. Rollout is strict with no legacy allowlist.
</domain>

<decisions>
## Implementation Decisions

### Phase Identity
- **D-01:** Phase 30 is a single focused phase implementing the Strict Module API and Import Custom Pylint Rules todo (`2026-07-01-strict-module-api-import-rules.md`). No multi-todo bundle.
- **D-02:** The full 12-rule spec from the todo document is authoritative — downstream agents must implement all 12 rules as defined.

### Rollout Strategy
- **D-03:** Fix all violations at once — one coordinated sweep across all ~50+ source modules. No phased sub-plans.
- **D-04:** No legacy allowlist. Every module must pass the new rules before the phase is complete. Any existing violation must be fixed, not exempted.

### Relationship to Existing Rules
- **D-05:** The new 12-rule checker supersedes BLQ1401-BLQ1404 (init_rules.py). Remove InitRulesChecker from the pylint plugin registration, delete init_rules.py, and remove its associated unit tests.
- **D-06:** Rule code range: BLQ1501-BLQ1512 — new range, clean separation from replaced BLQ14xx codes.

### Rule Definitions (from todo document)
- **D-07:** Rule 1 (BLQ1501): Every non-`__init__.py` module must define a top-level `__all__`.
- **D-08:** Rule 2 (BLQ1502): `__all__` must be a static list or tuple of unique string names.
- **D-09:** Rule 3 (BLQ1503): Every name in `__all__` must exist in the defining module.
- **D-10:** Rule 4 (BLQ1504): Every `__init__.py` must define exactly `__all__ = []`.
- **D-11:** Rule 5 (BLQ1505): `__init__.py` must not re-export names from submodules.
- **D-12:** Rule 6 (BLQ1506): Star imports (`from x import *`) are forbidden.
- **D-13:** Rule 7 (BLQ1507): Parent-relative imports using `..` are forbidden.
- **D-14:** Rule 8 (BLQ1508): Sibling modules must be imported with explicit one-dot relative imports.
- **D-15:** Rule 9 (BLQ1509): Prefer `from . import module` over `from .module import name` for sibling imports.
- **D-16:** Rule 10 (BLQ1510): Imported names from local modules must exist in the source module's `__all__`.
- **D-17:** Rule 11 (BLQ1511): Attribute access through imported local modules must target names present in the source module's `__all__`.
- **D-18:** Rule 12 (BLQ1512): If a module is in the same hierarchy path, enforce the sibling/local import form instead of absolute package import.

### Scope Exclusions
- **D-19:** `case` and `cases` paths are excluded — these are executable scenarios, fixtures, and test cases.
- **D-20:** Script-like files and packages (script/tool/CLI entrypoint areas) are excluded from the initial strict rollout.

### Acceptance Criteria
- **D-21:** Register the new checker in `src/pytest_bdd/_pylint/__init__.py` and remove InitRulesChecker.
- **D-22:** Unit tests covering passing and failing examples for each of the 12 rules.
- **D-23:** `pre-commit run --all-files` fails on violations and passes after all fixes.
- **D-24:** Rule messages have stable symbolic names (BLQ1501-BLQ1512) and clear remediation text.
- **D-25:** Implementation must document why any overlap with built-in Pylint/Ruff rules is not sufficient.

### the agent's Discretion
- The planner decides exact checker class name and file location (e.g., `module_api_rules.py` alongside existing checkers).
- The planner decides implementation order among the 12 rules and whether to combine multiple rules into one checker class.
- The planner decides how to handle the ~50+ module `__all__` additions — automated script or manual edits.
- The planner may choose to implement the 12 rules across one or multiple checker classes as long as all are registered.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/todos/pending/2026-07-01-strict-module-api-import-rules.md` — Full 12-rule specification, acceptance criteria, scope exclusions, and strict rollout mandate. **This is the primary requirements document.**

### Existing Pylint Infrastructure
- `src/pytest_bdd/_pylint/__init__.py` — Plugin entrypoint registering all 10 checker classes. Must be updated to add new checker and remove InitRulesChecker.
- `src/pytest_bdd/_pylint/checkers/init_rules.py` — Existing BLQ1401-BLQ1404 checker to be **replaced** (superseded, not modified).
- `src/pytest_bdd/_pylint/checkers/` — Directory of existing checkers; new checker should follow same pattern (`BaseChecker` subclass, message definitions, `visit_*` methods).

### Project Conventions
- `.planning/PROJECT.md` — Project constraints: ruff rules, attrs over dataclass, StashBound pattern.
- `.pre-commit-config.yaml` — Pre-commit hook configuration where the new checker must be integrated.
- `pyproject.toml` — Pylint configuration, rugff rules, and per-file ignores that may need updates.

### Prior Phase Context
- `.planning/phases/20-multiple-refactorings/` — Phase 20 established the pylint plugin architecture, `__init__.py` hygiene, and responsibility documentation patterns.
- `.planning/phases/29-cck-closure/29-CONTEXT.md` — Phase 29 deferred the Strict Module API todo to Phase 30.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Pylint checker pattern: All existing checkers extend `BaseChecker`, define `name`, `msgs` dict, and implement `visit_*`/`leave_*` AST visitor methods. The new checker should follow this exact pattern.
- Plugin registration: `src/pytest_bdd/_pylint/__init__.py` `register()` function imports checker classes and calls `linter.register_checker()`. Add new checker here, remove `InitRulesChecker`.
- Test patterns: Existing checker tests use pytest with Pylint's `testutils` for creating test modules and verifying messages. Look at `test_import_rules.py` and `test_responsibility_docs.py` for examples.
- Pre-commit integration: `.pre-commit-config.yaml` runs pylint with `--load-plugins=pytest_bdd._pylint` via repo-local hook.

### Established Patterns
- Message codes use `BLQ` prefix with 4-digit numbers grouped by domain (BLQ9xx = quality gates, BLQ10xx = plugins, BLQ11xx = typing, BLQ12xx = file size, BLQ13xx = layers, BLQ14xx = init rules, BLQ15xx = module API, BLQ16xx = test imports, BLQ17xx = noqa).
- Checker files contain explicit architectural metadata in docstrings (Responsibility, Delegates, Cohesion, Separation sections).
- Responsibility documentation is standard across the codebase — new checker must include full docstring with these sections.
- Custom rules are preferred over built-in Pylint/Ruff equivalents when project-specific semantics differ. Implementation must document why.

### Integration Points
- `src/pytest_bdd/_pylint/__init__.py` — Add new checker import + `register_checker()` call; remove InitRulesChecker import + call.
- `src/pytest_bdd/_pylint/checkers/` — New file (e.g., `module_api_rules.py`) alongside existing checkers.
- `pyproject.toml` — Pylint configuration section; may need per-file ignore updates for excluded paths (case/, scripts/).
- `.pre-commit-config.yaml` — No changes needed if pylint invocation already loads the full plugin.
- ~50+ source modules in `src/pytest_bdd/` — Each lacking `__all__` must be updated with the correct public API list.

</code_context>

<specifics>
## Specific Ideas

### 12 Rules (from todo document)
1. Every non-`__init__.py` module must define a top-level `__all__`
2. `__all__` must be a static list or tuple of unique string names
3. Every name in `__all__` must exist in the defining module
4. Every `__init__.py` must define exactly `__all__ = []`
5. `__init__.py` must not re-export names from submodules
6. Star imports are forbidden
7. Parent-relative imports using `..` are forbidden
8. Sibling modules must be imported with explicit one-dot relative imports
9. Prefer `from . import module` over `from .module import name`
10. Imported names from local modules must exist in source module's `__all__`
11. Attribute access through imported local modules must target `__all__` names
12. Same-hierarchy modules must use sibling/local import form, not absolute

### Scope Exclusions (from todo document)
- `case` and `cases` paths (executable scenarios, fixtures, test cases)
- Script-like files and packages (script/tool/CLI entrypoint areas) — initial strict rollout
</specifics>

<deferred>
## Deferred Ideas

### Pending Todos (not selected for this phase)
- Improve library typing using best practices from awesome-python-typing — separate phase candidate
- No TestClasses are allowed in tests — enforce via ruff rule — separate phase candidate
- Expand feature tests for undocumented behaviors — separate phase candidate
- Split xdist-remote tests into separate parallel GHA executor job — infrastructure phase
- Gather failed CI logs into workflow artifact — infrastructure phase
- Remove __init__.py usage and unify ruff rules project layout — potentially overlapping with this phase, defer until BLQ15xx complete
- Create custom pylint rule for noqa without reason — a BLQ17xx noqa_rules.py already exists; review if already covered

</deferred>

---

*Phase: 30-Strict Module API & Import Rules*
*Context gathered: 2026-07-02*
