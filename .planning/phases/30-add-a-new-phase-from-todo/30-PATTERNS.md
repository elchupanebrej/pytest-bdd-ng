# Phase 30: Strict Module API & Import Rules — Pattern Mapping

**Written:** 2026-07-02
**Source:** 30-CONTEXT.md + 30-RESEARCH.md

---

## Files to Create/Modify

### 1. CREATE: `src/pytest_bdd/_pylint/checkers/module_api_rules.py`

**Role:** New checker implementing all 12 BLQ1501–BLQ1512 rules as a single `ModuleApiRulesChecker` class.

**Data flow:**
```
Pylint AST traversal → ModuleApiRulesChecker.visit_* methods
    → filepath guard (exclude case/, script/, _gherkin_go/)
    → per-rule AST inspection
    → self.add_message("symbolic-name", node=node, args=(...))
```

**Closest analog:** `src/pytest_bdd/_pylint/checkers/init_rules.py` (to be deleted/replaced)

**Concrete excerpt from init_rules.py (`src/pytest_bdd/_pylint/checkers/init_rules.py:86-183`):**

```python
class InitRulesChecker(BaseChecker):
    name = "init-rules"

    msgs = {
        "E9051": (
            "BLQ1401: %s defines __all__ outside __init__.py. Remove __all__ list entirely.",
            "all-defined",
            "BLQ1401: Defining __all__ in non-__init__.py files is forbidden.",
        ),
        "E9052": (
            "BLQ1402: %s is empty or metadata-only. Delete this file (PEP 420).",
            "empty-init",
            "BLQ1402: Empty or metadata-only __init__.py files must be deleted.",
        ),
        # ... more messages
    }

    def visit_assign(self, node: nodes.Assign) -> None:
        filepath = node.root().file
        if not filepath or "pytest_bdd_toolchain" in filepath:
            return
        # ... check logic ...
```

**What needs to change:**
- Use message IDs `E9101`–`E9112` (next available range after E9071 for BLQ1601, E9081 for BLQ9xx responsibility, E9091 for BLQ920 test-responsibility)
- Symbolic names: `missing-all-exports`, `invalid-all-format`, `all-name-missing`, `init-all-required`, `init-reexport`, `forbidden-star-import`, `forbidden-parent-import`, `sibling-import-form`, `prefer-module-import`, `import-name-not-in-all`, `attribute-not-in-all`, `same-hierarchy-import`
- Filepath guard: exclude `case/`, `script/`, `_gherkin_go/` (no toolchain exclusion — these live in `src/pytest_bdd/`)
- `visit_module` collects `__all__` data + handles BLQ1501, BLQ1503, BLQ1504, BLQ1505
- `visit_assign` / `visit_annassign` handle BLQ1502 (format check on `__all__` value)
- `visit_importfrom` handles BLQ1506 (star imports), BLQ1507 (parent-relative), BLQ1508 (sibling form), BLQ1509 (prefer module import), BLQ1510 (names in __all__)
- `visit_import` handles BLQ1508 (sibling form for `import` statements)
- `visit_attribute` handles BLQ1511 (attribute access through imported modules)
- `visit_importfrom` handles BLQ1512 (same-hierarchy import form)
- Cross-file cache (dict with LRU) for BLQ1510/BLQ1511 sibling module `__all__` parsing
- Include full architectural docstring with Responsibility, Reason for existence, Delegates, Cohesion, Separation, Main consumers, State and side effects, Invariants, Architecture score sections
- Include `# init: allow` classification comment at top
- Include `from __future__ import annotations`

**Additional analog for cross-file resolution:** `src/pytest_bdd/_pylint/checkers/test_import_rules.py` (`src/pytest_bdd/_pylint/checkers/test_import_rules.py:258-342`) — `resolve_import_to_path()` function performs filesystem module resolution, similar pattern needed for BLQ1510/BLQ1511:

```python
def resolve_import_to_path(module_path: str) -> Path | None:
    if not module_path:
        return None
    parts = module_path.split(".")
    search_roots = [Path("src").resolve()]
    for p in get_test_paths():
        search_roots.append(Path(p).resolve())
        # ... subdirectory scanning ...
    for root in unique_roots:
        candidate_file = root.joinpath(*parts).with_suffix(".py")
        if candidate_file.is_file():
            return candidate_file
        # ...
    return None
```

---

### 2. MODIFY: `src/pytest_bdd/_pylint/__init__.py`

**Role:** Plugin entrypoint — update checker registration.

**Data flow:**
```
pylint loads plugin → register(linter) called → linter.register_checker(Checker(linter)) for all 10 checkers
```

**Closest analog:** Same file (current state), `src/pytest_bdd/_pylint/__init__.py:72-81`:

```python
from .checkers.init_rules import InitRulesChecker
```

```python
linter.register_checker(InitRulesChecker(linter))
```

**What needs to change:**
1. Remove import line: `from .checkers.init_rules import InitRulesChecker`
2. Add import line: `from .checkers.module_api_rules import ModuleApiRulesChecker`
3. Remove registration call: `linter.register_checker(InitRulesChecker(linter))`
4. Add registration call: `linter.register_checker(ModuleApiRulesChecker(linter))`
5. Update docstrings: all references to "10 checkers" → stays "10 checkers" (remove one, add one)
6. Update Responsibility docstring: replace InitRulesChecker references with ModuleApiRulesChecker
7. Update Delegates section: `InitRulesChecker` → `ModuleApiRulesChecker`; rule ranges `BLQ1401-BLQ1404` → `BLQ1501-BLQ1512`
8. Update `register()` docstring: same docstring updates
9. Checker count stays at 10 (9 existing + 1 new, minus 1 deleted = 10)

---

### 3. DELETE: `src/pytest_bdd/_pylint/checkers/init_rules.py`

**Role:** Superseded by module_api_rules.py. Remove file entirely.

**Closest analog:** N/A — this is a deletion.

**What needs to change:**
- Delete the file (it's at `src/pytest_bdd/_pylint/checkers/init_rules.py`)
- BLQ1401-BLQ1404 are fully replaced by BLQ1501-BLQ1505

---

### 4. MODIFY: `src/pytest_bdd/_pylint/checkers/__init__.py`

**Role:** Package marker for checkers subpackage. No functional changes needed.

**Closest analog:** Same file, `src/pytest_bdd/_pylint/checkers/__init__.py:57-60`:

```python
from __future__ import annotations

__all__: list[str] = []
```

**What needs to change:**
- No changes needed. Already has `__all__ = []` and is a pure package marker.
- The docstring will naturally become accurate after init_rules.py is deleted (it was only referenced as a sibling module, not imported here).

---

### 5. MODIFY: `pyproject.toml`

**Role:** Update pylint messages_control enable/disable lists.

**Closest analog:** Same file, `pyproject.toml:330-447`:

```toml
[tool.pylint.messages_control]
disable = [
  # ...
  "wildcard-import",
  "unused-wildcard-import",
  "useless-import-alias",
  "import-self",
  # ...
]
enable = [
  # ...
  "empty-init",
  "redundant-import-alias",
  "init-code-required",
  "all-defined",
  "test-import-outside-cases",
  # ...
]
```

**What needs to change:**

In `[tool.pylint.messages_control].enable`:
1. **Remove** 4 BLQ14xx symbols: `"empty-init"`, `"redundant-import-alias"`, `"init-code-required"`, `"all-defined"`
2. **Add** 12 BLQ15xx symbols:
   - `"missing-all-exports"` (BLQ1501)
   - `"invalid-all-format"` (BLQ1502)
   - `"all-name-missing"` (BLQ1503)
   - `"init-all-required"` (BLQ1504)
   - `"init-reexport"` (BLQ1505)
   - `"forbidden-star-import"` (BLQ1506)
   - `"forbidden-parent-import"` (BLQ1507)
   - `"sibling-import-form"` (BLQ1508)
   - `"prefer-module-import"` (BLQ1509)
   - `"import-name-not-in-all"` (BLQ1510)
   - `"attribute-not-in-all"` (BLQ1511)
   - `"same-hierarchy-import"` (BLQ1512)

Total enable count: 18 - 4 + 12 = 26 symbols

In `[tool.pylint.messages_control].disable`:
- No changes needed. `"wildcard-import"`, `"unused-wildcard-import"`, `"useless-import-alias"`, `"import-self"` remain disabled.

In `[tool.ruff.lint.per-file-ignores]`:
- May need to add per-file excludes for `case/`, `script/`, and `_gherkin_go/` paths in the checker's own filepath guard (not in pyproject.toml).
- The `"src/pytest_bdd/_pylint/checkers/*"` ignore entry already covers the new checker file with broad ignores — no pyproject.toml change needed for this.

---

### 6. CREATE: Test entries in `src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py`

**Role:** Unit tests for all 12 new rules.

**Data flow:**
```
pytest runs test function → _write(tmp_path / name, content) creates temp .py file
    → _run_pylint(path, *symbols) runs pylint subprocess with --load-plugins=pytest_bdd._pylint
    → assert result.returncode != 0 + assert "BLQ15XX" in result.stdout
```

**Closest analog:** `src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py:154-160` (test_import_rules test):

```python
def test_test_import_checker_reports_imports_outside_allowed_cases_path(tmp_path: Path) -> None:
    target = _write(tmp_path / "sample.py", "from pytest_bdd_toolchain.e2e import test_e2e\n")
    result = _run_pylint(target, "test-import-outside-cases")
    assert result.returncode != 0
    assert "BLQ1601" in result.stdout
```

**Also analog:** `src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py:124-142` (init_rules test — **this test function should be DELETED**):

```python
def test_init_checker_reports_all_namespace_package_rules(tmp_path: Path) -> None:
    package_init = _write(tmp_path / "pkg" / "__init__.py", '"""Package only."""\n')
    exports = _write(tmp_path / "exports.py", "__all__ = ['name']\nimport os as os\n")
    init_all_empty = _write(tmp_path / "pkg_empty_all" / "__init__.py", "__all__ = []\n")
    init_all_nonempty = _write(tmp_path / "pkg_nonempty_all" / "__init__.py", "__all__ = ['name']\n")
    # ... assertions for BLQ1401-BLQ1404 ...
```

**What needs to change:**
1. **Delete** `test_init_checker_reports_all_namespace_package_rules` test function (BLQ14xx rules are replaced)
2. **Add** test functions for each of the 12 new rules (can group related rules into shared test functions):
   - `test_module_api_missing_all_exports` — BLQ1501
   - `test_module_api_invalid_all_format` — BLQ1502
   - `test_module_api_all_name_missing` — BLQ1503
   - `test_module_api_init_all_required` — BLQ1504
   - `test_module_api_init_reexport` — BLQ1505
   - `test_module_api_forbidden_star_import` — BLQ1506
   - `test_module_api_forbidden_parent_import` — BLQ1507
   - `test_module_api_sibling_import_form` — BLQ1508
   - `test_module_api_prefer_module_import` — BLQ1509
   - `test_module_api_import_name_not_in_all` — BLQ1510
   - `test_module_api_attribute_not_in_all` — BLQ1511
   - `test_module_api_same_hierarchy_import` — BLQ1512

3. Test infrastructure uses existing `_run_pylint()` and `_write()` helpers (lines 14-38)
4. Test pattern: write temp .py file with compact inline code, run pylint with `--disable=all --enable=<symbol>`, assert message appears
5. Cross-file tests (BLQ1510, BLQ1511) need to write multiple temp files in the same `tmp_path` tree and configure `cwd=tmp_path` in `_run_pylint`
6. Init-rules test (BLQ1504, BLQ1505) pattern: write `tmp_path/pkg/__init__.py` with content, run pylint on it
7. Passing tests (no violation expected): assert `result.returncode == 0`

---

### 7. MODIFY: ~55–80+ source modules under `src/pytest_bdd/` — add `__all__`

**Role:** Every non-`__init__.py` module must declare `__all__` with its public API.

**Data flow:** `__all__` serves as the module's public API contract — consumed by BLQ1501-BLQ1503 (enforcement), BLQ1510-BLQ1511 (cross-module validation), and Python's `from module import *`.

**Closest analog — module with existing `__all__`:** `src/pytest_bdd/plugin/pickle_runner/plugin.py:57-61`:

```python
from __future__ import annotations

from pytest_bdd.plugin.pickle_runner.plugin._plugin import PickleRunner, PickleRunnerPlugin

__all__ = ["PickleRunner", "PickleRunnerPlugin"]
```

**Closest analog — `__init__.py` with non-empty `__all__`:** `src/pytest_bdd/__init__.py:84-95`:

```python
__all__: list[str] = [
    "FeaturePathType",
    "PytestBDDStepDefinitionWarning",
    "given",
    "not_implemented",
    "scenario",
    "scenarios",
    "step",
    "then",
    "tolerant",
    "when",
]
```

**Closest analog — module without `__all__` (current state):** `src/pytest_bdd/scenario.py` — has extensive imports and defines `ScenarioFunction`, `FeaturePathType`, `Args`, `ScenarioDecorator`, `ScenarioTest`, `ScenarioFilterT`, `scenario`, `scenarios`, `get_python_name_generator`, but no `__all__` declaration.

**What needs to change for each module (pattern):**
```python
# After the module docstring, before imports, add:
__all__ = ["PublicName1", "PublicName2", ...]
```

**Key modules needing `__all__` (non-exhaustive):**
- `src/pytest_bdd/scenario.py` — exports: `ScenarioFunction`, `Args`, `FeaturePathType`, `ScenarioDecorator`, `ScenarioTest`, `ScenarioFilterT`, `scenario`, `scenarios`, `get_python_name_generator`
- `src/pytest_bdd/parser.py` — exports: `BaseParser`, `GherkinParser`, `MarkdownGherkinParser`
- `src/pytest_bdd/collector.py` — exports: `FeatureFileModule`
- `src/pytest_bdd/collector_batch.py` — exports: `FeatureBatchParser`
- `src/pytest_bdd/scenario_locator/file_locator.py` — exports: `FileScenarioLocator`
- `src/pytest_bdd/scenario_locator/url_locator.py` — exports: `UrlScenarioLocator`
- `src/pytest_bdd/steps/registry.py` — multiple exports
- `src/pytest_bdd/steps/matcher.py` — multiple exports
- `src/pytest_bdd/steps/manager.py` — exports: `StepDefinitionManager`
- `src/pytest_bdd/steps/definition.py` — exports: `Definition`
- `src/pytest_bdd/steps/decorators.py` — exports: `given`, `when`, `then`, `step`, `tolerant`, `not_implemented`
- `src/pytest_bdd/model/scenario_run.py` — exports: `Run`, `ScenarioRun`, `FeatureRuntimeBinding`
- `src/pytest_bdd/model/stash_access.py` — exports: `StashBound`
- `src/pytest_bdd/model/message_converter.py` — exports for dict ↔ messages conversion
- `src/pytest_bdd/plugin/pickle_runner/plugin.py` — **already has __all__** — pattern reference
- All other plugin modules (~50+), util modules (~15+), compatibility modules (~8+), parsers modules, model modules

**Strategy:** Automated script to:
1. Walk all `.py` files under `src/pytest_bdd/` (excluding `case/`, `script/`, `_gherkin_go/`, `__init__.py`)
2. Parse each file with `ast.parse()`, extract top-level public names (from `FunctionDef`, `AsyncFunctionDef`, `ClassDef`, `Assign` for `Name` targets, `AnnAssign`, `ImportFrom` for re-exports)
3. Filter private names (prefixed with `_`)
4. Generate candidate `__all__ = [...]`
5. Insert after module docstring, before first import

**`__init__.py` modules need `__all__ = []` instead (per BLQ1504):**
- All `__init__.py` files under `src/pytest_bdd/` (except root `src/pytest_bdd/__init__.py`) must have `__all__ = []`
- Root `src/pytest_bdd/__init__.py` is exempt from BLQ1504 (already has non-empty `__all__` as the public API facade)
- Existing non-empty `__init__.py` files (like `allure_formatter/converter/__init__.py` with `__all__ = ["convert"]`) need refactoring — either move the re-export to the facade or create a dedicated module

---

## Summary Table

| # | Action | File | Analog | Key Change |
|---|--------|------|--------|------------|
| 1 | CREATE | `src/pytest_bdd/_pylint/checkers/module_api_rules.py` | `checkers/init_rules.py` + `checkers/test_import_rules.py` | 12 rules, E9101–E9112, single checker class |
| 2 | MODIFY | `src/pytest_bdd/_pylint/__init__.py` | Same file (current) | Swap InitRulesChecker → ModuleApiRulesChecker import/registration |
| 3 | DELETE | `src/pytest_bdd/_pylint/checkers/init_rules.py` | N/A | Remove file entirely |
| 4 | MODIFY | `src/pytest_bdd/_pylint/checkers/__init__.py` | Same file (current) | No changes needed |
| 5 | MODIFY | `pyproject.toml` | Same file (current) | Remove 4 BLQ14xx symbols, add 12 BLQ15xx symbols to enable list |
| 6 | CREATE+DELETE | `src/pytest_bdd_toolchain/case/unit/test_pylint_checkers.py` | Same file (current test pattern) | Delete init_rules test, add 12 new test functions |
| 7 | MODIFY | ~55–80+ source `.py` files under `src/pytest_bdd/` | `plugin/pickle_runner/plugin.py` (__all__ example) | Add `__all__` to every non-init module; `__all__ = []` for init files |

---

## Pattern Mapping Complete

*Generated: 2026-07-02*
