# Phase 30: Strict Module API & Import Rules — Research

**Written:** 2026-07-02
**Source todo:** `.planning/todos/pending/2026-07-01-strict-module-api-import-rules.md`

---

## Scope

Implement 12 custom Pylint rules (BLQ1501–BLQ1512) as a single `ModuleApiRulesChecker` class in
`src/pytest_bdd/_pylint/checkers/module_api_rules.py`. The checker enforces strict module export
discipline and import boundaries across `src/pytest_bdd/`, superseding the existing
BLQ1401–BLQ1404 `InitRulesChecker` in `init_rules.py`.

**Covered paths:** All `.py` files under `src/pytest_bdd/` except:
- `case` and `cases` paths (executable scenarios, fixtures, test cases)
- Script/tool/CLI entrypoint areas: `src/pytest_bdd/script/` and `src/pytest_bdd_toolchain/tool/`
- Default Pylint exclusion via `[tool.pylint.main] ignore-paths = [".*case.*"]`

**Out of scope:**
- `src/pytest_bdd_toolchain/` (except the test file `case/unit/test_pylint_checkers.py` where the
  new checker tests will be added)
- `_gherkin_go/` (go-parser bindings, generated/shared code)

---

## Current Architecture

### Pylint Plugin Structure

```
src/pytest_bdd/_pylint/
├── __init__.py          Plugin entrypoint — register() imports checkers, calls linter.register_checker()
└── checkers/
    ├── __init__.py      Package marker — __all__: list[str] = []
    ├── file_size_rules.py
    ├── init_rules.py    ← TO BE DELETED (BLQ1401–BLQ1404)
    ├── layer_rules.py
    ├── noqa_rules.py
    ├── plugin_patterns.py
    ├── quality_gates.py
    ├── responsibility_docs.py
    ├── test_import_rules.py
    ├── test_responsibility_docs.py
    └── typing_rules.py
```

### BaseChecker Pattern (from all existing checkers)

Every checker follows this pattern:

```python
from astroid import nodes
from pylint.checkers import BaseChecker

class ExampleChecker(BaseChecker):
    name = "example-rules"

    msgs = {
        "E9XXX": (
            "BLQXXXX: message with %s placeholders",
            "symbolic-name",
            "BLQXXXX: Short help description.",
        ),
    }

    def visit_assign(self, node: nodes.Assign) -> None:     # AST visitor
        filepath = node.root().file
        if not filepath or "excluded_path" in filepath:
            return
        # ... check logic ...
        self.add_message("symbolic-name", node=node, args=(arg1,))

    def visit_import(self, node: nodes.Import) -> None:     # another visitor
        ...
```

Key characteristics:
- Message code format: Pylint message ID `"E9NNN"` (E=error level), with `BLQXXXX` prefix in the message text
- Messages tuple: `(message_template, symbolic_name, help_description)`
- Symbolic names are used in `pyproject.toml` `[tool.pylint.messages_control].enable` lists
- Error-level codes start with `E9` prefix (existing ranges: E9001-E9003 quality, E9011-E9013 plugin, E9021-E9022 typing, E9031-E9032 file size, E9041-E9042 layer, E9051-E9054 init, E9061 test import, E9071-E9072 noqa, E9081-E9085 responsibility, E9091-E9094 test responsibility)
- Next available: `E9101` through `E9112` for BLQ1501–BLQ1512
- Visitors: `visit_module`, `visit_assign`, `visit_annassign`, `visit_import`, `visit_importfrom`, `visit_attribute`
- All checkers guard with pattern: `filepath = node.root().file; if not filepath: return`

### Plugin Registration (src/pytest_bdd/_pylint/__init__.py)

Current `register()` registers 10 checkers. Required changes:
1. Remove `InitRulesChecker` import and `register_checker()` call
2. Add `ModuleApiRulesChecker` import and `register_checker()` call
3. Update docstrings (references to "10 checkers" → "10 checkers", InitRulesChecker → ModuleApiRulesChecker)
4. The checkers/__init__.py stays unchanged (no imports needed, already `__all__ = []`)

### Pylint Configuration (pyproject.toml)

```toml
[tool.pylint.main]
ignore-paths = [".*case.*"]
load-plugins = ["pytest_bdd._pylint"]

[tool.pylint.messages_control]
disable = ["wildcard-import", "unused-wildcard-import", "useless-import-alias", "import-self", ...]
enable = ["empty-init", "redundant-import-alias", "init-code-required", "all-defined", ...]
```

The `enable` list currently has 18 symbols. After replacement:
- Remove: `"empty-init"`, `"redundant-import-alias"`, `"init-code-required"`, `"all-defined"` (BLQ1401–BLQ1404)
- Add: 12 new symbols for BLQ1501–BLQ1512

### Pre-commit Integration (.pre-commit-config.yaml)

```yaml
- id: pylint
  name: pylint-custom-rules
  entry: >-
    uv run --python 3.14 pylint
    src/pytest_bdd/
    src/pytest_bdd_toolchain/
  language: python
  additional_dependencies: ["uv"]
  types: [python]
  pass_filenames: false
```

Pylint loads the plugin via `pyproject.toml` `load-plugins`. No pre-commit config change needed.

---

## Rule Analysis

### BLQ1501: Every non-`__init__.py` module must define `__all__`

**Visitor:** `visit_module`
**Detection:** After the module body is parsed, scan `node.body` for assignments to `__all__`
(via `Assign`, `AnnAssign`). If no `__all__` found and not an `__init__.py`, emit.
**Edge cases:**
- Module with only imports and no `__all__` → violation
- Module with only a docstring → violation
- `__all__ = ()` (empty tuple) → acceptable (same as empty list)
- `__all__: list[str] = ["a"]` (annotated assign) → acceptable
- `__all__` defined conditionally (`if TYPE_CHECKING:`) → report anyway (encourage top-level)
- `__all__` via `list.append()` or `.extend()` → not detectable by AST, report
**Exclusions:** `__init__.py` files, `case/`, `script/`, `_gherkin_go/`

### BLQ1502: `__all__` must be a static list or tuple of unique string names

**Visitor:** `visit_assign`, `visit_annassign`
**Detection:** When `__all__` is found, inspect the value node:
- Must be `nodes.List` or `nodes.Tuple`
- Every element must be `nodes.Const` with `str` type
- Check for duplicates (set length < list length)
**Edge cases:**
- `__all__ = ["a", "a"]` → duplicate violation
- `__all__ = ["a", name]` → non-string violation
- `__all__ = some_function()` → not a list/tuple
- `__all__ = []` → OK (trivially unique and list)
- `__all__ = ("a", "b")` → OK (tuple, unique, strings)
**Exclusions:** `case/`, `script/`, `_gherkin_go/`

### BLQ1503: Every name in `__all__` must exist in the defining module

**Visitor:** `visit_module`
**Detection:** For modules with `__all__`, check each name against the module's top-level namespace. After visiting the full body (in `leave_module`), collect all top-level names (from `FunctionDef`, `AsyncFunctionDef`, `ClassDef`, `Assign`, `AnnAssign`, `Import`, `ImportFrom`). Compare `__all__` entries against collected names.
**Edge cases:**
- Names imported via `from x import y` → considered "in module" (bound in namespace)
- Names in `__all__` that are only in `if TYPE_CHECKING:` blocks → will not be detected, risk of false positive
- Private names in `__all__` (`_private_func`) → valid from checker perspective; separate convention
- Re-exports from `__init__.py` → handled by BLQ1505 separately
**Exclusions:** `case/`, `script/`, `_gherkin_go/`

### BLQ1504: Every `__init__.py` must define exactly `__all__ = []`

**Visitor:** `visit_module` (only for files named `__init__.py`)
**Detection:** If `__init__.py`, scan body for `__all__` assignment. Must be:
- Present (not missing)
- Assigned to an empty list `[]` (or empty tuple `()` or annotated `__all__: list[str] = []`)
**Edge cases:**
- `__all__ = []` → passes
- No `__all__` → violation
- `__all__ = ["a"]` → violation (non-empty)
- `__all__ = ()` → acceptable (empty tuple)
- `__all__: list[str] = []` → passes (annotated empty)
- `__all__` via `list()` (runtime call) → violation (not a literal)
**Exclusions:** `case/`, `script/`, `_gherkin_go/`

### BLQ1505: `__init__.py` must not re-export names from submodules

**Visitor:** `visit_importfrom` (in `__init__.py` files) + `visit_module`
**Detection:** In `__init__.py`, if there are `from .submodule import name` statements AND `__all__` contains those imported names (via BLQ1504/init-specific analysis), emit. More precisely: any `from .X import Y` in an `__init__.py` that results in `Y` appearing in the module's namespace AND `Y` is in `__all__` = re-export.
**Simpler approach:** In `__init__.py` files, forbid any `import`/`importfrom` that would add names beyond `__future__` imports. If `__all__ = []`, then no re-exports are happening — this is sufficient. Actually re-check: the rule says `__init__.py` must not re-export names from submodules. Since BLQ1504 enforces `__all__ = []`, this prevents re-exports through `__all__`. But `__init__.py` could still do `from .sub import Thing` without `Thing` in `__all__` — making `Thing` accessible as `pkg.Thing` but not declared in `__all__`. The intent is to prevent any form of re-export. So check for any `from .X import Y` where `Y` is not a private name (`_`) or `__future__` import.
**Edge cases:**
- `from .sub import _internal` → OK (private name, not public re-export)
- `from __future__ import annotations` → always allowed
- `import .sub` (no `from` clause) → this imports the submodule as attribute but doesn't pollute `__all__`; acceptable? The strict reading says no re-exports from submodules.
**Exclusions:** `case/`, `script/`, `_gherkin_go/`

### BLQ1506: Star imports are forbidden

**Visitor:** `visit_importfrom`
**Detection:** Check `node.names` for `("*", None)` pattern (star import).
**Overlap with Ruff:** Ruff F403 (`wildcard-import`) and F405 (`unused-wildcard-import`) handle star imports. However, the project disables these in pylint (`"wildcard-import"`, `"unused-wildcard-import"` disabled). Ruff F403 covers this — but only if the ruff rule is enabled. Check: ruff pyproject.toml select includes `"F"` (Pyflakes) which includes F403 and F405. So there IS overlap.

**Overlap resolution:** F403 is already handled by ruff. This rule is redundant if ruff F403 is active. However, the todo mandates BLQ1506 as a custom rule for consistency with the full 12-rule suite. Decision: implement BLQ1506 but document that ruff F403 already handles this for cases where ruff runs. The custom rule ensures coverage when only pylint runs.

### BLQ1507: Parent-relative imports using `..` are forbidden

**Visitor:** `visit_importfrom`
**Detection:** Check `node.level` — if > 1 (meaning `..` or more dots), emit. Also check `node.level == 1` with `node.modname` starting with `.` (redundant but explicit).
**Edge cases:**
- `from ..sibling import name` (level=2) → violation
- `from ...grandparent import name` (level=3) → violation
- `from . import module` (level=1) → NOT a violation (sibling import, allowed)
- `from .module import name` (level=1) → NOT a violation for this rule (handled by BLQ1508/BLQ1509)
- `import os` (level not applicable for `Import` node) → NOT relevant
**Exclusions:** `case/`, `script/`, `_gherkin_go/`

### BLQ1508: Sibling modules must be imported with explicit one-dot relative imports

**Visitor:** `visit_import`, `visit_importfrom`
**Detection:** When importing from the same package:
- For `visit_importfrom`: if source module's package path matches import's resolved package, require `node.level >= 1` (relative). If `node.level == 0` (absolute), emit.
- For `visit_import`: `import pytest_bdd.X.Y` should be `from . import Y` or `from .Y import ...` within the same hierarchy.
- Resolve "sibling": two modules are siblings if they share the same parent package and are at the same depth.
**Edge cases:**
- Module `pytest_bdd.model.scenario_run` importing `pytest_bdd.model.run` → should use `from .run import ...`
- Module `pytest_bdd.model.scenario_run` importing `pytest_bdd.steps.registry` → NOT a sibling (different parent package), absolute import is fine
- Standard library / third-party imports → never siblings, skip
**Exclusions:** `case/`, `script/`, `_gherkin_go/`, imports from outside `pytest_bdd`

### BLQ1509: Prefer `from . import module` over `from .module import name`

**Visitor:** `visit_importfrom`
**Detection:** For relative imports at level 1 (`from .`):
- `from . import module` → OK (module-level import)
- `from .module import name` → warn (prefer the form above)
**Rationale:** Module-level imports make provenance clear and prevent "bypass" of `__all__`. When you do `from .module import name`, you bypass the module's declared API surface.
**Edge cases:**
- `from .module import name1, name2` → warn (multiple names imported from sibling, bypasses `__all__`)
- `from . import module as alias` → OK (still module-level)
- `from ._private_module import _name` → warn? For now, warn consistently — the rule applies to all relative sibling imports.
**Exclusions:** `case/`, `script/`, `_gherkin_go/`

### BLQ1510: Imported names from local modules must exist in the source module's `__all__`

**Visitor:** `visit_importfrom` (relative level=1)
**Detection:** For `from .module import name1, name2`:
1. Resolve `module` to a file path (e.g., `from .registry import get_registry` → find `registry.py` in current directory)
2. Parse or AST-inspect `module` to extract its `__all__` names
3. Check each imported `name` is in `module.__all__`
**Challenge:** Requires cross-file analysis. Pylint runs per-file by default. Options:
  - Use `astroid.MANAGER.ast_from_module_name()` to load sibling module AST
  - Use a lightweight regex/text scan on the sibling `.py` file to extract `__all__` (fragile)
  - Store module `__all__` data during `visit_module` in a shared dict keyed by module path (requires `leave_module` or per-file cache)
  - Skip this rule if cross-file analysis is infeasible — defer to BLQ1501 enforcement that ensures `__all__` exists
**Risk:** High implementation complexity. The `astroid` `MANAGER.ast_from_module_name` approach may trigger cascading imports. The safe approach is to inspect the target file's AST by loading it from disk path resolution.
**Edge cases:**
- Sibling module has no `__all__` → BLQ1501 should have already caught this; for BLQ1510, treat as violation (importing from module with no declared API)
- Import from `__init__.py` sibling → `__init__.py` has `__all__ = []` by BLQ1504, so any `from . import name` where `name` is a submodule is fine
**Exclusions:** `case/`, `script/`, `_gherkin_go/`

### BLQ1511: Attribute access through imported local modules must target names in `__all__`

**Visitor:** `visit_attribute`
**Detection:** When code does `module.something`:
1. Check if `module` is a name imported via `from . import module` (a sibling module reference)
2. Check if `something` is in `module.__all__`
3. If not, emit
**Challenge:** Requires tracking which local names are sibling module imports (data flow from import visitors to attribute visitor). Requires cross-file `__all__` inspection like BLQ1510.
**Edge cases:**
- `module._private_api()` → warn (accessing non-`__all__` attribute)
- `module.public_function()` → OK
- `module.something.nested` → check first level (`something`) against `__all__`
- Attribute access on non-module objects (dicts, classes, etc.) → skip (only check known imported module references)
- `getattr(module, "dynamic")` → not detectable, skip
**Exclusions:** `case/`, `script/`, `_gherkin_go/`

### BLQ1512: Same-hierarchy modules must use sibling/local import form, not absolute

**Visitor:** `visit_import`, `visit_importfrom`
**Detection:** Very similar to BLQ1508 but broader — captures cases where the imported module shares a common ancestor package beyond immediate parent.
- For module `pytest_bdd.model.run.context`, importing `pytest_bdd.model.run.lifecycle` → should use `from .lifecycle import ...` not absolute
- The rule detects "same hierarchy path" = shared prefix at the `src/pytest_bdd/` level
**Edge cases:**
- Overlaps significantly with BLQ1508. `BLQ1508` = immediate sibling (same parent), `BLQ1512` = any shared hierarchy within `pytest_bdd`.
- Could be merged with BLQ1508 as one rule with two cases, but spec requires separate rules.
- `from pytest_bdd.model import run` when in `pytest_bdd.steps` → OK (different hierarchy)
- `from pytest_bdd.model.scenario_run import Run` when in `pytest_bdd.model.run.lifecycle` → warn (should be `from ..scenario_run import Run`)
**Exclusions:** `case/`, `script/`, `_gherkin_go/`

### Rule Code Allocation

| Rule | Pylint ID | Symbolic Name |
|------|-----------|---------------|
| BLQ1501 | E9101 | `missing-all-exports` |
| BLQ1502 | E9102 | `invalid-all-format` |
| BLQ1503 | E9103 | `all-name-missing` |
| BLQ1504 | E9104 | `init-all-required` |
| BLQ1505 | E9105 | `init-reexport` |
| BLQ1506 | E9106 | `forbidden-star-import` |
| BLQ1507 | E9107 | `forbidden-parent-import` |
| BLQ1508 | E9108 | `sibling-import-form` |
| BLQ1509 | E9109 | `prefer-module-import` |
| BLQ1510 | E9110 | `import-name-not-in-all` |
| BLQ1511 | E9111 | `attribute-not-in-all` |
| BLQ1512 | E9112 | `same-hierarchy-import` |

---

## Module Inventory

### Files with `__all__` (27 found by grep)

All are in-scope `__init__.py` files except:
- `src/pytest_bdd/__init__.py` — `__all__: list[str] = [` (non-empty, public API package — excluded from BLQ1504 because `pytest_bdd/__init__.py` IS the public API facade)
- `src/pytest_bdd/plugin/allure_formatter/converter/__init__.py` — `__all__ = ["convert"]` (non-empty, re-export)
- `src/pytest_bdd/plugin/pickle_runner/plugin.py` — `__all__ = ["PickleRunner", "PickleRunnerPlugin"]` (only non-init module with `__all__`)
- `src/pytest_bdd/plugin/pickle_runner/plugin/__init__.py` — `__all__ = ["PickleRunner", "PickleRunnerPlugin"]` (non-empty init)
- `src/pytest_bdd/scenario_locator/__init__.py` — `__all__: list[str] = [` (non-empty)

### Files missing `__all__` (non-init modules)

Approximately 80+ non-`__init__.py` modules under `src/pytest_bdd/` are missing `__all__`. Key examples:
- `scenario.py`, `parser.py`, `collector.py`, `collector_batch.py`, `utils.py`, `hook.py`, `feature_locator.py`, `const.py`, `mimetype.py`, `tag_expression.py`
- All `compatibility/*.py` (8+ files)
- All `util/*.py` (15+ files)
- All `model/*.py` (multiple, e.g., `scenario_run.py`, `stash_access.py`, `message_converter.py`)
- All `plugin/**/*.py` (except `pickle_runner/plugin.py`) — ~50+ files
- All `steps/*.py` (registry.py, matcher.py, manager.py, definition.py, decorators.py)
- All `parsers/*.py`
- All `scenario_locator/*.py` (file_locator.py, url_locator.py, base.py)
- All `script/*.py` (excluded from rule)
- All `message_stream_validation/*.py`

### Scope Exclusions Detail

**Case paths (excluded):**
- `src/pytest_bdd_toolchain/case/` — all contents excluded
- Any path containing `/case/` or `/cases/`

**Script/CLI paths (excluded):**
- `src/pytest_bdd/script/` and all subdirectories
- `src/pytest_bdd_toolchain/tool/`

**Pylint's own `ignore-paths` already excludes case patterns:**
```toml
ignore-paths = [".*case.*"]
```

Additional per-module exclusions may be needed for:
- `src/pytest_bdd/__init__.py` — the root package init IS the public API, so BLQ1504 (empty `__all__`) should not apply; this file should have `__all__` with actual public names. Yet BLQ1504 mandates `__all__ = []` for ALL `__init__.py`. This is a conflict — the root package's `__init__.py` serves as the library's public API surface. **Resolution:** Either exempt `src/pytest_bdd/__init__.py` from BLQ1504, or define a custom "root package" exception.

---

## Overlap Analysis

### With Built-in Pylint Rules

| Custom Rule | Pylint Built-in | Overlap? | Why Custom Is Needed |
|-------------|----------------|----------|---------------------|
| BLQ1506 (star imports) | `wildcard-import` (W0401) | **Full** | Pylint's wildcard-import is disabled in pyproject.toml. Ruff F403 handles this. Custom rule needed for consistency within BLQ15xx suite during pylint-only runs. |
| BLQ1507 (parent imports) | None | **None** | No existing rule checks for `..` relative imports. |
| BLQ1512 (same-hierarchy) | None | **None** | No existing rule checks absolute-vs-relative sibling imports. |

### With Ruff Rules

| Custom Rule | Ruff Rule | Overlap? | Why Custom Is Needed |
|-------------|-----------|----------|---------------------|
| BLQ1501–BLQ1505 (`__all__` rules) | None | **None** | Ruff has no `__all__` enforcement rules. |
| BLQ1506 (star imports) | F403 (`wildcard-import`) | **Full** | Ruff already catches this. Custom rule is redundant but required by spec for pylint-only coverage. |
| BLQ1507 (parent imports) | None | **None** | No existing ruff rule. |
| BLQ1508/BLQ1512 (import form) | None | **None** | No existing ruff rule for relative-vs-absolute preference. |
| BLQ1509 (import style) | None | **None** | No existing rule. |
| BLQ1510/BLQ1511 (cross-module validation) | None | **None** | Cross-file analysis beyond ruff's scope. |

### With Existing Custom Rules (BLQ14xx)

| BLQ15xx | BLQ14xx | Relationship |
|---------|---------|-------------|
| BLQ1501 | BLQ1401 | BLQ1401 forbade `__all__` in non-init files. **BLQ1501 reverses that**: requires `__all__` in non-init files. This is the core philosophical shift — from "no `__all__` outside init" to "every module must declare its API." |
| BLQ1504 | BLQ1402/BLQ1403 | BLQ1402/1403 forbid empty/docstring-only `__init__.py` files. BLQ1504 requires `__all__ = []`. Compatible but stricter. |
| BLQ1505 | BLQ1403 (non-empty `__all__`) | BLQ1403 already required `__all__ = []`. BLQ1505 adds the re-export check. |

BLQ1404 (redundant import aliases) is handled by ruff's `useless-import-alias` + pylint's disabled `useless-import-alias`. Not carried forward to BLQ15xx.

---

## Risk Assessment

### High Risk

1. **BLQ1510 (cross-file `__all__` validation):** Requires loading AST of sibling modules during lint. Risks:
   - Circular import problems when astroid resolves sibling modules
   - Performance: parsing ~50+ sibling modules for every `visit_importfrom`
   - **Mitigation:** Cache parsed `__all__` data in a class-level dict keyed by resolved file path. Use `astroid.MANAGER.ast_from_file()` with error handling. Skip if file can't be parsed.

2. **BLQ1511 (attribute access tracking):** Requires maintaining a name-to-module mapping across visitor calls. Risks:
   - False positives on non-module objects with same name
   - False negatives on dynamic attribute access
   - **Mitigation:** Track only names imported via `from . import module` (which creates module references). Use a set of "known module names" populated during `visit_import`/`visit_importfrom`.

3. **~80+ module `__all__` additions:** Manual audit of every non-init module to determine its public API. Risks:
   - Incorrect `__all__` listings that miss re-exported names
   - Private names accidentally exposed
   - **Mitigation:** Automated script to suggest `__all__` based on AST analysis of top-level names; manual review required for final approval.

### Medium Risk

4. **`__init__.py` re-export blockage (BLQ1505):** Existing `__init__.py` files like `allure_formatter/converter/__init__.py` (`__all__ = ["convert"]`) will need to be refactored. Options:
   - Move the re-exported function to the `__init__.py` itself
   - Create a dedicated facade module
   - Accept the breakage and document that the import path changes

5. **Root package `__init__.py` conflict:** `src/pytest_bdd/__init__.py` serves as the library's public API. BLQ1504 says it must have `__all__ = []` but that would hide all public names. **Resolution needed:** exempt root package init from BLQ1504, or define special handling.

### Low Risk

6. **Pre-commit hook compatibility:** No changes needed to `.pre-commit-config.yaml` — pylint already loads the plugin via pyproject.toml.
7. **Test infrastructure:** Existing test pattern (`test_pylint_checkers.py`) works via subprocess invocation. New tests follow identical pattern.
8. **Rule overlap with BLQ14xx:** Clear replacement — delete `init_rules.py`, update plugin registration. No ambiguity.

---

## Recommendations

### Implementation Order

1. **Delete `init_rules.py`** and update `_pylint/__init__.py` registration (remove InitRulesChecker, add placeholder for ModuleApiRulesChecker)
2. **Create `module_api_rules.py`** with checker skeleton (name, msgs dict, empty visitors)
3. **Implement simplest rules first:** BLQ1506 (star imports), BLQ1507 (parent imports), BLQ1501 (missing `__all__`)
4. **Implement `__all__` format rules:** BLQ1502 (format check), BLQ1503 (name existence)
5. **Implement init rules:** BLQ1504 (empty `__all__`), BLQ1505 (no re-export)
6. **Implement import form rules:** BLQ1508 (sibling form), BLQ1509 (module-level prefer), BLQ1512 (hierarchy form)
7. **Implement cross-file rules last:** BLQ1510 (name in `__all__`), BLQ1511 (attribute in `__all__`)
8. **Add all 12 symbols to pyproject.toml enable list**
9. **Add all 55+ `__all__` declarations** to source modules
10. **Write tests** in `src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py`
11. **Verify with `pre-commit run --all-files`**

### Checker Architecture Decision

Use a single `ModuleApiRulesChecker` class (not multiple checker classes). Rationale:
- All 12 rules share scope exclusions, filepath guards, and module resolution logic
- A single `visit_module` can collect `__all__` data once for use by BLQ1501/BLQ1502/BLQ1503/BLQ1504
- Cross-file `__all__` cache (for BLQ1510/BLQ1511) is shared state — cleaner in one class
- Matches existing pattern: `InitRulesChecker` handles 4 rules; `QualityGatesChecker` handles 3 rules
- Reducing class count from 10 to 10 (remove InitRulesChecker, add ModuleApiRulesChecker)

### `__all__` Population Strategy

**Automated first pass:** Script that:
1. Walks `src/pytest_bdd/` (excluding `case/`, `script/`, `_gherkin_go/`)
2. For each non-init `.py` file, parses AST to extract top-level names (functions, classes, constants)
3. Generates candidate `__all__ = [...]` with all public names (excluding `_`-prefixed)
4. Writes to a review file for manual curation

**Manual curation needed for:**
- Re-exported names (from sibling imports)
- Semi-private names used by test infrastructure
- Plugin modules where public API is the plugin class + entrypoint/hook functions

### Exemptions to Define

| Path/Pattern | Exempted From | Reason |
|-------------|---------------|--------|
| `src/pytest_bdd/__init__.py` | BLQ1504 | Root package init IS the public API facade |
| `src/pytest_bdd/_pylint/**/*.py` | All BLQ1501–BLQ1512 | Pylint plugin code is tooling, not library surface |
| `src/pytest_bdd/script/**/*.py` | All rules | CLI scripts and tooling |
| `src/pytest_bdd/_gherkin_go/*.py` | All rules | Go parser bindings |
| `src/pytest_bdd/compatibility/*.py` | BLQ1508, BLQ1509 | Compatibility shims often need special import patterns |
| `case`, `cases` paths | All rules | Test fixtures and scenarios |

### Performance Considerations

- BLQ1510/BLQ1511 cross-file analysis: Use an in-memory LRU cache (max 200 entries) to avoid re-parsing sibling modules
- The astroid module manager's `ast_from_module_name()` can be memoized
- For files without `__all__` (pre-BLQ1501 fix), BLQ1510/BLQ1511 should emit warnings rather than errors initially
- Consider making cross-file rules (BLQ1510, BLQ1511) opt-in or initially warning-level until all modules have `__all__`

---

*Research completed: 2026-07-02*
*Next: Phase 30 planning (`30-PLAN.md`) based on these findings*
